from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.student_enrollment import StudentEnrollment
from models.student import Student
from models.course import Course
from models.semester import Semester
from utils.decorators import admin_required, lecturer_required, student_required, get_current_user
from utils.validators import validate_required_fields, ValidationError

student_enrollments_bp = Blueprint('student_enrollments', __name__)

@student_enrollments_bp.route('', methods=['GET'])
@lecturer_required
def get_all_student_enrollments():
    try:
        current_user = get_current_user()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        student_id = request.args.get('student_id')
        course_id = request.args.get('course_id')
        semester_id = request.args.get('semester_id')
        status = request.args.get('status')
        
        query = StudentEnrollment.query
        
        # If user is student, only show their enrollments
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile:
                query = query.filter(StudentEnrollment.student_id == student_profile.id)
        
        if student_id and current_user.user_type in ['lecturer', 'admin']:
            query = query.filter(StudentEnrollment.student_id == student_id)
        
        if course_id:
            query = query.filter(StudentEnrollment.course_id == course_id)
        
        if semester_id:
            query = query.filter(StudentEnrollment.semester_id == semester_id)
        
        if status:
            query = query.filter(StudentEnrollment.enrollment_status == status)
        
        enrollments = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'student_enrollments': [enrollment.to_dict() for enrollment in enrollments.items],
            'pagination': {
                'page': enrollments.page,
                'pages': enrollments.pages,
                'per_page': enrollments.per_page,
                'total': enrollments.total,
                'has_next': enrollments.has_next,
                'has_prev': enrollments.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/<enrollment_id>', methods=['GET'])
@student_required
def get_student_enrollment(enrollment_id):
    try:
        current_user = get_current_user()
        enrollment = StudentEnrollment.query.get(enrollment_id)
        
        if not enrollment:
            return jsonify({'error': 'Student enrollment not found'}), 404
        
        # Check if student can access this enrollment
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile and enrollment.student_id != student_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        return jsonify({'student_enrollment': enrollment.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('', methods=['POST'])
@admin_required
def create_student_enrollment():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['student_id', 'course_id', 'semester_id']
        validate_required_fields(data, required_fields)
        
        # Check if student exists
        student = Student.query.get(data['student_id'])
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Check if course exists
        course = Course.query.get(data['course_id'])
        if not course or not course.is_active:
            return jsonify({'error': 'Course not found or inactive'}), 404
        
        # Check if semester exists
        semester = Semester.query.get(data['semester_id'])
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        # Check if enrollment already exists
        existing = StudentEnrollment.query.filter_by(
            student_id=data['student_id'],
            course_id=data['course_id'],
            semester_id=data['semester_id']
        ).first()
        if existing:
            return jsonify({'error': 'Student enrollment already exists'}), 409
        
        # Validate enrollment status
        if 'enrollment_status' in data:
            if data['enrollment_status'] not in ['enrolled', 'dropped', 'completed']:
                return jsonify({'error': 'Invalid enrollment status'}), 400
        
        # Create student enrollment
        enrollment = StudentEnrollment(
            student_id=data['student_id'],
            course_id=data['course_id'],
            semester_id=data['semester_id'],
            enrollment_status=data.get('enrollment_status', 'enrolled'),
            grade=data.get('grade'),
            enrolled_by=current_user.id
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        return jsonify({
            'message': 'Student enrollment created successfully',
            'student_enrollment': enrollment.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/<enrollment_id>', methods=['PUT'])
@lecturer_required
def update_student_enrollment(enrollment_id):
    try:
        current_user = get_current_user()
        enrollment = StudentEnrollment.query.get(enrollment_id)
        
        if not enrollment:
            return jsonify({'error': 'Student enrollment not found'}), 404
        
        data = request.get_json()
        
        # Update enrollment status
        if 'enrollment_status' in data:
            if data['enrollment_status'] not in ['enrolled', 'dropped', 'completed']:
                return jsonify({'error': 'Invalid enrollment status'}), 400
            enrollment.enrollment_status = data['enrollment_status']
        
        # Update grade (only lecturers and admins can update grades)
        if 'grade' in data and current_user.user_type in ['lecturer', 'admin']:
            enrollment.grade = data['grade']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Student enrollment updated successfully',
            'student_enrollment': enrollment.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/<enrollment_id>', methods=['DELETE'])
@admin_required
def delete_student_enrollment(enrollment_id):
    try:
        enrollment = StudentEnrollment.query.get(enrollment_id)
        
        if not enrollment:
            return jsonify({'error': 'Student enrollment not found'}), 404
        
        # Change status to dropped instead of deleting
        enrollment.enrollment_status = 'dropped'
        db.session.commit()
        
        return jsonify({'message': 'Student enrollment dropped successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/student/<student_id>/current', methods=['GET'])
@student_required
def get_student_current_enrollments(student_id):
    try:
        current_user = get_current_user()
        
        # Check if student can access these enrollments
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile and str(student_profile.id) != student_id:
                return jsonify({'error': 'Access denied'}), 403
        
        # Get current semester
        current_semester = Semester.query.filter_by(is_current=True).first()
        if not current_semester:
            return jsonify({'error': 'No current semester set'}), 404
        
        enrollments = StudentEnrollment.query.filter_by(
            student_id=student_id,
            semester_id=current_semester.id,
            enrollment_status='enrolled'
        ).all()
        
        return jsonify({
            'student_enrollments': [enrollment.to_dict() for enrollment in enrollments],
            'semester': current_semester.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/course/<course_id>/enrolled', methods=['GET'])
@lecturer_required
def get_course_enrolled_students(course_id):
    try:
        semester_id = request.args.get('semester_id')
        
        query = StudentEnrollment.query.filter_by(
            course_id=course_id,
            enrollment_status='enrolled'
        )
        
        if semester_id:
            query = query.filter_by(semester_id=semester_id)
        else:
            # Default to current semester
            current_semester = Semester.query.filter_by(is_current=True).first()
            if current_semester:
                query = query.filter_by(semester_id=current_semester.id)
        
        enrollments = query.all()
        
        return jsonify({
            'enrolled_students': [enrollment.to_dict() for enrollment in enrollments]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/bulk-enroll', methods=['POST'])
@admin_required
def bulk_enroll_students():
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # Validate required fields
        required_fields = ['student_ids', 'course_id', 'semester_id']
        validate_required_fields(data, required_fields)
        
        if not isinstance(data['student_ids'], list) or not data['student_ids']:
            return jsonify({'error': 'student_ids must be a non-empty list'}), 400
        
        # Check if course exists
        course = Course.query.get(data['course_id'])
        if not course or not course.is_active:
            return jsonify({'error': 'Course not found or inactive'}), 404
        
        # Check if semester exists
        semester = Semester.query.get(data['semester_id'])
        if not semester:
            return jsonify({'error': 'Semester not found'}), 404
        
        successful_enrollments = []
        failed_enrollments = []
        
        for student_id in data['student_ids']:
            try:
                # Check if student exists
                student = Student.query.get(student_id)
                if not student:
                    failed_enrollments.append({
                        'student_id': student_id,
                        'error': 'Student not found'
                    })
                    continue
                
                # Check if enrollment already exists
                existing = StudentEnrollment.query.filter_by(
                    student_id=student_id,
                    course_id=data['course_id'],
                    semester_id=data['semester_id']
                ).first()
                if existing:
                    failed_enrollments.append({
                        'student_id': student_id,
                        'error': 'Enrollment already exists'
                    })
                    continue
                
                # Create enrollment
                enrollment = StudentEnrollment(
                    student_id=student_id,
                    course_id=data['course_id'],
                    semester_id=data['semester_id'],
                    enrollment_status='enrolled',
                    enrolled_by=current_user.id
                )
                
                db.session.add(enrollment)
                successful_enrollments.append(student_id)
                
            except Exception as e:
                failed_enrollments.append({
                    'student_id': student_id,
                    'error': str(e)
                })
        
        db.session.commit()
        
        return jsonify({
            'message': f'Bulk enrollment completed. {len(successful_enrollments)} successful, {len(failed_enrollments)} failed',
            'successful_enrollments': successful_enrollments,
            'failed_enrollments': failed_enrollments
        }), 200
        
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@student_enrollments_bp.route('/statistics', methods=['GET'])
@lecturer_required
def get_enrollment_statistics():
    try:
        # Get current semester
        current_semester = Semester.query.filter_by(is_current=True).first()
        
        # Total enrollments
        total_enrollments = StudentEnrollment.query.count()
        
        # Current semester enrollments
        current_semester_enrollments = 0
        if current_semester:
            current_semester_enrollments = StudentEnrollment.query.filter_by(
                semester_id=current_semester.id
            ).count()
        
        # Enrollments by status
        status_stats = db.session.query(
            StudentEnrollment.enrollment_status,
            db.func.count(StudentEnrollment.id).label('count')
        ).group_by(StudentEnrollment.enrollment_status).all()
        
        # Enrollments by course (current semester)
        course_stats = []
        if current_semester:
            course_stats = db.session.query(
                Course.course_code,
                Course.course_title,
                db.func.count(StudentEnrollment.id).label('count')
            ).join(StudentEnrollment).filter(
                StudentEnrollment.semester_id == current_semester.id,
                StudentEnrollment.enrollment_status == 'enrolled'
            ).group_by(Course.course_code, Course.course_title).all()
        
        return jsonify({
            'total_enrollments': total_enrollments,
            'current_semester_enrollments': current_semester_enrollments,
            'by_status': [
                {'status': stat.enrollment_status, 'count': stat.count} 
                for stat in status_stats
            ],
            'by_course': [
                {
                    'course_code': stat.course_code,
                    'course_title': stat.course_title,
                    'count': stat.count
                } 
                for stat in course_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500