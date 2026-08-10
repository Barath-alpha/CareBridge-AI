from flask import Blueprint, request, jsonify, redirect, current_app, render_template_string
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from app import bcrypt, db
import datetime
import re
import urllib.parse
import requests
import uuid

# ObjectId is only available when using pymongo (not the local JSON fallback)
try:
    from bson.objectid import ObjectId
    _HAS_OBJECTID = True
except ImportError:
    _HAS_OBJECTID = False

auth_bp = Blueprint('auth', __name__)


def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))


@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    # Required field validation
    required_fields = ['full_name', 'email', 'mobile_number', 'password']
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return jsonify({'message': f'Missing required field: {field}'}), 400

    email    = data['email'].strip().lower()
    mobile   = data['mobile_number'].strip()
    password = data['password']

    # Validate email format
    if not is_valid_email(email):
        return jsonify({'message': 'Invalid email address format'}), 400

    # Validate password length
    if len(password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters'}), 400

    # Check if user already exists (email or mobile)
    existing_user = db.users.find_one({
        '$or': [
            {'email': email},
            {'mobile_number': mobile}
        ]
    })
    if existing_user:
        if existing_user.get('email') == email:
            return jsonify({'message': 'An account with this email already exists'}), 409
        return jsonify({'message': 'An account with this mobile number already exists'}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Build user document
    new_user = {
        'full_name':          data['full_name'].strip(),
        'email':              email,
        'mobile_number':      mobile,
        'age':                data.get('age'),
        'gender':             data.get('gender', ''),
        'preferred_language': data.get('preferred_language', 'English'),
        'country':            data.get('country', '').strip(),
        'emergency_contact':  data.get('emergency_contact', '').strip(),
        'password':           hashed_password,
        'role':               'patient',
        'created_at':         datetime.datetime.utcnow(),
        'profile_complete':   False,
    }

    result = db.users.insert_one(new_user)

    return jsonify({
        'message': 'Account created successfully',
        'user_id': str(result.inserted_id)
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No input data provided'}), 400

    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    # Look up user by email
    user = db.users.find_one({'email': email})

    if not user:
        return jsonify({'message': 'Invalid email or password'}), 401

    # Verify password
    if not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'message': 'Invalid email or password'}), 401

    # Create JWT — expires in 7 days by default (set in config)
    access_token = create_access_token(
        identity=str(user['_id']),
        additional_claims={
            'full_name': user.get('full_name', ''),
            'email':     user.get('email', ''),
            'role':      user.get('role', 'patient'),
        }
    )

    return jsonify({
        'message':      'Login successful',
        'access_token': access_token,
        'user': {
            'id':        str(user['_id']),
            'full_name': user.get('full_name', ''),
            'email':     user.get('email', ''),
            'role':      user.get('role', 'patient'),
        }
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    """Return the current authenticated user's profile."""
    user_id = get_jwt_identity()

    user = None
    # Try pymongo ObjectId lookup first
    if _HAS_OBJECTID:
        try:
            user = db.users.find_one({'_id': ObjectId(user_id)})
        except Exception:
            pass
    # Fallback: string _id (local JSON DB)
    if user is None:
        user = db.users.find_one({'_id': user_id})

    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify({
        'id':                 str(user['_id']),
        'full_name':          user.get('full_name', ''),
        'email':              user.get('email', ''),
        'mobile_number':      user.get('mobile_number', ''),
        'age':                user.get('age'),
        'gender':             user.get('gender', ''),
        'preferred_language': user.get('preferred_language', 'English'),
        'country':            user.get('country', ''),
        'emergency_contact':  user.get('emergency_contact', ''),
        'role':               user.get('role', 'patient'),
        'created_at':         str(user.get('created_at', '')),
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Client-side logout — token is removed on the frontend.
    This endpoint exists for any server-side cleanup if needed.
    """
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/google')
def google_login():
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    redirect_uri = request.host_url.rstrip('/') + '/api/auth/google/callback'
    
    # Construct Google OAuth Authorization URL
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'select_account'
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)


@auth_bp.route('/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        return 'Missing authorization code from Google', 400
        
    client_id = current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = current_app.config.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = request.host_url.rstrip('/') + '/api/auth/google/callback'
    
    # Exchange code for access token
    token_url = 'https://oauth2.googleapis.com/token'
    payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_res = requests.post(token_url, data=payload)
        token_data = token_res.json()
        
        if 'error' in token_data:
            return f"Google token exchange failed: {token_data.get('error_description', token_data['error'])}", 400
            
        access_token = token_data.get('access_token')
        
        # Get user info from Google
        user_info_res = requests.get('https://www.googleapis.com/oauth2/v3/userinfo', headers={
            'Authorization': f'Bearer {access_token}'
        })
        user_info = user_info_res.json()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        if not email:
            return 'Could not retrieve email from Google user info', 400
            
        # Check if user already exists
        user = db.users.find_one({'email': email})
        
        if not user:
            # Create a new patient account for this Google login
            new_user = {
                'full_name': name or email.split('@')[0],
                'email': email,
                'mobile_number': '',
                'password': bcrypt.generate_password_hash(str(uuid.uuid4())).decode('utf-8'),
                'role': 'patient',
                'created_at': datetime.datetime.utcnow(),
                'profile_complete': False,
            }
            # Insert into database
            db.users.insert_one(new_user)
            
            # Retrieve user
            user = db.users.find_one({'email': email})
            
        # Create JWT access token
        jwt_token = create_access_token(
            identity=str(user['_id']),
            additional_claims={
                'full_name': user.get('full_name', ''),
                'email': user.get('email', ''),
                'role': user.get('role', 'patient'),
            }
        )
        
        # Return elegant HTML block that stores token and redirects to dashboard
        html_success = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Logging in...</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #0f172a;
                    color: #f1f5f9;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    margin: 0;
                }}
                .spinner {{
                    width: 50px;
                    height: 50px;
                    border: 3px solid rgba(255,255,255,0.1);
                    border-radius: 50%;
                    border-top-color: #3b82f6;
                    animation: spin 1s ease-in-out infinite;
                    margin-bottom: 20px;
                }}
                @keyframes spin {{
                    to {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="spinner"></div>
            <p>Authentication successful! Redirecting you to your CareBridge AI dashboard...</p>
            <script>
                localStorage.setItem('access_token', "{jwt_token}");
                localStorage.setItem('user', JSON.stringify({{
                    "id": "{str(user['_id'])}",
                    "full_name": "{user.get('full_name', '')}",
                    "email": "{user.get('email', '')}",
                    "role": "{user.get('role', 'patient')}"
                }}));
                window.location.href = '/dashboard';
            </script>
        </body>
        </html>
        """
        return render_template_string(html_success)
        
    except Exception as e:
        return f"Authentication error: {str(e)}", 500
