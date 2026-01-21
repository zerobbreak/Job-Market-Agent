from flask import Blueprint, request, jsonify, g
import uuid
import time
import threading
from functools import wraps
from appwrite.client import Client
from appwrite.services.account import Account
from config import Config

auth_bp = Blueprint('auth', __name__)

otp_store = {}
otp_lock = threading.Lock()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow CORS preflight requests to pass through without auth
        # so that the browser can complete OPTIONS checks successfully.
        if request.method == 'OPTIONS':
            # Flask-CORS will attach the appropriate CORS headers.
            return '', 200

        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        else:
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        try:
            client = Client()
            client.set_endpoint(Config.APPWRITE_ENDPOINT)
            client.set_project(Config.APPWRITE_PROJECT_ID)
            client.set_jwt(token)
            
            account = Account(client)
            user = account.get()
            
            g.user = user
            g.user_id = user['$id']
            g.client = client
        except Exception as e:
            return jsonify({'error': f'Invalid or expired token: {str(e)}'}), 401
             
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/otp', methods=['POST'])
@login_required
def generate_otp():
    try:
        auth_header = request.headers.get('Authorization')
        jwt = auth_header.split(' ')[1]
        otp = str(uuid.uuid4())
        
        with otp_lock:
            now = time.time()
            otp_store[otp] = {'jwt': jwt, 'expires': now + Config.OTP_EXPIRY_SECONDS}
            
        return jsonify({'success': True, 'token': otp})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
