from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
import uuid
import datetime

caregiver_bp = Blueprint('caregiver', __name__)

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

@caregiver_bp.route('/api/caregivers/invite', methods=['POST'])
@jwt_required()
def invite_caregiver():
    """Generates caregiver invitation record."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing caregiver email'}), 400

    email = data['email'].strip().lower()
    relation = data.get('relation', 'Family Member')
    permissions = data.get('permissions', {
        'view_progress': True,
        'view_medications': True,
        'view_appointments': True,
        'view_reports': False,
        'receive_alerts': True
    })

    try:
        invite_id = str(uuid.uuid4())
        db.caregiverInvites.insert_one({
            '_id': invite_id,
            'patient_id': user_id,
            'email': email,
            'relation': relation,
            'permissions': permissions,
            'status': 'Pending',
            'created_at': datetime.datetime.utcnow().isoformat()
        })
        return jsonify({
            'message': 'Caregiver invitation generated successfully',
            'invite_id': invite_id
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@caregiver_bp.route('/api/caregivers/portal', methods=['GET'])
@jwt_required()
def get_caregiver_dashboard():
    """Pulls patient data mapping for authenticated caregivers."""
    user_id = get_jwt_identity()
    user = find_user_by_id(user_id)

    try:
        # Load active connection mappings where current user is caregiver
        connections = list(db.caregivers.find({'caregiver_email': user.get('email')}))
        if not connections:
            return jsonify({'message': 'No connected patients found', 'patients': []}), 200

        hydrated_patients = []
        for conn in connections:
            patient_id = conn.get('patient_id')
            patient = find_user_by_id(patient_id)
            
            if not patient:
                continue

            # Load metrics based on permissions
            perms = conn.get('permissions', {})
            patient_data = {
                'patient_id': patient_id,
                'name': patient.get('full_name'),
                'email': patient.get('email'),
                'relation': conn.get('relation'),
                'permissions': perms
            }

            # If permitted, fetch today's recovery metrics
            if perms.get('view_progress'):
                plan = db.recoveryPlans.find_one({'user_id': patient_id})
                patient_data['diagnosis'] = plan.get('diagnosis') if plan else 'N/A'
                patient_data['recovery_score'] = 78 # static or dynamically evaluated progress metric

            if perms.get('view_medications'):
                meds = list(db.medications.find({'user_id': patient_id}))
                patient_data['medications'] = [{'name': m.get('name'), 'dosage': m.get('dosage')} for m in meds]

            if perms.get('view_appointments'):
                appts = list(db.appointments.find({'user_id': patient_id, 'status': 'Upcoming'}))
                patient_data['appointments'] = [{'doctor': a.get('doctor'), 'date': a.get('date')} for a in appts]

            hydrated_patients.append(patient_data)

        return jsonify({'patients': hydrated_patients}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
