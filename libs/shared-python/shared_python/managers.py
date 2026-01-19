"""
Custom Django managers for multi-tenant visibility scoping.
Filters queries based on user's company visibility list.
"""
import uuid
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    from django.db.models import QuerySet


class VisibilityScopedManager(models.Manager):
    """
    Manager that filters records based on visibility_list M2M field.
    
    Usage:
        # In views/mutations, get user's visible company IDs
        visible_ids = request.user.get_visible_company_ids()
        
        # Query with scoping
        customers = Customer.objects.for_user(visible_ids)
    """
    
    def get_queryset(self) -> 'QuerySet':
        return super().get_queryset()
    
    def for_user(
        self,
        visible_company_ids: list[uuid.UUID],
        user_role: str | None = None
    ) -> 'QuerySet':
        """
        Filter queryset based on user's visible company IDs.
        
        Args:
            visible_company_ids: List of company UUIDs user can access.
                                 Empty list = SYSTEM_ADMIN (see all).
            user_role: Optional role string for explicit bypass check.
        
        Returns:
            Filtered QuerySet containing only visible records.
        """
        # SYSTEM_ADMIN bypass: empty list means see all records
        if not visible_company_ids or user_role == 'SYSTEM_ADMIN':
            return self.get_queryset()
        
        # Filter by visibility_list M2M containing any of user's company IDs
        return self.get_queryset().filter(
            visibility_list__id__in=visible_company_ids
        ).distinct()
    
    def for_company(
        self,
        company_id: uuid.UUID,
        include_children: bool = False
    ) -> 'QuerySet':
        """
        Filter queryset for a specific company.
        
        Args:
            company_id: The company UUID to filter by.
            include_children: If True, include records visible to child companies.
        
        Returns:
            Filtered QuerySet.
        """
        if include_children:
            # This requires fetching the company hierarchy
            # In practice, pass pre-computed IDs from Identity Service
            return self.get_queryset().filter(
                visibility_list__id=company_id
            )
        return self.get_queryset().filter(
            visibility_list__id=company_id
        )


class CompanyScopedManager(models.Manager):
    """
    Simpler manager for models with a direct company_id foreign key.
    Used in Identity Service for User model.
    """
    
    def get_queryset(self) -> 'QuerySet':
        return super().get_queryset()
    
    def for_company(self, company_id: uuid.UUID) -> 'QuerySet':
        """Filter queryset by company_id field."""
        return self.get_queryset().filter(company_id=company_id)
    
    def for_companies(self, company_ids: list[uuid.UUID]) -> 'QuerySet':
        """Filter queryset by multiple company IDs."""
        return self.get_queryset().filter(company_id__in=company_ids)
