import os
import requests
from flask import current_app

class ImageService:
    """Service to handle non-diagnostic educational image generation via Cloudflare Workers AI."""

    @staticmethod
    def generate_educational_image(prompt: str) -> bytes | None:
        account_id = current_app.config.get('CLOUDFLARE_ACCOUNT_ID')
        api_token = current_app.config.get('CLOUDFLARE_API_TOKEN')

        if not account_id or not api_token:
            # Safe local mock fallback logic if keys are not present
            return None

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Enforce educational, non-diagnostic graphics only
        safe_prompt = f"Educational medical vector illustration of {prompt}, flat design, friendly patient guide, no diagnostic scans, no prescription, clean style"
        payload = {"prompt": safe_prompt}

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                # Return raw binary bytes of the generated illustration
                return res.content
        except Exception:
            pass

        return None
