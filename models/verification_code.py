from app import db
from datetime import datetime, timedelta
import secrets
import string

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(secrets.token_urlsafe(16)))
    email = db.Column(db.String(255), nullable=False, index=True)
    user_type = db.Column(db.Enum('student', 'lecturer', 'admin', name='user_type_enum'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(50), nullable=False, default='registration')  # registration, password_reset, etc.
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    max_attempts = db.Column(db.Integer, default=5, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.code:
            self.code = self.generate_code()
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10 minutes expiry
    
    def generate_code(self):
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    def regenerate_code(self):
        """Generate a new code and reset expiry"""
        self.code = self.generate_code()
        self.expires_at = datetime.utcnow() + timedelta(minutes=10)
        self.attempts = 0
        self.is_used = False
        self.used_at = None
    
    def verify_code(self, entered_code):
        """Verify the entered code"""
        if self.is_used:
            return False
        
        if self.is_expired():
            return False
        
        if self.attempts >= self.max_attempts:
            return False
        
        self.attempts += 1
        
        if self.code == entered_code:
            return True
        
        return False
    
    def is_expired(self):
        """Check if the code has expired"""
        return datetime.utcnow() > self.expires_at
    
    def mark_as_used(self):
        """Mark the code as used"""
        self.is_used = True
        self.used_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<VerificationCode {self.id}: {self.email} - {self.purpose}>'
