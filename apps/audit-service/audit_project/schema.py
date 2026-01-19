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
        - COMPANY_ADMIN: sees own company + all descendant companies
        - USER: sees only own company
        """
        # info.context is the HttpRequest object
        request = info.context
        user = getattr(request, 'user', None)
        
        if not user or not user.is_authenticated:
            return AuditLog.objects.none()
        
        # System admins see everything
        if user.role == 'SYSTEM_ADMIN':
            return AuditLog.objects.all()[:limit]
        
        # No company = no access
        if not user.company_id:
            return AuditLog.objects.none()
        
        # Filter by company_id
        # Note: For proper hierarchy support, we would need to query Identity Service
        # for descendant company IDs. For now, filtering by exact company match.
        return AuditLog.objects.filter(company_id=user.company_id)[:limit]

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
            if user.role == 'SYSTEM_ADMIN':
                return log
            
            # No company = no access
            if not user.company_id:
                return None
            
            # Check if user's company matches the log's company
            if user.company_id == log.company_id:
                return log
            
            return None
        except AuditLog.DoesNotExist:
            return None


schema = build_schema(query=Query)
