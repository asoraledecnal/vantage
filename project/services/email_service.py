"""
Service layer for handling email operations.

This module provides functions for sending emails, abstracting the
details of the email provider implementation (e.g., SendGrid). This allows
the rest of the application to send emails without needing to know the
specifics of the API calls.
"""

import os
import requests

def send_verification_email(user_email: str, token: str, frontend_url: str):
    """
    Sends an email verification link to a newly registered user.

    Args:
        user_email: The email address of the user to verify.
        token: The unique verification token generated for the user.
        frontend_url: The base URL of the frontend application where the user
                      will click the verification link.
    """
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    verified_sender = os.environ.get('VERIFIED_SENDER_EMAIL')

    if not sendgrid_api_key or not verified_sender:
        print("Email service not fully configured for verification (SENDGRID_API_KEY or VERIFIED_SENDER_EMAIL is missing). Skipping verification email send.")
        return

    verification_link = f"{frontend_url}/verify?token={token}" # Assuming a frontend /verify route
    
    email_body = f"""
    Hello,

    Thank you for registering with Vantage.
    Please click the link below to verify your email address:

    {verification_link}

    This link will expire in a short time.

    If you did not register for this service, please ignore this email.

    Best regards,
    The Vantage Team
    """

    payload = {
        "personalizations": [{"to": [{"email": user_email}]}],
        "from": {"email": verified_sender, "name": "Vantage Verification"},
        "subject": "Vantage: Verify Your Email Address",
        "content": [{"type": "text/plain", "value": email_body}]
    }

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {sendgrid_api_key}"},
            json=payload
        )
        if 200 <= response.status_code < 300:
            print(f"Verification email sent successfully to {user_email}.")
        else:
            print(f"Failed to send verification email to {user_email}. Status: {response.status_code}, Body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"A network exception occurred while sending verification email: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in send_verification_email: {e}")


def send_feedback_email(name: str, email: str, subject: str, message: str):
    """
    Sends a feedback email using the SendGrid Web API.

    This function constructs and sends an email with the provided feedback details.
    It retrieves SendGrid configuration from environment variables. If the required
    configuration is not present, it logs a message and exits gracefully.

    Args:
        name: The name of the person submitting the feedback.
        email: The email address of the sender, used for the 'Reply-To' header.
        subject: The subject of the feedback message.
        message: The main content of the feedback.
    """
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
    admin_email = os.environ.get('ADMIN_EMAIL')
    verified_sender = os.environ.get('VERIFIED_SENDER_EMAIL')

    if not all([sendgrid_api_key, admin_email, verified_sender]):
        print("Email service not fully configured (SENDGRID_API_KEY, ADMIN_EMAIL, or VERIFIED_SENDER_EMAIL is missing). Skipping email send.")
        return

    email_body = f"""
    New Feedback Received:
    ----------------------
    Name: {name}
    Email: {email}
    Subject: {subject or 'N/A'}

    Message:
    {message}
    """

    payload = {
        "personalizations": [{"to": [{"email": admin_email}]}],
        "from": {"email": verified_sender, "name": "Vantage Feedback"},
        "reply_to": {"email": email, "name": name},
        "subject": f"New Feedback: {subject or 'No Subject'}",
        "content": [{"type": "text/plain", "value": email_body}]
    }

    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {sendgrid_api_key}"},
            json=payload
        )
        # Check for successful status codes (2xx)
        if 200 <= response.status_code < 300:
            print("Feedback email sent successfully via SendGrid.")
        else:
            print(f"Failed to send email via SendGrid. Status: {response.status_code}, Body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"A network exception occurred while sending email via SendGrid: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in send_feedback_email: {e}")
