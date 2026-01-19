from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'company_id', 'created_at', 'kafka_offset')
    list_filter = ('event_type', 'created_at')
    search_fields = ('event_type', 'company_id')
    readonly_fields = ('id', 'event_type', 'payload', 'company_id', 'kafka_offset', 'kafka_partition', 'created_at')
    
    def has_add_permission(self, request):
        return False  # Immutable - no manual creation
    
    def has_delete_permission(self, request, obj=None):
        return False  # Immutable - no deletion
