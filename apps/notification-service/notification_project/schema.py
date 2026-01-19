"""Notification service GraphQL schema."""
import graphene
from graphene_federation import build_schema

from notifications.schema import Query as NotificationsQuery, Mutation as NotificationsMutation


class Query(NotificationsQuery, graphene.ObjectType):
    """Root Query for notification service."""
    pass


class Mutation(NotificationsMutation, graphene.ObjectType):
    """Root Mutation for notification service."""
    pass


schema = build_schema(query=Query, mutation=Mutation)