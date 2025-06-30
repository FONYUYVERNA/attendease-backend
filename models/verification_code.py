from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
import uuid
import secrets
import random

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    phone_number = db.Column(db.String(20))
    code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), default='registration')
    attempts = db.Column(db.Integer, default=0)
    max_attempts = db.Column(db.Integer, default=3)
    is_verified = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.code = self.generate_code()
        self.expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    def generate_code(self):
        """Generate a 6-digit verification code"""
        return str(random.randint(100000, 999999))
    
    def verify_code(self, provided_code):
        """Verify the provided code"""
        # Check if code has expired
        if datetime.utcnow() > self.expires_at:
            return False, "Verification code has expired"
        
        # Check if maximum attempts exceeded
        if self.attempts >= self.max_attempts:
            return False, "Maximum verification attempts exceeded"
        
        # Increment attempts
        self.attempts += 1
        
        # Check if code matches
        if self.code != provided_code:
            return False, f"Invalid verification code. {self.max_attempts - self.attempts} attempts remaining"
        
        # Code is valid
        return True, "Code verified successfully"
    
    def is_expired(self):
        """Check if the verification code has expired"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'user_type': self.user_type,
            'phone_number': self.phone_number,
            'purpose': self.purpose,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'is_verified': self.is_verified,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
