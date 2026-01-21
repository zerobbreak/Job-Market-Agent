from flask import Blueprint, request, jsonify, g, Response, send_file
from routes.auth_routes import login_required
from services.job_store import load_job_state
from utils.signed_urls import validate_signed_url
from utils.pdf_generator import PDFGenerator
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.client import Client
from config import Config
import logging
import os
import tempfile
import requests as _req

file_bp = Blueprint('file', __name__)
logger = logging.getLogger(__name__)

@file_bp.route('/signed-url', methods=['GET', 'POST'])
@login_required
def get_signed_url():
    """Generate a signed URL for a file"""
    try:
        from utils.signed_urls import generate_signed_url
        data = request.get_json() if request.method == 'POST' else request.args
        file_id = data.get('file_id')
        bucket_id = data.get('bucket_id')
        file_type = data.get('file_type', 'storage')
        
        if not file_id:
            return jsonify({'success': False, 'error': 'file_id required'}), 400
            
        url = generate_signed_url(file_id, bucket_id or '', file_type)
        return jsonify({'success': True, 'url': url})
    except Exception as e:
        logger.error(f"Error generating signed URL: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@file_bp.route('/download-signed', methods=['GET'])
def download_signed():
    """Public endpoint for signed downloads (bypasses login_required)"""
    try:
        file_id = request.args.get('file_id')
        bucket_id = request.args.get('bucket_id')
        file_type = request.args.get('file_type')
        expires = request.args.get('expires')
        signature = request.args.get('signature')
        
        if not all([file_id, file_type, expires, signature]):
            return jsonify({'error': 'Missing signature parameters'}), 400
            
        if not validate_signed_url(file_id, bucket_id or '', file_type, int(expires), signature):
            return jsonify({'error': 'Invalid or expired signature'}), 403
            
        if file_type == 'storage':
            return _download_storage_file(file_id, bucket_id)
        elif file_type == 'preview_cv':
            return _download_preview_file(file_id, 'cv')
        elif file_type == 'preview_cover_letter':
            return _download_preview_file(file_id, 'cover_letter')
        else:
            return jsonify({'error': 'Invalid file_type'}), 400
    except Exception as e:
        logger.error(f"Error in signed download: {e}")
        return jsonify({'error': str(e)}), 500

def _download_storage_file(file_id: str, bucket_id: str):
    try:
        # Server-side client for signed URL download
        client = Client()
        client.set_endpoint(Config.APPWRITE_ENDPOINT)
        client.set_project(Config.APPWRITE_PROJECT_ID)
        client.set_key(Config.APPWRITE_API_KEY)
        
        storage = Storage(client)
        file_info = storage.get_file(bucket_id, file_id)
        filename = file_info.get('name', 'download')
        
        url = f"{Config.APPWRITE_ENDPOINT}/storage/buckets/{bucket_id}/files/{file_id}/download"
        headers = {'X-Appwrite-Project': Config.APPWRITE_PROJECT_ID, 'X-Appwrite-Key': Config.APPWRITE_API_KEY}
        
        r = _req.get(url, headers=headers, stream=True)
        if r.status_code != 200: return jsonify({'error': 'Download failed'}), r.status_code
        
        def generate():
            for chunk in r.iter_content(chunk_size=8192): yield chunk
            
        return Response(generate(), headers={
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/octet-stream' # Simplification
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _download_preview_file(job_id: str, doc_type: str):
    try:
        job_info = load_job_state(job_id)
        if not job_info: return jsonify({'error': 'Job not found'}), 404
            
        if job_info.get('status') != 'done': return jsonify({'error': 'Preview not ready'}), 400
        
        result = job_info.get('result', {})
        template_type = job_info.get('template_type', 'modern')
        generator = PDFGenerator()
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
            
        markdown_content = result.get('cv_markdown' if doc_type == 'cv' else 'cl_markdown', '')
        header = result.get('header', {})
        sections = result.get('sections', {}) if doc_type == 'cv' else {}
        
        template = template_type if doc_type == 'cv' else 'cover_letter'
        success = generator.generate_pdf(markdown_content, output_path, template_name=template, header=header, sections=sections)
        
        if success:
            return send_file(output_path, as_attachment=True, download_name=f"{doc_type}.pdf")
        return jsonify({'error': 'PDF generation failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@file_bp.route('/signed-url-test', methods=['GET'])
@login_required
def test_signed_url():
    # Simple test for developers
    return jsonify({'message': 'Signed URL system active'})
