from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.geofence_area import GeofenceArea
from utils.decorators import admin_required, lecturer_required
from utils.validators import validate_required_fields, validate_coordinates, ValidationError

geofence_areas_bp = Blueprint('geofence_areas', __name__)

@geofence_areas_bp.route('', methods=['GET'])
@lecturer_required
def get_all_geofence_areas():
    try:
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        geofence_type = request.args.get('type')
        building = request.args.get('building')
        search = request.args.get('search')
        
        query = GeofenceArea.query
        
        if active_only:
            query = query.filter(GeofenceArea.is_active == True)
        
        if geofence_type:
            query = query.filter(GeofenceArea.geofence_type == geofence_type)
        
        if building:
            query = query.filter(GeofenceArea.building.ilike(f'%{building}%'))
        
        if search:
            query = query.filter(
                db.or_(
                    GeofenceArea.name.ilike(f'%{search}%'),
                    GeofenceArea.building.ilike(f'%{search}%')
                )
            )
        
        geofence_areas = query.order_by(GeofenceArea.name).all()
        
        return jsonify({
            'geofence_areas': [area.to_dict() for area in geofence_areas]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geofence_areas_bp.route('/<area_id>', methods=['GET'])
@lecturer_required
def get_geofence_area(area_id):
    try:
        area = GeofenceArea.query.get(area_id)
        
        if not area:
            return jsonify({'error': 'Geofence area not found'}), 404
        
        return jsonify({'geofence_area': area.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geofence_areas_bp.route('', methods=['POST'])
@admin_required
def create_geofence_area():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'geofence_type', 'center_latitude', 'center_longitude']
        validate_required_fields(data, required_fields)
        
        # Validate coordinates
        validate_coordinates(data['center_latitude'], data['center_longitude'])
        
        # Validate geofence type
        if data['geofence_type'] not in ['circular', 'rectangular']:
            return jsonify({'error': 'Invalid geofence type. Must be circular or rectangular'}), 400
        
        # Validate specific requirements based on geofence type
        if data['geofence_type'] == 'circular':
            if 'radius_meters' not in data or not data['radius_meters']:
                return jsonify({'error': 'Radius is required for circular geofence'}), 400
            if data['radius_meters'] <= 0:
                return jsonify({'error': 'Radius must be greater than 0'}), 400
        
        elif data['geofence_type'] == 'rectangular':
            required_rect_fields = ['north_latitude', 'south_latitude', 'east_longitude', 'west_longitude']
            for field in required_rect_fields:
                if field not in data or data[field] is None:
                    return jsonify({'error': f'{field} is required for rectangular geofence'}), 400
            
            # Validate rectangular coordinates
            for lat_field in ['north_latitude', 'south_latitude']:
                validate_coordinates(data[lat_field], data['center_longitude'])
            for lng_field in ['east_longitude', 'west_longitude']:
                validate_coordinates(data['center_latitude'], data[lng_field])
            
            # Validate logical bounds
            if data['north_latitude'] <= data['south_latitude']:
                return jsonify({'error': 'North latitude must be greater than south latitude'}), 400
            if data['east_longitude'] <= data['west_longitude']:
                return jsonify({'error': 'East longitude must be greater than west longitude'}), 400
        
        # Create geofence area
        geofence_area = GeofenceArea(
            name=data['name'],
            description=data.get('description'),
            geofence_type=data['geofence_type'],
            center_latitude=data['center_latitude'],
            center_longitude=data['center_longitude'],
            radius_meters=data.get('radius_meters') if data['geofence_type'] == 'circular' else None,
            north_latitude=data.get('north_latitude') if data['geofence_type'] == 'rectangular' else None,
            south_latitude=data.get('south_latitude') if data['geofence_type'] == 'rectangular' else None,
            east_longitude=data.get('east_longitude') if data['geofence_type'] == 'rectangular' else None,
            west_longitude=data.get('west_longitude') if data['geofence_type'] == 'rectangular' else None,
            building=data.get('building'),
            floor=data.get('floor'),
            capacity=data.get('capacity')
        )
        
        db.session.add(geofence_area)
        db.session.commit()
        
        return jsonify({
            'message': 'Geofence area created successfully',
            'geofence_area': geofence_area.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@geofence_areas_bp.route('/<area_id>', methods=['PUT'])
@admin_required
def update_geofence_area(area_id):
    try:
        area = GeofenceArea.query.get(area_id)
        
        if not area:
            return jsonify({'error': 'Geofence area not found'}), 404
        
        data = request.get_json()
        
        # Update basic fields
        basic_fields = ['name', 'description', 'building', 'floor', 'capacity', 'is_active']
        for field in basic_fields:
            if field in data:
                setattr(area, field, data[field])
        
        # Update coordinates if provided
        if 'center_latitude' in data:
            validate_coordinates(data['center_latitude'], area.center_longitude)
            area.center_latitude = data['center_latitude']
        
        if 'center_longitude' in data:
            validate_coordinates(area.center_latitude, data['center_longitude'])
            area.center_longitude = data['center_longitude']
        
        # Update geofence type and related fields
        if 'geofence_type' in data:
            if data['geofence_type'] not in ['circular', 'rectangular']:
                return jsonify({'error': 'Invalid geofence type'}), 400
            
            area.geofence_type = data['geofence_type']
            
            # Reset fields based on new type
            if data['geofence_type'] == 'circular':
                area.north_latitude = None
                area.south_latitude = None
                area.east_longitude = None
                area.west_longitude = None
                if 'radius_meters' not in data:
                    return jsonify({'error': 'Radius is required for circular geofence'}), 400
            else:  # rectangular
                area.radius_meters = None
        
        # Update type-specific fields
        if area.geofence_type == 'circular':
            if 'radius_meters' in data:
                if data['radius_meters'] <= 0:
                    return jsonify({'error': 'Radius must be greater than 0'}), 400
                area.radius_meters = data['radius_meters']
        
        elif area.geofence_type == 'rectangular':
            rect_fields = ['north_latitude', 'south_latitude', 'east_longitude', 'west_longitude']
            for field in rect_fields:
                if field in data:
                    if field.endswith('_latitude'):
                        validate_coordinates(data[field], area.center_longitude)
                    else:
                        validate_coordinates(area.center_latitude, data[field])
                    setattr(area, field, data[field])
            
            # Validate bounds after updates
            if (area.north_latitude and area.south_latitude and 
                area.north_latitude <= area.south_latitude):
                return jsonify({'error': 'North latitude must be greater than south latitude'}), 400
            
            if (area.east_longitude and area.west_longitude and 
                area.east_longitude <= area.west_longitude):
                return jsonify({'error': 'East longitude must be greater than west longitude'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': 'Geofence area updated successfully',
            'geofence_area': area.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@geofence_areas_bp.route('/<area_id>', methods=['DELETE'])
@admin_required
def delete_geofence_area(area_id):
    try:
        area = GeofenceArea.query.get(area_id)
        
        if not area:
            return jsonify({'error': 'Geofence area not found'}), 404
        
        # Check if area has associated course assignments or attendance sessions
        if area.course_assignments or area.attendance_sessions:
            # Soft delete - deactivate instead of deleting
            area.is_active = False
            db.session.commit()
            return jsonify({'message': 'Geofence area deactivated successfully'}), 200
        
        # Hard delete if no associations
        db.session.delete(area)
        db.session.commit()
        
        return jsonify({'message': 'Geofence area deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@geofence_areas_bp.route('/check-location', methods=['POST'])
@lecturer_required
def check_location_in_geofence():
    try:
        data = request.get_json()
        
        required_fields = ['latitude', 'longitude', 'geofence_area_id']
        validate_required_fields(data, required_fields)
        
        # Validate coordinates
        validate_coordinates(data['latitude'], data['longitude'])
        
        # Get geofence area
        area = GeofenceArea.query.get(data['geofence_area_id'])
        if not area or not area.is_active:
            return jsonify({'error': 'Geofence area not found or inactive'}), 404
        
        # Check if location is within geofence using database function
        result = db.session.execute(
            "SELECT is_within_geofence(:lat, :lng, :geofence_id)",
            {
                'lat': data['latitude'],
                'lng': data['longitude'],
                'geofence_id': data['geofence_area_id']
            }
        ).fetchone()
        
        is_within = result[0] if result else False
        
        return jsonify({
            'is_within_geofence': is_within,
            'geofence_area': area.to_dict()
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@geofence_areas_bp.route('/statistics', methods=['GET'])
@admin_required
def get_geofence_statistics():
    try:
        # Total active geofence areas
        total_areas = GeofenceArea.query.filter_by(is_active=True).count()
        
        # Areas by type
        type_stats = db.session.query(
            GeofenceArea.geofence_type,
            db.func.count(GeofenceArea.id).label('count')
        ).filter(GeofenceArea.is_active == True).group_by(GeofenceArea.geofence_type).all()
        
        # Areas by building
        building_stats = db.session.query(
            GeofenceArea.building,
            db.func.count(GeofenceArea.id).label('count')
        ).filter(
            GeofenceArea.is_active == True,
            GeofenceArea.building.isnot(None)
        ).group_by(GeofenceArea.building).all()
        
        return jsonify({
            'total_areas': total_areas,
            'by_type': [{'type': stat.geofence_type, 'count': stat.count} for stat in type_stats],
            'by_building': [{'building': stat.building, 'count': stat.count} for stat in building_stats]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500