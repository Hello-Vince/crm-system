import uuid

from django.db import models


class Customer(models.Model):
    """
    Customer record with visibility list.
    Multiple companies can have access to the same customer record.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    
    # Address fields for geocoding
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='USA')
    
    # Geocoded coordinates (populated by geocode-worker)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    geocoded_at = models.DateTimeField(null=True, blank=True)
    
    # JSON list of company UUIDs that can see this record (works on both PostgreSQL and SQLite)
    visible_to_company_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of company UUIDs that have visibility to this customer"
    )
    
    # Track which company created the record
    created_by_company_id = models.UUIDField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_by_company_id']),
            models.Index(fields=['email']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.email})"

    @property
    def full_address(self) -> str:
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.postal_code, self.country])
        return ', '.join(parts)
