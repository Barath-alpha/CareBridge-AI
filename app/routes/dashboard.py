from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@dashboard_bp.route('/recovery-plan')
def recovery_plan_page():
    return render_template('recovery_plan.html')

@dashboard_bp.route('/medications')
def medications_page():
    return render_template('medications.html')

@dashboard_bp.route('/appointments')
def appointments_page():
    return render_template('appointments.html')

@dashboard_bp.route('/daily-checkin')
def daily_checkin_page():
    return render_template('daily_checkin.html')

@dashboard_bp.route('/upload-summary')
def upload_summary_page():
    return render_template('upload_summary.html')

@dashboard_bp.route('/reports')
def reports_page():
    return render_template('reports.html')

@dashboard_bp.route('/family-portal')
def family_portal_page():
    return render_template('family_portal.html')

@dashboard_bp.route('/emergency')
def emergency_page():
    return render_template('emergency.html')

@dashboard_bp.route('/today')
def today_page():
    return render_template('today_view.html')

@dashboard_bp.route('/clinician')
def clinician_page():
    return render_template('clinician_center.html')

@dashboard_bp.route('/analytics')
def analytics_page():
    return render_template('analytics_dashboard.html')

@dashboard_bp.route('/vault')
def vault_page():
    return render_template('document_vault.html')

@dashboard_bp.route('/journal')
def journal_page():
    return render_template('recovery_journal.html')

@dashboard_bp.route('/settings')
def settings_page():
    return render_template('security_privacy.html')

@dashboard_bp.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_stats():
    user_id = get_jwt_identity()
    # Sample stats for UI - in production, pull from MongoDB aggregations
    return jsonify({
        "recovery_score": 78,
        "medication_adherence": 92,
        "days_since_discharge": 12,
        "upcoming_appointments": 2
    }), 200
