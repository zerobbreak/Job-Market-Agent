from flask import Blueprint, jsonify, request
from services.task_manager import task_manager
from services.job_store import get_recent_failures, get_application_stats
from routes.auth_routes import login_required
import logging
import psutil
import os

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

@admin_bp.route('/health', methods=['GET'])
# @login_required # Uncomment to secure this endpoint
def system_health():
    """
    Get comprehensive system health status.
    Monitors:
    - Task Manager (Threads)
    - System Resources (CPU, Memory)
    - Job Failures (Circuit Breaker)
    """
    try:
        # Task Manager Stats
        tm_stats = task_manager.get_system_stats()
        
        # System Resources
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        system_stats = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_usage_mb": round(mem_info.rss / 1024 / 1024, 2),
            "uptime_seconds": int(psutil.time.time() - process.create_time())
        }
        
        # Business Logic Health
        failures = get_recent_failures(limit=10)
        app_stats = get_application_stats()
        
        return jsonify({
            "status": "ok",
            "task_manager": tm_stats,
            "system": system_stats,
            "business_metrics": {
                "recent_job_failures": failures,
                "total_applications": app_stats.get('total', 0),
                "application_breakdown": app_stats
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
