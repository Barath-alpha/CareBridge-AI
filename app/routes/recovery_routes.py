from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
import google.generativeai as genai
import os
import json
import uuid
import datetime

recovery_bp = Blueprint('recovery', __name__)

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

@recovery_bp.route('/api/recovery/upload-summary', methods=['POST'])
@jwt_required()
def upload_summary():
    """AI Discharge-to-Recovery Plan Extraction endpoint."""
    user_id = get_jwt_identity()
    
    # In a full production app, we would use PDF/OCR parsing.
    # Here we support both raw text and mock file parsing.
    text_data = request.form.get('text', '').strip()
    
    # If a file is uploaded
    file = request.files.get('file')
    if file:
        # Mock file text extraction (simulating scanned/PDF parsing)
        text_data = f"Uploaded File: {file.filename}\n" + (file.read().decode('utf-8', errors='ignore') or "Patient: John Doe, Diagnosis: Coronary Artery Bypass, Meds: Paracetamol 500mg daily, Followup: Cardiology clinic in 7 days.")
        
    if not text_data:
        return jsonify({'error': 'No file or text data provided'}), 400

    try:
        # Fetch key and configure Gemini
        api_key = os.environ.get('GEMINI_API_KEY') or current_app.config.get('GEMINI_API_KEY')
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Analyze this hospital discharge summary and extract the following information in JSON format:
        
        {{
            "patient_name": "",
            "diagnosis": "",
            "discharge_date": "",
            "medications": [
                {{"name": "", "dosage": "", "frequency": "", "instructions": "", "purpose": ""}}
            ],
            "follow_up_appointments": [
                {{"doctor": "", "specialty": "", "date": "", "location": ""}}
            ],
            "dietary_recommendations": [],
            "activity_restrictions": [],
            "warning_signs": [],
            "special_care_instructions": [],
            "recovery_duration": ""
        }}
        
        Also, convert all medical terminology into simple, patient-friendly language.
        
        Discharge Summary:
        {text_data}
        
        Return ONLY the JSON object, no additional text."""

        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Clean potential markdown output from Gemini
        if raw_text.startswith('```'):
            raw_text = raw_text.split('```')[1]
            if raw_text.startswith('json'):
                raw_text = raw_text[4:]
        
        parsed_data = json.loads(raw_text.strip())
        
        # Save temporary draft to db
        draft_id = str(uuid.uuid4())
        db.recoveryPlansDrafts.insert_one({
            '_id': draft_id,
            'user_id': user_id,
            'extracted_data': parsed_data,
            'created_at': datetime.datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'success': True,
            'draft_id': draft_id,
            'data': parsed_data
        }), 200

    except Exception as e:
        return jsonify({'error': f'AI Extraction failed: {str(e)}'}), 500


@recovery_bp.route('/api/recovery/approve-plan', methods=['POST'])
@jwt_required()
def approve_plan():
    """Saves approved recovery plan and initializes tasks/schedules."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({'error': 'No approved data provided'}), 400

    approved_data = data['data']

    try:
        # Create Recovery Plan record
        plan_id = str(uuid.uuid4())
        recovery_plan = {
            '_id': plan_id,
            'user_id': user_id,
            'patient_name': approved_data.get('patient_name'),
            'diagnosis': approved_data.get('diagnosis'),
            'discharge_date': approved_data.get('discharge_date'),
            'dietary_recommendations': approved_data.get('dietary_recommendations', []),
            'activity_restrictions': approved_data.get('activity_restrictions', []),
            'warning_signs': approved_data.get('warning_signs', []),
            'special_care_instructions': approved_data.get('special_care_instructions', []),
            'created_at': datetime.datetime.utcnow().isoformat(),
            'approved': True
        }
        db.recoveryPlans.insert_one(recovery_plan)

        # Clear existing schedules if any
        db.medications.delete_many({'user_id': user_id})
        db.appointments.delete_many({'user_id': user_id})
        db.recoveryTasks.delete_many({'user_id': user_id})

        # Insert Medications
        for idx, med in enumerate(approved_data.get('medications', [])):
            db.medications.insert_one({
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'name': med.get('name'),
                'dosage': med.get('dosage'),
                'frequency': med.get('frequency'),
                'instructions': med.get('instructions'),
                'purpose': med.get('purpose', 'Recovery Support'),
                'active': True
            })

        # Insert Appointments
        for appt in approved_data.get('follow_up_appointments', []):
            db.appointments.insert_one({
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'doctor': appt.get('doctor'),
                'specialty': appt.get('specialty'),
                'date': appt.get('date'),
                'location': appt.get('location'),
                'status': 'Upcoming'
            })

        # Generate recovery milestones & daily tasks (Default 14 day setup)
        today = datetime.date.today()
        for day_offset in range(14):
            task_date = (today + datetime.timedelta(days=day_offset)).isoformat()
            # Default Daily Hydration Task
            db.recoveryTasks.insert_one({
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'date': task_date,
                'title': 'Hydration Reminder',
                'description': 'Drink at least 2 liters of water daily.',
                'completed': False
            })
            # Default Rest Task
            db.recoveryTasks.insert_one({
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'date': task_date,
                'title': 'Rest Period',
                'description': 'Take a 30-minute nap or quiet rest in the afternoon.',
                'completed': False
            })
            # Add general recovery instructions as daily task
            db.recoveryTasks.insert_one({
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'date': task_date,
                'title': 'Recovery Stretch & Gentle Walk',
                'description': 'Complete a 10-15 minute light walk around the house.',
                'completed': False
            })

        return jsonify({'message': 'Plan approved and initialized successfully', 'plan_id': plan_id}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to approve plan: {str(e)}'}), 500


@recovery_bp.route('/api/recovery/checkin', methods=['POST'])
@jwt_required()
def submit_checkin():
    """Daily checkin with built-in rule based warning alerts."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No check-in metrics provided'}), 400

    pain = int(data.get('pain', 1))
    mood = data.get('mood', 'good')
    temp = float(data.get('temp', 98.6))
    sleep = int(data.get('sleep', 8))
    appetite = data.get('appetite', 'normal')
    hydration = int(data.get('hydration', 1)) # liters
    symptoms = data.get('symptoms', []) # List of selected symptoms
    notes = data.get('notes', '').strip()

    try:
        checkin_id = str(uuid.uuid4())
        checkin = {
            '_id': checkin_id,
            'user_id': user_id,
            'date': datetime.date.today().isoformat(),
            'pain': pain,
            'mood': mood,
            'temp': temp,
            'sleep': sleep,
            'appetite': appetite,
            'hydration': hydration,
            'symptoms': symptoms,
            'notes': notes,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        db.dailyCheckins.insert_one(checkin)

        # Predefined clinician-approved warning signs rules (non-diagnostic)
        alert_triggered = False
        alert_reason = []

        if pain >= 7:
            alert_triggered = True
            alert_reason.append(f"Severe Pain Reported: {pain}/10")
        if temp >= 101.0:
            alert_triggered = True
            alert_reason.append(f"High Body Temperature: {temp}°F")
        if 'chest_pain' in symptoms:
            alert_triggered = True
            alert_reason.append("Urgent Warning Sign: Chest Pain Reported")
        if 'breathlessness' in symptoms:
            alert_triggered = True
            alert_reason.append("Urgent Warning Sign: Breathlessness Reported")

        if alert_triggered:
            # Dispatch to care coordinator escalation log
            alert_id = str(uuid.uuid4())
            db.alerts.insert_one({
                '_id': alert_id,
                'user_id': user_id,
                'date': datetime.date.today().isoformat(),
                'level': 'Priority' if any(s in ['chest_pain', 'breathlessness'] for s in symptoms) else 'Attention',
                'reason': ', '.join(alert_reason),
                'details': f"Temp: {temp}°F, Pain: {pain}/10, Symptoms: {', '.join(symptoms)}",
                'status': 'Active',
                'created_at': datetime.datetime.utcnow().isoformat()
            })

        return jsonify({
            'message': 'Check-in recorded successfully',
            'checkin_id': checkin_id,
            'alert_triggered': alert_triggered
        }), 201

    except Exception as e:
        return jsonify({'error': f'Check-in logging failed: {str(e)}'}), 500


@recovery_bp.route('/api/recovery/medication-log', methods=['POST'])
@jwt_required()
def log_medication():
    """Logs medication dose compliance (Taken, Skipped, Unable)."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or 'medication_id' not in data or 'status' not in data:
        return jsonify({'error': 'Missing medication id or log status'}), 400

    med_id = data['medication_id']
    status = data['status'] # 'taken', 'skipped', 'unable'
    notes = data.get('notes', '')

    try:
        log_id = str(uuid.uuid4())
        db.medicationLogs.insert_one({
            '_id': log_id,
            'user_id': user_id,
            'medication_id': med_id,
            'date': datetime.date.today().isoformat(),
            'time': datetime.datetime.utcnow().strftime('%H:%M:%S'),
            'status': status,
            'notes': notes,
            'created_at': datetime.datetime.utcnow().isoformat()
        })
        return jsonify({'message': 'Medication log recorded', 'log_id': log_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recovery_bp.route('/api/recovery/today', methods=['GET'])
@jwt_required()
def get_today_command_center():
    """Pulls consolidated metrics for Today View dashboard."""
    user_id = get_jwt_identity()
    today_str = datetime.date.today().isoformat()

    try:
        # Load user info
        user = find_user_by_id(user_id)
        
        # Load active recovery plan
        plan = db.recoveryPlans.find_one({'user_id': user_id})
        
        # Load tasks
        tasks = list(db.recoveryTasks.find({'user_id': user_id, 'date': today_str}))
        
        # Load active medications
        meds = list(db.medications.find({'user_id': user_id, 'active': True}))
        
        # Load todays medication logs
        med_logs = list(db.medicationLogs.find({'user_id': user_id, 'date': today_str}))
        
        # Load today's checkin
        checkin = db.dailyCheckins.find_one({'user_id': user_id, 'date': today_str})
        
        # Load appointments
        appointments = list(db.appointments.find({'user_id': user_id, 'status': 'Upcoming'}))

        # Adherence Calculation (Non-clinical Engagement Score)
        task_comp = sum(1 for t in tasks if t.get('completed'))
        med_comp = sum(1 for l in med_logs if l.get('status') == 'taken')
        
        total_items = len(tasks) + len(meds) + 1 # tasks + meds + checkin
        completed_items = task_comp + med_comp + (1 if checkin else 0)
        
        adherence_score = int((completed_items / total_items) * 100) if total_items > 0 else 100

        return jsonify({
            'user': {
                'name': user.get('full_name', 'Patient'),
                'email': user.get('email')
            },
            'recovery_plan': plan,
            'adherence_score': adherence_score,
            'tasks': tasks,
            'medications': meds,
            'medication_logs': med_logs,
            'checkin_completed': checkin is not None,
            'appointments': appointments
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
