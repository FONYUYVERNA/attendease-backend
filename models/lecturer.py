from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Lecturer(db.Model):
    __tablename__ = 'lecturers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    lecturer_id = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    institutional_email = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))
    profile_image_url = db.Column(db.String(500))
    specialization = db.Column(db.String(255))
    hire_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course_assignments = db.relationship('CourseAssignment', backref='lecturer', cascade='all, delete-orphan')
    attendance_sessions_started = db.relationship('AttendanceSession', backref='started_by_lecturer', cascade='all, delete-orphan')
    attendance_overrides = db.relationship('AttendanceOverride', backref='overridden_by_lecturer')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'lecturer_id': self.lecturer_id,
            'full_name': self.full_name,
            'institutional_email': self.institutional_email,
            'phone_number': self.phone_number,
            'profile_image_url': self.profile_image_url,
            'specialization': self.specialization,
            'hire_date': self.hire_date.isoformat() if self.hire_date else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }