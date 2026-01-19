"""
Kafka consumer management command for notification service.
"""
import signal
import sys

from django.core.management.base import BaseCommand

from shared_python.kafka_client import KafkaConsumer, RetryableError, PermanentError

from notifications.models import Notification


class Command(BaseCommand):
    help = 'Start Kafka consumer for notifications'

    def handle(self, *args, **options):
        consumer = KafkaConsumer(
            group_id='notification-service-group',
            topics=['crm.customer.created'],
            handler=self.handle_event,
        )

        def signal_handler(signum, frame):
            self.stdout.write('[notification-service] Shutting down...')
            consumer.stop()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        self.stdout.write('[notification-service] Starting consumer...')
        consumer.start()

    def handle_event(self, event: dict) -> None:
        """
        Handle incoming Kafka event by creating notifications.

        Raises:
            RetryableError: For database connection errors, temporary failures
            PermanentError: For data validation errors, invalid event format
        """
        try:
            event_type = event.get('event_type', 'customer_created')
            customer_id = event.get('customer_id')
            customer_name = event.get('name')
            company_id = event.get('company_id')
            visibility_list = event.get('visibility_list', [])

            # Validate required fields
            if not customer_id or not customer_name:
                raise PermanentError(f"Missing required fields: customer_id={customer_id}, customer_name={customer_name}")

            if not isinstance(visibility_list, list):
                raise PermanentError(f"visibility_list must be a list, got {type(visibility_list)}")

            # Create notification for new customer
            Notification.objects.create(
                event_type=event_type,
                title=f"New Customer: {customer_name}",
                message=f"A new customer '{customer_name}' has been added to your system.",
                visible_to_company_ids=visibility_list,
                related_entity_id=customer_id,
            )

        except Exception as e:
            # Check if it's a database-related error (retryable)
            if 'connection' in str(e).lower() or 'database' in str(e).lower():
                raise RetryableError(f"Database error creating notification: {e}") from e
            else:
                # Data validation errors, etc. - don't retry
                raise PermanentError(f"Error creating notification: {e}") from e