"""CRM service URL configuration."""
from django.contrib import admin
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from customers import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('internal/customers/<uuid:customer_id>/coordinates', views.update_customer_coordinates, name='update_coordinates'),
]
