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
        "description": "Retrieves registration metadata, registrar, owner hints, and key lifecycle dates for a domain.",
        "keywords": ["whois", "registration", "domain", "owner", "registrar", "expiration"],
        "usage": [
            "Provide a fully qualified domain name such as example.com (no protocol).",
            "Check creation/expiration dates to spot lapsed ownership risk.",
            "Review registrar and name servers for sudden changes that can signal hijacks.",
            "Use WHOIS email/phone fields cautiously—they may be redacted for privacy.",
        ],
        "example": "/api/whois (POST with JSON payload: {\"host\":\"example.com\"})",
    },
    "dns_records": {
        "title": "DNS Records",
        "description": "Enumerates standard DNS record types (A, AAAA, MX, CNAME, TXT) for resolution and mail flow validation.",
        "keywords": ["dns", "records", "mx", "cname", "txt", "ns", "spf", "dkim"],
        "usage": [
            "Run it when you need to confirm IP resolution or MX mail server settings.",
            "Compare A vs AAAA vs CNAME to catch conflicting host mappings.",
            "Inspect TXT for SPF/DKIM/DMARC posture and misconfigurations.",
            "Use alongside WHOIS to align DNS with the registered domain owner.",
        ],
        "example": "/api/dns (POST with JSON payload: {\"host\":\"example.com\"})",
    },
    "ip_geolocation": {
        "title": "IP Geolocation",
        "description": "Translates a host into an IP address and fetches geographic/ASN data to validate hosting location.",
        "keywords": ["geoip", "geolocation", "location", "ip", "asn", "isp"],
        "usage": [
            "Combine with DNS or WHOIS to understand where the infrastructure lives.",
            "Use country/ISP/ASN data to flag traffic leaving expected regions.",
            "Correlate with port scan results to see if exposed services sit in risky geos.",
        ],
        "example": "/api/geoip (POST with JSON payload: {\"host\":\"example.com\"})",
    },
    "port_scan": {
        "title": "Port Scan",
        "description": "Checks whether a TCP port is open on the host for quick exposure checks.",
        "keywords": ["port", "scan", "tcp", "open", "exposure", "service"],
        "usage": [
            "Default port is 80; specify another port via the `port` field.",
            "Use this tool before intrusive scans; it keeps the timeout short and scope narrow.",
            "Scan common service ports (80, 443, 22, 3389, 8080) to inventory what’s reachable.",
            "If blocked or slow, confirm firewall rules or test from another vantage point.",
        ],
        "example": "/api/port_scan (POST with JSON payload: {\"host\":\"example.com\", \"port\":443})",
    },
    "speed": {
        "title": "Speed Test",
        "description": "Measures download, upload, and ping speeds from the server's location to gauge connectivity quality.",
        "keywords": ["speed", "bandwidth", "ping", "download", "upload", "latency"],
        "usage": [
            "Run this to gauge the server’s outbound bandwidth before launching downloads.",
            "Expect a longer response time; inform users that it may take a minute.",
            "Compare multiple runs to spot congestion or throttling over time.",
        ],
        "example": "/api/speed (POST without payload)",
    },
    "domain": {
        "title": "Domain Research",
        "description": "Runs configurable diagnostics for WHOIS, DNS, GeoIP, and port scans in one request for quicker triage.",
        "keywords": ["domain research", "fields", "combined", "batch", "package", "bundle"],
        "usage": [
            "Send a `fields` array to control which tools run (default is all).",
            "Validate the port range (1-65535) before requesting a custom port scan.",
            "Use WHOIS + DNS + GeoIP together to spot mismatches across ownership, hosting, and routing.",
            "Start with a narrow `fields` list for speed, then expand when deeper detail is needed.",
            "Capture results to create a baseline and compare future runs for drift.",
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
