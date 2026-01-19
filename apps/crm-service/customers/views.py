"""
Internal API views for service-to-service communication.
"""
import json
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Customer


@csrf_exempt
@require_http_methods(["PATCH"])
def update_customer_coordinates(request, customer_id):
    """
    Internal API endpoint to update customer coordinates after geocoding.
    
    This endpoint is called by the geocode-worker service after geocoding completes.
    No authentication required as it's for internal service-to-service communication.
    
    Args:
        request: Django HTTP request
        customer_id: UUID of the customer to update
    
    Returns:
        JSON response with success status
    """
    try:
        customer = Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return JsonResponse(
            {'error': 'Customer not found'},
            status=404
        )
    
    try:
        data = json.loads(request.body)
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        return JsonResponse(
            {'error': f'Invalid request data: {str(e)}'},
            status=400
        )
    
    # Update customer coordinates
    customer.latitude = latitude
    customer.longitude = longitude
    customer.geocoded_at = timezone.now()
    customer.save()
    
    return JsonResponse({
        'success': True,
        'customer_id': str(customer.id),
        'latitude': float(customer.latitude),
        'longitude': float(customer.longitude),
    })
