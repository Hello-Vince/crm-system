"""CRM Service GraphQL schema."""
import graphene
from graphene_django import DjangoObjectType
from graphene_federation import build_schema, extends, external, key

from customers.models import Customer
from customers.mutations import Mutation as CustomerMutation


class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'


@extends
@key('id')
class CompanyReference(graphene.ObjectType):
    id = external(graphene.UUID())


class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.UUID(required=True))

    def resolve_customers(self, info):
        """
        Return customers filtered by user's access rights.
        - SYSTEM_ADMIN: sees all customers
        - COMPANY_ADMIN: sees own company + all descendant companies
        - USER: sees only own company
        """
        user = info.context.user
        
        if not user.is_authenticated:
            return Customer.objects.none()
        
        # System admins see everything
        if user.role == 'SYSTEM_ADMIN':
            return Customer.objects.all()
        
        # No company = no access
        if not user.company_id:
            return Customer.objects.none()
        
        # Filter by visible_to_company_ids
        # User's company_id must be in the customer's visibility list
        return Customer.objects.filter(visible_to_company_ids__contains=[user.company_id])

    def resolve_customer(self, info, id):
        """
        Return a single customer if user has access to it.
        """
        user = info.context.user
        
        if not user.is_authenticated:
            return None
        
        try:
            customer = Customer.objects.get(id=id)
            
            # System admins see everything
            if user.role == 'SYSTEM_ADMIN':
                return customer
            
            # No company = no access
            if not user.company_id:
                return None
            
            # Check if user's company is in the visibility list
            if user.company_id in customer.visible_to_company_ids:
                return customer
            
            return None
        except Customer.DoesNotExist:
            return None


class Mutation(CustomerMutation, graphene.ObjectType):
    pass


schema = build_schema(query=Query, mutation=Mutation)
