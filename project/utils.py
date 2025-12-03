"""
Utility functions for the Vantage application.

This module contains miscellaneous helper functions that are used across
the application but do not belong to a specific domain or service. This
includes validators, formatters, and other general-purpose tools.
"""

import re
import ipaddress

def is_valid_host(host: str) -> bool:
    """
    Validates if a given string is a valid, non-malicious hostname or IP address.

    This function checks against a list of malicious characters and then
    validates the format as either an IP address or a standard DNS hostname.

    Args:
        host: The hostname or IP address string to validate.

    Returns:
        True if the host is valid, False otherwise.
    """
    if not host or not isinstance(host, str) or host.startswith('-'):
        return False
    
    # Block common command injection and malicious characters
    if any(char in host for char in ";|&`$()<>"):
        return False

    # Check if it's a valid IP address
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass

    # If not an IP, check if it's a valid hostname according to RFC 1035
    # This regex allows for domains like 'localhost' and standard TLDs.
    hostname_regex = re.compile(
        r"^(?:[a-zA-Z0-9]"  # First character of a label
        r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)"  # Subsequent characters of a label
        r"+[a-zA-Z]{2,6}$"  # TLD
    )
    return hostname_regex.match(host) is not None
