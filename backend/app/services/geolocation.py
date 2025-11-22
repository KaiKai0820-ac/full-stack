"""IP geolocation service using MaxMind GeoIP2 and ipapi.co fallback."""

import logging
from typing import Any

import geoip2.database
import geoip2.errors
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeolocationService:
    """Service for IP geolocation using MaxMind GeoIP2 database with ipapi.co fallback."""

    def __init__(self):
        self.maxmind_reader: geoip2.database.Reader | None = None
        self.ipapi_key: str | None = settings.IPAPI_CO_API_KEY

        # Initialize MaxMind reader if database path is configured
        if settings.MAXMIND_GEOIP2_DATABASE_PATH:
            try:
                self.maxmind_reader = geoip2.database.Reader(
                    settings.MAXMIND_GEOIP2_DATABASE_PATH
                )
                logger.info("MaxMind GeoIP2 database loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load MaxMind GeoIP2 database: {e}")
                self.maxmind_reader = None

    def get_location_from_ip(self, ip_address: str) -> dict[str, Any]:
        """
        Get location information from IP address.
        
        Args:
            ip_address: IP address to geolocate
            
        Returns:
            Dictionary with location information:
            {
                "country": str,
                "city": str | None,
                "latitude": float | None,
                "longitude": float | None,
                "location_source": "IP" | "precise"
            }
        """
        # Try MaxMind first
        if self.maxmind_reader:
            try:
                response = self.maxmind_reader.city(ip_address)
                return {
                    "country": response.country.iso_code or "Unknown",
                    "city": response.city.names.get("en") if response.city.names else None,
                    "latitude": float(response.location.latitude) if response.location.latitude else None,
                    "longitude": float(response.location.longitude) if response.location.longitude else None,
                    "location_source": "IP",
                }
            except geoip2.errors.AddressNotFoundError:
                logger.debug(f"IP address {ip_address} not found in MaxMind database")
            except Exception as e:
                logger.warning(f"Error querying MaxMind database: {e}")

        # Fallback to ipapi.co if MaxMind fails and API key is available
        if self.ipapi_key:
            try:
                response = httpx.get(
                    f"https://ipapi.co/{ip_address}/json/",
                    headers={"User-Agent": "UserInfo-Report-Service"},
                    params={"key": self.ipapi_key},
                    timeout=5.0,
                )
                response.raise_for_status()
                data = response.json()

                return {
                    "country": data.get("country_code", "Unknown"),
                    "city": data.get("city"),
                    "latitude": float(data["latitude"]) if data.get("latitude") else None,
                    "longitude": float(data["longitude"]) if data.get("longitude") else None,
                    "location_source": "IP",
                }
            except Exception as e:
                logger.warning(f"Error querying ipapi.co: {e}")

        # Return default if all methods fail
        logger.warning(f"Could not geolocate IP address {ip_address}, returning default")
        return {
            "country": "Unknown",
            "city": None,
            "latitude": None,
            "longitude": None,
            "location_source": "IP",
        }

    def enrich_location_snapshot(
        self, ip_address: str, opt_out_flags: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Enrich location snapshot with IP geolocation, respecting opt-out flags.
        
        Args:
            ip_address: IP address to geolocate
            opt_out_flags: User opt-out preferences (e.g., {"location_tracking": True})
            
        Returns:
            Location snapshot dictionary compatible with UserSession.location_snapshot
        """
        # Check if location tracking is opted out
        if opt_out_flags and opt_out_flags.get("location_tracking", False):
            return {
                "country": "Unknown",
                "city": None,
                "latitude": None,
                "longitude": None,
                "location_source": "IP",
            }

        # Get location from IP
        location = self.get_location_from_ip(ip_address)

        # Return location snapshot
        return {
            "country": location["country"],
            "city": location.get("city"),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "location_source": location["location_source"],
        }

    def close(self):
        """Close MaxMind database reader."""
        if self.maxmind_reader:
            self.maxmind_reader.close()
            self.maxmind_reader = None


# Global service instance
geolocation_service = GeolocationService()

