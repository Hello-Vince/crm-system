"""
Kafka producer and consumer utilities for event-driven architecture.
"""
import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable

from confluent_kafka import Consumer, Producer, KafkaError


class RetryableError(Exception):
    """Error that should trigger retry with exponential backoff."""
    pass


class PermanentError(Exception):
    """Error that should not be retried - send directly to DLQ."""
    pass


class KafkaProducer:
    """
    Kafka producer for publishing events.
    """
    _instance: 'KafkaProducer | None' = None

    def __new__(cls) -> 'KafkaProducer':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_producer()
        return cls._instance

    def _init_producer(self) -> None:
        self._producer = Producer({
            'bootstrap.servers': os.getenv(
                'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
            ),
            'client.id': 'crm-service-producer',
            'acks': 'all',
            'retries': 3,
        })

    def publish(
        self,
        topic: str,
        key: str,
        value: dict[str, Any],
    ) -> None:
        """
        Publish an event to a Kafka topic.

        Args:
            topic: Kafka topic name (e.g., 'crm.customer.created')
            key: Message key for partitioning
            value: Event payload dictionary
        """
        self._producer.produce(
            topic=topic,
            key=key.encode('utf-8'),
            value=json.dumps(value).encode('utf-8'),
            callback=self._delivery_callback,
        )
        self._producer.flush()

    def _delivery_callback(self, err: KafkaError | None, msg) -> None:
        if err:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')


class DeadLetterQueueProducer:
    """
    Kafka producer for sending failed messages to Dead Letter Queue topics.
    """
    _instance: 'DeadLetterQueueProducer | None' = None

    def __new__(cls) -> 'DeadLetterQueueProducer':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_producer()
        return cls._instance

    def _init_producer(self) -> None:
        self._producer = Producer({
            'bootstrap.servers': os.getenv(
                'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
            ),
            'client.id': 'dlq-producer',
            'acks': 'all',
            'retries': 3,
        })

    def send_to_dlq(
        self,
        original_topic: str,
        original_partition: int,
        original_offset: int,
        original_payload: dict[str, Any],
        failure_reason: str,
        retry_count: int,
        consumer_group: str,
    ) -> None:
        """
        Send a failed message to the Dead Letter Queue.

        Args:
            original_topic: Original topic the message came from
            original_partition: Original partition
            original_offset: Original offset
            original_payload: Original message payload
            failure_reason: Reason for failure
            retry_count: Number of retry attempts made
            consumer_group: Consumer group that failed to process
        """
        dlq_topic = f"{original_topic}.dlq.{consumer_group}"

        dlq_message = {
            "original_topic": original_topic,
            "original_partition": original_partition,
            "original_offset": original_offset,
            "original_payload": original_payload,
            "failure_reason": failure_reason,
            "retry_count": retry_count,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "consumer_group": consumer_group,
        }

        self._producer.produce(
            topic=dlq_topic,
            key=f"{original_topic}:{original_partition}:{original_offset}".encode('utf-8'),
            value=json.dumps(dlq_message).encode('utf-8'),
            callback=self._delivery_callback,
        )
        self._producer.flush()

    def _delivery_callback(self, err: KafkaError | None, msg) -> None:
        if err:
            print(f'DLQ message delivery failed: {err}')
        else:
            print(f'DLQ message delivered to {msg.topic()} [{msg.partition()}]')


