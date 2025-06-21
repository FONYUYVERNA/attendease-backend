from app import db
from models import geofence_type_enum
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class GeofenceArea(db.Model):
    __tablename__ = 'geofence_areas'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    geofence_type = db.Column(geofence_type_enum, nullable=False, default='circular')
    center_latitude = db.Column(db.Numeric(10, 8), nullable=False)
    center_longitude = db.Column(db.Numeric(11, 8), nullable=False)
    radius_meters = db.Column(db.Integer)
    north_latitude = db.Column(db.Numeric(10, 8))
    south_latitude = db.Column(db.Numeric(10, 8))
    east_longitude = db.Column(db.Numeric(11, 8))
    west_longitude = db.Column(db.Numeric(11, 8))
    building = db.Column(db.String(100))
    floor = db.Column(db.String(20))
    capacity = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course_assignments = db.relationship('CourseAssignment', backref='geofence_area')
    attendance_sessions = db.relationship('AttendanceSession', backref='geofence_area')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'geofence_type': self.geofence_type,
            'center_latitude': float(self.center_latitude),
            'center_longitude': float(self.center_longitude),
            'radius_meters': self.radius_meters,
            'north_latitude': float(self.north_latitude) if self.north_latitude else None,
            'south_latitude': float(self.south_latitude) if self.south_latitude else None,
            'east_longitude': float(self.east_longitude) if self.east_longitude else None,
            'west_longitude': float(self.west_longitude) if self.west_longitude else None,
            'building': self.building,
            'floor': self.floor,
            'capacity': self.capacity,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }