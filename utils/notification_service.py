import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class NotificationService:
    """
    Service for sending notifications via email and SMS
    Since we're using fake emails/phones, we'll simulate the sending
    """
    
    @staticmethod
    def send_verification_code(code, contact, delivery_method='Email'):
        """
        Send verification code via email or SMS
        For testing purposes, we'll just log the code
        """
        print(f"\n📨 SENDING VERIFICATION CODE")
        print(f"🔢 Code: {code}")
        print(f"📧 Contact: {contact}")
        print(f"📱 Method: {delivery_method}")
        print(f"⏰ Time: {datetime.now()}")
        
        try:
            if delivery_method == 'Email':
                return NotificationService._send_email_notification(code, contact)
            elif delivery_method == 'SMS':
                return NotificationService._send_sms_notification(code, contact)
            else:
                print(f"❌ Unknown delivery method: {delivery_method}")
                return False
        except Exception as e:
            print(f"❌ Notification sending failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_notification(code, email):
        """
        Simulate sending email notification
        In production, this would use a real email service
        """
        print(f"📧 Simulating email to: {email}")
        print(f"📝 Email Subject: AttendEase - Verification Code")
        print(f"📄 Email Body:")
        print(f"   Your AttendEase verification code is: {code}")
        print(f"   This code will expire in 10 minutes.")
        print(f"   If you didn't request this code, please ignore this email.")
        print(f"✅ Email simulation completed")
        return True
    
    @staticmethod
    def _send_sms_notification(code, phone):
        """
        Simulate sending SMS notification
        In production, this would use a real SMS service like Twilio
        """
        print(f"📱 Simulating SMS to: {phone}")
        print(f"💬 SMS Message:")
        print(f"   AttendEase verification code: {code}")
        print(f"   Expires in 10 minutes.")
        print(f"✅ SMS simulation completed")
        return True
    
    @staticmethod
    def send_attendance_notification(student_email, course_name, session_id):
        """
        Send attendance session notification to student
        """
        print(f"\n🎓 SENDING ATTENDANCE NOTIFICATION")
        print(f"👤 Student: {student_email}")
        print(f"📚 Course: {course_name}")
        print(f"🆔 Session: {session_id}")
        print(f"📝 Message: New attendance session started for {course_name}")
        print(f"✅ Attendance notification sent")
        return True
    
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
    def send_password_reset_code(email, code):
        """
        Send password reset code
        """
        print(f"\n🔐 SENDING PASSWORD RESET CODE")
        print(f"📧 Email: {email}")
        print(f"🔢 Code: {code}")
        print(f"📝 Message: Your password reset code is: {code}")
        print(f"✅ Password reset notification sent")
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
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

class NotificationService:
    """
    Service for sending notifications via email and SMS
    Since we're using fake emails/phones, we'll simulate the sending
    """
    
    @staticmethod
    def send_verification_code(code, contact, delivery_method='Email'):
        """
        Send verification code via email or SMS
        For testing purposes, we'll just log the code
        """
        print(f"\n📨 SENDING VERIFICATION CODE")
        print(f"🔢 Code: {code}")
        print(f"📧 Contact: {contact}")
        print(f"📱 Method: {delivery_method}")
        print(f"⏰ Time: {datetime.now()}")
        
        try:
            if delivery_method == 'Email':
                return NotificationService._send_email_notification(code, contact)
            elif delivery_method == 'SMS':
                return NotificationService._send_sms_notification(code, contact)
            else:
                print(f"❌ Unknown delivery method: {delivery_method}")
                return False
        except Exception as e:
            print(f"❌ Notification sending failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_notification(code, email):
        """
        Simulate sending email notification
        In production, this would use a real email service
        """
        print(f"📧 Simulating email to: {email}")
        print(f"📝 Email Subject: AttendEase - Verification Code")
        print(f"📄 Email Body:")
        print(f"   Your AttendEase verification code is: {code}")
        print(f"   This code will expire in 10 minutes.")
        print(f"   If you didn't request this code, please ignore this email.")
        print(f"✅ Email simulation completed")
        return True
    
    @staticmethod
    def _send_sms_notification(code, phone):
        """
        Simulate sending SMS notification
        In production, this would use a real SMS service like Twilio
        """
        print(f"📱 Simulating SMS to: {phone}")
        print(f"💬 SMS Message:")
        print(f"   AttendEase verification code: {code}")
        print(f"   Expires in 10 minutes.")
        print(f"✅ SMS simulation completed")
        return True
    
    @staticmethod
    def send_attendance_notification(student_email, course_name, session_id):
        """
        Send attendance session notification to student
        """
        print(f"\n🎓 SENDING ATTENDANCE NOTIFICATION")
        print(f"👤 Student: {student_email}")
        print(f"📚 Course: {course_name}")
        print(f"🆔 Session: {session_id}")
        print(f"📝 Message: New attendance session started for {course_name}")
        print(f"✅ Attendance notification sent")
        return True
    
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
    def send_password_reset_code(email, code):
        """
        Send password reset code
        """
        print(f"\n🔐 SENDING PASSWORD RESET CODE")
        print(f"📧 Email: {email}")
        print(f"🔢 Code: {code}")
        print(f"📝 Message: Your password reset code is: {code}")
        print(f"✅ Password reset notification sent")
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
