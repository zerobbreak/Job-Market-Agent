import hmac
import hashlib
import time
from urllib.parse import urlencode
from app.core.config import get_settings

settings = get_settings()

def generate_signed_url(file_id: str, bucket_id: str, file_type: str = 'storage', 
                       expires_in: int = 3600, base_url: str = None) -> str:
    """
    Generate a cryptographically signed URL for secure file downloads.
    """
    secret = settings.effective_signed_url_secret
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
        base_url = settings.api_base_url.rstrip('/')

    if not base_url.startswith('http'):
        base_url = f"http://{base_url}"
    
    return f"{base_url}/api/v1/files/download-signed?{urlencode(params)}"

def validate_signed_url(file_id: str, bucket_id: str, file_type: str, 
                        expires: int, signature: str) -> bool:
    """
    Validate a signed URL signature and expiration.
    """
    if int(time.time()) > int(expires):
        return False
    
    secret = settings.effective_signed_url_secret
    payload = f"{file_type}|{file_id}|{bucket_id}|{expires}"
    
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
