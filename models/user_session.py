from app import db
from datetime import datetime, timedelta
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import secrets

class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    device_info = db.Column(JSONB)
    ip_address = db.Column(db.Text)
    user_agent = db.Column(db.Text)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='user_sessions')
    
    def __init__(self, **kwargs):
        super(UserSession, self).__init__(**kwargs)
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=30)
    
    def __repr__(self):
        return f'<UserSession {self.session_token[:8]}... for {self.user_id}>'
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'session_token': self.session_token,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def extend_session(self, days=30):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def deactivate(self):
        """Deactivate session"""
        self.is_active = False
        db.session.commit()
    
    @staticmethod
    def create_session(user_id, device_info=None, ip_address=None, user_agent=None):
        """Create a new user session"""
        try:
            session = UserSession(
                user_id=user_id,
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.session.add(session)
            db.session.commit()
            return session
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user session: {e}")
            return None
    
    @staticmethod
    def get_active_session(session_token):
        """Get active session by token"""
        session = UserSession.query.filter_by(
            session_token=session_token,
            is_active=True
        ).first()
        
        if session and not session.is_expired():
            # Update last activity
            session.last_activity = datetime.utcnow()
            db.session.commit()
            return session
        elif session:
            # Deactivate expired session
            session.deactivate()
        
        return None
    
    @staticmethod
    def cleanup_expired_sessions():
        """Remove expired sessions"""
        try:
            expired_sessions = UserSession.query.filter(
                UserSession.expires_at < datetime.utcnow()
            ).all()
            
            for session in expired_sessions:
                db.session.delete(session)
            
            db.session.commit()
            return len(expired_sessions)
        except Exception as e:
            db.session.rollback()
            print(f"Error cleaning up expired sessions: {e}")
            return 0
