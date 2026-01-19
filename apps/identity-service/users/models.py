import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from companies.models import Company


class UserManager(BaseUserManager):
    """Custom user manager that handles optional company field."""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """Create and save a superuser (SYSTEM_ADMIN with no company)."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "SYSTEM_ADMIN")
        extra_fields.setdefault("company", None)

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with role-based access and company association.
    SYSTEM_ADMIN users don't need a company (company is nullable).
    """

    class UserRole(models.TextChoices):
        SYSTEM_ADMIN = "SYSTEM_ADMIN", "System Admin"
        COMPANY_ADMIN = "COMPANY_ADMIN", "Company Admin"
        USER = "USER", "User"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)

    # Company is nullable - SYSTEM_ADMIN users don't need a company
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # is_superuser is provided by PermissionsMixin

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"

    def get_visible_company_ids(self) -> list[uuid.UUID]:
        """
        Return list of company IDs this user can access.
        - SYSTEM_ADMIN: All companies (empty list = no filter)
        - COMPANY_ADMIN: Own company + all descendants
        - USER: Only own company
        """
        if self.role == self.UserRole.SYSTEM_ADMIN:
            return []  # Empty list signals "no filter" in managers

        if not self.company:
            return []  # No company means no access (except SYSTEM_ADMIN)

        if self.role == self.UserRole.COMPANY_ADMIN:
            return self.company.get_descendant_ids()

        # Regular USER
        return [self.company.id]
