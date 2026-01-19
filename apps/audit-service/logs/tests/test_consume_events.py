"""
Tests for audit service Kafka consumer.
Tests idempotency, error handling, and event processing.
"""
import uuid
from unittest.mock import patch

import pytest
from django.db import IntegrityError
from django.test import TestCase

from logs.management.commands.consume_events import Command
from logs.models import AuditLog
from shared_python.kafka_client import PermanentError, RetryableError


class TestAuditConsumerIdempotency(TestCase):
    """Test idempotency based on topic+partition+offset."""

    def setUp(self):
        self.command = Command()

    def test_duplicate_message_skipped(self):
        """Test that duplicate messages are skipped based on topic+partition+offset."""
        # Create existing audit log
        AuditLog.objects.create(
            event_type="crm.customer.created",
            payload={"test": "data"},
            company_id=uuid.uuid4(),
            kafka_offset=100,
            kafka_partition=0,
            kafka_topic="crm.customer.created",
        )

        # Attempt to process same message again
        event = {
            "event_type": "crm.customer.created",
            "company_id": str(uuid.uuid4()),
            "test": "new data",
            "_offset": 100,
            "_partition": 0,
            "_topic": "crm.customer.created",
        }

        # Should not raise error and should not create duplicate
        self.command.handle_event(event)

        # Should still only have one log
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_same_offset_different_partition_allowed(self):
        """Test that same offset on different partition is allowed."""
        # Create existing audit log
        AuditLog.objects.create(
            event_type="crm.customer.created",
            payload={"test": "data"},
            company_id=uuid.uuid4(),
            kafka_offset=100,
            kafka_partition=0,
            kafka_topic="crm.customer.created",
        )

        # Process message with same offset but different partition
        event = {
            "event_type": "crm.customer.created",
            "company_id": str(uuid.uuid4()),
            "test": "data partition 1",
            "_offset": 100,
            "_partition": 1,  # Different partition
            "_topic": "crm.customer.created",
        }

        self.command.handle_event(event)

        # Should have two logs now
        self.assertEqual(AuditLog.objects.count(), 2)

    def test_same_partition_different_topic_allowed(self):
        """Test that same partition+offset on different topic is allowed."""
        # Create existing audit log
        AuditLog.objects.create(
            event_type="identity.company.created",
            payload={"test": "company data"},
            company_id=uuid.uuid4(),
            kafka_offset=100,
            kafka_partition=0,
            kafka_topic="identity.company.created",
        )

        # Process message with same offset/partition but different topic
        event = {
            "event_type": "crm.customer.created",
            "company_id": str(uuid.uuid4()),
            "test": "customer data",
            "_offset": 100,
            "_partition": 0,
            "_topic": "crm.customer.created",  # Different topic
        }

        self.command.handle_event(event)

        # Should have two logs now
        self.assertEqual(AuditLog.objects.count(), 2)

    def test_unique_constraint_enforced(self):
        """Test that the unique constraint prevents duplicate insertions."""
        # Create first log
        AuditLog.objects.create(
            event_type="test.event",
            payload={"test": "data"},
            kafka_offset=50,
            kafka_partition=1,
            kafka_topic="test.topic",
        )

        # Attempt to create duplicate - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            AuditLog.objects.create(
                event_type="different.event",
                payload={"different": "data"},
                kafka_offset=50,  # Same offset
                kafka_partition=1,  # Same partition
                kafka_topic="test.topic",  # Same topic
            )


