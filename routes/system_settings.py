from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.system_setting import SystemSetting
from models.admin import Admin
from utils.decorators import admin_required, get_current_user
from utils.validators import validate_required_fields, ValidationError
import json

system_settings_bp = Blueprint('system_settings', __name__)

@system_settings_bp.route('', methods=['GET'])
@jwt_required()
def get_all_system_settings():
    try:
        current_user = get_current_user()
        
        # Non-admin users can only see public settings
        if current_user.user_type != 'admin':
            settings = SystemSetting.query.filter_by(is_public=True).all()
        else:
            settings = SystemSetting.query.all()
        
        return jsonify({
            'system_settings': [setting.to_dict() for setting in settings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/<setting_key>', methods=['GET'])
@jwt_required()
def get_system_setting(setting_key):
    try:
        current_user = get_current_user()
        setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
        
        if not setting:
            return jsonify({'error': 'System setting not found'}), 404
        
        # Check if user can access this setting
        if not setting.is_public and current_user.user_type != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'system_setting': setting.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('', methods=['POST'])
@admin_required
def create_system_setting():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['setting_key', 'setting_value']
        validate_required_fields(data, required_fields)
        
        # Check if setting key already exists
        if SystemSetting.query.filter_by(setting_key=data['setting_key']).first():
            return jsonify({'error': 'Setting key already exists'}), 409
        
        # Validate setting type
        setting_type = data.get('setting_type', 'string')
        if setting_type not in ['string', 'number', 'boolean', 'json']:
            return jsonify({'error': 'Invalid setting type'}), 400
        
        # Validate setting value based on type
        setting_value = data['setting_value']
        if setting_type == 'number':
            try:
                float(setting_value)
            except ValueError:
                return jsonify({'error': 'Setting value must be a valid number'}), 400
        elif setting_type == 'boolean':
            if setting_value not in ['true', 'false', True, False]:
                return jsonify({'error': 'Setting value must be true or false'}), 400
        elif setting_type == 'json':
            try:
                json.loads(setting_value) if isinstance(setting_value, str) else setting_value
            except (json.JSONDecodeError, TypeError):
                return jsonify({'error': 'Setting value must be valid JSON'}), 400
        
        # Get admin profile
        admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
        
        # Create system setting
        setting = SystemSetting(
            setting_key=data['setting_key'],
            setting_value=str(setting_value),
            setting_type=setting_type,
            description=data.get('description'),
            is_public=data.get('is_public', False),
            updated_by=admin_profile.id if admin_profile else None
        )
        
        db.session.add(setting)
        db.session.commit()
        
        return jsonify({
            'message': 'System setting created successfully',
            'system_setting': setting.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/<setting_key>', methods=['PUT'])
@admin_required
def update_system_setting(setting_key):
    try:
        current_user = get_current_user()
        setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
        
        if not setting:
            return jsonify({'error': 'System setting not found'}), 404
        
        data = request.get_json()
        
        # Update setting value
        if 'setting_value' in data:
            setting_value = data['setting_value']
            
            # Validate setting value based on type
            if setting.setting_type == 'number':
                try:
                    float(setting_value)
                except ValueError:
                    return jsonify({'error': 'Setting value must be a valid number'}), 400
            elif setting.setting_type == 'boolean':
                if setting_value not in ['true', 'false', True, False]:
                    return jsonify({'error': 'Setting value must be true or false'}), 400
            elif setting.setting_type == 'json':
                try:
                    json.loads(setting_value) if isinstance(setting_value, str) else setting_value
                except (json.JSONDecodeError, TypeError):
                    return jsonify({'error': 'Setting value must be valid JSON'}), 400
            
            setting.setting_value = str(setting_value)
        
        # Update other fields
        if 'description' in data:
            setting.description = data['description']
        
        if 'is_public' in data:
            setting.is_public = data['is_public']
        
        # Update the updated_by field
        admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
        if admin_profile:
            setting.updated_by = admin_profile.id
        
        db.session.commit()
        
        return jsonify({
            'message': 'System setting updated successfully',
            'system_setting': setting.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/<setting_key>', methods=['DELETE'])
@admin_required
def delete_system_setting(setting_key):
    try:
        setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
        
        if not setting:
            return jsonify({'error': 'System setting not found'}), 404
        
        db.session.delete(setting)
        db.session.commit()
        
        return jsonify({'message': 'System setting deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/bulk-update', methods=['POST'])
@admin_required
def bulk_update_settings():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        if not isinstance(data, dict) or 'settings' not in data:
            return jsonify({'error': 'Invalid request format. Expected {settings: {...}}'}), 400
        
        settings_data = data['settings']
        if not isinstance(settings_data, dict):
            return jsonify({'error': 'Settings must be a dictionary'}), 400
        
        admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
        updated_settings = []
        created_settings = []
        
        for setting_key, setting_value in settings_data.items():
            setting = SystemSetting.query.filter_by(setting_key=setting_key).first()
            
            if setting:
                # Update existing setting
                # Validate based on existing type
                if setting.setting_type == 'number':
                    try:
                        float(setting_value)
                    except ValueError:
                        return jsonify({'error': f'Setting {setting_key} must be a valid number'}), 400
                elif setting.setting_type == 'boolean':
                    if setting_value not in ['true', 'false', True, False]:
                        return jsonify({'error': f'Setting {setting_key} must be true or false'}), 400
                elif setting.setting_type == 'json':
                    try:
                        json.loads(setting_value) if isinstance(setting_value, str) else setting_value
                    except (json.JSONDecodeError, TypeError):
                        return jsonify({'error': f'Setting {setting_key} must be valid JSON'}), 400
                
                setting.setting_value = str(setting_value)
                if admin_profile:
                    setting.updated_by = admin_profile.id
                updated_settings.append(setting_key)
            else:
                # Create new setting (default to string type)
                new_setting = SystemSetting(
                    setting_key=setting_key,
                    setting_value=str(setting_value),
                    setting_type='string',
                    updated_by=admin_profile.id if admin_profile else None
                )
                db.session.add(new_setting)
                created_settings.append(setting_key)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Bulk update completed. Updated: {len(updated_settings)}, Created: {len(created_settings)}',
            'updated_settings': updated_settings,
            'created_settings': created_settings
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/public', methods=['GET'])
def get_public_settings():
    """Get public settings without authentication"""
    try:
        settings = SystemSetting.query.filter_by(is_public=True).all()
        
        return jsonify({
            'public_settings': [setting.to_dict() for setting in settings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/categories', methods=['GET'])
@admin_required
def get_settings_by_category():
    """Group settings by category (based on key prefix)"""
    try:
        settings = SystemSetting.query.all()
        categories = {}
        
        for setting in settings:
            # Extract category from setting key (e.g., "app.name" -> "app")
            parts = setting.setting_key.split('.')
            category = parts[0] if len(parts) > 1 else 'general'
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(setting.to_dict())
        
        return jsonify({'categories': categories}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@system_settings_bp.route('/reset-defaults', methods=['POST'])
@admin_required
def reset_to_defaults():
    """Reset system settings to default values"""
    try:
        current_user = get_current_user()
        admin_profile = Admin.query.filter_by(user_id=current_user.id).first()
        
        # Define default settings
        default_settings = {
            'app.name': 'AttendEase',
            'app.version': '1.0.0',
            'attendance.late_threshold_minutes': '15',
            'attendance.auto_end_minutes': '120',
            'geofence.default_radius_meters': '50',
            'notifications.enabled': 'true',
            'face_recognition.confidence_threshold': '0.8'
        }
        
        reset_count = 0
        for key, value in default_settings.items():
            setting = SystemSetting.query.filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = value
                if admin_profile:
                    setting.updated_by = admin_profile.id
                reset_count += 1
            else:
                # Create if doesn't exist
                new_setting = SystemSetting(
                    setting_key=key,
                    setting_value=value,
                    setting_type='string',
                    description=f'Default setting for {key}',
                    updated_by=admin_profile.id if admin_profile else None
                )
                db.session.add(new_setting)
                reset_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Reset {reset_count} settings to default values'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500