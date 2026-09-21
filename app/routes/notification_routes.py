"""
notification_routes.py — Routes for sending FCM HTTP v1 notifications and managing device tokens.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.services.fcm_service import fcm_service
import datetime

try:
    from bson.objectid import ObjectId
    _HAS_OBJECTID = True
except ImportError:
    _HAS_OBJECTID = False

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')


@notification_bp.route('/register-token', methods=['POST'])
@jwt_required(optional=True)
def register_device_token():
    """Register or update a user's FCM device token."""
    data = request.get_json() or {}
    token = data.get('fcm_token')
    platform = data.get('platform', 'web')

    if not token:
        return jsonify({'message': 'fcm_token is required'}), 400

    user_id = get_jwt_identity()

    if user_id:
        query_id = user_id
        if _HAS_OBJECTID:
            try:
                query_id = ObjectId(user_id)
            except Exception:
                pass

        try:
            db.users.update_one(
                {'_id': query_id},
                {
                    '$set': {
                        'fcm_token': token,
                        'device_platform': platform,
                        'token_updated_at': datetime.datetime.utcnow().isoformat()
                    }
                }
            )
        except Exception as e:
            return jsonify({'message': f'Failed to store device token: {str(e)}'}), 500

    return jsonify({
        'message': 'FCM device token registered successfully',
        'fcm_token': token
    }), 200


@notification_bp.route('/send', methods=['POST'])
def send_notification():
    """
    Send an FCM message using HTTP v1 API.
    Accepts:
    - token OR topic OR condition
    - title, body, image_url
    - data (dictionary)
    - click_action
    """
    data = request.get_json() or {}

    token = data.get('token')
    topic = data.get('topic')
    condition = data.get('condition')
    title = data.get('title', 'CareBridge AI Notification')
    body = data.get('body', '')
    image_url = data.get('image_url')
    custom_data = data.get('data')
    click_action = data.get('click_action', '/today')

    if not token and not topic and not condition:
        return jsonify({'message': 'Target (token, topic, or condition) is required'}), 400

    result = fcm_service.send_message(
        token=token,
        topic=topic,
        condition=condition,
        title=title,
        body=body,
        image_url=image_url,
        data=custom_data,
        click_action=click_action
    )

    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code


@notification_bp.route('/test', methods=['POST'])
def send_test_notification():
    """Send a quick test notification to a token or topic."""
    data = request.get_json() or {}
    token = data.get('token')
    topic = data.get('topic', 'all_patients' if not token else None)

    title = data.get('title', 'CareBridge AI • Test Message')
    body = data.get('body', 'This is a live test notification delivered via FCM HTTP v1 API.')

    result = fcm_service.send_message(
        token=token,
        topic=topic,
        title=title,
        body=body,
        data={'test': 'true', 'timestamp': datetime.datetime.utcnow().isoformat()},
        click_action='/settings'
    )

    return jsonify({
        'status': 'success' if result.get('success') else 'error',
        'result': result
    }), 200 if result.get('success') else 400


@notification_bp.route('/medication-reminder', methods=['POST'])
def send_medication_reminder():
    """Trigger an automated medication reminder."""
    data = request.get_json() or {}
    token = data.get('token')
    medication_name = data.get('medication_name', 'Prescribed Medication')
    dosage = data.get('dosage', '1 dose')
    time_str = data.get('time', 'Now')

    title = f"💊 Medication Reminder: {medication_name}"
    body = f"It's time to take {dosage} of {medication_name} ({time_str}). Tap to confirm dose."

    result = fcm_service.send_message(
        token=token,
        topic=data.get('topic', 'medication_reminders' if not token else None),
        title=title,
        body=body,
        data={
            'type': 'medication_reminder',
            'medication': medication_name,
            'dosage': dosage,
            'action': 'confirm_dose'
        },
        click_action='/medications'
    )

    return jsonify(result), 200 if result.get('success') else 400


@notification_bp.route('/emergency-alert', methods=['POST'])
def send_emergency_alert():
    """Dispatch an urgent caregiver/clinician emergency escalation push."""
    data = request.get_json() or {}
    patient_name = data.get('patient_name', 'Patient')
    severity = data.get('severity', 'High')
    symptoms = data.get('symptoms', 'Reported elevated pain or fever')

    title = f"🚨 CareBridge Emergency Alert: {patient_name}"
    body = f"Severity: {severity}. {symptoms}. Immediate caregiver triage requested."

    result = fcm_service.send_message(
        token=data.get('token'),
        topic=data.get('topic', 'emergency_escalations'),
        title=title,
        body=body,
        data={
            'type': 'emergency_alert',
            'patient_name': patient_name,
            'severity': severity,
            'timestamp': datetime.datetime.utcnow().isoformat()
        },
        click_action='/emergency'
    )

    return jsonify(result), 200 if result.get('success') else 400
