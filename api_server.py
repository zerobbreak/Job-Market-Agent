from flask import Flask, request, jsonify, send_file, g
from flask_cors import CORS
import os
import json
import re
from werkzeug.utils import secure_filename
from main import JobApplicationPipeline
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.services.messaging import Messaging
from appwrite.id import ID
from appwrite.query import Query
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # For session management

# Initialize Appwrite Client
client = Client()
client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
# client.set_key(os.getenv('APPWRITE_API_KEY')) # Only needed for admin tasks

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Appwrite Constants
DATABASE_ID = 'job-market-db'
COLLECTION_ID_JOBS = 'jobs'
COLLECTION_ID_APPLICATIONS = 'applications'
COLLECTION_ID_PROFILES = 'profiles'
BUCKET_ID_CVS = 'cv-bucket'

# Global storage for pipelines and profiles (in production, use Redis or database)
pipeline_store = {}
profile_store = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Create a new client instance for this request to be thread-safe
            # and to set the JWT for this specific user
            request_client = Client()
            request_client.set_endpoint(os.getenv('APPWRITE_API_ENDPOINT', 'https://cloud.appwrite.io/v1'))
            request_client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
            request_client.set_jwt(token)
            
            account = Account(request_client)
            user = account.get()
            
            # Store user info in Flask's global 'g' object
            g.user = user
            g.user_id = user['$id']
            g.client = request_client # Pass the authenticated client for DB operations
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/search-jobs', methods=['POST'])
@login_required
def search_jobs():
    try:
        data = request.get_json()
        query = data.get('query', '')
        location = data.get('location', '')
        max_results = int(data.get('max_results', 10))
        
        # Initialize the pipeline
        pipeline = JobApplicationPipeline()
        
        # Search for jobs using pipeline API (query, location, max_results)
        jobs = pipeline.search_jobs(query=query or 'Python Developer', location=location or 'South Africa', max_results=max_results)
        
        # Format jobs for frontend
        formatted_jobs = []
        for job in jobs[:10]:  # Limit to 10 jobs
            formatted_jobs.append({
                'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'location': job.get('location', ''),
                'description': (job.get('description', '') or '')[:200] + ('...' if job.get('description') else ''),
                'url': job.get('url', ''),
            })
        
        return jsonify({'jobs': formatted_jobs})
    
    except Exception as e:
        print(f"Error searching jobs: {e}")
        return jsonify({'jobs': [], 'error': str(e)})

