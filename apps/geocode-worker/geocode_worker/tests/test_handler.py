from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from shared_python.kafka_client import PermanentError, RetryableError

from geocode_worker.handler import handle_customer_created


class TestGeocodeWorkerErrorClassification:
    @patch("geocode_worker.handler.MockGeocodingClient")
    def test_missing_customer_id_raises_permanent_error(self, mock_geocoding_client):
        """Test that missing customer_id raises PermanentError"""
        event = {
            # Missing customer_id
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "Missing customer_id or address" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    def test_missing_address_raises_permanent_error(self, mock_geocoding_client):
        """Test that missing address raises PermanentError"""
        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            # Missing address
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "Missing customer_id or address" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    def test_geocoding_client_error_propagates(self, mock_geocoding_client):
        """Test that geocoding client errors propagate as-is"""
        # Mock geocoding client to raise an error
        mock_client_instance = Mock()
        mock_client_instance.geocode = AsyncMock(
            side_effect=Exception("Geocoding service error")
        )
        mock_geocoding_client.return_value = mock_client_instance

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345",
        }

        with pytest.raises(Exception) as exc_info:
            handle_customer_created(event)

        assert "Geocoding service error" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    @patch("httpx.AsyncClient")
    def test_network_timeout_raises_retryable_error(
        self, mock_async_client, mock_geocoding_client
    ):
        """Test that HTTP timeouts are treated as retryable"""
        # Mock geocoding client to return coordinates (async)
        mock_client_instance = Mock()
        mock_client_instance.geocode = AsyncMock(return_value=(-33.8688, 151.2093))
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to raise timeout (async context manager)
        mock_http_client = AsyncMock()
        mock_http_client.patch = AsyncMock(
            side_effect=httpx.TimeoutException("Request timed out")
        )
        mock_async_client.return_value.__aenter__.return_value = mock_http_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345",
        }

        with pytest.raises(RetryableError) as exc_info:
            handle_customer_created(event)

        assert "Request timeout updating coordinates" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    @patch("httpx.AsyncClient")
    def test_http_5xx_error_raises_retryable_error(
        self, mock_async_client, mock_geocoding_client
    ):
        """Test that HTTP 5xx errors are treated as retryable"""
        # Mock geocoding client to return coordinates (async)
        mock_client_instance = Mock()
        mock_client_instance.geocode = AsyncMock(return_value=(-33.8688, 151.2093))
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to return 500 error (async context manager)
        mock_response = Mock()
        mock_response.status_code = 500
        mock_http_client = AsyncMock()
        mock_http_client.patch = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=mock_response
            )
        )
        mock_async_client.return_value.__aenter__.return_value = mock_http_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345",
        }

        with pytest.raises(RetryableError) as exc_info:
            handle_customer_created(event)

        assert "Server error (500)" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    @patch("httpx.AsyncClient")
    def test_http_4xx_error_raises_permanent_error(
        self, mock_async_client, mock_geocoding_client
    ):
        """Test that HTTP 4xx errors are treated as permanent"""
        # Mock geocoding client to return coordinates (async)
        mock_client_instance = Mock()
        mock_client_instance.geocode = AsyncMock(return_value=(-33.8688, 151.2093))
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to return 400 error (async context manager)
        mock_response = Mock()
        mock_response.status_code = 400
        mock_http_client = AsyncMock()
        mock_http_client.patch = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Bad Request", request=Mock(), response=mock_response
            )
        )
        mock_async_client.return_value.__aenter__.return_value = mock_http_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345",
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "Client error (400)" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    @patch("httpx.AsyncClient")
    def test_network_connection_error_raises_retryable_error(
        self, mock_async_client, mock_geocoding_client
    ):
        """Test that network connection errors are treated as retryable"""
        # Mock geocoding client to return coordinates (async)
        mock_client_instance = Mock()
        mock_client_instance.geocode = AsyncMock(return_value=(-33.8688, 151.2093))
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to raise connection error (async context manager)
        mock_http_client = AsyncMock()
        mock_http_client.patch = AsyncMock(
            side_effect=httpx.RequestError("Connection failed")
        )
        mock_async_client.return_value.__aenter__.return_value = mock_http_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345",
        }

        with pytest.raises(RetryableError) as exc_info:
            handle_customer_created(event)

        assert "Network error updating coordinates" in str(exc_info.value)

    @patch("geocode_worker.handler.MockGeocodingClient")
    @patch("httpx.AsyncClient")
    def test_successful_geocoding_updates_customer(
        self, mock_async_client, mock_geocoding_client
    ):
        """Test successful geocoding workflow"""
        # Mock geocoding client to return coordinates (async)
        mock_client_instance = Mock()
        mock_client_instance.geocode = AsyncMock(return_value=(-33.8688, 151.2093))
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client for successful response (async context manager)
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock(return_value=None)
        mock_http_client = AsyncMock()
        mock_http_client.patch = AsyncMock(return_value=mock_response)
        mock_async_client.return_value.__aenter__.return_value = mock_http_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345",
        }

        # Should not raise any exception
        handle_customer_created(event)

        # Verify geocoding was called
        mock_client_instance.geocode.assert_called_once_with(
            "123 Main St, Test City, TS 12345"
        )

        # Verify HTTP request was made
        mock_http_client.patch.assert_called_once()
        call_args = mock_http_client.patch.call_args
        expected_url = (
            "http://crm-service:8002/internal/customers/"
            "123e4567-e89b-12d3-a456-426614174000/coordinates"
        )
        assert call_args[0][0] == expected_url
        assert call_args[1]["json"] == {"latitude": -33.8688, "longitude": 151.2093}
