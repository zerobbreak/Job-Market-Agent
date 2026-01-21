import hmac
import hashlib
import time
import os
from urllib.parse import urlencode
from flask import request
from config import Config

def generate_signed_url(file_id: str, bucket_id: str, file_type: str = 'storage', 
                       expires_in: int = 3600, base_url: str = None) -> str:
    """
    Generate a cryptographically signed URL for secure file downloads.
    """
    secret = Config.SIGNED_URL_SECRET
    expires_at = int(time.time()) + expires_in
    
    payload = f"{file_type}|{file_id}|{bucket_id}|{expires_at}"
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    params = {
        'file_id': file_id,
        'bucket_id': bucket_id,
        'file_type': file_type,
        'expires': expires_at,
        'signature': signature
    }
    
    if not base_url:
        try:
            base_url = request.host_url.rstrip('/')
        except RuntimeError:
            base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    
    if not base_url.startswith('http'):
        base_url = f"http://{base_url}"
    
    return f"{base_url}/api/files/download-signed?{urlencode(params)}"

def validate_signed_url(file_id: str, bucket_id: str, file_type: str, 
                        expires: int, signature: str) -> bool:
    """
    Validate a signed URL signature and expiration.
    """
    if int(time.time()) > int(expires):
        return False
    
    secret = Config.SIGNED_URL_SECRET
    payload = f"{file_type}|{file_id}|{bucket_id}|{expires}"
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
