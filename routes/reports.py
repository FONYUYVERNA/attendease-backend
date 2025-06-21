from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from models.attendance_record import AttendanceRecord
from models.attendance_session import AttendanceSession
from models.student import Student
from models.course import Course
from models.course_assignment import CourseAssignment
from models.student_enrollment import StudentEnrollment
from models.semester import Semester
from models.lecturer import Lecturer
from models.department import Department
from utils.decorators import lecturer_required, admin_required, get_current_user
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/attendance/course/<course_assignment_id>', methods=['GET'])
@lecturer_required
def get_course_attendance_report(course_assignment_id):
    """Get attendance report for a specific course"""
    try:
        current_user = get_current_user()
        
        # Get course assignment
        course_assignment = CourseAssignment.query.get(course_assignment_id)
        if not course_assignment:
            return jsonify({'error': 'Course assignment not found'}), 404
        
        # Check if lecturer can access this report
        if current_user.user_type == 'lecturer':
            lecturer_profile = Lecturer.query.filter_by(user_id=current_user.id).first()
            if lecturer_profile and course_assignment.lecturer_id != lecturer_profile.id:
                return jsonify({'error': 'Access denied'}), 403
        
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get all sessions for this course assignment
        sessions_query = AttendanceSession.query.filter_by(
            course_assignment_id=course_assignment_id
        )
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                sessions_query = sessions_query.filter(AttendanceSession.started_at >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                sessions_query = sessions_query.filter(AttendanceSession.started_at < end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        sessions = sessions_query.order_by(AttendanceSession.started_at).all()
        
        # Get enrolled students
        enrolled_students = StudentEnrollment.query.filter_by(
            course_id=course_assignment.course_id,
            semester_id=course_assignment.semester_id,
            enrollment_status='enrolled'
        ).all()
        
        # Build attendance matrix
        attendance_data = []
        for enrollment in enrolled_students:
            student = Student.query.get(enrollment.student_id)
            student_data = {
                'student': student.to_dict(),
                'enrollment': enrollment.to_dict(),
                'sessions': [],
                'statistics': {
                    'total_sessions': len(sessions),
                    'present': 0,
                    'late': 0,
                    'absent': 0,
                    'attendance_percentage': 0
                }
            }
            
            for session in sessions:
                attendance_record = AttendanceRecord.query.filter_by(
                    session_id=session.id,
                    student_id=student.id
                ).first()
                
                if attendance_record:
                    session_data = {
                        'session_id': str(session.id),
                        'session_name': session.session_name,
                        'session_date': session.started_at.isoformat(),
                        'status': attendance_record.attendance_status,
                        'check_in_time': attendance_record.check_in_time.isoformat() if attendance_record.check_in_time else None
                    }
                    
                    # Update statistics
                    if attendance_record.attendance_status == 'present':
                        student_data['statistics']['present'] += 1
                    elif attendance_record.attendance_status == 'late':
                        student_data['statistics']['late'] += 1
                    else:
                        student_data['statistics']['absent'] += 1
                else:
                    session_data = {
                        'session_id': str(session.id),
                        'session_name': session.session_name,
                        'session_date': session.started_at.isoformat(),
                        'status': 'absent',
                        'check_in_time': None
                    }
                    student_data['statistics']['absent'] += 1
                
                student_data['sessions'].append(session_data)
            
            # Calculate attendance percentage
            attended = student_data['statistics']['present'] + student_data['statistics']['late']
            total = student_data['statistics']['total_sessions']
            student_data['statistics']['attendance_percentage'] = (attended / total * 100) if total > 0 else 0
            
            attendance_data.append(student_data)
        
        # Course and session summary
        course = Course.query.get(course_assignment.course_id)
        semester = Semester.query.get(course_assignment.semester_id)
        
        # Overall statistics
        total_possible_attendance = len(enrolled_students) * len(sessions)
        total_present = sum(student['statistics']['present'] for student in attendance_data)
        total_late = sum(student['statistics']['late'] for student in attendance_data)
        total_absent = sum(student['statistics']['absent'] for student in attendance_data)
        
        overall_attendance_rate = ((total_present + total_late) / total_possible_attendance * 100) if total_possible_attendance > 0 else 0
        
        return jsonify({
            'course': course.to_dict(),
            'semester': semester.to_dict(),
            'course_assignment': course_assignment.to_dict(),
            'report_period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_sessions': len(sessions)
            },
            'overall_statistics': {
                'total_students': len(enrolled_students),
                'total_sessions': len(sessions),
                'total_possible_attendance': total_possible_attendance,
                'total_present': total_present,
                'total_late': total_late,
                'total_absent': total_absent,
                'overall_attendance_rate': round(overall_attendance_rate, 2)
            },
            'sessions': [session.to_dict() for session in sessions],
            'student_attendance': attendance_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/attendance/student/<student_id>', methods=['GET'])
@lecturer_required
def get_student_attendance_report(student_id):
    """Get attendance report for a specific student"""
    try:
        current_user = get_current_user()
        
        # Get student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Check if student can access their own report
        if current_user.user_type == 'student':
            student_profile = Student.query.filter_by(user_id=current_user.id).first()
            if student_profile and str(student_profile.id) != student_id:
                return jsonify({'error': 'Access denied'}), 403
        
        # Get date range and course filter
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        course_id = request.args.get('course_id')
        semester_id = request.args.get('semester_id')
        
        # Build query for attendance records
        records_query = AttendanceRecord.query.filter_by(student_id=student_id)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                records_query = records_query.filter(AttendanceRecord.check_in_time >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                records_query = records_query.filter(AttendanceRecord.check_in_time < end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Join with sessions and course assignments to filter by course/semester
        if course_id or semester_id:
            records_query = records_query.join(AttendanceSession).join(CourseAssignment)
            
            if course_id:
                records_query = records_query.filter(CourseAssignment.course_id == course_id)
            
            if semester_id:
                records_query = records_query.filter(CourseAssignment.semester_id == semester_id)
        
        attendance_records = records_query.order_by(AttendanceRecord.check_in_time.desc()).all()
        
        # Get student's enrollments for context
        enrollments_query = StudentEnrollment.query.filter_by(
            student_id=student_id,
            enrollment_status='enrolled'
        )
        
        if semester_id:
            enrollments_query = enrollments_query.filter_by(semester_id=semester_id)
        
        enrollments = enrollments_query.all()
        
        # Calculate statistics by course
        course_statistics = []
        for enrollment in enrollments:
            course = Course.query.get(enrollment.course_id)
            course_assignment = CourseAssignment.query.filter_by(
                course_id=enrollment.course_id,
                semester_id=enrollment.semester_id
            ).first()
            
            if course_assignment:
                # Get all sessions for this course
                all_sessions = AttendanceSession.query.filter_by(
                    course_assignment_id=course_assignment.id
                ).all()
                
                # Filter sessions by date range if provided
                if start_date or end_date:
                    filtered_sessions = []
                    for session in all_sessions:
                        session_date = session.started_at.date()
                        
                        include_session = True
                        if start_date:
                            if session_date < datetime.strptime(start_date, '%Y-%m-%d').date():
                                include_session = False
                        if end_date:
                            if session_date > datetime.strptime(end_date, '%Y-%m-%d').date():
                                include_session = False
                        
                        if include_session:
                            filtered_sessions.append(session)
                    
                    all_sessions = filtered_sessions
                
                # Get student's attendance for these sessions
                session_ids = [session.id for session in all_sessions]
                student_records = AttendanceRecord.query.filter(
                    AttendanceRecord.student_id == student_id,
                    AttendanceRecord.session_id.in_(session_ids)
                ).all()
                
                # Calculate statistics
                present_count = len([r for r in student_records if r.attendance_status == 'present'])
                late_count = len([r for r in student_records if r.attendance_status == 'late'])
                absent_count = len(all_sessions) - len(student_records)
                
                attendance_rate = ((present_count + late_count) / len(all_sessions) * 100) if all_sessions else 0
                
                course_statistics.append({
                    'course': course.to_dict(),
                    'enrollment': enrollment.to_dict(),
                    'statistics': {
                        'total_sessions': len(all_sessions),
                        'present': present_count,
                        'late': late_count,
                        'absent': absent_count,
                        'attendance_rate': round(attendance_rate, 2)
                    }
                })
        
        # Overall statistics
        total_records = len(attendance_records)
        present_count = len([r for r in attendance_records if r.attendance_status == 'present'])
        late_count = len([r for r in attendance_records if r.attendance_status == 'late'])
        absent_count = len([r for r in attendance_records if r.attendance_status == 'absent'])
        
        return jsonify({
            'student': student.to_dict(),
            'report_period': {
                'start_date': start_date,
                'end_date': end_date,
                'course_filter': course_id,
                'semester_filter': semester_id
            },
            'overall_statistics': {
                'total_records': total_records,
                'present': present_count,
                'late': late_count,
                'absent': absent_count
            },
            'course_statistics': course_statistics,
            'attendance_records': [
                {
                    **record.to_dict(),
                    'session': AttendanceSession.query.get(record.session_id).to_dict()
                }
                for record in attendance_records
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Add the missing student performance endpoint
@reports_bp.route('/students/performance', methods=['GET'])
@admin_required
def get_students_performance_report():
    """Get performance report for all students"""
    try:
        semester_id = request.args.get('semester_id')
        department_id = request.args.get('department_id')
        level = request.args.get('level')
        
        # Build base query for students
        students_query = Student.query
        
        if department_id:
            students_query = students_query.filter_by(department_id=department_id)
        
        if level:
            students_query = students_query.filter_by(level=level)
        
        students = students_query.all()
        
        student_performance = []
        for student in students:
            # Get enrollments
            enrollments_query = StudentEnrollment.query.filter_by(
                student_id=student.id,
                enrollment_status='enrolled'
            )
            
            if semester_id:
                enrollments_query = enrollments_query.filter_by(semester_id=semester_id)
            
            enrollments = enrollments_query.all()
            
            # Calculate overall attendance statistics
            total_sessions = 0
            total_attended = 0
            
            for enrollment in enrollments:
                course_assignment = CourseAssignment.query.filter_by(
                    course_id=enrollment.course_id,
                    semester_id=enrollment.semester_id
                ).first()
                
                if course_assignment:
                    sessions = AttendanceSession.query.filter_by(
                        course_assignment_id=course_assignment.id
                    ).count()
                    
                    attended = AttendanceRecord.query.filter_by(
                        student_id=student.id
                    ).join(AttendanceSession).filter(
                        AttendanceSession.course_assignment_id == course_assignment.id,
                        AttendanceRecord.attendance_status.in_(['present', 'late'])
                    ).count()
                    
                    total_sessions += sessions
                    total_attended += attended
            
            attendance_rate = (total_attended / total_sessions * 100) if total_sessions > 0 else 0
            
            student_performance.append({
                'student': student.to_dict(),
                'statistics': {
                    'total_courses': len(enrollments),
                    'total_sessions': total_sessions,
                    'total_attended': total_attended,
                    'attendance_rate': round(attendance_rate, 2)
                }
            })
        
        # Sort by attendance rate
        student_performance.sort(key=lambda x: x['statistics']['attendance_rate'], reverse=True)
        
        return jsonify({
            'filters': {
                'semester_id': semester_id,
                'department_id': department_id,
                'level': level
            },
            'student_performance': student_performance
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/attendance/summary', methods=['GET'])
@admin_required
def get_attendance_summary_report():
    """Get attendance summary report"""
    try:
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        department_id = request.args.get('department_id')
        level = request.args.get('level')
        
        # Build base query
        base_query = db.session.query(AttendanceRecord).join(AttendanceSession)
        
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                base_query = base_query.filter(AttendanceSession.started_at >= start_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                base_query = base_query.filter(AttendanceSession.started_at < end_date_obj)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # Apply filters
        if department_id or level:
            base_query = base_query.join(Student)
            
            if department_id:
                base_query = base_query.filter(Student.department_id == department_id)
            
            if level:
                base_query = base_query.filter(Student.level == level)
        
        # Overall statistics
        total_records = base_query.count()
        
        status_stats = base_query.with_entities(
            AttendanceRecord.attendance_status,
            func.count(AttendanceRecord.id).label('count')
        ).group_by(AttendanceRecord.attendance_status).all()
        
        return jsonify({
            'report_period': {
                'start_date': start_date,
                'end_date': end_date,
                'department_filter': department_id,
                'level_filter': level
            },
            'overall_statistics': {
                'total_records': total_records,
                'by_status': [
                    {'status': stat.attendance_status, 'count': stat.count}
                    for stat in status_stats
                ]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/courses/performance', methods=['GET'])
@admin_required
def get_course_performance_report():
    """Get course performance report"""
    try:
        semester_id = request.args.get('semester_id')
        department_id = request.args.get('department_id')
        
        # Get current semester if not specified
        if not semester_id:
            current_semester = Semester.query.filter_by(is_current=True).first()
            if current_semester:
                semester_id = current_semester.id
        
        if not semester_id:
            return jsonify({'error': 'No semester specified and no current semester set'}), 400
        
        # Build query for course assignments
        assignments_query = CourseAssignment.query.filter_by(
            semester_id=semester_id,
            is_active=True
        )
        
        if department_id:
            assignments_query = assignments_query.join(Course).filter(
                Course.department_id == department_id
            )
        
        assignments = assignments_query.all()
        
        course_performance = []
        for assignment in assignments:
            course = Course.query.get(assignment.course_id)
            lecturer = Lecturer.query.get(assignment.lecturer_id)
            
            # Get enrolled students count
            enrolled_count = StudentEnrollment.query.filter_by(
                course_id=assignment.course_id,
                semester_id=semester_id,
                enrollment_status='enrolled'
            ).count()
            
            # Get total sessions
            total_sessions = AttendanceSession.query.filter_by(
                course_assignment_id=assignment.id
            ).count()
            
            # Get attendance statistics
            attendance_stats = db.session.query(
                func.count(AttendanceRecord.id).label('total_records'),
                func.sum(func.case([(AttendanceRecord.attendance_status == 'present', 1)], else_=0)).label('present'),
                func.sum(func.case([(AttendanceRecord.attendance_status == 'late', 1)], else_=0)).label('late')
            ).join(AttendanceSession).filter(
                AttendanceSession.course_assignment_id == assignment.id
            ).first()
            
            total_records = attendance_stats.total_records or 0
            present_count = attendance_stats.present or 0
            late_count = attendance_stats.late or 0
            
            # Calculate expected total records (sessions * enrolled students)
            expected_total = total_sessions * enrolled_count
            absent_count = expected_total - total_records
            
            # Calculate attendance rate
            attended = present_count + late_count
            attendance_rate = (attended / expected_total * 100) if expected_total > 0 else 0
            
            course_performance.append({
                'course': course.to_dict(),
                'lecturer': lecturer.to_dict(),
                'assignment': assignment.to_dict(),
                'statistics': {
                    'enrolled_students': enrolled_count,
                    'total_sessions': total_sessions,
                    'expected_total_records': expected_total,
                    'actual_records': total_records,
                    'present': present_count,
                    'late': late_count,
                    'absent': absent_count,
                    'attendance_rate': round(attendance_rate, 2)
                }
            })
        
        # Sort by attendance rate (descending)
        course_performance.sort(key=lambda x: x['statistics']['attendance_rate'], reverse=True)
        
        semester = Semester.query.get(semester_id)
        
        return jsonify({
            'semester': semester.to_dict() if semester else None,
            'department_filter': department_id,
            'course_performance': course_performance
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/export/attendance', methods=['POST'])
@lecturer_required
def export_attendance_report():
    """Generate export data for attendance reports"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        report_type = data.get('report_type', 'course')  # course, student, summary
        format_type = data.get('format', 'json')  # json, csv (future: pdf, excel)
        
        if report_type == 'course':
            course_assignment_id = data.get('course_assignment_id')
            if not course_assignment_id:
                return jsonify({'error': 'course_assignment_id required for course report'}), 400
            
            # Reuse the course attendance report logic
            # This would typically generate a file and return a download link
            # For now, return the data structure
            return jsonify({
                'message': 'Export functionality would be implemented here',
                'report_type': report_type,
                'format': format_type,
                'download_url': f'/api/reports/download/{course_assignment_id}'
            }), 200
        
        return jsonify({'error': 'Invalid report type'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
