"""
fcm_service.py — Firebase Cloud Messaging (FCM) HTTP v1 API Service.
Supports sending push notifications to:
- Specific device registration tokens
- Topics (e.g. 'all_patients', 'caregivers', 'emergency_alerts')
- Conditions
- Custom data and notification payloads
Authorizes via Google OAuth 2.0 access tokens (ADC / Service Account JSON).
"""

import os
import json
import logging
import requests
from typing import Optional, Dict, Any

try:
    import google.auth
    import google.auth.transport.requests
    from google.oauth2 import service_account
    _HAS_GOOGLE_AUTH = True
except ImportError:
    _HAS_GOOGLE_AUTH = False

logger = logging.getLogger(__name__)

FCM_SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']


class FCMService:
    """Service to construct and dispatch FCM HTTP v1 messages."""

    def __init__(self, project_id: Optional[str] = None, service_account_path: Optional[str] = None):
        self.project_id = project_id or os.environ.get('FIREBASE_PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT') or 'carebridge-ai-app'
        self.service_account_path = service_account_path or os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        self._cached_token = None
        self._credentials = None
        self._checked_credentials = False

    def get_access_token(self) -> Optional[str]:
        """
        Mint a short-lived OAuth 2.0 access token using Google Auth library.
        Returns access token string or None if credentials are not configured.
        """
        if not _HAS_GOOGLE_AUTH:
            return None

        if self._checked_credentials and not self._credentials:
            return None

        try:
            # 1. Check explicit service account file path
            if self.service_account_path and os.path.exists(self.service_account_path):
                self._credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path,
                    scopes=FCM_SCOPES
                )
            elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')):
                self._credentials = service_account.Credentials.from_service_account_file(
                    os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                    scopes=FCM_SCOPES
                )
            elif not self._checked_credentials:
                # 2. Try Application Default Credentials (ADC) once
                self._checked_credentials = True
                try:
                    self._credentials, detected_project = google.auth.default(scopes=FCM_SCOPES)
                    if detected_project and not self.project_id:
                        self.project_id = detected_project
                except Exception:
                    self._credentials = None

            self._checked_credentials = True

            if self._credentials:
                request = google.auth.transport.requests.Request()
                self._credentials.refresh(request)
                return self._credentials.token

        except Exception as e:
            logger.error(f"[FCM] Failed to mint OAuth 2.0 access token: {e}")

        return None

    def send_message(
        self,
        token: Optional[str] = None,
        topic: Optional[str] = None,
        condition: Optional[str] = None,
        title: Optional[str] = None,
        body: Optional[str] = None,
        image_url: Optional[str] = None,
        data: Optional[Dict[str, str]] = None,
        click_action: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a notification/data message using FCM HTTP v1 API.
        URL: POST https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send
        """
        # Validate target
        if not token and not topic and not condition:
            return {
                'success': False,
                'error': 'Missing target: must specify one of token, topic, or condition'
            }

        # Build message payload structure
        message: Dict[str, Any] = {}

        if token:
            message['token'] = token
        elif topic:
            # Remove leading /topics/ if present, FCM v1 handles raw topic names
            message['topic'] = topic.replace('/topics/', '')
        elif condition:
            message['condition'] = condition

        # Notification payload
        if title or body or image_url:
            notification: Dict[str, str] = {}
            if title:
                notification['title'] = str(title)
            if body:
                notification['body'] = str(body)
            if image_url:
                notification['image'] = str(image_url)
            message['notification'] = notification

        # Data payload (all values must be strings)
        if data:
            message['data'] = {str(k): str(v) for k, v in data.items()}

        # Webpush / Link customization
        if click_action:
            message['webpush'] = {
                'fcm_options': {
                    'link': click_action
                }
            }

        payload = {'message': message}

        # Retrieve OAuth 2.0 access token
        access_token = self.get_access_token()

        if not access_token:
            # Simulated environment / dev mode response
            import uuid
            simulated_id = f"projects/{self.project_id}/messages/0:{int(uuid.uuid4().int % 1e16):016x}%demo"
            logger.info(f"[FCM Simulated] Notification dispatched to target. Payload: {json.dumps(payload)}")
            return {
                'success': True,
                'simulated': True,
                'message_id': simulated_id,
                'note': 'Executed in development/simulation mode. To connect live FCM, configure GOOGLE_APPLICATION_CREDENTIALS.',
                'payload': payload
            }

        # Send live HTTP v1 request to Google FCM
        url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; UTF-8'
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            res_data = response.json()

            if response.status_code == 200:
                return {
                    'success': True,
                    'message_id': res_data.get('name'),
                    'raw_response': res_data
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': res_data.get('error', {}).get('message', 'FCM request failed'),
                    'raw_response': res_data
                }
        except Exception as e:
            logger.error(f"[FCM] Exception sending HTTP v1 message: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_to_token(self, token: str, title: str, body: str, data: Optional[Dict[str, str]] = None, image_url: Optional[str] = None):
        """Send notification to a specific device registration token."""
        return self.send_message(token=token, title=title, body=body, data=data, image_url=image_url)

    def send_to_topic(self, topic: str, title: str, body: str, data: Optional[Dict[str, str]] = None, image_url: Optional[str] = None):
        """Send notification to all devices subscribed to a topic."""
        return self.send_message(topic=topic, title=title, body=body, data=data, image_url=image_url)


fcm_service = FCMService()
