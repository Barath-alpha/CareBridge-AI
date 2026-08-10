from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
import uuid
import datetime

journal_bp = Blueprint('journal', __name__)

@journal_bp.route('/api/journal/timeline', methods=['GET'])
@jwt_required()
def get_journal_entries():
    """Lists private journal timeline notes."""
    user_id = get_jwt_identity()

    try:
        entries = list(db.recoveryJournal.find({'user_id': user_id}))
        # Sort by date descending
        entries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return jsonify({'entries': entries}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@journal_bp.route('/api/journal/timeline', methods=['POST'])
@jwt_required()
def create_journal_entry():
    """Records daily notes, mood, and milestone details."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'note' not in data:
        return jsonify({'error': 'Missing note text'}), 400

    note = data['note'].strip()
    mood = data.get('mood', 'neutral')
    milestone = bool(data.get('milestone', False))
    share_with_care_team = bool(data.get('share_with_care_team', False))

    try:
        entry_id = str(uuid.uuid4())
        entry = {
            '_id': entry_id,
            'user_id': user_id,
            'note': note,
            'mood': mood,
            'milestone': milestone,
            'share_with_care_team': share_with_care_team,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        db.recoveryJournal.insert_one(entry)
        return jsonify({
            'message': 'Journal entry logged successfully',
            'entry': entry
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
