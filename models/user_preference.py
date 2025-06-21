from app import db
from models import theme_mode_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    theme_mode = db.Column(theme_mode_enum, default='system')
    auto_login = db.Column(db.Boolean, default=False)
    notification_enabled = db.Column(db.Boolean, default=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    preferences_data = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'theme_mode': self.theme_mode,
            'auto_login': self.auto_login,
            'notification_enabled': self.notification_enabled,
            'email_notifications': self.email_notifications,
            'push_notifications': self.push_notifications,
            'language': self.language,
            'timezone': self.timezone,
            'preferences_data': self.preferences_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }