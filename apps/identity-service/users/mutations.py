"""
GraphQL mutations for user authentication.
"""
import graphene
from django.contrib.auth import authenticate

from .models import User
from .views import create_jwt_token, decode_jwt_token


class LoginInput(graphene.InputObjectType):
    email = graphene.String(required=True)
    password = graphene.String(required=True)


class AuthUserType(graphene.ObjectType):
    """User type for authentication responses with JWT payload fields."""
    id = graphene.UUID()
    email = graphene.String()
    firstName = graphene.String()
    lastName = graphene.String()
    role = graphene.String()
    companyId = graphene.UUID()
    companyName = graphene.String()


class LoginPayload(graphene.ObjectType):
    token = graphene.String()
    user = graphene.Field(AuthUserType)


class Login(graphene.Mutation):
    """
    GraphQL mutation to authenticate user and return JWT token.
    """
    class Arguments:
        input = LoginInput(required=True)

    Output = LoginPayload

    @classmethod
    def mutate(cls, root, info, input: LoginInput):
        try:
            user = User.objects.select_related('company').get(email=input.email)
            if not user.check_password(input.password):
                raise Exception('Invalid credentials')
            if not user.is_active:
                raise Exception('User account is disabled')
        except User.DoesNotExist:
            raise Exception('Invalid credentials')

        # Generate JWT token
        token = create_jwt_token(user)
        
        return LoginPayload(
            token=token,
            user=AuthUserType(
                id=user.id,
                email=user.email,
                firstName=user.first_name,
                lastName=user.last_name,
                role=user.role,
                companyId=user.company.id if user.company else None,
                companyName=user.company.name if user.company else None,
            )
        )


class Mutation(graphene.ObjectType):
    login = Login.Field()
