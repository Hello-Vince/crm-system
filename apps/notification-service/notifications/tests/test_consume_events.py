"""
Tests for notification service Kafka consumer.
"""
import uuid
from unittest.mock import Mock, patch

from django.db import InterfaceError, OperationalError
from django.test import TestCase

from notifications.management.commands.consume_events import Command
from shared_python.kafka_client import PermanentError, RetryableError


class TestNotificationConsumerErrorClassification(TestCase):
    """Test error classification in notification consumer."""

    def setUp(self):
        self.command = Command()

    def test_missing_customer_id_raises_permanent_error(self):
        """Test that missing customer_id raises PermanentError."""
        event = {
            "event_type": "crm.customer.created",
            "name": "Test Customer",
            "visibility_list": [str(uuid.uuid4())],
            # Missing customer_id
        }

        with self.assertRaises(PermanentError) as context:
            self.command.handle_event(event)

        self.assertIn("Missing required fields", str(context.exception))

    def test_missing_customer_name_raises_permanent_error(self):
        """Test that missing customer name raises PermanentError."""
        event = {
            "event_type": "crm.customer.created",
            "customer_id": str(uuid.uuid4()),
            # Missing name
            "visibility_list": [str(uuid.uuid4())],
        }

        with self.assertRaises(PermanentError) as context:
            self.command.handle_event(event)

        self.assertIn("Missing required fields", str(context.exception))

    def test_invalid_visibility_list_type_raises_permanent_error(self):
        """Test that invalid visibility_list type raises PermanentError."""
        event = {
            "event_type": "crm.customer.created",
            "customer_id": str(uuid.uuid4()),
            "name": "Test Customer",
            "visibility_list": "not-a-list",  # Invalid type
        }

        with self.assertRaises(PermanentError) as context:
            self.command.handle_event(event)

        self.assertIn("visibility_list must be a list", str(context.exception))

    @patch("notifications.models.Notification.objects.create")
    def test_database_operational_error_raises_retryable_error(self, mock_create):
        """Test that OperationalError (connection issues) raises RetryableError."""
        mock_create.side_effect = OperationalError("database connection lost")

        event = {
            "event_type": "crm.customer.created",
            "customer_id": str(uuid.uuid4()),
            "name": "Test Customer",
            "visibility_list": [str(uuid.uuid4())],
        }

        with self.assertRaises(RetryableError) as context:
            self.command.handle_event(event)

        self.assertIn("Database error", str(context.exception))

    @patch("notifications.models.Notification.objects.create")
    def test_connection_error_raises_retryable_error(self, mock_create):
        """Test that connection errors raise RetryableError."""
        mock_create.side_effect = Exception("connection refused")

        event = {
            "event_type": "crm.customer.created",
            "customer_id": str(uuid.uuid4()),
            "name": "Test Customer",
            "visibility_list": [str(uuid.uuid4())],
        }

        with self.assertRaises(RetryableError) as context:
            self.command.handle_event(event)

        self.assertIn("Database error", str(context.exception))

    @patch("notifications.models.Notification.objects.create")
    def test_non_database_error_raises_permanent_error(self, mock_create):
        """Test that non-database errors raise PermanentError."""
        mock_create.side_effect = Exception("Some validation error")

        event = {
            "event_type": "crm.customer.created",
            "customer_id": str(uuid.uuid4()),
            "name": "Test Customer",
            "visibility_list": [str(uuid.uuid4())],
        }

        with self.assertRaises(PermanentError) as context:
            self.command.handle_event(event)

        self.assertIn("Error creating notification", str(context.exception))

    @patch("notifications.models.Notification.objects.create")
    def test_successful_notification_creation(self, mock_create):
        """Test successful notification creation."""
        mock_create.return_value = Mock()

        customer_id = str(uuid.uuid4())
        company_id = str(uuid.uuid4())

        event = {
            "event_type": "crm.customer.created",
            "customer_id": customer_id,
            "name": "Test Customer",
            "visibility_list": [company_id],
        }

        # Should not raise any exception
        self.command.handle_event(event)

        # Verify notification was created with correct parameters
        mock_create.assert_called_once()
        call_args = mock_create.call_args

        self.assertEqual(call_args[1]["event_type"], "crm.customer.created")
        self.assertEqual(call_args[1]["title"], "New Customer: Test Customer")
        self.assertEqual(
            call_args[1]["message"],
            "A new customer 'Test Customer' has been added to your system.",
        )
        self.assertEqual(call_args[1]["visible_to_company_ids"], [company_id])
        self.assertEqual(call_args[1]["related_entity_id"], customer_id)

    @patch("notifications.models.Notification.objects.create")
    def test_notification_creation_with_multiple_visibility_companies(
        self, mock_create
    ):
        """Test notification creation with multiple companies in visibility list."""
        mock_create.return_value = Mock()

        customer_id = str(uuid.uuid4())
        company_id1 = str(uuid.uuid4())
        company_id2 = str(uuid.uuid4())

        event = {
            "event_type": "crm.customer.created",
            "customer_id": customer_id,
            "name": "Test Customer",
            "visibility_list": [company_id1, company_id2],
        }

        self.command.handle_event(event)

        mock_create.assert_called_once()
        call_args = mock_create.call_args

        self.assertEqual(
            call_args[1]["visible_to_company_ids"], [company_id1, company_id2]
        )
