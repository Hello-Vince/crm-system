"""Identity Service GraphQL schema."""
import graphene
from graphene_django import DjangoObjectType
from graphene_federation import build_schema, key

from companies.models import Company
from users.models import User
from users.mutations import Mutation as UsersMutation, AuthUserType
from users.views import decode_jwt_token


@key('id')
class CompanyType(DjangoObjectType):
    class Meta:
        model = Company
        fields = '__all__'

    @classmethod
    def resolve_reference(cls, info, **data):
        return Company.objects.get(id=data.get('id'))


@key('id')
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id', 'email', 'company', 'role', 'first_name', 'last_name', 'is_active')

    @classmethod
    def resolve_reference(cls, info, **data):
        return User.objects.get(id=data.get('id'))


class Query(graphene.ObjectType):
    companies = graphene.List(CompanyType)
    company = graphene.Field(CompanyType, id=graphene.UUID(required=True))
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.UUID(required=True))
    me = graphene.Field(AuthUserType, description="Get current authenticated user from JWT token")

    def resolve_companies(self, info):
        return Company.objects.all()

    def resolve_company(self, info, id):
        return Company.objects.get(id=id)

    def resolve_users(self, info):
        return User.objects.all()

    def resolve_user(self, info, id):
        return User.objects.get(id=id)

    def resolve_me(self, info):
        """Get current user from JWT token in Authorization header."""
        auth_header = info.context.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        payload = decode_jwt_token(token)
        if not payload:
            return None
        
        try:
            user = User.objects.select_related('company').get(id=payload['user_id'])
            return AuthUserType(
                id=user.id,
                email=user.email,
                firstName=user.first_name,
                lastName=user.last_name,
                role=user.role,
                companyId=user.company.id if user.company else None,
                companyName=user.company.name if user.company else None,
            )
        except User.DoesNotExist:
            return None


class Mutation(UsersMutation, graphene.ObjectType):
    pass


schema = build_schema(query=Query, mutation=Mutation)
