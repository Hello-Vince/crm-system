"""
Geocode Worker - Kafka consumer for address geocoding.
Consumer Group: geocode-worker-group
"""
import signal
import sys

from shared_python.kafka_client import KafkaConsumer

from .handler import handle_customer_created

CONSUMER_GROUP = "geocode-worker-group"
TOPICS = ["crm.customer.created"]


def main() -> None:
    consumer = KafkaConsumer(
        group_id=CONSUMER_GROUP,
        topics=TOPICS,
        handler=handle_customer_created,
    )
    
    # Graceful shutdown
    def signal_handler(signum, frame):
        print(f'[{CONSUMER_GROUP}] Shutting down...')
        consumer.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    consumer.start()


if __name__ == '__main__':
    main()
