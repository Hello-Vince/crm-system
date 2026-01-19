import pytest
from unittest.mock import patch, Mock
import httpx
from geocode_worker.handler import handle_customer_created
from shared_python.kafka_client import RetryableError, PermanentError


class TestGeocodeWorkerErrorClassification:
    @patch('geocode_worker.handler.MockGeocodingClient')
    def test_missing_customer_id_raises_permanent_error(self, mock_geocoding_client):
        """Test that missing customer_id raises PermanentError"""
        event = {
            # Missing customer_id
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "Missing customer_id or address" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    def test_missing_address_raises_permanent_error(self, mock_geocoding_client):
        """Test that missing address raises PermanentError"""
        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            # Missing address
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "Missing customer_id or address" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    def test_geocoding_client_error_raises_permanent_error(self, mock_geocoding_client):
        """Test that geocoding client errors are treated as permanent"""
        # Mock geocoding client to raise an error
        mock_client_instance = Mock()
        mock_client_instance.geocode.side_effect = Exception("Geocoding service error")
        mock_geocoding_client.return_value = mock_client_instance

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "Unexpected error in geocode handler" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    @patch('httpx.AsyncClient')
    def test_network_timeout_raises_retryable_error(self, mock_async_client, mock_geocoding_client):
        """Test that HTTP timeouts are treated as retryable"""
        # Mock geocoding client to return coordinates
        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = (-33.8688, 151.2093)
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to raise timeout
        mock_client = Mock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.patch.side_effect = httpx.TimeoutException("Request timed out")
        mock_async_client.return_value = mock_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(RetryableError) as exc_info:
            handle_customer_created(event)

        assert "Request timeout to CRM service" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    @patch('httpx.AsyncClient')
    def test_http_5xx_error_raises_retryable_error(self, mock_async_client, mock_geocoding_client):
        """Test that HTTP 5xx errors are treated as retryable"""
        # Mock geocoding client to return coordinates
        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = (-33.8688, 151.2093)
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to return 500 error
        mock_client = Mock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=Mock(status_code=500)
        )
        mock_client.patch.return_value = mock_response
        mock_async_client.return_value = mock_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(RetryableError) as exc_info:
            handle_customer_created(event)

        assert "CRM service returned server error (5xx)" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    @patch('httpx.AsyncClient')
    def test_http_4xx_error_raises_permanent_error(self, mock_async_client, mock_geocoding_client):
        """Test that HTTP 4xx errors are treated as permanent"""
        # Mock geocoding client to return coordinates
        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = (-33.8688, 151.2093)
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to return 400 error
        mock_client = Mock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=Mock(status_code=400)
        )
        mock_client.patch.return_value = mock_response
        mock_async_client.return_value = mock_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(PermanentError) as exc_info:
            handle_customer_created(event)

        assert "CRM service returned client error (4xx)" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    @patch('httpx.AsyncClient')
    def test_network_connection_error_raises_retryable_error(self, mock_async_client, mock_geocoding_client):
        """Test that network connection errors are treated as retryable"""
        # Mock geocoding client to return coordinates
        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = (-33.8688, 151.2093)
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client to raise connection error
        mock_client = Mock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.patch.side_effect = httpx.RequestError("Connection failed")
        mock_async_client.return_value = mock_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345"
        }

        with pytest.raises(RetryableError) as exc_info:
            handle_customer_created(event)

        assert "Network error connecting to CRM service" in str(exc_info.value)

    @patch('geocode_worker.handler.MockGeocodingClient')
    @patch('httpx.AsyncClient')
    def test_successful_geocoding_updates_customer(self, mock_async_client, mock_geocoding_client):
        """Test successful geocoding workflow"""
        # Mock geocoding client to return coordinates
        mock_client_instance = Mock()
        mock_client_instance.geocode.return_value = (-33.8688, 151.2093)
        mock_geocoding_client.return_value = mock_client_instance

        # Mock HTTP client for successful response
        mock_client = Mock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_client.patch.return_value = mock_response
        mock_async_client.return_value = mock_client

        event = {
            "customer_id": "123e4567-e89b-12d3-a456-426614174000",
            "address": "123 Main St, Test City, TS 12345"
        }

        # Should not raise any exception
        handle_customer_created(event)

        # Verify geocoding was called
        mock_client_instance.geocode.assert_called_once_with("123 Main St, Test City, TS 12345")

        # Verify HTTP request was made
        mock_client.patch.assert_called_once()
        call_args = mock_client.patch.call_args
        assert call_args[0][0] == "http://crm-service:8002/internal/customers/123e4567-e89b-12d3-a456-426614174000/coordinates"
        assert call_args[1]["json"] == {"latitude": -33.8688, "longitude": 151.2093}