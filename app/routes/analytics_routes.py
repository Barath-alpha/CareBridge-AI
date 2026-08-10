from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

analytics_bp = Blueprint('analytics', __name__)

def find_user_by_id(uid):
    if not uid:
        return None
    try:
        from bson.objectid import ObjectId
        user = db.users.find_one({'_id': ObjectId(uid)})
        if user:
            return user
    except Exception:
        pass
    return db.users.find_one({'_id': uid})

@analytics_bp.route('/api/analytics/dashboard', methods=['GET'])
@jwt_required()
def get_operational_analytics():
    """Compiles de-identified operational KPIs for hospital administrators."""
    user_id = get_jwt_identity()
    user = find_user_by_id(user_id)

    # Strict Admin Portal Access
    if not user or user.get('role') not in ['admin', 'doctor']:
        return jsonify({'error': 'Unauthorized access to Hospital Analytics Dashboard'}), 403

    try:
        # 1. Operational Counts
        active_plans = db.recoveryPlans.count_documents({})
        unresolved_alerts = db.alerts.count_documents({'status': 'Active'})
        resolved_alerts = db.alerts.count_documents({'status': 'Resolved'})

        # 2. Aggregated Check-In Compliance Rate
        total_checkins = db.dailyCheckins.count_documents({})
        # Assume standard 14 checkins target per active recovery plan
        target_checkins = active_plans * 14
        compliance_rate = int((total_checkins / target_checkins) * 100) if target_checkins > 0 else 100

        # 3. Aggregated Medication Adherence Rate
        total_med_logs = db.medicationLogs.count_documents({})
        taken_med_logs = db.medicationLogs.count_documents({'status': 'taken'})
        adherence_rate = int((taken_med_logs / total_med_logs) * 100) if total_med_logs > 0 else 100

        # 4. Department Workload (Mock de-identified breakdown)
        coordinator_workload = [
            {'name': 'Cardiology Care Team', 'assigned_patients': 12, 'active_alerts': 2},
            {'name': 'Neurology Care Team', 'assigned_patients': 8, 'active_alerts': 1},
            {'name': 'Orthopedics Care Team', 'assigned_patients': 15, 'active_alerts': 4}
        ]

        return jsonify({
            'kpis': {
                'active_programs': active_plans,
                'unresolved_alerts': unresolved_alerts,
                'resolved_alerts': resolved_alerts,
                'checkin_compliance': min(compliance_rate, 100),
                'medication_adherence': min(adherence_rate, 100)
            },
            'workload': coordinator_workload
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
