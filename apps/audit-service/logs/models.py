import uuid

from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit log for all Kafka events.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, db_index=True)
    payload = models.JSONField()
    company_id = models.UUIDField(db_index=True, null=True)
    kafka_offset = models.BigIntegerField()
    kafka_partition = models.IntegerField()
    kafka_topic = models.CharField(max_length=255, default='unknown')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['company_id', 'created_at']),
        ]
        # Unique constraint on topic + partition + offset
        constraints = [
            models.UniqueConstraint(
                fields=['kafka_topic', 'kafka_partition', 'kafka_offset'],
                name='unique_kafka_message'
            )
        ]
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.event_type} at {self.created_at}"