@app.route('/api/apply-job', methods=['POST'])
@login_required
def apply_job():
    try:
        # Check if using session_id (Apply with AI)
        if request.is_json:
            data = request.get_json()
            session_id = g.user_id # Use user_id as session_id
            job_data = data.get('job')
            
            # Ensure pipeline exists
            if session_id not in pipeline_store:
                 # Try to reconstruct pipeline if profile exists in DB
                 # For now, simplistic check
                 pipeline_store[session_id] = JobApplicationPipeline()
            
            pipeline = pipeline_store[session_id]
            
            # Generate application materials
            print(f"Generating application for {job_data.get('company')} using session {session_id}")
            app_result = pipeline.generate_application_package(job_data)
            
            if not app_result:
                return jsonify({'success': False, 'error': 'Failed to generate application materials'})
            
            # Generate interview prep
            interview_prep_path = pipeline.prepare_interview(job_data)
            
            # --- Appwrite Integration: Save Application ---
            try:
                databases = Databases(g.client)
                storage = Storage(g.client)
                
                # Upload generated files to Storage
                # (Implementation omitted for brevity, but similar to CV upload)
                
                # Create Application Record
                databases.create_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_APPLICATIONS,
                    document_id=ID.unique(),
                    data={
                        'userId': g.user_id,
                        'jobTitle': job_data.get('title', 'Unknown'),
                        'company': job_data.get('company', 'Unknown'),
                        'status': 'applied',
                        # 'files': ... (store file IDs)
                    }
                )
            except Exception as e:
                print(f"Error saving application to DB: {e}")

            return jsonify({
                'success': True,
                'message': 'Application generated successfully',
                'files': {
                    'cv': f"/api/download?path={app_result['cv_path']}",
                    'cover_letter': f"/api/download?path={app_result['cover_letter_path']}",
                    'interview_prep': f"/api/download?path={interview_prep_path}" if interview_prep_path else None
                }
            })

        # Fallback to file upload method (Legacy) - REMOVED or kept as is but less prioritized
        # ... (Legacy code omitted for clarity, assuming JSON flow is primary now)
        return jsonify({'success': False, 'error': 'Legacy upload method deprecated. Please use Apply with AI.'})
    
    except Exception as e:
        print(f"Error applying to job: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download', methods=['GET'])
def download_file():
    try:
        file_path = request.args.get('path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
            
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/applications', methods=['GET'])
@login_required
def get_applications():
    try:
        databases = Databases(g.client)
        
        # Query applications for the current user
        result = databases.list_documents(
            database_id=DATABASE_ID,
            collection_id=COLLECTION_ID_APPLICATIONS,
            queries=[
                Query.equal('userId', g.user_id),
                Query.order_desc('$createdAt')
            ]
        )
        
        applications = []
        for doc in result['documents']:
            applications.append({
                'id': doc['$id'],
                'jobTitle': doc.get('jobTitle', 'Unknown Position'),
                'company': doc.get('company', 'Unknown Company'),
                'status': doc.get('status', 'applied'),
                'appliedDate': doc.get('$createdAt', '').split('T')[0], # Format date
                # 'files': ... 
            })
            
        return jsonify({'applications': applications})
    
    except Exception as e:
        print(f"Error getting applications: {e}")
        # Fallback to empty list or handle error gracefully
        return jsonify({'applications': [], 'error': str(e)})

@app.route('/api/analyze-cv', methods=['POST'])
@login_required
def analyze_cv():
    """Analyze uploaded CV and build candidate profile"""
    try:
        cv_file = request.files['cv']
        
        if cv_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if cv_file and allowed_file(cv_file.filename):
            filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cv_file.save(cv_path)
            
            # Initialize the pipeline
            pipeline = JobApplicationPipeline(cv_path=cv_path)
            
            # Load CV
            cv_content = pipeline.load_cv()
            if not cv_content:
                return jsonify({'success': False, 'error': 'Failed to load CV'})
            
            # Build profile using AI
            profile_text = pipeline.build_profile(cv_content)
            
            if not profile_text:
                return jsonify({'success': False, 'error': 'Failed to build profile'})
            
            # Parse profile text to extract structured data
            profile_data = parse_profile(profile_text)
            
            # --- Appwrite Integration ---
            try:
                databases = Databases(g.client)
                storage = Storage(g.client)
                
                # 1. Upload CV to Storage using InputFile
                from appwrite.input_file import InputFile
                
                result = storage.create_file(
                    bucket_id=BUCKET_ID_CVS,
                    file_id=ID.unique(),
                    file=InputFile.from_path(cv_path)
                )
                file_id = result['$id']

                # 2. Save Profile to Database
                # Check if profile already exists for this user
                existing_profiles = databases.list_documents(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', g.user_id)]
                )
                
                profile_doc_data = {
                    'userId': g.user_id,
                    'skills': json.dumps(profile_data.get('skills', [])), # Store as JSON string
                    'experience_level': profile_data.get('experience_level', 'N/A'),
                    # Add other fields as needed by your schema
                }

                if existing_profiles['total'] > 0:
                    # Update existing profile
                    profile_id = existing_profiles['documents'][0]['$id']
                    databases.update_document(
                        database_id=DATABASE_ID,
                        collection_id=COLLECTION_ID_PROFILES,
                        document_id=profile_id,
                        data=profile_doc_data
                    )
                else:
                    # Create new profile
                    databases.create_document(
                        database_id=DATABASE_ID,
                        collection_id=COLLECTION_ID_PROFILES,
                        document_id=ID.unique(),
                        data=profile_doc_data
                    )
                
                # Store pipeline in memory for immediate subsequent requests (like matching)
                # In a stateless architecture, we'd rebuild it from the stored data
                # For now, we'll keep the session_id concept for the immediate session
                # but rely on DB for persistence.
                session_id = g.user_id # Use user_id as session_id for simplicity in this flow
                pipeline_store[session_id] = pipeline
                profile_store[session_id] = {
                    'profile_data': profile_data,
                    'raw_profile': profile_text,
                    'cv_filename': filename,
                    'cv_content': cv_content,
                    'file_id': file_id 
                }

            except Exception as db_error:
                print(f"Appwrite Error: {db_error}")
                # Continue even if DB save fails, to return result to user
                # But in production you'd want to handle this better
            
            # Clean up local file
            # os.remove(cv_path) # Keep for now if pipeline needs it, or ensure pipeline loads content into memory

            return jsonify({
                'success': True,
                'session_id': g.user_id, # Return user_id as session_id
                'profile': profile_data,
                'raw_profile': profile_text,
                'cv_filename': filename
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    except Exception as e:
        print(f"Error analyzing CV: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/match-jobs', methods=['POST'])
@login_required
def match_jobs():
    """Find and rank jobs based on CV profile"""
    try:
        data = request.get_json()
        # session_id is now effectively user_id
        session_id = g.user_id 
        location = data.get('location', 'South Africa')
        max_results = int(data.get('max_results', 20))
        
        profile_info = None
        
        # 1. Try to get from memory first
        if session_id in profile_store:
            profile_info = profile_store[session_id]
        
        # 2. If not in memory, try to fetch from Appwrite DB
        if not profile_info:
            try:
                databases = Databases(g.client)
                existing_profiles = databases.list_documents(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    queries=[Query.equal('userId', g.user_id)]
                )
                
                if existing_profiles['total'] > 0:
                    doc = existing_profiles['documents'][0]
                    profile_data = {
                        'skills': json.loads(doc.get('skills', '[]')),
                        'experience_level': doc.get('experience_level', ''),
                        # Reconstruct other fields if saved
                    }
                    
                    # Reconstruct profile_info structure
                    profile_info = {
                        'profile_data': profile_data,
                        'raw_profile': '', # Might not be saved
                        'cv_filename': 'Stored Profile',
                        'cv_content': '' # Might not be saved
                    }
                    
                    # Cache back to memory
                    profile_store[session_id] = profile_info
                    
            except Exception as e:
                print(f"Error fetching profile from DB: {e}")

        if not profile_info:
            return jsonify({'success': False, 'error': 'No profile found. Please upload CV first.'})
        
        # Ensure pipeline exists
        pipeline = pipeline_store.get(session_id)
        if not pipeline:
            # Re-initialize pipeline if missing (e.g. server restart)
            pipeline = JobApplicationPipeline()
            pipeline_store[session_id] = pipeline
        
        # Extract skills from profile to build search query
        profile_data = profile_info['profile_data']
        skills = profile_data.get('skills', [])
        
        # Build search query from top skills
        search_query = ' '.join(skills[:3]) if skills else 'Software Developer'
        
        print(f"\n=== Job Matching ===")
        print(f"Search query: {search_query}")
        print(f"Location: {location}")
        
        # Search for jobs
        jobs = pipeline.search_jobs(
            query=search_query,
            location=location,
            max_results=max_results
        )
        
        if not jobs:
            return jsonify({'success': True, 'matches': []})
        
        print(f"Found {len(jobs)} jobs, scoring matches...")
        
        # Score and rank jobs based on profile match
        matches = []
        for job in jobs[:max_results]:
            match_result = score_job_match(job, profile_info)
            
            # Better location handling with fallbacks
            job_location = (
                job.get('location') or 
                job.get('job_location') or 
                job.get('city') or 
                ''
            )
            
            # Replace placeholder values with search location
            if not job_location or job_location in ['Unknown Location', 'N/A', 'unknown', '']:
                job_location = location
            
            matches.append({
                'job': {
                    'id': str(job.get('job_hash', job.get('url', job.get('title', '')))),
                    'title': job.get('title', 'Unknown Position'),
                    'company': job.get('company', 'Unknown Company'),
                    'location': job_location,
                    'description': job.get('description', 'No description available'),
                    'url': job.get('url', ''),
                },
                'match_score': match_result['score'],
                'match_reasons': match_result['reasons']
            })
        
        # Sort by match score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"Returning {len(matches)} matched jobs")
        
        # Send email notification for high-quality matches
        try:
            # Get user email and name from Appwrite account
            account = Account(g.client)
            user_account = account.get()
            user_email = user_account['email']
            user_name = user_account['name'] or 'there'
            
            # Send notification (async, won't block response)
            send_job_match_notification(user_email, user_name, matches, threshold=70)
        except Exception as notify_error:
            # Don't fail job matching if notification fails
            print(f"Note: Email notification skipped - {notify_error}")
        
        return jsonify({
            'success': True,
            'matches': matches
        })
    
    except Exception as e:
        print(f"Error matching jobs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/profile', methods=['POST'])
@login_required
def get_profile():
    """Retrieve analyzed profile"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in profile_store:
            return jsonify({'success': False, 'error': 'No profile found'})
        
        profile_info = profile_store[session_id]
        
        return jsonify({
            'success': True,
            'profile': profile_info['profile_data'],
            'raw_profile': profile_info['raw_profile'],
            'cv_filename': profile_info['cv_filename']
        })
    
    except Exception as e:
        print(f"Error getting profile: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        user_id = g.user_id
        
        # Validate profile data
        if not data:
            return jsonify({'success': False, 'error': 'No profile data provided'}), 400
        
        # Update profile in Appwrite
        try:
            # Check if profile exists
            existing_profiles = databases.list_documents(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID_PROFILES,
                queries=[
                    Query.equal('userId', user_id)
                ]
            )
            
            profile_doc = {
                'userId': user_id,
                'skills': json.dumps(data.get('skills', [])),
                'experience_level': data.get('experience_level', ''),
                'education': data.get('education', ''),
                'strengths': json.dumps(data.get('strengths', [])),
                'career_goals': data.get('career_goals', ''),
                'updated_at': datetime.now().isoformat()
            }
            
            if existing_profiles['total'] > 0:
                # Update existing profile
                doc_id = existing_profiles['documents'][0]['$id']
                databases.update_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    document_id=doc_id,
                    data=profile_doc
                )
            else:
                # Create new profile
                databases.create_document(
                    database_id=DATABASE_ID,
                    collection_id=COLLECTION_ID_PROFILES,
                    document_id=ID.unique(),
                    data=profile_doc
                )
            
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
            
        except Exception as db_error:
            print(f"Database error updating profile: {db_error}")
            return jsonify({'success': False, 'error': 'Failed to update profile in database'}), 500
            
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



def send_job_match_notification(user_email, user_name, matches, threshold=70):
    """
    Send email notification for high-quality job matches using Appwrite Messaging
    
    Args:
        user_email: User's email address
        user_name: User's name
        matches: List of matched jobs with scores
        threshold: Minimum match score to notify (default 70%)
    """
    try:
        # Filter high-quality matches
        high_quality_matches = [m for m in matches if m['match_score'] >= threshold]
        
        if not high_quality_matches:
            print(f"No matches above {threshold}% threshold for {user_email}")
            return
        
        # Sort by score (highest first)
        high_quality_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Limit to top 5 matches for email
        top_matches = high_quality_matches[:5]
        
        # Build email content
        email_subject = f"🎯 {len(high_quality_matches)} New Job Matches Found!"
        
        # Create HTML email body
        matches_html = ""
        for match in top_matches:
            job = match['job']
            score = match['match_score']
            reasons = match['match_reasons'][:3]  # Top 3 reasons
            
            # Color code based on score
            if score >= 80:
                badge_color = "#10b981"  # green
            elif score >= 70:
                badge_color = "#f59e0b"  # yellow
            else:
                badge_color = "#6b7280"  # gray
            
            matches_html += f"""
            <div style="background: #f9fafb; border-left: 4px solid {badge_color}; padding: 20px; margin-bottom: 20px; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                    <h3 style="margin: 0; color: #111827; font-size: 18px;">{job['title']}</h3>
                    <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 14px;">{score}% Match</span>
                </div>
                <p style="color: #6b7280; margin: 5px 0;">{job['company']} • {job['location']}</p>
                <div style="margin-top: 10px;">
                    <p style="font-weight: 600; color: #374151; margin-bottom: 5px;">Why this matches:</p>
                    <ul style="margin: 0; padding-left: 20px; color: #6b7280;">
                        {''.join([f"<li>{reason}</li>" for reason in reasons])}
                    </ul>
                </div>
                <a href="{job['url']}" style="display: inline-block; margin-top: 15px; background: linear-gradient(to right, #2563eb, #7c3aed); color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 600;">View Job Details</a>
            </div>
            """
        
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #374151; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(to right, #2563eb, #7c3aed); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">✨ Job Market Agent</h1>
                <p style="color: #e0e7ff; margin: 10px 0 0 0;">AI-Powered Career Matching</p>
            </div>
            
            <div style="background: white; padding: 30px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
                <h2 style="color: #111827; margin-top: 0;">Hi {user_name}! 👋</h2>
                <p style="color: #6b7280; font-size: 16px;">Great news! We found <strong>{len(high_quality_matches)} high-quality job matches</strong> that align with your profile and career goals.</p>
                
                <div style="margin: 30px 0;">
                    {matches_html}
                </div>
                
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; padding: 20px; border-radius: 8px; margin-top: 30px;">
                    <p style="margin: 0; color: #1e40af; font-size: 14px;">
                        💡 <strong>Tip:</strong> Jobs with 80%+ match scores are excellent fits for your skills and experience. We recommend applying to these first!
                    </p>
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 30px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #9ca3af; font-size: 14px; margin: 0;">
                        You're receiving this email because you have notifications enabled in your Job Market Agent profile.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email via Appwrite Messaging
        try:
            messaging = Messaging(client)
            
            # Create email message
            # Note: This requires an email provider to be configured in Appwrite console
            message = messaging.create_email(
                message_id=ID.unique(),
                subject=email_subject,
                content=email_body,
                topics=[],  # Can use topics for user segmentation
                users=[],   # Will send to specific email instead
                targets=[user_email],  # Direct email
                draft=False,
                html=True
            )
            
            print(f"✅ Email notification sent to {user_email} for {len(high_quality_matches)} matches")
            return True
            
        except Exception as email_error:
            # Graceful degradation - log error but don't fail job matching
            print(f"⚠️  Failed to send email notification: {email_error}")
            print(f"   This is likely because no email provider is configured in Appwrite console")
            print(f"   Job matching will continue normally")
            return False
            
    except Exception as e:
        print(f"Error in send_job_match_notification: {e}")
        return False

def parse_profile(profile_text):
    """Parse AI-generated profile text into structured data"""
    profile_data = {
        'skills': [],
        'experience_level': '',
        'education': '',
        'strengths': [],
        'career_goals': ''
    }
    
    try:
        # Try to find JSON content
        json_str = profile_text
        
        # Handle markdown code blocks
        if '```json' in profile_text:
            json_str = profile_text.split('```json')[1].split('```')[0]
        elif '```' in profile_text:
            json_str = profile_text.split('```')[1].split('```')[0]
            
        # Clean up string
        json_str = json_str.strip()
        
        # Parse JSON
        data = json.loads(json_str)
        
        # Update profile data with parsed values
        profile_data.update(data)
        
        # Ensure lists are actually lists
        if isinstance(profile_data['skills'], str):
            profile_data['skills'] = [s.strip() for s in profile_data['skills'].split(',')]
            
        if isinstance(profile_data['strengths'], str):
            profile_data['strengths'] = [s.strip() for s in profile_data['strengths'].split(',')]
            
    except Exception as e:
        print(f"Error parsing profile JSON: {e}")
        # Fallback to regex if JSON parsing fails
        try:
            # Extract skills
            skills_match = re.search(r'(?:Skills|Technical Skills|Expertise)[:\s]*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\n[A-Z]|$)', profile_text, re.IGNORECASE)
            if skills_match:
                skills_text = skills_match.group(1)
                skills = re.findall(r'(?:[-•*]\s*)?([A-Za-z][A-Za-z0-9+#\.\s]+?)(?=[,;\n]|$)', skills_text)
                profile_data['skills'] = [s.strip() for s in skills if len(s.strip()) > 2][:10]
            
            # Extract experience level
            exp_match = re.search(r'(?:Experience Level|Experience|Years)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
            if exp_match:
                profile_data['experience_level'] = exp_match.group(1).strip()
            
            # Extract education
            edu_match = re.search(r'(?:Education|Degree|Qualification)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
            if edu_match:
                profile_data['education'] = edu_match.group(1).strip()
            
            # Extract strengths
            strengths_match = re.search(r'(?:Strengths|Key Strengths)[:\s]*([^\n]+(?:\n[^\n]+)*?)(?=\n\n|\n[A-Z]|$)', profile_text, re.IGNORECASE)
            if strengths_match:
                strengths_text = strengths_match.group(1)
                strengths = re.findall(r'(?:[-•*]\s*)?([^\n,;]+)', strengths_text)
                profile_data['strengths'] = [s.strip() for s in strengths if len(s.strip()) > 5][:5]
            
            # Extract career goals
            goals_match = re.search(r'(?:Career Goals|Goals|Aspirations)[:\s]*([^\n]+)', profile_text, re.IGNORECASE)
            if goals_match:
                profile_data['career_goals'] = goals_match.group(1).strip()
        except Exception as e2:
            print(f"Error in fallback parsing: {e2}")
    
    return profile_data

def score_job_match(job, profile_info):
    """Score how well a job matches the candidate profile"""
    profile_data = profile_info['profile_data']
    job_title = job.get('title', '').lower()
    job_description = (job.get('description', '') or '').lower()
    job_company = job.get('company', '').lower()
    
    # Combine all job text for better matching
    job_text = f"{job_title} {job_description} {job_company}"
    
    score = 20  # Base score - gives credit for being in search results
    reasons = []
    
    # Debug output
    print(f"\n=== Scoring: {job.get('title', 'Unknown')} ===")
    
    # Check skill matches (more flexible matching)
    skills = profile_data.get('skills', [])
    matched_skills = []
    
    for skill in skills:
        skill_lower = skill.lower()
        skill_words = [w for w in skill_lower.split() if len(w) > 2]
        
        # Try exact match first
        if skill_lower in job_text:
            matched_skills.append(skill)
            score += 15
            print(f"  ✓ Exact skill: {skill}")
        # Try partial match (any significant word from skill)
        elif any(word in job_text for word in skill_words):
            matched_skills.append(skill)
            score += 10
            print(f"  ✓ Partial skill: {skill}")
    
    if matched_skills:
        reasons.append(f"Matches your skills: {', '.join(matched_skills[:3])}")
    
    # Check experience level alignment
    experience = profile_data.get('experience_level', '').lower()
    if experience:
        if 'senior' in experience and 'senior' in job_text:
            score += 15
            reasons.append("Senior level match")
        elif 'junior' in experience and ('junior' in job_text or 'entry' in job_text):
            score += 15
            reasons.append("Junior/Entry level match")
        elif 'mid' in experience and ('mid' in job_text or 'intermediate' in job_text):
            score += 15
            reasons.append("Mid-level match")
        else:
            score += 5  # General experience consideration
    
    # Check strengths alignment
    strengths = profile_data.get('strengths', [])
    for strength in strengths[:2]:  # Check top 2 strengths
        strength_words = [w for w in strength.lower().split() if len(w) > 3]
        if any(word in job_text for word in strength_words):
            score += 8
            reasons.append(f"Leverages {strength}")
            print(f"  ✓ Strength: {strength}")
    
    # Check career goals
    goals = profile_data.get('career_goals', '').lower()
    if goals:
        goal_words = [w for w in goals.split() if len(w) > 3]
        if any(word in job_text for word in goal_words):
            score += 10
            reasons.append("Aligns with career goals")
    
    # Ensure score is between 0-100
    score = min(score, 100)
    
    print(f"  Score: {score}")
    
    # Add default reason if no specific reasons found
    if not reasons:
        reasons.append("Relevant to your profile")
    
    return {
        'score': score,
        'reasons': reasons[:3]
    }

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=8000)
