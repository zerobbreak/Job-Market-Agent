from flask import Blueprint, request, jsonify, g
from routes.auth_routes import login_required
from appwrite.services.databases import Databases
from appwrite.id import ID
from appwrite.query import Query
from config import Config
from services import job_store
from services.recommendation_engine import engine
import json
import logging
from datetime import datetime

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

# Max rate for analytics (following main.py)
MAX_RATE_ANALYTICS_PER_MIN = 30

@analytics_bp.route('', methods=['POST'])
@login_required
def track_event():
    try:
        data = request.get_json() or {}
        event = data.get('event')
        properties = data.get('properties', {})
        page = data.get('page')
        
        if not event:
            return jsonify({'success': False, 'error': 'Missing event'}), 400
            
        databases = Databases(g.client)
        databases.create_document(
            Config.DATABASE_ID,
            Config.COLLECTION_ID_ANALYTICS,
            ID.unique(),
            data={
                'userId': g.user_id,
                'event': event,
                'properties': json.dumps(properties),
                'page': page or '',
                'created_at': datetime.now().isoformat()
            }
        )
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/engagement', methods=['GET'])
@login_required
def get_engagement_analytics():
    try:
        days = int(request.args.get('days', 30))
        analytics = job_store.get_engagement_analytics(days=days)
        return jsonify({'success': True, 'analytics': analytics})
    except Exception as e:
        logger.error(f"Error getting engagement analytics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/heatmap', methods=['GET'])
@login_required
def get_application_heatmap():
    try:
        heatmap = job_store.get_application_heatmap()
        return jsonify({'success': True, 'heatmap': heatmap})
    except Exception as e:
        logger.error(f"Error getting heatmap: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/track-view', methods=['POST'])
@login_required
def track_application_view():
    try:
        data = request.get_json()
        app_id = data.get('application_id')
        if not app_id:
            return jsonify({'success': False, 'error': 'application_id required'}), 400
        
        job_store.track_view(app_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error tracking view: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/update-status', methods=['POST'])
@login_required
def update_analytics_status():
    try:
        data = request.get_json()
        app_id = data.get('application_id')
        status = data.get('status')
        additional_data = data.get('additional_data', {})
        
        if not app_id or not status:
            return jsonify({'success': False, 'error': 'application_id and status required'}), 400
        
        job_store.update_application_status(app_id, status, additional_data)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@analytics_bp.route('/market-stats', methods=['GET'])
@login_required
def get_market_stats():
    try:
        role = request.args.get('role')
        location = request.args.get('location')
        
        stats = engine.get_market_stats(role, location)
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        logger.error(f"Error getting market stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
