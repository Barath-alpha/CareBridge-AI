from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db
import os
import uuid
import datetime

document_bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'txt'}
MAX_FILE_SIZE_MB = 10

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@document_bp.route('/api/documents/vault', methods=['GET'])
@jwt_required()
def get_vault_documents():
    """Lists files metadata belonging to the patient."""
    user_id = get_jwt_identity()

    try:
        docs = list(db.documents.find({'user_id': user_id}))
        return jsonify({'documents': docs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@document_bp.route('/api/documents/vault/upload', methods=['POST'])
@jwt_required()
def upload_vault_document():
    """Saves document securely to static/uploads/vault and registers metadata."""
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({'error': 'No file element found in request'}), 400

    file = request.files['file']
    category = request.form.get('category', 'Other') # 'Discharge Summary', 'Prescription', 'Lab Report'
    title = request.form.get('title', file.filename).strip()

    if file.filename == '':
        return jsonify({'error': 'No file selected for upload'}), 400

    # File size validation (Flask request limit or manual stream checking)
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        return jsonify({'error': f'File exceeds maximum size limit of {MAX_FILE_SIZE_MB}MB'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Supported formats: PDF, PNG, JPG, JPEG, TXT'}), 400

    try:
        # Resolve target directory
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'vault')
        os.makedirs(upload_dir, exist_ok=True)

        doc_id = str(uuid.uuid4())
        safe_name = f"{doc_id}_{secure_filename(file.filename)}"
        file_path = os.path.join(upload_dir, safe_name)
        
        # Save file to filesystem
        file.save(file_path)

        # Store metadata in DB
        doc_metadata = {
            '_id': doc_id,
            'user_id': user_id,
            'title': title or file.filename,
            'category': category,
            'filename': safe_name,
            'file_url': f"/static/uploads/vault/{safe_name}",
            'size_mb': round(size_mb, 2),
            'shared_with_caregiver': False,
            'shared_with_care_team': True,
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        db.documents.insert_one(doc_metadata)

        # Add Audit log
        db.auditLogs.insert_one({
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': 'Document Upload',
            'details': f"Uploaded file: {title} ({category})",
            'timestamp': datetime.datetime.utcnow().isoformat()
        })

        return jsonify({
            'message': 'Document uploaded successfully',
            'document': doc_metadata
        }), 201

    except Exception as e:
        return jsonify({'error': f'File upload failed: {str(e)}'}), 500


@document_bp.route('/api/documents/vault/<id>', methods=['DELETE'])
@jwt_required()
def delete_vault_document(id):
    """Deletes metadata and local file."""
    user_id = get_jwt_identity()

    try:
        doc = db.documents.find_one({'_id': id, 'user_id': user_id})
        if not doc:
            return jsonify({'error': 'Document not found or unauthorized'}), 404

        # Remove local file
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'vault')
        file_path = os.path.join(upload_dir, doc.get('filename'))
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove metadata
        db.documents.delete_one({'_id': id})

        # Audit log
        db.auditLogs.insert_one({
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'action': 'Document Deletion',
            'details': f"Deleted document: {doc.get('title')}",
            'timestamp': datetime.datetime.utcnow().isoformat()
        })

        return jsonify({'message': 'Document deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@document_bp.route('/api/documents/vault/share', methods=['POST'])
@jwt_required()
def toggle_document_share():
    """Toggles patient controlled sharing switches."""
    user_id = get_jwt_identity()
    data = request.get_json()

    if not data or 'document_id' not in data or 'target' not in data or 'status' not in data:
        return jsonify({'error': 'Missing parameters'}), 400

    doc_id = data['document_id']
    target = data['target'] # 'caregiver' or 'care_team'
    status = bool(data['status'])

    try:
        doc = db.documents.find_one({'_id': doc_id, 'user_id': user_id})
        if not doc:
            return jsonify({'error': 'Document not found'}), 404

        field = 'shared_with_caregiver' if target == 'caregiver' else 'shared_with_care_team'
        db.documents.update_one({'_id': doc_id}, {'$set': {field: status}})

        return jsonify({'message': f"Document sharing updated for {target}"}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
