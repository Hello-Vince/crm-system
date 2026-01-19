"""
Geocode handler - simulates Google Maps geocoding lookup.
"""

import asyncio
import os
from typing import Any

import httpx

from shared_python.geocoding import MockGeocodingClient
from shared_python.kafka_client import RetryableError, PermanentError


async def _handle_customer_created_async(event: dict[str, Any]) -> None:
    """
    Async handler for crm.customer.created event by geocoding the address.

    Args:
        event: Kafka event payload with customer_id and address.

    Raises:
        RetryableError: For network timeouts, server errors
        PermanentError: For client errors, invalid data
    """
    customer_id = event.get("customer_id")
    address = event.get("address")

    if not customer_id or not address:
        raise PermanentError(f"Missing customer_id or address: customer_id={customer_id}, address={address}")

    if not isinstance(customer_id, str) or not isinstance(address, str):
        raise PermanentError(f"Invalid data types: customer_id={type(customer_id)}, address={type(address)}")

    # Use mock geocoding client (async)
    geocoding_client = MockGeocodingClient()
    lat, lng = await geocoding_client.geocode(address)

    # Update customer via CRM Service internal API
    crm_service_url = os.getenv("CRM_SERVICE_INTERNAL_URL", "http://crm-service:8002")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{crm_service_url}/internal/customers/{customer_id}/coordinates",
                json={"latitude": lat, "longitude": lng},
                timeout=10.0,
            )
            response.raise_for_status()
    except httpx.TimeoutException as e:
        raise RetryableError(f"Request timeout updating coordinates for customer {customer_id}: {e}") from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code >= 500:
            # Server errors - retry
            raise RetryableError(f"Server error ({e.response.status_code}) updating coordinates for customer {customer_id}: {e}") from e
        else:
            # Client errors (4xx) - don't retry
            raise PermanentError(f"Client error ({e.response.status_code}) updating coordinates for customer {customer_id}: {e}") from e
    except httpx.RequestError as e:
        # Network/connection errors - retry
        raise RetryableError(f"Network error updating coordinates for customer {customer_id}: {e}") from e


def handle_customer_created(event: dict[str, Any]) -> None:
    """
    Synchronous wrapper for async handler.
    KafkaConsumer expects a sync handler, so we wrap the async function.

    Args:
        event: Kafka event payload with customer_id and address.
    """
    asyncio.run(_handle_customer_created_async(event))
