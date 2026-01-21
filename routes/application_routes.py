from flask import Blueprint, request, jsonify, g
from routes.auth_routes import login_required
from appwrite.services.databases import Databases
from appwrite.query import Query
from config import Config
import logging

application_bp = Blueprint('application', __name__)
logger = logging.getLogger(__name__)

@application_bp.route('', methods=['GET'])
@login_required
def get_applications():
    try:
        databases = Databases(g.client)
        try:
            page = int(request.args.get('page', '1'))
            limit = int(request.args.get('limit', '10'))
        except Exception:
            page, limit = 1, 10
        offset = max(0, (page - 1) * limit)
        
        result = databases.list_documents(
            database_id=Config.DATABASE_ID,
            collection_id=Config.COLLECTION_ID_APPLICATIONS,
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$createdAt'),
                Query.limit(limit),
                Query.offset(offset)
            ]
        )
        applications = []
        for doc in result['documents']:
            applications.append({
                'id': doc['$id'],
                'jobTitle': doc.get('jobTitle', 'Unknown Position'),
                'company': doc.get('company', 'Unknown Company'),
                'jobUrl': doc.get('jobUrl', ''),
                'location': doc.get('location', ''),
                'status': doc.get('status', 'applied'),
                'appliedDate': doc.get('$createdAt', '').split('T')[0],
                'files': doc.get('files')
            })
        return jsonify({
            'applications': applications, 
            'page': page, 
            'limit': limit, 
            'total': result.get('total', len(applications))
        })
    except Exception as e:
        logger.error(f"Error fetching applications: {e}")
        return jsonify({'applications': [], 'error': str(e)}), 500

@application_bp.route('/<doc_id>/status', methods=['PUT'])
@login_required
def update_application_status(doc_id):
    try:
        data = request.get_json() or {}
        new_status = data.get('status')
        allowed = {'pending', 'applied', 'interview', 'rejected'}
        if new_status not in allowed:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
            
        databases = Databases(g.client)
        doc = databases.get_document(Config.DATABASE_ID, Config.COLLECTION_ID_APPLICATIONS, doc_id)
        if doc.get('userId') != g.user_id:
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
            
        databases.update_document(Config.DATABASE_ID, Config.COLLECTION_ID_APPLICATIONS, doc_id, data={'status': new_status})
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating application status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
