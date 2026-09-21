from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
import os
import google.generativeai as genai

ai_bp = Blueprint('ai', __name__)

GEMINI_MODELS = [
    'gemini-flash-latest',
    'gemini-pro-latest',
    'gemini-2.5-flash-lite',
    'gemini-2.5-pro',
    'gemini-1.5-flash',
    'gemini-1.5-pro'
]

def _generate_with_gemini(user_prompt: str, system_prompt: str = None) -> str:
    """Helper to dispatch Gemini requests with automatic model fallback."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        genai.configure(api_key=api_key)
    
    last_err = None
    for model_name in GEMINI_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            if system_prompt:
                chat = model.start_chat(history=[])
                full_message = f"{system_prompt}\n\nPatient asks: {user_prompt}"
                response = chat.send_message(full_message)
            else:
                response = model.generate_content(user_prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_err = e
            continue
    raise last_err or Exception("All Gemini models failed to respond")

@ai_bp.route('/ai-assistant')
def ai_page():
    return render_template('ai_assistant.html')

@ai_bp.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']

    try:
        system_prompt = """You are CareBridge AI, a compassionate and knowledgeable healthcare assistant 
        specializing in post-discharge patient recovery. You help patients understand their medications, 
        follow recovery plans, track symptoms, and answer healthcare questions. 
        Always be clear, empathetic, and advise patients to consult their doctor for serious concerns.
        Format your responses in a readable way using markdown when appropriate."""

        response_text = _generate_with_gemini(user_prompt=user_message, system_prompt=system_prompt)
        return jsonify({'response': response_text}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/api/ai/analyze-discharge', methods=['POST'])
def analyze_discharge():
    """Analyze discharge summary text with Gemini AI"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    discharge_text = data['text']
    
    try:
        prompt = f"""Analyze this hospital discharge summary and extract the following information in JSON format:
        
        {{
            "patient_name": "",
            "diagnosis": "",
            "discharge_date": "",
            "medications": [
                {{"name": "", "dosage": "", "frequency": "", "instructions": "", "side_effects": ""}}
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
        {discharge_text}
        
        Return ONLY the JSON object, no additional text."""
        
        raw_text = _generate_with_gemini(user_prompt=prompt)
        
        # Try to parse the response as JSON
        import json
        try:
            # Clean the response text
            text = raw_text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            parsed = json.loads(text)
            return jsonify({'success': True, 'data': parsed}), 200
        except json.JSONDecodeError:
            return jsonify({'success': True, 'data': {'raw': raw_text}}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
