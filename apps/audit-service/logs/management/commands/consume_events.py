"""
Kafka consumer management command for audit service.
"""
import signal
import sys

from django.core.management.base import BaseCommand

from shared_python.kafka_client import KafkaConsumer, RetryableError, PermanentError

from logs.models import AuditLog


class Command(BaseCommand):
    help = 'Start Kafka consumer for audit logging'

    def handle(self, *args, **options):
        consumer = KafkaConsumer(
            group_id='audit-service-group',
            topics=['crm.customer.created', 'crm.customer.updated', 'identity.company.created'],
            handler=self.handle_event,
        )
        
        def signal_handler(signum, frame):
            self.stdout.write('[audit-service] Shutting down...')
            consumer.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        self.stdout.write('[audit-service] Starting consumer...')
        consumer.start()
    
    def handle_event(self, event: dict) -> None:
        """
        Handle incoming Kafka event by storing in audit log.
        Implements idempotency via kafka topic+partition+offset check.

        Raises:
            RetryableError: For database connection errors, temporary failures
            PermanentError: For data validation errors, invalid event format
        """
        try:
            event_type = event.get('event_type', 'unknown')
            company_id = event.get('company_id')
            kafka_offset = event.get('_offset', 0)
            kafka_partition = event.get('_partition', 0)
            kafka_topic = event.get('_topic', 'unknown')

            # Validate required fields
            if not isinstance(kafka_topic, str) or not isinstance(kafka_partition, int) or not isinstance(kafka_offset, int):
                raise PermanentError(f"Invalid Kafka metadata: topic={kafka_topic}, partition={kafka_partition}, offset={kafka_offset}")

            # Check if already processed (idempotency)
            if AuditLog.objects.filter(
                kafka_topic=kafka_topic,
                kafka_partition=kafka_partition,
                kafka_offset=kafka_offset
            ).exists():
                # This is not an error - just idempotency working
                return

            # Store immutable audit log
            AuditLog.objects.create(
                event_type=event_type,
                payload=event,
                company_id=company_id,
                kafka_offset=kafka_offset,
                kafka_partition=kafka_partition,
                kafka_topic=kafka_topic,
            )

        except Exception as e:
            # Check if it's a database-related error (retryable)
            error_msg = str(e).lower()
            if ('connection' in error_msg or
                'database' in error_msg or
                'operational' in error_msg or
                'timeout' in error_msg):
                raise RetryableError(f"Database error storing audit log: {e}") from e
            else:
                # Data validation errors, etc. - don't retry
                raise PermanentError(f"Error storing audit log: {e}") from e
