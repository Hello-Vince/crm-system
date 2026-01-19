import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock, call
from shared_python.kafka_client import (
    KafkaConsumer, RetryableError, PermanentError, DeadLetterQueueProducer
)


class TestKafkaConsumerRetry:
    def test_retry_with_exponential_backoff(self):
        """Test exponential backoff retry logic"""
        handler = Mock(side_effect=[
            RetryableError("Temporary error"),
            RetryableError("Temporary error"),
            None  # Success on third attempt
        ])

        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=handler,
            max_retries=3,
            retry_backoff_base=0.1  # Fast for testing
        )

        msg = MagicMock()
        msg.offset.return_value = 1
        msg.partition.return_value = 0
        msg.topic.return_value = "test.topic"
        msg.value.return_value = b'{"test": "data"}'

        value = {"_topic": "test.topic", "_partition": 0, "_offset": 1}

        start_time = time.time()
        result = consumer._process_with_retry(msg, value)
        elapsed = time.time() - start_time

        assert result is True
        assert handler.call_count == 3
        # Should have waited ~0.1s + ~0.2s = ~0.3s total
        assert elapsed >= 0.2  # Allow some margin

    def test_max_retries_exceeded_sends_to_dlq(self):
        """Test that max retries exceeded sends message to DLQ"""
        handler = Mock(side_effect=RetryableError("Always fails"))

        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=handler,
            max_retries=2
        )

        with patch.object(consumer.dlq_producer, 'publish_dlq') as mock_dlq:
            msg = MagicMock()
            msg.offset.return_value = 1
            msg.partition.return_value = 0
            msg.topic.return_value = "test.topic"

            value = {"_topic": "test.topic", "_partition": 0, "_offset": 1}

            result = consumer._process_with_retry(msg, value)

            assert result is False
            assert handler.call_count == 3  # Initial + 2 retries
            assert mock_dlq.called
            assert consumer.metrics['messages_dlq_total'] == 1

    def test_permanent_error_sent_directly_to_dlq(self):
        """Test that permanent errors are sent directly to DLQ without retries"""
        handler = Mock(side_effect=PermanentError("Permanent error"))

        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=handler,
            max_retries=3
        )

        with patch.object(consumer.dlq_producer, 'publish_dlq') as mock_dlq:
            msg = MagicMock()
            msg.offset.return_value = 1
            msg.partition.return_value = 0
            msg.topic.return_value = "test.topic"

            value = {"_topic": "test.topic", "_partition": 0, "_offset": 1}

            result = consumer._process_with_retry(msg, value)

            assert result is False
            assert handler.call_count == 1  # Only initial attempt
            assert mock_dlq.called
            assert consumer.metrics['messages_dlq_total'] == 1

    def test_retryable_error_retries_until_success(self):
        """Test that retryable errors eventually succeed"""
        handler = Mock(side_effect=[
            RetryableError("First attempt fails"),
            RetryableError("Second attempt fails"),
            None  # Third attempt succeeds
        ])

        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=handler,
            max_retries=3
        )

        msg = MagicMock()
        msg.offset.return_value = 1
        msg.partition.return_value = 0
        msg.topic.return_value = "test.topic"

        value = {"_topic": "test.topic", "_partition": 0, "_offset": 1}

        result = consumer._process_with_retry(msg, value)

        assert result is True
        assert handler.call_count == 3
        assert consumer.metrics['messages_processed_total'] == 1
        assert consumer.metrics['messages_retried_total'] == 2

    def test_metrics_counters_increment_correctly(self):
        """Test that metrics counters are incremented properly"""
        handler = Mock(side_effect=[
            RetryableError("Fail"),
            RetryableError("Fail"),
            RetryableError("Fail")  # Will exceed max_retries=2
        ])

        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=handler,
            max_retries=2
        )

        with patch.object(consumer.dlq_producer, 'publish_dlq'):
            msg = MagicMock()
            msg.offset.return_value = 1
            msg.partition.return_value = 0
            msg.topic.return_value = "test.topic"

            value = {"_topic": "test.topic", "_partition": 0, "_offset": 1}

            consumer._process_with_retry(msg, value)

            assert consumer.metrics['messages_retried_total'] == 2
            assert consumer.metrics['messages_failed_total'] == 1
            assert consumer.metrics['messages_dlq_total'] == 1
            assert consumer.metrics['messages_processed_total'] == 0

    def test_successful_processing_no_retries(self):
        """Test successful processing doesn't increment retry counters"""
        handler = Mock(return_value=None)  # Success

        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=handler
        )

        msg = MagicMock()
        msg.offset.return_value = 1
        msg.partition.return_value = 0
        msg.topic.return_value = "test.topic"

        value = {"_topic": "test.topic", "_partition": 0, "_offset": 1}

        result = consumer._process_with_retry(msg, value)

        assert result is True
        assert consumer.metrics['messages_processed_total'] == 1
        assert consumer.metrics['messages_retried_total'] == 0
        assert consumer.metrics['messages_failed_total'] == 0


