"""Audit Service GraphQL schema."""
import graphene
from graphene_django import DjangoObjectType
from graphene_federation import build_schema

from logs.models import AuditLog


class AuditLogType(DjangoObjectType):
    class Meta:
        model = AuditLog
        fields = '__all__'


class Query(graphene.ObjectType):
    audit_logs = graphene.List(AuditLogType, limit=graphene.Int(default_value=100))
    audit_log = graphene.Field(AuditLogType, id=graphene.UUID(required=True))

    def resolve_audit_logs(self, info, limit=100):
        """
        Return audit logs filtered by user's access rights.
        - SYSTEM_ADMIN: sees all logs
        - Others: see logs from any company in their hierarchy
        """
        # info.context is the HttpRequest object
        request = info.context
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return AuditLog.objects.none()

        # System admins see everything
        if user.role == "SYSTEM_ADMIN":
            return AuditLog.objects.all()[:limit]

        # No visible companies = no access
        if not user.visible_company_ids:
            return AuditLog.objects.none()

        # Filter by any of user's visible company IDs
        return AuditLog.objects.filter(company_id__in=user.visible_company_ids)[:limit]

    def resolve_audit_log(self, info, id):
        """
        Return a single audit log if user has access to it.
        """
        user = info.context.user

        if not user.is_authenticated:
            return None

        try:
            log = AuditLog.objects.get(id=id)

            # System admins see everything
            if user.role == "SYSTEM_ADMIN":
                return log

            # No visible companies = no access
            if not user.visible_company_ids:
                return None

            # Check if log's company is in user's visible companies
            if str(log.company_id) in user.visible_company_ids:
                return log

            return None
        except AuditLog.DoesNotExist:
            return None


schema = build_schema(query=Query)
