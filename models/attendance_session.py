from app import db
from models import session_status_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AttendanceSession(db.Model):
    __tablename__ = 'attendance_sessions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_assignment_id = db.Column(UUID(as_uuid=True), db.ForeignKey('course_assignments.id'), nullable=False)
    geofence_area_id = db.Column(UUID(as_uuid=True), db.ForeignKey('geofence_areas.id'), nullable=False)
    session_name = db.Column(db.String(255))
    topic = db.Column(db.String(255))
    started_by = db.Column(UUID(as_uuid=True), db.ForeignKey('lecturers.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    session_status = db.Column(session_status_enum, default='active')
    expected_students = db.Column(db.Integer, default=0)
    checked_in_students = db.Column(db.Integer, default=0)
    late_threshold_minutes = db.Column(db.Integer, default=15)
    auto_end_minutes = db.Column(db.Integer, default=120)
    notes = db.Column(db.Text)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='session', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'course_assignment_id': str(self.course_assignment_id),
            'geofence_area_id': str(self.geofence_area_id),
            'session_name': self.session_name,
            'topic': self.topic,
            'started_by': str(self.started_by),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'session_status': self.session_status,
            'expected_students': self.expected_students,
            'checked_in_students': self.checked_in_students,
            'late_threshold_minutes': self.late_threshold_minutes,
            'auto_end_minutes': self.auto_end_minutes,
            'notes': self.notes
        }