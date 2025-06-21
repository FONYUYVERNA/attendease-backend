from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AcademicYear(db.Model):
    __tablename__ = 'academic_years'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    year_name = db.Column(db.String(20), unique=True, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    semesters = db.relationship('Semester', backref='academic_year', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'year_name': self.year_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_current': self.is_current,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }