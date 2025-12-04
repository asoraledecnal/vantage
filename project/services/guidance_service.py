"""
Service that returns usage guidance for the diagnostic tools.

Each method stays simple so routes can just request the guidance text they need
without knowing the instruction details.
"""

from __future__ import annotations

from typing import Dict, Iterable

TOOL_GUIDANCE: Dict[str, Dict[str, str | Iterable[str]]] = {
    "whois": {
        "title": "WHOIS Lookup",
        "description": "Retrieves registration metadata, registrar, and key dates for a domain.",
        "keywords": ["whois", "registration", "domain", "owner"],
        "usage": [
            "Provide a fully qualified domain name such as example.com.",
            "Check the creation/expiration dates to ensure domain ownership is current.",
            "Look at the registrar and name servers for signs of recent transfers.",
        ],
        "example": "/api/whois (POST with JSON payload: {\"host\":\"example.com\"})",
    },
    "dns_records": {
        "title": "DNS Records",
        "description": "Enumerates standard DNS record types (A, AAAA, MX, CNAME, TXT).",
        "keywords": ["dns", "records", "mx", "cname", "txt"],
        "usage": [
            "Run it when you need to confirm IP resolution or MX mail server settings.",
            "Compare results across record types to catch inconsistencies.",
        ],
        "example": "/api/dns (POST with JSON payload: {\"host\":\"example.com\"})",
    },
    "ip_geolocation": {
        "title": "IP Geolocation",
        "description": "Translates a host into an IP address and fetches its geographic data.",
        "keywords": ["geoip", "geolocation", "location", "ip"],
        "usage": [
            "Combine with DNS or WHOIS to understand where the infrastructure lives.",
            "Use the returned country and ISP data to highlight unexpected hosting locations.",
        ],
        "example": "/api/geoip (POST with JSON payload: {\"host\":\"example.com\"})",
    },
    "port_scan": {
        "title": "Port Scan",
        "description": "Checks whether a TCP port is open on the host.",
        "keywords": ["port", "scan", "tcp", "open"],
        "usage": [
            "Default port is 80; specify another port via the `port` field.",
            "Use this tool before running intrusive scans; it keeps the timeout short.",
        ],
        "example": "/api/port_scan (POST with JSON payload: {\"host\":\"example.com\", \"port\":443})",
    },
    "speed": {
        "title": "Speed Test",
        "description": "Measures download, upload, and ping speeds from the server's location.",
        "keywords": ["speed", "bandwidth", "ping", "download", "upload"],
        "usage": [
            "Run this to gauge the server’s outbound bandwidth before launching downloads.",
            "Expect a longer response time; inform users that it may take a minute.",
        ],
        "example": "/api/speed (POST without payload)",
    },
    "domain": {
        "title": "Domain Research",
        "description": "Runs configurable diagnostics for WHOIS, DNS, GeoIP, and port scans in one request.",
        "keywords": ["domain research", "fields", "combined", "batch", "package"],
        "usage": [
            "Send a `fields` array to control which tools run (default is all).",
            "Validate the port range (1-65535) before requesting a custom port scan.",
        ],
        "example": "/api/domain (POST with JSON payload: {\"domain\":\"example.com\",\"fields\":[\"whois\",\"dns_records\"]})",
    },
}


class DiagnosticGuidanceService:
    """Provides per-tool instructions for diagnostic API consumers."""

    def get_guidance(self, tool: str) -> Dict[str, str | Iterable[str]]:
        normalized = tool.strip().lower() if tool else ""
        guidance = TOOL_GUIDANCE.get(normalized)
        if guidance:
            return guidance
        return {
            "title": "Tool guidance not found",
            "description": "Provide one of the supported tool names.",
            "supported_tools": self.supported_tools(),
        }

    def supported_tools(self) -> Iterable[str]:
        """Returns the list of supported tool keys."""
        return sorted(TOOL_GUIDANCE.keys())
