"""
Service layer for domain-related operations.

This module provides a suite of functions for performing network diagnostics
and reconnaissance on a given domain. It encapsulates the logic for tools
like WHOIS, DNS lookups, geolocation, port scanning, and speed tests,
separating the core business logic from the web-facing routes.
"""

import socket
import datetime
from typing import Any, Optional, Dict, List

import requests
import speedtest
import dns.resolver
import whois

def get_whois_data(domain: str) -> Dict[str, Any]:
    """
    Retrieves WHOIS information for a given domain.

    Args:
        domain: The domain name to query.

    Returns:
        A dictionary containing key WHOIS data, or an error dictionary.
    """
    try:
        w = whois.whois(domain)

        def _get(key: str) -> Any:
            return w.get(key) if isinstance(w, dict) else getattr(w, key, None)

        def _iso(val: Any) -> Optional[str]:
            if val is None:
                return None
            if isinstance(val, list):
                val = val[0] if val else None
                if val is None:
                    return None
            if isinstance(val, (datetime.datetime, datetime.date)):
                return val.isoformat()
            return str(val)

        return {
            "domain_name": _get("domain_name"),
            "registrar": _get("registrar"),
            "creation_date": _iso(_get("creation_date")),
            "expiration_date": _iso(_get("expiration_date")),
            "name_servers": _get("name_servers"),
            "status": _get("status"),
        }
    except Exception as e:
        return {"error": str(e)}

def get_dns_records(domain: str) -> Dict[str, Any]:
    """
    Resolves various DNS record types for a given domain.

    Args:
        domain: The domain name to query.

    Returns:
        A dictionary where keys are record types (A, AAAA, MX, etc.)
        and values are lists of records or an error dictionary.
    """
    records = {}
    for record_type in ['A', 'AAAA', 'MX', 'CNAME', 'TXT']:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            records[record_type] = [str(rdata) for rdata in answers]
        except Exception as e:
            records[record_type] = {"error": str(e)}
    return records

def get_ip_geolocation(domain: str) -> Dict[str, Any]:
    """
    Performs an IP geolocation lookup for a given domain.

    Args:
        domain: The domain name to geolocate.

    Returns:
        A dictionary containing geolocation data or an error dictionary.
    """
    try:
        ip_address = socket.gethostbyname(domain)
        response = requests.get(f"http://ip-api.com/json/{ip_address}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def scan_port(domain: str, port: int) -> Dict[str, Any]:
    """
    Scans a specific port on a given domain to see if it is open.

    Args:
        domain: The domain name to scan.
        port: The port number to check.

    Returns:
        A dictionary with the port number and its status ('open' or 'closed'),
        or an error dictionary.
    """
    try:
        ip_address = socket.gethostbyname(domain)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((ip_address, port))
            return {"port": port, "status": "open" if result == 0 else "closed"}
    except Exception as e:
        return {"error": str(e)}

def get_speed_test() -> Dict[str, Any]:
    """
    Performs a network speed test to measure download, upload, and ping.

    Returns:
        A dictionary containing download/upload speeds in Mbps and ping in ms,
        or an error dictionary.
    """
    try:
        st = speedtest.Speedtest()
        st.download()
        st.upload()
        results = st.results.dict()
        return {
            "download": f"{results['download'] / 1_000_000:.2f} Mbps",
            "upload": f"{results['upload'] / 1_000_000:.2f} Mbps",
            "ping": f"{results['ping']:.2f} ms",
        }
    except Exception as e:
        return {"error": str(e)}
