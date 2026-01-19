"""
Mock Geocoding client - simulates Google Maps Geocoding API.
"""
import asyncio


class MockGeocodingClient:
    """
    Simulates Google Maps Geocoding API for local development.
    Returns fixed mock coordinates with simulated latency for zero-config operation.
    """
    
    async def geocode(self, address: str) -> tuple[float, float]:
        """
        Geocode an address to latitude/longitude coordinates.
        Simulates API latency with a 1-second delay.
        
        Args:
            address: Full address string to geocode.
        
        Returns:
            Tuple of (latitude, longitude) as floats.
        """
        print(f'[MockGeocoding] Geocoding address: {address}')
        
        # Simulate API latency
        await asyncio.sleep(1)
        
        # Return fixed mock coordinates (Sydney, Australia)
        # This ensures zero-config operation without external API keys
        lat = -33.8688
        lng = 151.2093
        
        print(f'[MockGeocoding] Geocoded: {address} -> ({lat}, {lng})')
        
        return (round(lat, 7), round(lng, 7))
    
    def reverse_geocode(
        self,
        latitude: float,
        longitude: float
    ) -> str | None:
        """
        Reverse geocode coordinates to an address.
        
        Args:
            latitude: Latitude coordinate.
            longitude: Longitude coordinate.
        
        Returns:
            Address string or None if not found.
        """
        # Mock implementation - return a generic address
        return f"Mock Address at ({latitude:.4f}, {longitude:.4f})"
