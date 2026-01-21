from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
import os
import logging
import sys

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configure logging - Production Ready (Stdout)
    # Using simple format for now, but to stdout for container log collection
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    logger = logging.getLogger(__name__)

    # Configure CORS - Battle-tested configuration used by industry leaders
    # Based on best practices from AWS API Gateway, Google Cloud, and major SaaS platforms
    default_origins = [
        'http://localhost:5173',
        'https://job-market-agent.vercel.app',
        'https://job-market-frontend.vercel.app',
        'https://job-market-agent.onrender.com'
    ]
    
    # Explicit CORS configuration with automatic OPTIONS handling
    CORS(app, 
         resources={
             r"/api/*": {
                 "origins": default_origins,
                 "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                 "allow_headers": [
                     "Content-Type", 
                     "Authorization", 
                     "X-Appwrite-Project", 
                     "X-Appwrite-JWT",
                     "Accept",
                     "Origin",
                     "X-Requested-With"
                 ],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True,
                 "max_age": 3600  # Cache preflight for 1 hour
             }
         },
         automatic_options=True  # Automatically handle OPTIONS requests
    )

    # Register Blueprints
    from routes.auth_routes import auth_bp
    from routes.profile_routes import profile_bp
    from routes.job_routes import job_bp
    from routes.analytics_routes import analytics_bp
    from routes.application_routes import application_bp
    from routes.file_routes import file_bp
    from routes.admin_routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(job_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(application_bp, url_prefix='/api/applications')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    # Initialize Task Manager (Background Worker)
    # Only start if not in reloader mode (to avoid duplicate workers) or check environment
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        try:
            from services.task_manager import task_manager
            task_manager.start()
            logger.info("Task Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to start Task Manager: {e}")

    @app.route('/')
    def index():
        return jsonify({"status": "running", "message": "Job Market Agent API (Production Ready) is active."})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
