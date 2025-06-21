from app import db
from models import attendance_status_enum, check_in_method_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('attendance_sessions.id'), nullable=False)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    attendance_status = db.Column(attendance_status_enum, nullable=False)
    check_in_method = db.Column(check_in_method_enum, default='face_recognition')
    face_match_confidence = db.Column(db.Numeric(5, 2))
    location_latitude = db.Column(db.Numeric(10, 8))
    location_longitude = db.Column(db.Numeric(11, 8))
    device_info = db.Column(JSONB)
    is_verified = db.Column(db.Boolean, default=True)
    verified_by = db.Column(UUID(as_uuid=True), db.ForeignKey('lecturers.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    verified_by_lecturer = db.relationship('Lecturer', foreign_keys=[verified_by])
    overrides = db.relationship('AttendanceOverride', backref='attendance_record', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('session_id', 'student_id', name='unique_session_student'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'student_id': str(self.student_id),
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'attendance_status': self.attendance_status,
            'check_in_method': self.check_in_method,
            'face_match_confidence': float(self.face_match_confidence) if self.face_match_confidence else None,
            'location_latitude': float(self.location_latitude) if self.location_latitude else None,
            'location_longitude': float(self.location_longitude) if self.location_longitude else None,
            'device_info': self.device_info,
            'is_verified': self.is_verified,
            'verified_by': str(self.verified_by) if self.verified_by else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }