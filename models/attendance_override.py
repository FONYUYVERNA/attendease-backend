from app import db
from models import attendance_status_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AttendanceOverride(db.Model):
    __tablename__ = 'attendance_overrides'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attendance_record_id = db.Column(UUID(as_uuid=True), db.ForeignKey('attendance_records.id'), nullable=False)
    original_status = db.Column(attendance_status_enum, nullable=False)
    new_status = db.Column(attendance_status_enum, nullable=False)
    override_reason = db.Column(db.Text, nullable=False)
    overridden_by = db.Column(UUID(as_uuid=True), db.ForeignKey('lecturers.id'), nullable=False)
    overridden_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(UUID(as_uuid=True), db.ForeignKey('admins.id'))
    approved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'attendance_record_id': str(self.attendance_record_id),
            'original_status': self.original_status,
            'new_status': self.new_status,
            'override_reason': self.override_reason,
            'overridden_by': str(self.overridden_by),
            'overridden_at': self.overridden_at.isoformat() if self.overridden_at else None,
            'approved_by': str(self.approved_by) if self.approved_by else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }