import uuid

from django.db import models


class Notification(models.Model):
    """Model for storing in-app notifications."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100)  # e.g., "customer_created"
    title = models.CharField(max_length=255)
    message = models.TextField()
    visible_to_company_ids = models.JSONField(default=list)
    related_entity_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_by_user_ids = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type}: {self.title}"

    def is_read_by(self, user_id):
        """Check if a specific user has read this notification."""
        return str(user_id) in [str(uid) for uid in self.read_by_user_ids]

    def mark_read_by(self, user_id):
        """Mark notification as read by a specific user."""
        user_id_str = str(user_id)
        if user_id_str not in [str(uid) for uid in self.read_by_user_ids]:
            self.read_by_user_ids.append(user_id_str)
            self.save()

    def get_unread_count_for_user(self, user_id):
        """Get count of unread notifications for a user."""
        return Notification.objects.filter(
            visible_to_company_ids__contains=[str(user_id)]
        ).exclude(
            read_by_user_ids__contains=[str(user_id)]
        ).count()