class KafkaConsumer:
    """
    Kafka consumer for processing events with retry logic and DLQ support.
    Each worker uses a unique consumer group for fan-out.
    """

    def __init__(
        self,
        group_id: str,
        topics: list[str],
        handler: Callable[[dict[str, Any]], None],
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        retry_backoff_max: float = 60.0,
    ):
        self.group_id = group_id
        self.topics = topics
        self.handler = handler
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.retry_backoff_max = retry_backoff_max
        self._running = False

        # Metrics counters
        self.metrics = {
            'messages_processed_total': 0,
            'messages_retried_total': 0,
            'messages_failed_total': 0,
            'messages_dlq_total': 0,
        }

        self._consumer = Consumer({
            'bootstrap.servers': os.getenv(
                'KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092'
            ),
            'group.id': group_id,
            'auto.offset.reset': 'earliest',  # Start from earliest if no committed offset
            'enable.auto.commit': False,
        })

        # Initialize DLQ producer
        self._dlq_producer = DeadLetterQueueProducer()

    def _log_structured(
        self,
        level: str,
        message: str,
        topic: str = "",
        partition: int = -1,
        offset: int = -1,
        event_type: str = "",
        **extra_fields
    ) -> None:
        """Log structured JSON message for observability."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "consumer_group": self.group_id,
            "message": message,
        }

        # Add optional fields if provided
        if topic:
            log_entry["topic"] = topic
        if partition >= 0:
            log_entry["partition"] = partition
        if offset >= 0:
            log_entry["offset"] = offset
        if event_type:
            log_entry["event_type"] = event_type

        # Add any extra fields
        log_entry.update(extra_fields)

        print(json.dumps(log_entry))

    def _log_metrics(self) -> None:
        """Log current metrics counters."""
        self._log_structured(
            level="INFO",
            message="Consumer metrics update",
            type="metrics",
            **self.metrics
        )

    def _process_with_retry(self, msg, value: dict) -> bool:
        """
        Process message with exponential backoff retry.

        Returns:
            bool: True if message was successfully processed, False if sent to DLQ
        """
        original_topic = value.get('_topic', 'unknown')
        partition = value.get('_partition', -1)
        offset = value.get('_offset', -1)
        event_type = value.get('event_type', 'unknown')

        for attempt in range(self.max_retries + 1):
            try:
                self.handler(value)
                self.metrics['messages_processed_total'] += 1

                self._log_structured(
                    level="INFO",
                    message="Message processed successfully",
                    topic=original_topic,
                    partition=partition,
                    offset=offset,
                    event_type=event_type,
                    attempt=attempt
                )

                # Log metrics every 100 messages
                if self.metrics['messages_processed_total'] % 100 == 0:
                    self._log_metrics()

                return True

            except RetryableError as e:
                self.metrics['messages_retried_total'] += 1

                if attempt < self.max_retries:
                    backoff = min(self.retry_backoff_base * (2 ** attempt), self.retry_backoff_max)

                    self._log_structured(
                        level="WARNING",
                        message=f"Retryable error, will retry in {backoff}s",
                        topic=original_topic,
                        partition=partition,
                        offset=offset,
                        event_type=event_type,
                        error=str(e),
                        retry_attempt=attempt + 1,
                        backoff_seconds=backoff
                    )

                    time.sleep(backoff)
                else:
                    # Max retries exceeded - send to DLQ
                    self.metrics['messages_dlq_total'] += 1

                    self._log_structured(
                        level="CRITICAL",
                        message="Max retries exceeded, sending to DLQ",
                        topic=original_topic,
                        partition=partition,
                        offset=offset,
                        event_type=event_type,
                        error=str(e),
                        retry_count=self.max_retries
                    )

                    self._dlq_producer.send_to_dlq(
                        original_topic=original_topic,
                        original_partition=partition,
                        original_offset=offset,
                        original_payload=value,
                        failure_reason=str(e),
                        retry_count=self.max_retries,
                        consumer_group=self.group_id,
                    )
                    return False

            except PermanentError as e:
                # Don't retry - send directly to DLQ
                self.metrics['messages_failed_total'] += 1
                self.metrics['messages_dlq_total'] += 1

                self._log_structured(
                    level="ERROR",
                    message="Permanent error, sending to DLQ",
                    topic=original_topic,
                    partition=partition,
                    offset=offset,
                    event_type=event_type,
                    error=str(e)
                )

                self._dlq_producer.send_to_dlq(
                    original_topic=original_topic,
                    original_partition=partition,
                    original_offset=offset,
                    original_payload=value,
                    failure_reason=str(e),
                    retry_count=0,
                    consumer_group=self.group_id,
                )
                return False

            except Exception as e:
                # Unknown exception - treat as retryable for safety
                self.metrics['messages_retried_total'] += 1

                if attempt < self.max_retries:
                    backoff = min(self.retry_backoff_base * (2 ** attempt), self.retry_backoff_max)

                    self._log_structured(
                        level="WARNING",
                        message=f"Unexpected error, will retry in {backoff}s",
                        topic=original_topic,
                        partition=partition,
                        offset=offset,
                        event_type=event_type,
                        error=str(e),
                        retry_attempt=attempt + 1,
                        backoff_seconds=backoff
                    )

                    time.sleep(backoff)
                else:
                    # Max retries exceeded - send to DLQ
                    self.metrics['messages_dlq_total'] += 1

                    self._log_structured(
                        level="CRITICAL",
                        message="Max retries exceeded for unexpected error, sending to DLQ",
                        topic=original_topic,
                        partition=partition,
                        offset=offset,
                        event_type=event_type,
                        error=str(e),
                        retry_count=self.max_retries
                    )

                    self._dlq_producer.send_to_dlq(
                        original_topic=original_topic,
                        original_partition=partition,
                        original_offset=offset,
                        original_payload=value,
                        failure_reason=str(e),
                        retry_count=self.max_retries,
                        consumer_group=self.group_id,
                    )
                    return False

        return False

    def start(self) -> None:
        """Start consuming messages in a loop."""
        self._consumer.subscribe(self.topics)
        self._running = True

        self._log_structured(
            level="INFO",
            message=f"Starting consumer for topics: {self.topics}",
            max_retries=self.max_retries,
            retry_backoff_base=self.retry_backoff_base,
            retry_backoff_max=self.retry_backoff_max
        )

        while self._running:
            msg = self._consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                self._log_structured(
                    level="ERROR",
                    message=f"Kafka consumer error: {msg.error()}"
                )
                continue

            try:
                # Parse message value
                value = json.loads(msg.value().decode('utf-8'))

                # Add metadata to the event
                value['_offset'] = msg.offset()
                value['_partition'] = msg.partition()
                value['_topic'] = msg.topic()

                # Infer event_type from topic if not present
                if 'event_type' not in value:
                    value['event_type'] = msg.topic()

                # Process message with retry logic
                success = self._process_with_retry(msg, value)

                if success:
                    # Commit offset only after successful processing (including DLQ sends)
                    self._consumer.commit(asynchronous=False)

            except Exception as e:
                # This should not happen as _process_with_retry handles all exceptions
                # But as a safety net, log and continue
                import traceback
                self._log_structured(
                    level="CRITICAL",
                    message=f"Unexpected error in message processing loop: {e}",
                    traceback=traceback.format_exc()
                )
                # Don't commit offset on unexpected error
    
    def stop(self) -> None:
        """Stop the consumer loop."""
        self._running = False

        # Log final metrics before shutdown
        self._log_metrics()
        self._log_structured(
            level="INFO",
            message="Consumer stopping"
        )

        self._consumer.close()
