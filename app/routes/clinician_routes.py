from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db

clinician_bp = Blueprint('clinician', __name__)

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

@clinician_bp.route('/api/clinician/patients', methods=['GET'])
@jwt_required()
def get_prioritized_patients():
    """Returns patient index list sorted by alerts to prioritize coordinators."""
    user_id = get_jwt_identity()
    user = find_user_by_id(user_id)

    if not user or user.get('role') not in ['doctor', 'care_coordinator', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        # Load all patients
        patients = list(db.users.find({'role': 'patient'}))
        
        prioritized_list = []
        for p in patients:
            p_id = str(p.get('_id'))
            
            # Count active alerts for this patient
            alert_count = db.alerts.count_documents({'user_id': p_id, 'status': 'Active'})
            
            # Load recovery plan details
            plan = db.recoveryPlans.find_one({'user_id': p_id})
            
            # Load adherence statistics
            checkins_count = db.dailyCheckins.count_documents({'user_id': p_id})
            
            prioritized_list.append({
                'patient_id': p_id,
                'name': p.get('full_name'),
                'email': p.get('email'),
                'mobile': p.get('mobile_number'),
                'diagnosis': plan.get('diagnosis') if plan else 'No Active Plan',
                'active_alerts': alert_count,
                'checkins_logged': checkins_count,
                'urgency_score': alert_count * 10 + (1 if not plan else 0) # higher score = higher priority
            })

        # Sort by urgency score descending
        prioritized_list.sort(key=lambda x: x['urgency_score'], reverse=True)

        return jsonify({'patients': prioritized_list}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clinician_bp.route('/api/clinician/patient-profile/<id>', methods=['GET'])
@jwt_required()
def get_patient_profile(id):
    """Pulls detailed patient file (adherence history, check-ins, alert history)."""
    user_id = get_jwt_identity()
    user = find_user_by_id(user_id)

    if not user or user.get('role') not in ['doctor', 'care_coordinator', 'admin']:
        return jsonify({'error': 'Access denied'}), 403

    try:
        patient = find_user_by_id(id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        plan = db.recoveryPlans.find_one({'user_id': id})
        meds = list(db.medications.find({'user_id': id}))
        appts = list(db.appointments.find({'user_id': id}))
        checkins = list(db.dailyCheckins.find({'user_id': id}))
        alerts = list(db.alerts.find({'user_id': id}))
        documents = list(db.documents.find({'user_id': id}))

        return jsonify({
            'patient': {
                'id': patient.get('_id'),
                'name': patient.get('full_name'),
                'email': patient.get('email'),
                'mobile': patient.get('mobile_number'),
                'age': patient.get('age'),
                'gender': patient.get('gender'),
                'emergency_contact': patient.get('emergency_contact')
            },
            'recovery_plan': plan,
            'medications': meds,
            'appointments': appts,
            'check_ins': checkins,
            'alerts': alerts,
            'documents': documents
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
