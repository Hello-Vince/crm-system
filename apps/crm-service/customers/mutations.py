import uuid

import graphene
from graphene_django import DjangoObjectType

from shared_python.kafka_client import KafkaProducer

from .models import Customer


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'


class CreateCustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()
    address_line1 = graphene.String(required=True)
    address_line2 = graphene.String()
    city = graphene.String(required=True)
    state = graphene.String(required=True)
    postal_code = graphene.String(required=True)
    country = graphene.String()
    visibility_company_ids = graphene.List(graphene.UUID)


class CreateCustomer(graphene.Mutation):
    """
    Create a new customer and publish event to Kafka for async processing.
    """
    class Arguments:
        input = CreateCustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()

    @classmethod
    def mutate(cls, root, info, input: CreateCustomerInput):
        # Get authenticated user from JWT middleware
        user = info.context.user
        
        if not user.is_authenticated:
            raise Exception('Authentication required to create customers')
        
        if not user.company_id:
            raise Exception('User must belong to a company to create customers')
        
        # Use authenticated user's company ID
        company_id = user.company_id
        
        # Set visibility list (default: creator's company + any specified)
        # Convert all UUIDs to strings for JSON storage
        visibility_ids = [str(company_id)]
        if input.visibility_company_ids:
            visibility_ids.extend([str(cid) for cid in input.visibility_company_ids])
        
        # Create customer
        customer = Customer.objects.create(
            name=input.name,
            email=input.email,
            phone=input.phone or '',
            address_line1=input.address_line1,
            address_line2=input.address_line2 or '',
            city=input.city,
            state=input.state,
            postal_code=input.postal_code,
            country=input.country or 'USA',
            created_by_company_id=company_id,
            visible_to_company_ids=list(set(visibility_ids)),
        )
        
        # Publish Kafka event AFTER successful commit
        kafka_producer = KafkaProducer()
        kafka_producer.publish(
            topic='crm.customer.created',
            key=str(customer.id),
            value={
                'customer_id': str(customer.id),
                'name': customer.name,
                'email': customer.email,
                'address': customer.full_address,
                'company_id': str(company_id),
                'visibility_list': [str(cid) for cid in customer.visible_to_company_ids],
            }
        )
        
        return CreateCustomer(customer=customer, success=True)


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
