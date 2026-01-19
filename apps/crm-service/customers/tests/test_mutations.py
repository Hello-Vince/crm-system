"""
Tests for Customer mutations.
"""
import uuid
from unittest.mock import Mock, patch

from django.test import TestCase

from customers.models import Customer
from customers.mutations import CreateCustomer


class TestCreateCustomerMutation(TestCase):
    """Test CreateCustomer mutation."""

    def setUp(self):
        self.company_id = uuid.uuid4()
        self.parent_company_id = uuid.uuid4()
        self.child_company_id = uuid.uuid4()

    def test_create_customer_requires_authentication(self):
        """Mutation should fail without authentication."""
        user = Mock()
        user.is_authenticated = False

        info = Mock()
        info.context = Mock()
        info.context.user = user

        mutation = CreateCustomer()
        input_data = Mock()
        input_data.name = "Test Customer"
        input_data.email = "test@test.com"
        input_data.address_line1 = "123 Main St"
        input_data.city = "Test City"
        input_data.state = "TS"
        input_data.postal_code = "12345"
        input_data.country = "USA"
        input_data.phone = None
        input_data.address_line2 = None
        input_data.visibility_company_ids = None

        with self.assertRaises(Exception) as context:
            mutation.mutate(root=None, info=info, input=input_data)

        self.assertIn("Authentication required", str(context.exception))

    def test_create_customer_requires_company(self):
        """Mutation should fail if user has no company."""
        user = Mock()
        user.is_authenticated = True
        user.company_id = None

        info = Mock()
        info.context = Mock()
        info.context.user = user

        mutation = CreateCustomer()
        input_data = Mock()
        input_data.name = "Test Customer"
        input_data.email = "test@test.com"
        input_data.address_line1 = "123 Main St"
        input_data.city = "Test City"
        input_data.state = "TS"
        input_data.postal_code = "12345"
        input_data.country = "USA"
        input_data.phone = None
        input_data.address_line2 = None
        input_data.visibility_company_ids = None

        with self.assertRaises(Exception) as context:
            mutation.mutate(root=None, info=info, input=input_data)

        self.assertIn("must belong to a company", str(context.exception))

    @patch("customers.mutations.KafkaProducer")
    def test_create_customer_publishes_kafka_event(self, mock_kafka_producer_class):
        """Mutation should publish Kafka event after successful creation."""
        # Setup mock user
        user = Mock()
        user.is_authenticated = True
        user.company_id = self.company_id

        info = Mock()
        info.context = Mock()
        info.context.user = user

        # Setup mock Kafka producer
        mock_producer = Mock()
        mock_kafka_producer_class.return_value = mock_producer

        mutation = CreateCustomer()
        input_data = Mock()
        input_data.name = "Test Customer"
        input_data.email = "test@test.com"
        input_data.address_line1 = "123 Main St"
        input_data.city = "Test City"
        input_data.state = "TS"
        input_data.postal_code = "12345"
        input_data.country = "USA"
        input_data.phone = None
        input_data.address_line2 = None
        input_data.visibility_company_ids = None

        result = mutation.mutate(root=None, info=info, input=input_data)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.customer)

        # Verify customer was created in database
        customer = Customer.objects.get(id=result.customer.id)
        self.assertEqual(customer.name, "Test Customer")
        self.assertEqual(customer.email, "test@test.com")
        self.assertEqual(customer.created_by_company_id, self.company_id)

        # Verify Kafka event was published
        mock_producer.publish.assert_called_once()

    @patch("customers.mutations.KafkaProducer")
    def test_visibility_list_includes_creator_company(self, mock_kafka_producer_class):
        """Customer visibility list should include creator's company."""
        mock_kafka_producer_class.return_value = Mock()

        user = Mock()
        user.is_authenticated = True
        user.company_id = self.company_id

        info = Mock()
        info.context = Mock()
        info.context.user = user

        mutation = CreateCustomer()
        input_data = Mock()
        input_data.name = "Test Customer"
        input_data.email = "test@test.com"
        input_data.address_line1 = "123 Main St"
        input_data.city = "Test City"
        input_data.state = "TS"
        input_data.postal_code = "12345"
        input_data.country = "USA"
        input_data.phone = None
        input_data.address_line2 = None
        input_data.visibility_company_ids = None

        result = mutation.mutate(root=None, info=info, input=input_data)

        customer = Customer.objects.get(id=result.customer.id)
        # visible_to_company_ids stores strings in JSONField
        self.assertIn(str(self.company_id), customer.visible_to_company_ids)

    @patch("customers.mutations.KafkaProducer")
    def test_visibility_list_includes_additional_companies(self, mock_kafka_producer_class):
        """Customer visibility list should include specified additional companies."""
        mock_kafka_producer_class.return_value = Mock()

        user = Mock()
        user.is_authenticated = True
        user.company_id = self.company_id

        info = Mock()
        info.context = Mock()
        info.context.user = user

        mutation = CreateCustomer()
        input_data = Mock()
        input_data.name = "Test Customer"
        input_data.email = "test@test.com"
        input_data.address_line1 = "123 Main St"
        input_data.city = "Test City"
        input_data.state = "TS"
        input_data.postal_code = "12345"
        input_data.country = "USA"
        input_data.phone = None
        input_data.address_line2 = None
        input_data.visibility_company_ids = [self.parent_company_id, self.child_company_id]

        result = mutation.mutate(root=None, info=info, input=input_data)

        customer = Customer.objects.get(id=result.customer.id)
        # visible_to_company_ids stores strings in JSONField
        self.assertIn(str(self.company_id), customer.visible_to_company_ids)
        self.assertIn(str(self.parent_company_id), customer.visible_to_company_ids)
        self.assertIn(str(self.child_company_id), customer.visible_to_company_ids)
