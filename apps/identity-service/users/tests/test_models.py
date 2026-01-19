"""
Tests for User model visibility and access control.
"""
from django.test import TestCase

from companies.models import Company
from users.models import User


class TestUserVisibleCompanyIds(TestCase):
    """Test user visibility based on role and company hierarchy."""

    def setUp(self):
        # Create company hierarchy for testing
        self.parent = Company.objects.create(name="Parent Corp")
        self.child1 = Company.objects.create(name="Child 1", parent=self.parent)
        self.child2 = Company.objects.create(name="Child 2", parent=self.parent)

    def test_system_admin_returns_empty_list(self):
        """System admin sees all records (empty list = no filter)."""
        user = User.objects.create_user(
            email="admin@test.com",
            password="test123",
            role=User.UserRole.SYSTEM_ADMIN,
        )
        self.assertEqual(user.get_visible_company_ids(), [])

    def test_company_admin_returns_descendant_ids(self):
        """Company admin sees own company + all descendants."""
        user = User.objects.create_user(
            email="admin@test.com",
            password="test123",
            company=self.parent,
            role=User.UserRole.COMPANY_ADMIN,
        )
        visible_ids = user.get_visible_company_ids()
        self.assertIn(self.parent.id, visible_ids)
        self.assertIn(self.child1.id, visible_ids)
        self.assertIn(self.child2.id, visible_ids)
        self.assertEqual(len(visible_ids), 3)

    def test_regular_user_returns_own_company_id(self):
        """Regular user sees only own company."""
        user = User.objects.create_user(
            email="user@test.com",
            password="test123",
            company=self.child1,
            role=User.UserRole.USER,
        )
        self.assertEqual(user.get_visible_company_ids(), [self.child1.id])

    def test_user_without_company_returns_empty_list(self):
        """User without company association returns empty list."""
        user = User.objects.create_user(
            email="user@test.com",
            password="test123",
            role=User.UserRole.USER,
        )
        self.assertEqual(user.get_visible_company_ids(), [])


class TestUserCreation(TestCase):
    """Test user creation functionality."""

    def test_create_user_with_email(self):
        """Test creating a user with email."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            email="super@example.com",
            password="superpass123",
        )
        self.assertEqual(user.email, "super@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertEqual(user.role, User.UserRole.SYSTEM_ADMIN)

    def test_user_str_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        # User.__str__ returns "email (role)"
        self.assertIn("test@example.com", str(user))
        self.assertIn("User", str(user))
