from app import db
from models import setting_type_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    setting_type = db.Column(setting_type_enum, default='string')
    description = db.Column(db.Text)
    is_public = db.Column(db.Boolean, default=False)
    updated_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admins.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'setting_key': self.setting_key,
            'setting_value': self.setting_value,
            'setting_type': self.setting_type,
            'description': self.description,
            'is_public': self.is_public,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }