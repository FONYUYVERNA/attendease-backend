from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class CourseAssignment(db.Model):
    __tablename__ = 'course_assignments'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lecturer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('lecturers.id'), nullable=False)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    semester_id = db.Column(UUID(as_uuid=True), db.ForeignKey('semesters.id'), nullable=False)
    geofence_area_id = db.Column(UUID(as_uuid=True), db.ForeignKey('geofence_areas.id'))
    assigned_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admins.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    attendance_sessions = db.relationship('AttendanceSession', backref='course_assignment', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('lecturer_id', 'course_id', 'semester_id', name='unique_assignment'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'lecturer_id': str(self.lecturer_id),
            'course_id': str(self.course_id),
            'semester_id': str(self.semester_id),
            'geofence_area_id': str(self.geofence_area_id) if self.geofence_area_id else None,
            'assigned_by': str(self.assigned_by),
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'is_active': self.is_active
        }