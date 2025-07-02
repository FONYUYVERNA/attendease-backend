from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID
import secrets
import string
import uuid

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    # Production has UUID, not string - match exactly
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), nullable=False, index=True)
    
    # Production has character varying, not enum - match exactly
    user_type = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    code = db.Column(db.String(10), nullable=False)
    
    # Production has character varying with NULL default - match exactly
    purpose = db.Column(db.String(50), nullable=True, default='registration')
    
    # Production has these columns - keep them
    is_verified = db.Column(db.Boolean, nullable=True, default=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Backend expects these columns - keep them too
    is_used = db.Column(db.Boolean, nullable=False, default=False)
    used_at = db.Column(db.DateTime, nullable=True)
    
    # Production has integer with NULL default - match exactly
    attempts = db.Column(db.Integer, nullable=True, default=0)
    max_attempts = db.Column(db.Integer, nullable=True, default=5)
    
    # Production has timestamp without time zone with NULL default - match exactly
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
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
        # Also reset the old columns for compatibility
        self.is_verified = False
        self.verified_at = None
    
    def verify_code(self, entered_code):
        """Verify the entered code"""
        if self.is_used:
            return False
        
        if self.is_expired():
            return False
        
        if self.attempts and self.attempts >= (self.max_attempts or 5):
            return False
        
        # Increment attempts (handle None case)
        self.attempts = (self.attempts or 0) + 1
        
        if self.code == entered_code:
            return True
        
        return False
    
    def is_expired(self):
        """Check if the code has expired"""
        return datetime.utcnow() > self.expires_at
    
    def mark_as_used(self):
        """Mark the code as used - update both old and new columns"""
        self.is_used = True
        self.used_at = datetime.utcnow()
        # Also update old columns for compatibility
        self.is_verified = True
        self.verified_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<VerificationCode {self.id}: {self.email} - {self.purpose}>'
