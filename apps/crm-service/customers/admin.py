from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'city', 'state', 'created_at')
    list_filter = ('state', 'country', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('visible_to_company_ids',)
