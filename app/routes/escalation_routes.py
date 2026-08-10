from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
import uuid
import datetime

escalation_bp = Blueprint('escalation', __name__)

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

@escalation_bp.route('/api/escalation/alerts', methods=['GET'])
@jwt_required()
def get_escalation_alerts():
    """Lists all active alerts in the escalation center."""
    user_id = get_jwt_identity()
    user = find_user_by_id(user_id)
    
    if not user or user.get('role') not in ['doctor', 'care_coordinator', 'admin']:
        return jsonify({'error': 'Unauthorized access to Escalation Center'}), 403

    try:
        # Load all active alerts
        alerts = list(db.alerts.find({'status': 'Active'}))
        
        # Hydrate alerts with patient details
        hydrated_alerts = []
        for alert in alerts:
            patient = find_user_by_id(alert.get('user_id'))
            hydrated_alerts.append({
                '_id': alert.get('_id'),
                'patient_name': patient.get('full_name') if patient else 'Unknown Patient',
                'patient_email': patient.get('email') if patient else '',
                'date': alert.get('date'),
                'level': alert.get('level', 'Attention'),
                'reason': alert.get('reason'),
                'details': alert.get('details'),
                'status': alert.get('status'),
                'created_at': alert.get('created_at')
            })
            
        return jsonify({'alerts': hydrated_alerts}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@escalation_bp.route('/api/escalation/action', methods=['POST'])
@jwt_required()
def process_alert_action():
    """Clinician workflow action (Acknowledge, Review, Contact, Resolve)."""
    user_id = get_jwt_identity()
    user = find_user_by_id(user_id)
    
    if not user or user.get('role') not in ['doctor', 'care_coordinator', 'admin']:
        return jsonify({'error': 'Unauthorized action'}), 403

    data = request.get_json()
    if not data or 'alert_id' not in data or 'action' not in data:
        return jsonify({'error': 'Missing alert_id or action parameter'}), 400

    alert_id = data['alert_id']
    action = data['action'] # 'Acknowledge', 'Contact', 'Escalate', 'Resolve'
    notes = data.get('notes', '').strip()

    try:
        alert = db.alerts.find_one({'_id': alert_id})
        if not alert:
            return jsonify({'error': 'Alert not found'}), 404

        # Log action inside audit collection
        action_id = str(uuid.uuid4())
        db.alertActions.insert_one({
            '_id': action_id,
            'alert_id': alert_id,
            'user_id': user_id,
            'clinician_name': user.get('full_name'),
            'action': action,
            'notes': notes,
            'created_at': datetime.datetime.utcnow().isoformat()
        })

        # Update alert status if resolving
        if action == 'Resolve':
            db.alerts.update_one({'_id': alert_id}, {'$set': {'status': 'Resolved'}})
        else:
            db.alerts.update_one({'_id': alert_id}, {'$set': {'status': f'In Progress ({action})'}})

        return jsonify({
            'message': f"Alert successfully updated: {action}",
            'action_id': action_id
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
