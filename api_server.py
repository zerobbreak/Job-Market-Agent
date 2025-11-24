from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from werkzeug.utils import secure_filename
from main import JobApplicationPipeline

app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/search-jobs', methods=['POST'])
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
def apply_job():
    try:
        # Check if CV file is present
        if 'cv' not in request.files:
            return jsonify({'success': False, 'error': 'No CV file provided'})
        
        cv_file = request.files['cv']
        job_data = json.loads(request.form.get('job', '{}'))
        
        if cv_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if cv_file and allowed_file(cv_file.filename):
            filename = secure_filename(cv_file.filename)
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            cv_file.save(cv_path)
            
            # Initialize the pipeline
            pipeline = JobApplicationPipeline()
            
            # Load CV
            success = pipeline.load_cv(cv_path)
            if not success:
                return jsonify({'success': False, 'error': 'Failed to load CV'})
            
            # Build profile
            pipeline.build_profile()
            
            # Generate application materials
            job_description = f"{job_data.get('title', '')} at {job_data.get('company', '')}. {job_data.get('description', '')}"
            cv_content = pipeline.generate_cv(job_description)
            cover_letter = pipeline.generate_cover_letter(job_description)
            
            # Save application materials
            output_dir = f"applications/{job_data.get('company', 'unknown').replace(' ', '_')}"
            os.makedirs(output_dir, exist_ok=True)
            
            # Save CV
            cv_filename = os.path.join(output_dir, f"cv_{filename}")
            with open(cv_filename, 'w', encoding='utf-8') as f:
                f.write(cv_content)
            
            # Save cover letter
            cover_letter_filename = os.path.join(output_dir, "cover_letter.html")
            with open(cover_letter_filename, 'w', encoding='utf-8') as f:
                f.write(cover_letter)
            
            # Generate interview prep
            interview_prep = pipeline.prepare_interview(job_description)
            
            # Save interview prep
            interview_filename = os.path.join(output_dir, "interview_prep.txt")
            with open(interview_filename, 'w', encoding='utf-8') as f:
                f.write(interview_prep)
            
            # Clean up uploaded file
            os.remove(cv_path)
            
            return jsonify({
                'success': True,
                'message': 'Application generated successfully',
                'files': {
                    'cv': cv_filename,
                    'cover_letter': cover_letter_filename,
                    'interview_prep': interview_filename
                }
            })
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
    
    except Exception as e:
        print(f"Error applying to job: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/applications', methods=['GET'])
def get_applications():
    try:
        applications = []
        if os.path.exists('applications'):
            for company_dir in os.listdir('applications'):
                company_path = os.path.join('applications', company_dir)
                if os.path.isdir(company_path):
                    # Get creation date
                    stat = os.stat(company_path)
                    applications.append({
                        'id': company_dir,
                        'company': company_dir.replace('_', ' '),
                        'status': 'applied',
                        'appliedDate': stat.st_ctime,
                        'files': os.listdir(company_path)
                    })
        
        return jsonify({'applications': applications})
    
    except Exception as e:
        print(f"Error getting applications: {e}")
        return jsonify({'applications': [], 'error': str(e)})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(debug=True, port=8000)