class TestAuditConsumerEventProcessing(TestCase):
    """Test event processing functionality."""

    def setUp(self):
        self.command = Command()

    def test_new_message_processed_successfully(self):
        """Test that new messages are processed and stored."""
        customer_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())

        event = {
            "event_type": "crm.customer.created",
            "company_id": company_id,
            "customer_id": customer_id,
            "name": "Test Customer",
            "_offset": 200,
            "_partition": 2,
            "_topic": "crm.customer.created",
        }

        self.command.handle_event(event)

        # Should have created one log
        self.assertEqual(AuditLog.objects.count(), 1)

        log = AuditLog.objects.first()
        self.assertEqual(log.event_type, "crm.customer.created")
        self.assertEqual(log.kafka_offset, 200)
        self.assertEqual(log.kafka_partition, 2)
        self.assertEqual(log.kafka_topic, "crm.customer.created")
        self.assertEqual(log.payload["customer_id"], customer_id)

    def test_event_without_company_id_stored(self):
        """Test that events without company_id are still stored."""
        event = {
            "event_type": "system.event",
            "_offset": 300,
            "_partition": 0,
            "_topic": "system.events",
        }

        self.command.handle_event(event)

        log = AuditLog.objects.first()
        self.assertIsNone(log.company_id)
        self.assertEqual(log.event_type, "system.event")


class TestAuditConsumerErrorHandling(TestCase):
    """Test error handling and classification."""

    def setUp(self):
        self.command = Command()

    def test_invalid_kafka_metadata_raises_permanent_error(self):
        """Test that invalid Kafka metadata raises PermanentError."""
        event = {
            "event_type": "test.event",
            "_offset": None,  # Invalid - should be int
            "_partition": 0,
            "_topic": "test.topic",
        }

        with self.assertRaises(PermanentError) as context:
            self.command.handle_event(event)

        self.assertIn("Invalid Kafka metadata", str(context.exception))

    def test_missing_offset_uses_default(self):
        """Test that missing offset defaults to 0."""
        event = {
            "event_type": "test.event",
            # No _offset provided
            "_partition": 0,
            "_topic": "test.topic",
        }

        self.command.handle_event(event)

        log = AuditLog.objects.first()
        self.assertEqual(log.kafka_offset, 0)

    @patch("logs.models.AuditLog.objects.filter")
    def test_database_connection_error_raises_retryable(self, mock_filter):
        """Test that database connection errors are retryable."""
        mock_filter.side_effect = Exception("connection refused")

        event = {
            "event_type": "crm.customer.created",
            "_offset": 100,
            "_partition": 0,
            "_topic": "crm.customer.created",
        }

        with self.assertRaises(RetryableError) as context:
            self.command.handle_event(event)

        self.assertIn("Database error", str(context.exception))

    @patch("logs.models.AuditLog.objects.filter")
    def test_database_timeout_error_raises_retryable(self, mock_filter):
        """Test that database timeout errors are retryable."""
        mock_filter.side_effect = Exception("timeout error")

        event = {
            "event_type": "crm.customer.created",
            "_offset": 100,
            "_partition": 0,
            "_topic": "crm.customer.created",
        }

        with self.assertRaises(RetryableError) as context:
            self.command.handle_event(event)

        self.assertIn("Database error", str(context.exception))


class TestAuditLogModel(TestCase):
    """Test AuditLog model functionality."""

    def test_audit_log_creation(self):
        """Test basic audit log creation."""
        log = AuditLog.objects.create(
            event_type="test.event",
            payload={"key": "value"},
            company_id=uuid.uuid4(),
            kafka_offset=1,
            kafka_partition=0,
            kafka_topic="test.topic",
        )

        self.assertIsNotNone(log.id)
        self.assertIsNotNone(log.created_at)
        self.assertEqual(log.event_type, "test.event")

    def test_audit_log_str_representation(self):
        """Test audit log string representation."""
        log = AuditLog.objects.create(
            event_type="test.event",
            payload={},
            kafka_offset=1,
            kafka_partition=0,
            kafka_topic="test.topic",
        )

        str_repr = str(log)
        self.assertIn("test.event", str_repr)

    def test_audit_log_ordering(self):
        """Test that audit logs are ordered by created_at descending."""
        AuditLog.objects.create(
            event_type="first",
            payload={},
            kafka_offset=1,
            kafka_partition=0,
            kafka_topic="test",
        )
        AuditLog.objects.create(
            event_type="second",
            payload={},
            kafka_offset=2,
            kafka_partition=0,
            kafka_topic="test",
        )

        logs = list(AuditLog.objects.all())
        # Most recent first
        self.assertEqual(logs[0].event_type, "second")
        self.assertEqual(logs[1].event_type, "first")
