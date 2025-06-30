import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending email and SMS notifications"""
    
    @staticmethod
    def send_verification_code(email, phone_number, code, user_type):
        """
        Send verification code via email or SMS
        For testing purposes, we'll just display the code in the console
        """
        
        # Display the verification code prominently in the console
        print("\n" + "🎯" * 50)
        print("🔑 VERIFICATION CODE GENERATED 🔑")
        print("🎯" * 50)
        print(f"📧 Email: {email}")
        print(f"👤 User Type: {user_type}")
        print(f"🔢 CODE: {code}")
        print(f"📱 Phone: {phone_number if phone_number else 'N/A'}")
        print(f"📤 Delivery Method: {'SMS' if user_type == 'lecturer' else 'Email'}")
        print("🎯" * 50)
        print(f"🚨 COPY THIS CODE: {code} 🚨")
        print("🎯" * 50 + "\n")
        
        # In a real implementation, you would:
        # 1. Send email for students/admins
        # 2. Send SMS for lecturers
        # 3. Use services like SendGrid, Twilio, etc.
        
        if user_type == 'lecturer' and phone_number:
            # Simulate SMS sending
            print(f"📱 [SIMULATED SMS] Sending to {phone_number}: Your AttendEase verification code is {code}")
            return True, f"SMS sent to {phone_number}"
        else:
            # Simulate email sending
            print(f"📧 [SIMULATED EMAIL] Sending to {email}: Your AttendEase verification code is {code}")
            return True, f"Email sent to {email}"
    
    @staticmethod
    def send_email(to_email, subject, body, html_body=None):
        """
        Send email using SMTP (for future implementation)
        """
        try:
            # This would be implemented with actual SMTP settings
            # For now, just simulate
            print(f"📧 [EMAIL SIMULATION] To: {to_email}, Subject: {subject}")
            print(f"📝 Body: {body}")
            return True, "Email sent successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def send_sms(phone_number, message):
        """
        Send SMS using SMS service (for future implementation)
        """
        try:
            # This would be implemented with Twilio or similar service
            # For now, just simulate
            print(f"📱 [SMS SIMULATION] To: {phone_number}")
            print(f"📝 Message: {message}")
            return True, "SMS sent successfully"
        except Exception as e:
            return False, str(e)
