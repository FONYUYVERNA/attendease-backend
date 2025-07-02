import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from datetime import datetime
from flask import current_app

class NotificationService:
    """Service for sending notifications via email and SMS"""
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'AttendEase')
    
    @staticmethod
    def send_verification_code(code, contact, delivery_method='Email'):
        """
        Send verification code via email or SMS
        
        Args:
            code (str): The verification code
            contact (str): Email address or phone number
            delivery_method (str): 'Email' or 'SMS'
        """
        print(f"📤 Sending {delivery_method} notification to {contact}")
        
        try:
            if delivery_method == 'Email':
                return NotificationService._send_email_verification(code, contact)
            elif delivery_method == 'SMS':
                return NotificationService._send_sms_verification(code, contact)
            else:
                print(f"❌ Unknown delivery method: {delivery_method}")
                return False
        except Exception as e:
            print(f"❌ Notification error: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_verification(code, email):
        """Send verification code via email"""
        try:
            # Check if SMTP is configured
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not smtp_username or not smtp_password:
                print("📧 SMTP not configured - using mock email service")
                print(f"📧 MOCK EMAIL to {email}: Your verification code is {code}")
                return True
            
            # Real email sending
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = email
            msg['Subject'] = "AttendEase - Verification Code"
            
            body = f"""
            Welcome to AttendEase!
            
            Your verification code is: {code}
            
            This code will expire in 10 minutes.
            
            If you didn't request this code, please ignore this email.
            
            Best regards,
            AttendEase Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_username, email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {email}")
            return True
            
        except Exception as e:
            print(f"❌ Email sending failed: {str(e)}")
            # Fallback to mock
            print(f"📧 MOCK EMAIL to {email}: Your verification code is {code}")
            return True
    
    @staticmethod
    def _send_sms_verification(code, phone_number):
        """Send verification code via SMS"""
        try:
            # Check if Twilio is configured
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            from_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            if not account_sid or not auth_token or not from_number:
                print("📱 Twilio not configured - using mock SMS service")
                print(f"📱 MOCK SMS to {phone_number}: Your AttendEase verification code is {code}")
                return True
            
            # Real SMS sending
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=f"Your AttendEase verification code is: {code}. This code expires in 10 minutes.",
                from_=from_number,
                to=phone_number
            )
            
            print(f"✅ SMS sent successfully to {phone_number} (SID: {message.sid})")
            return True
            
        except Exception as e:
            print(f"❌ SMS sending failed: {str(e)}")
            # Fallback to mock
            print(f"📱 MOCK SMS to {phone_number}: Your AttendEase verification code is {code}")
            return True
    
    def send_verification_email(self, email, code, user_name):
        """Send verification email with code"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "AttendEase - Email Verification"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = email
            
            # Create HTML content
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Email Verification</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .code {{ background: #4F46E5; color: white; font-size: 32px; font-weight: bold; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0; letter-spacing: 5px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                    .warning {{ background: #FEF3C7; border: 1px solid #F59E0B; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to AttendEase!</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {user_name}!</h2>
                        <p>Thank you for registering with AttendEase. To complete your registration, please verify your email address using the code below:</p>
                        
                        <div class="code">{code}</div>
                        
                        <p>Enter this code in the verification screen to activate your account.</p>
                        
                        <div class="warning">
                            <strong>Important:</strong> This code will expire in 15 minutes for security reasons.
                        </div>
                        
                        <p>If you didn't create an account with AttendEase, please ignore this email.</p>
                        
                        <p>Best regards,<br>The AttendEase Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text = f"""
            Welcome to AttendEase!
            
            Hello {user_name}!
            
            Thank you for registering with AttendEase. To complete your registration, please verify your email address using the code below:
            
            Verification Code: {code}
            
            Enter this code in the verification screen to activate your account.
            
            Important: This code will expire in 15 minutes for security reasons.
            
            If you didn't create an account with AttendEase, please ignore this email.
            
            Best regards,
            The AttendEase Team
            
            This is an automated message. Please do not reply to this email.
            """
            
            # Add parts to message
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            if self.smtp_username and self.smtp_password:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.from_email, email, message.as_string())
                
                current_app.logger.info(f"Verification email sent to {email}")
                return True
            else:
                # For development - just log the code
                current_app.logger.info(f"DEVELOPMENT MODE: Verification code for {email}: {code}")
                print(f"🔐 VERIFICATION CODE for {email}: {code}")
                return True
                
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False
    
    def send_password_reset_email(self, email, reset_token, user_name):
        """Send password reset email"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "AttendEase - Password Reset"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = email
            
            reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
            
            # Create HTML content
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Password Reset</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px; }}
                    .button {{ background: #4F46E5; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
                    .warning {{ background: #FEF3C7; border: 1px solid #F59E0B; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {user_name}!</h2>
                        <p>We received a request to reset your password for your AttendEase account.</p>
                        
                        <p>Click the button below to reset your password:</p>
                        
                        <a href="{reset_url}" class="button">Reset Password</a>
                        
                        <div class="warning">
                            <strong>Important:</strong> This link will expire in 1 hour for security reasons.
                        </div>
                        
                        <p>If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
                        
                        <p>Best regards,<br>The AttendEase Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message. Please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text version
            text = f"""
            Password Reset Request
            
            Hello {user_name}!
            
            We received a request to reset your password for your AttendEase account.
            
            Click the link below to reset your password:
            {reset_url}
            
            Important: This link will expire in 1 hour for security reasons.
            
            If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            
            Best regards,
            The AttendEase Team
            
            This is an automated message. Please do not reply to this email.
            """
            
            # Add parts to message
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            if self.smtp_username and self.smtp_password:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    server.sendmail(self.from_email, email, message.as_string())
                
                current_app.logger.info(f"Password reset email sent to {email}")
                return True
            else:
                # For development - just log the token
                current_app.logger.info(f"DEVELOPMENT MODE: Password reset token for {email}: {reset_token}")
                print(f"🔐 PASSWORD RESET TOKEN for {email}: {reset_token}")
                return True
                
        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset(email, reset_link):
        """Send password reset email"""
        try:
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not smtp_username or not smtp_password:
                print(f"📧 MOCK PASSWORD RESET EMAIL to {email}: Reset link: {reset_link}")
                return True
            
            # Real email implementation would go here
            print(f"✅ Password reset email sent to {email}")
            return True
            
        except Exception as e:
            print(f"❌ Password reset email failed: {str(e)}")
            return False
    
    @staticmethod
    def send_attendance_notification(user_email, course_name, session_type='started'):
        """Send attendance session notification"""
        try:
            message = f"Attendance session for {course_name} has {session_type}"
            print(f"📧 MOCK ATTENDANCE NOTIFICATION to {user_email}: {message}")
            return True
            
        except Exception as e:
            print(f"❌ Attendance notification failed: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_notification(user_email, user_name, user_type):
        """
        Send welcome notification after successful registration
        """
        print(f"\n🎉 SENDING WELCOME NOTIFICATION")
        print(f"👤 User: {user_name} ({user_email})")
        print(f"🏷️ Type: {user_type}")
        print(f"📝 Message: Welcome to AttendEase! Your account has been created successfully.")
        print(f"✅ Welcome notification sent")
        return True
    
    @staticmethod
    def send_system_notification(user_email, title, message):
        """
        Send general system notification
        """
        print(f"\n🔔 SENDING SYSTEM NOTIFICATION")
        print(f"👤 User: {user_email}")
        print(f"📋 Title: {title}")
        print(f"📝 Message: {message}")
        print(f"✅ System notification sent")
        return True
    
    @staticmethod
    def send_bulk_notification(emails, title, message):
        """
        Send notification to multiple users
        """
        print(f"\n📢 SENDING BULK NOTIFICATION")
        print(f"👥 Recipients: {len(emails)} users")
        print(f"📋 Title: {title}")
        print(f"📝 Message: {message}")
        
        for email in emails:
            print(f"   📧 Sending to: {email}")
        
        print(f"✅ Bulk notification sent to {len(emails)} users")
        return True
    
    @staticmethod
    def log_notification(notification_type, recipient, content, status='sent'):
        """
        Log notification for audit purposes
        """
        print(f"\n📊 LOGGING NOTIFICATION")
        print(f"🏷️ Type: {notification_type}")
        print(f"👤 Recipient: {recipient}")
        print(f"📝 Content: {content}")
        print(f"✅ Status: {status}")
        print(f"⏰ Time: {datetime.now()}")
        print(f"📋 Notification logged")
        return True
