from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.notification import Notification
from models.user import User
from utils.decorators import admin_required, get_current_user
from utils.validators import validate_required_fields, ValidationError
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
@jwt_required()
def get_user_notifications():
    try:
        current_user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        notification_type = request.args.get('type')
        
        query = Notification.query.filter_by(recipient_id=current_user.id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        if notification_type:
            query = query.filter_by(notification_type=notification_type)
        
        # Filter out expired notifications
        query = query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        notifications = query.order_by(Notification.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications.items],
            'pagination': {
                'page': notifications.page,
                'pages': notifications.pages,
                'per_page': notifications.per_page,
                'total': notifications.total,
                'has_next': notifications.has_next,
                'has_prev': notifications.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<notification_id>', methods=['GET'])
@jwt_required()
def get_notification(notification_id):
    try:
        current_user = get_current_user()
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Check if user can access this notification
        if notification.recipient_id != current_user.id and current_user.user_type != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'notification': notification.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('', methods=['POST'])
@admin_required
def create_notification():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['recipient_id', 'notification_type', 'title', 'message']
        validate_required_fields(data, required_fields)
        
        # Validate notification type
        valid_types = ['session_started', 'session_ending', 'attendance_reminder', 'system_alert', 'course_update']
        if data['notification_type'] not in valid_types:
            return jsonify({'error': 'Invalid notification type'}), 400
        
        # Check if recipient exists
        recipient = User.query.get(data['recipient_id'])
        if not recipient:
            return jsonify({'error': 'Recipient not found'}), 404
        
        # Parse expires_at if provided
        expires_at = None
        if data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expires_at format. Use ISO format'}), 400
        
        # Create notification
        notification = Notification(
            recipient_id=data['recipient_id'],
            sender_id=current_user.id,
            notification_type=data['notification_type'],
            title=data['title'],
            message=data['message'],
            data=data.get('data'),
            expires_at=expires_at
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Notification created successfully',
            'notification': notification.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<notification_id>/mark-read', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    try:
        current_user = get_current_user()
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Check if user can mark this notification as read
        if notification.recipient_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.session.commit()
        
        return jsonify({
            'message': 'Notification marked as read',
            'notification': notification.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    try:
        current_user = get_current_user()
        
        # Update all unread notifications for the user
        unread_notifications = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).all()
        
        for notification in unread_notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Marked {len(unread_notifications)} notifications as read'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    try:
        current_user = get_current_user()
        notification = Notification.query.get(notification_id)
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        # Check if user can delete this notification
        if notification.recipient_id != current_user.id and current_user.user_type != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Notification deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/broadcast', methods=['POST'])
@admin_required
def broadcast_notification():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['user_type', 'notification_type', 'title', 'message']
        validate_required_fields(data, required_fields)
        
        # Validate notification type
        valid_types = ['session_started', 'session_ending', 'attendance_reminder', 'system_alert', 'course_update']
        if data['notification_type'] not in valid_types:
            return jsonify({'error': 'Invalid notification type'}), 400
        
        # Validate user type
        if data['user_type'] not in ['all', 'student', 'lecturer', 'admin']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        # Get target users
        query = User.query.filter_by(is_active=True)
        if data['user_type'] != 'all':
            query = query.filter_by(user_type=data['user_type'])
        
        target_users = query.all()
        
        # Parse expires_at if provided
        expires_at = None
        if data.get('expires_at'):
            try:
                expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid expires_at format. Use ISO format'}), 400
        
        # Create notifications for all target users
        notifications_created = 0
        for user in target_users:
            notification = Notification(
                recipient_id=user.id,
                sender_id=current_user.id,
                notification_type=data['notification_type'],
                title=data['title'],
                message=data['message'],
                data=data.get('data'),
                expires_at=expires_at
            )
            db.session.add(notification)
            notifications_created += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Broadcast notification sent to {notifications_created} users'
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    try:
        current_user = get_current_user()
        
        unread_count = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        ).count()
        
        return jsonify({'unread_count': unread_count}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/cleanup-expired', methods=['POST'])
@admin_required
def cleanup_expired_notifications():
    try:
        # Delete expired notifications
        expired_notifications = Notification.query.filter(
            Notification.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_notifications)
        for notification in expired_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Cleaned up {count} expired notifications'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/statistics', methods=['GET'])
@admin_required
def get_notification_statistics():
    try:
        # Total notifications
        total_notifications = Notification.query.count()
        
        # Unread notifications
        unread_notifications = Notification.query.filter_by(is_read=False).count()
        
        # Notifications by type
        type_stats = db.session.query(
            Notification.notification_type,
            db.func.count(Notification.id).label('count')
        ).group_by(Notification.notification_type).all()
        
        # Recent notifications (last 7 days)
        from datetime import timedelta
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_notifications = Notification.query.filter(
            Notification.created_at >= seven_days_ago
        ).count()
        
        return jsonify({
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'recent_notifications_7_days': recent_notifications,
            'by_type': [
                {'type': stat.notification_type, 'count': stat.count} 
                for stat in type_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500