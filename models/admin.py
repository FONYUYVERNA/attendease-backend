from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    admin_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    institution = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    profile_image_url = db.Column(db.String(500))
    role = db.Column(db.String(50), default='System Administrator')
    permissions = db.Column(JSONB)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course_assignments_made = db.relationship('CourseAssignment', backref='assigned_by_admin')
    system_settings_updated = db.relationship('SystemSetting', backref='updated_by_admin')
    attendance_overrides_approved = db.relationship('AttendanceOverride', backref='approved_by_admin')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'admin_id': self.admin_id,
            'full_name': self.full_name,
            'institution': self.institution,
            'phone_number': self.phone_number,
            'profile_image_url': self.profile_image_url,
            'role': self.role,
            'permissions': self.permissions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
