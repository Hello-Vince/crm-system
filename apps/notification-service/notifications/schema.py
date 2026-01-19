import graphene
from graphene_django import DjangoObjectType

from .models import Notification


class NotificationType(DjangoObjectType):
    """GraphQL type for Notification model."""

    is_read = graphene.Boolean()

    class Meta:
        model = Notification
        fields = ('id', 'event_type', 'title', 'message', 'created_at')

    def resolve_is_read(self, info):
        """Check if current user has read this notification."""
        user = info.context.user
        if user and user.is_authenticated:
            return self.is_read_by(user.id)
        return False


class Query(graphene.ObjectType):
    """Queries for notifications."""

    notifications = graphene.List(
        NotificationType,
        limit=graphene.Int(default_value=20),
        unread_only=graphene.Boolean(default_value=False),
    )
    unread_notification_count = graphene.Int()

    def resolve_notifications(self, info, limit=20, unread_only=False):
        """Get notifications for the current user based on company visibility."""
        user = info.context.user

        if not user or not user.is_authenticated:
            return []

        # SYSTEM_ADMIN can see all notifications, others see only their company's notifications
        if user.role == 'SYSTEM_ADMIN':
            qs = Notification.objects.all()
        else:
            qs = Notification.objects.filter(
                visible_to_company_ids__contains=[user.company_id]
            )

        if unread_only:
            qs = qs.exclude(read_by_user_ids__contains=[user.id])

        return qs.order_by('-created_at')[:limit]

    def resolve_unread_notification_count(self, info):
        """Get count of unread notifications for current user."""
        user = info.context.user

        if not user or not user.is_authenticated:
            return 0

        # SYSTEM_ADMIN can see all notifications, others see only their company's notifications
        if user.role == 'SYSTEM_ADMIN':
            qs = Notification.objects.all()
        else:
            qs = Notification.objects.filter(
                visible_to_company_ids__contains=[user.company_id]
            )

        return qs.exclude(read_by_user_ids__contains=[user.id]).count()


class MarkNotificationRead(graphene.Mutation):
    """Mutation to mark a notification as read."""

    class Arguments:
        notification_id = graphene.UUID(required=True)

    success = graphene.Boolean()
    notification = graphene.Field(NotificationType)

    def mutate(self, root, info, notification_id):
        user = info.context.user

        if not user or not user.is_authenticated:
            raise Exception('Authentication required')

        try:
            if user.role == 'SYSTEM_ADMIN':
                notification = Notification.objects.get(id=notification_id)
            else:
                notification = Notification.objects.get(
                    id=notification_id,
                    visible_to_company_ids__contains=[user.company_id]
                )
        except Notification.DoesNotExist:
            raise Exception('Notification not found or not accessible')

        notification.mark_read_by(user.id)

        return MarkNotificationRead(success=True, notification=notification)


class Mutation(graphene.ObjectType):
    """Mutations for notifications."""

    mark_notification_read = MarkNotificationRead.Field()