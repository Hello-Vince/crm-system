"""
Tests for Customer GraphQL queries and access control.
"""

import uuid
from unittest.mock import Mock

from django.test import TestCase
from graphene.test import Client

from crm_project.schema import schema
from customers.models import Customer


class TestCustomerQueryAccessControl(TestCase):
    """Test customer query access control based on visibility."""

    def setUp(self):
        self.parent_company_id = uuid.uuid4()
        self.child_company_id = uuid.uuid4()

        self.parent_customer = Customer.objects.create(
            name="Parent Customer",
            email="parent@test.com",
            address_line1="123 Parent St",
            city="Parent City",
            state="PS",
            postal_code="11111",
            created_by_company_id=self.parent_company_id,
            visible_to_company_ids=[str(self.parent_company_id)],
        )

        self.child_customer = Customer.objects.create(
            name="Child Customer",
            email="child@test.com",
            address_line1="456 Child St",
            city="Child City",
            state="CS",
            postal_code="22222",
            created_by_company_id=self.child_company_id,
            visible_to_company_ids=[str(self.child_company_id)],
        )

        self.shared_customer = Customer.objects.create(
            name="Shared Customer",
            email="shared@test.com",
            address_line1="789 Shared St",
            city="Shared City",
            state="SS",
            postal_code="33333",
            created_by_company_id=self.parent_company_id,
            visible_to_company_ids=[
                str(self.parent_company_id),
                str(self.child_company_id),
            ],
        )

    def _create_mock_request(self, user):
        request = Mock()
        request.user = user
        return request

    def test_system_admin_sees_all_customers(self):
        """System admin can see all customers."""
        user = Mock()
        user.is_authenticated = True
        user.role = "SYSTEM_ADMIN"
        user.company_id = None

        query = """
            query {
                customers {
                    id
                    name
                }
            }
        """

        client = Client(schema)
        result = client.execute(query, context_value=self._create_mock_request(user))

        self.assertNotIn("errors", result)
        self.assertEqual(len(result["data"]["customers"]), 3)

    def test_unauthenticated_user_sees_nothing(self):
        """Unauthenticated users see empty customer list."""
        user = Mock()
        user.is_authenticated = False

        query = """
            query {
                customers {
                    id
                    name
                }
            }
        """

        client = Client(schema)
        result = client.execute(query, context_value=self._create_mock_request(user))

        self.assertNotIn("errors", result)
        self.assertEqual(result["data"]["customers"], [])


class TestCustomerModel(TestCase):
    """Test Customer model functionality."""

    def test_customer_creation(self):
        """Test basic customer creation."""
        company_id = uuid.uuid4()
        customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            address_line1="123 Test St",
            city="Test City",
            state="TS",
            postal_code="12345",
            created_by_company_id=company_id,
            visible_to_company_ids=[str(company_id)],
        )

        self.assertIsNotNone(customer.id)
        self.assertEqual(customer.name, "Test Customer")

    def test_customer_full_address(self):
        """Test full address property."""
        customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            address_line1="123 Test St",
            address_line2="Suite 100",
            city="Test City",
            state="TS",
            postal_code="12345",
            country="USA",
            created_by_company_id=uuid.uuid4(),
        )

        self.assertIn("123 Test St", customer.full_address)
        self.assertIn("Suite 100", customer.full_address)
