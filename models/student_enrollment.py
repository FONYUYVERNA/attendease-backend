from app import db
from models import enrollment_status_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class StudentEnrollment(db.Model):
    __tablename__ = 'student_enrollments'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUID(as_uuid=True), db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    semester_id = db.Column(UUID(as_uuid=True), db.ForeignKey('semesters.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    enrollment_status = db.Column(enrollment_status_enum, default='enrolled')
    grade = db.Column(db.String(5))
    enrolled_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    
    # Relationships
    enrolled_by_user = db.relationship('User', foreign_keys=[enrolled_by])
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'semester_id', name='unique_enrollment'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'student_id': str(self.student_id),
            'course_id': str(self.course_id),
            'semester_id': str(self.semester_id),
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'enrollment_status': self.enrollment_status,
            'grade': self.grade,
            'enrolled_by': str(self.enrolled_by) if self.enrolled_by else None
        }