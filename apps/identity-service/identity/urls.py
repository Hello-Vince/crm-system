"""Identity service URL configuration."""
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from users.views import login_view, me_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('api/auth/login', login_view, name='login'),
    path('api/auth/me', me_view, name='me'),
]