class TestDeadLetterQueueProducer:
    def test_publish_dlq_formats_message_correctly(self):
        """Test that DLQ messages are formatted correctly"""
        with patch('shared_python.kafka_client.KafkaProducer') as mock_producer_class:
            mock_producer = Mock()
            mock_producer_class.return_value = mock_producer

            dlq_producer = DeadLetterQueueProducer()

            dlq_producer.publish_dlq(
                original_topic="crm.customer.created",
                consumer_group="test-group",
                original_msg_value={"test": "data"},
                failure_reason="Test failure",
                retry_count=2,
                original_offset=100,
                original_partition=0
            )

            # Verify the call
            assert mock_producer.publish.called
            call_args = mock_producer.publish.call_args
            topic, key, payload = call_args[0]

            # Check topic naming convention
            assert topic == "crm.customer.created.dlq.test-group"

            # Check payload structure
            assert payload['original_topic'] == "crm.customer.created"
            assert payload['original_partition'] == 0
            assert payload['original_offset'] == 100
            assert payload['original_payload'] == {"test": "data"}
            assert payload['failure_reason'] == "Test failure"
            assert payload['retry_count'] == 2
            assert payload['consumer_group'] == "test-group"
            assert 'failed_at' in payload

    def test_dlq_producer_singleton(self):
        """Test that DLQ producer is a singleton"""
        producer1 = DeadLetterQueueProducer()
        producer2 = DeadLetterQueueProducer()

        assert producer1 is producer2


class TestKafkaConsumerMetrics:
    def test_metrics_logging_format(self):
        """Test that metrics are logged in structured format"""
        consumer = KafkaConsumer(
            group_id="test-group",
            topics=["test.topic"],
            handler=Mock()
        )

        consumer.metrics = {
            'messages_processed_total': 10,
            'messages_retried_total': 5,
            'messages_failed_total': 2,
            'messages_dlq_total': 1,
        }

        with patch('shared_python.kafka_client._log_structured') as mock_log:
            consumer._log_metrics()

            mock_log.assert_called_once()
            call_args = mock_log.call_args

            assert call_args[1]['level'] == 'INFO'
            assert call_args[1]['consumer_group'] == 'test-group'
            assert call_args[1]['type'] == 'metrics'
            assert call_args[1]['metrics'] == consumer.metrics


class TestErrorClassification:
    def test_retryable_error_inheritance(self):
        """Test that RetryableError is an Exception"""
        error = RetryableError("test")
        assert isinstance(error, Exception)

    def test_permanent_error_inheritance(self):
        """Test that PermanentError is an Exception"""
        error = PermanentError("test")
        assert isinstance(error, Exception)

    def test_error_messages_preserved(self):
        """Test that error messages are preserved"""
        retryable = RetryableError("retry message")
        permanent = PermanentError("permanent message")

        assert str(retryable) == "retry message"
        assert str(permanent) == "permanent message"