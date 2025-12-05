"""
Service for handling One-Time Password (OTP) generation and verification.
"""

import hashlib
import os
import secrets

def generate_otp(length=6):
    """
    Generates a secure random OTP of a specified length.

    Args:
        length (int): The number of digits in the OTP.

    Returns:
        str: The generated OTP as a string.
    """
    if length <= 0:
        raise ValueError("OTP length must be positive.")
    limit = 10 ** length
    return str(secrets.randbelow(limit)).zfill(length)

def hash_otp(otp):
    """
    Hashes an OTP using SHA256 with a salt for secure storage.

    Returns:
        str: The hex digest of the hashed OTP.
    """
    salt = os.environ.get('OTP_SALT')
    if not salt:
        raise ValueError("OTP_SALT environment variable is not set.")
    return hashlib.sha256(f"{salt}{otp}".encode()).hexdigest()

def verify_otp(submitted_otp, stored_hash):
    """
    Verifies a submitted OTP against a stored hash.

    Args:
        submitted_otp (str): The OTP submitted by the user.
        stored_hash (str): The hash stored in the database.

    Returns:
        bool: True if the OTP is valid, False otherwise.
    """
    salt = os.environ.get('OTP_SALT')
    if not salt:
        raise ValueError("OTP_SALT environment variable is not set.")
    hashed_input = hashlib.sha256(f"{salt}{submitted_otp}".encode()).hexdigest()
    return hashed_input == stored_hash
