from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Semester(db.Model):
    __tablename__ = 'semesters'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    academic_year_id = db.Column(UUID(as_uuid=True), db.ForeignKey('academic_years.id'), nullable=False)
    semester_number = db.Column(db.SmallInteger, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course_assignments = db.relationship('CourseAssignment', backref='semester', cascade='all, delete-orphan')
    student_enrollments = db.relationship('StudentEnrollment', backref='semester', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('academic_year_id', 'semester_number', name='unique_semester_year'),
        db.CheckConstraint('semester_number IN (1, 2)', name='check_semester_number')
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'academic_year_id': str(self.academic_year_id),
            'semester_number': self.semester_number,
            'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def validate_dates(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        return True
