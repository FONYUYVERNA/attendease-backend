from app import db
from models import level_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_code = db.Column(db.String(20), unique=True, nullable=False)
    course_title = db.Column(db.String(255), nullable=False)
    department_id = db.Column(UUID(as_uuid=True), db.ForeignKey('departments.id'), nullable=False)
    level = db.Column(level_enum, nullable=False)
    credit_units = db.Column(db.SmallInteger, default=3)
    semester_number = db.Column(db.SmallInteger)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('CourseAssignment', backref='course', cascade='all, delete-orphan')
    enrollments = db.relationship('StudentEnrollment', backref='course', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.CheckConstraint('semester_number IN (1, 2)', name='check_course_semester_number'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'course_code': self.course_code,
            'course_title': self.course_title,
            'department_id': str(self.department_id),
            'level': self.level,
            'credit_units': self.credit_units,
            'semester_number': self.semester_number,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }