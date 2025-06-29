from app import db
from models import level_enum, gender_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    matricle_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    department_id = db.Column(UUID(as_uuid=True), db.ForeignKey('departments.id'), nullable=False)
    level = db.Column(level_enum, nullable=False)
    gender = db.Column(gender_enum, nullable=False)
    phone_number = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    profile_image_url = db.Column(db.String(500))
    face_encoding_data = db.Column(db.Text)
    is_face_registered = db.Column(db.Boolean, default=False)
    enrollment_year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = db.relationship('Department', backref='students')
    enrollments = db.relationship('StudentEnrollment', backref='student', cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='student', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'matricle_number': self.matricle_number,
            'full_name': self.full_name,
            'department_id': str(self.department_id),
            'level': self.level,
            'gender': self.gender,
            'phone_number': self.phone_number,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'profile_image_url': self.profile_image_url,
            'is_face_registered': self.is_face_registered,
            'enrollment_year': self.enrollment_year,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def is_matricle_unique(cls, matricle_number, exclude_id=None):
        """Check if matricle number is unique"""
        query = cls.query.filter_by(matricle_number=matricle_number)
        if exclude_id:
            query = query.filter(cls.id != exclude_id)
        return query.first() is None

    @classmethod  
    def validate_matricle_uniqueness(cls, matricle_number, exclude_id=None):
        """Validate matricle number uniqueness and raise error if not unique"""
        if not cls.is_matricle_unique(matricle_number, exclude_id):
            from utils.validators import ValidationError
            raise ValidationError(f"Matricle number '{matricle_number}' already exists", "matricle_number")
