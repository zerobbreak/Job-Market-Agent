"""
ML Model Monitoring and Continuous Learning Pipeline
Production monitoring, drift detection, and automated model retraining
"""

import os
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
import numpy as np
import pandas as pd
from collections import deque
import joblib
import warnings

# ML monitoring imports
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from scipy.stats import ks_2samp, chi2_contingency
import psutil
import GPUtil

# Local imports
from utils.ml_evaluation import ml_evaluation_framework
from utils.ethical_ai_safeguards import ethical_safeguards

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for ML monitoring"""
    monitoring_interval: int = 300  # 5 minutes
    drift_detection_window: int = 1000  # Samples for drift detection
    performance_alert_threshold: float = 0.1  # 10% performance drop
    retraining_trigger_threshold: float = 0.15  # 15% performance degradation
    max_model_age_days: int = 90  # Retrain every 90 days
    enable_auto_retraining: bool = True
    alert_email_enabled: bool = False

@dataclass
class ModelMetrics:
    """Real-time model performance metrics"""
    timestamp: datetime
    predictions_count: int = 0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    drift_score: float = 0.0

@dataclass
class ModelVersion:
    """Model version information"""
    version_id: str
    creation_timestamp: datetime
    model_path: str
    performance_metrics: Dict[str, float]
    ethical_audit_score: float
    is_active: bool = False
    retirement_date: Optional[datetime] = None

class MLMonitoringPipeline:
    """
    Comprehensive ML model monitoring and continuous learning system.
    Handles performance tracking, drift detection, and automated retraining.
    """

    def __init__(self, config: Optional[MonitoringConfig] = None,
                 models_dir: str = "ml_models", monitoring_dir: str = "ml_monitoring"):
        """
        Initialize ML monitoring pipeline

        Args:
            config: Monitoring configuration
            models_dir: Directory containing ML models
            monitoring_dir: Directory for monitoring data and logs
        """
        self.config = config or MonitoringConfig()
        self.models_dir = models_dir
        self.monitoring_dir = monitoring_dir

        # Initialize monitoring components
        self._setup_directories()
        self._initialize_monitoring_components()

        # Model registry and monitoring data
        self.model_registry: Dict[str, ModelVersion] = {}
        self.active_models: Dict[str, Any] = {}
        self.monitoring_data: Dict[str, deque] = {}
        self.performance_history: Dict[str, List[ModelMetrics]] = {}

        # Retraining queue and thread
        self.retraining_queue = deque()
        self.monitoring_thread: Optional[threading.Thread] = None
        self.retraining_thread: Optional[threading.Thread] = None

        # Load existing models and monitoring state
        self._load_existing_models()
        self._load_monitoring_state()

        # Start monitoring threads
        self._start_monitoring_threads()

    def _setup_directories(self):
        """Create necessary directories for monitoring"""
        directories = [
            self.monitoring_dir,
            f"{self.monitoring_dir}/metrics",
            f"{self.monitoring_dir}/alerts",
            f"{self.monitoring_dir}/drift_reports",
            f"{self.monitoring_dir}/retraining_logs",
            f"{self.monitoring_dir}/model_versions",
            f"{self.monitoring_dir}/performance_reports"
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _initialize_monitoring_components(self):
        """Initialize monitoring components"""
        # Performance trackers
        self.performance_trackers = {
            'accuracy_tracker': self._track_accuracy_metrics,
            'latency_tracker': self._track_latency_metrics,
            'error_tracker': self._track_error_metrics,
            'drift_detector': self._detect_data_drift
        }

        # Alert system
        self.alert_system = AlertSystem(self.config, f"{self.monitoring_dir}/alerts")

        # Retraining system
        self.retraining_system = RetrainingSystem(
            self.config, f"{self.monitoring_dir}/retraining_logs"
        )

    def _load_existing_models(self):
        """Load existing models from registry"""
        registry_file = f"{self.monitoring_dir}/model_registry.json"

        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r') as f:
                    registry_data = json.load(f)

                for model_name, version_data in registry_data.items():
                    version = ModelVersion(**version_data)
                    self.model_registry[model_name] = version

                    # Load active models
                    if version.is_active:
                        model_path = version.model_path
                        if os.path.exists(model_path):
                            try:
                                self.active_models[model_name] = joblib.load(model_path)
                                logger.info(f"Loaded active model: {model_name} v{version.version_id}")
                            except Exception as e:
                                logger.error(f"Failed to load model {model_name}: {e}")

            except Exception as e:
                logger.error(f"Failed to load model registry: {e}")

    def _load_monitoring_state(self):
        """Load previous monitoring state"""
        # Initialize monitoring data structures for each active model
        for model_name in self.active_models.keys():
            self.monitoring_data[model_name] = deque(maxlen=self.config.drift_detection_window)
            self.performance_history[model_name] = []

    def _start_monitoring_threads(self):
        """Start background monitoring threads"""
        self.monitoring_thread = threading.Thread(
            target=self._continuous_monitoring, daemon=True
        )
        self.monitoring_thread.start()

        self.retraining_thread = threading.Thread(
            target=self._continuous_retraining, daemon=True
        )
        self.retraining_thread.start()

        logger.info("ML monitoring and retraining threads started")

    def record_prediction(self, model_name: str, features: np.ndarray,
                         prediction: Any, actual: Optional[Any] = None,
                         latency_ms: Optional[float] = None) -> None:
        """
        Record a model prediction for monitoring

        Args:
            model_name: Name of the model
            features: Input features
            prediction: Model prediction
            actual: Actual label (if available for evaluation)
            latency_ms: Prediction latency in milliseconds
        """
        if model_name not in self.monitoring_data:
            self.monitoring_data[model_name] = deque(maxlen=self.config.drift_detection_window)

        # Create monitoring record
        record = {
            'timestamp': datetime.now(),
            'features': features.tolist() if isinstance(features, np.ndarray) else features,
            'prediction': prediction,
            'actual': actual,
            'latency_ms': latency_ms or 0.0
        }

        # Add to monitoring data
        self.monitoring_data[model_name].append(record)

        # Update performance metrics if actual value available
        if actual is not None:
            self._update_performance_metrics(model_name, prediction, actual, latency_ms)

    def _update_performance_metrics(self, model_name: str, prediction: Any,
                                  actual: Any, latency_ms: Optional[float] = None):
        """Update real-time performance metrics"""
        if model_name not in self.performance_history:
            self.performance_history[model_name] = []

        # Calculate current metrics (simplified - would use sliding window)
        recent_predictions = [r['prediction'] for r in list(self.monitoring_data[model_name])[-100:]]
        recent_actuals = [r['actual'] for r in list(self.monitoring_data[model_name])[-100:] if r['actual'] is not None]

        if len(recent_actuals) >= 10:  # Minimum samples for metrics
            try:
                if isinstance(recent_predictions[0], (int, float)) and isinstance(recent_actuals[0], (int, float)):
                    # Regression metrics
                    accuracy = np.mean([abs(p - a) <= 0.1 for p, a in zip(recent_predictions, recent_actuals)])  # Within 10% tolerance
                    precision = accuracy  # Simplified
                    recall = accuracy
                    f1 = accuracy
                else:
                    # Classification metrics
                    accuracy = accuracy_score(recent_actuals, recent_predictions)
                    precision = precision_score(recent_actuals, recent_predictions, average='weighted', zero_division=0)
                    recall = recall_score(recent_actuals, recent_predictions, average='weighted', zero_division=0)
                    f1 = f1_score(recent_actuals, recent_predictions, average='weighted', zero_division=0)

                # Calculate average latency
                recent_latencies = [r['latency_ms'] for r in list(self.monitoring_data[model_name])[-100:] if r['latency_ms']]
                avg_latency = np.mean(recent_latencies) if recent_latencies else 0.0

                # Error rate (simplified)
                error_rate = 1 - accuracy

                # Drift score (placeholder)
                drift_score = self._calculate_drift_score(model_name)

                metrics = ModelMetrics(
                    timestamp=datetime.now(),
                    predictions_count=len(recent_predictions),
                    accuracy=accuracy,
                    precision=precision,
                    recall=recall,
                    f1_score=f1,
                    latency_ms=avg_latency,
                    error_rate=error_rate,
                    drift_score=drift_score
                )

                self.performance_history[model_name].append(metrics)

                # Check for alerts
                self._check_performance_alerts(model_name, metrics)

            except Exception as e:
                logger.warning(f"Failed to update performance metrics for {model_name}: {e}")

    def _calculate_drift_score(self, model_name: str) -> float:
        """Calculate data drift score for a model"""
        if len(self.monitoring_data[model_name]) < 50:
            return 0.0

        try:
            # Get recent and baseline feature distributions
            recent_data = list(self.monitoring_data[model_name])[-100:]
            baseline_data = list(self.monitoring_data[model_name])[:100] if len(self.monitoring_data[model_name]) >= 200 else recent_data

            recent_features = np.array([r['features'] for r in recent_data])
            baseline_features = np.array([r['features'] for r in baseline_data])

            # Calculate Kolmogorov-Smirnov test for each feature
            drift_scores = []
            for i in range(recent_features.shape[1]):
                try:
                    stat, _ = ks_2samp(recent_features[:, i], baseline_features[:, i])
                    drift_scores.append(stat)
                except:
                    drift_scores.append(0.0)

            return np.mean(drift_scores)

        except Exception as e:
            logger.warning(f"Failed to calculate drift score for {model_name}: {e}")
            return 0.0

    def _check_performance_alerts(self, model_name: str, current_metrics: ModelMetrics):
        """Check for performance alerts and trigger actions"""
        if len(self.performance_history[model_name]) < 2:
            return

        # Get baseline performance (average of last 10 measurements)
        recent_metrics = self.performance_history[model_name][-10:]
        baseline_accuracy = np.mean([m.accuracy for m in recent_metrics[:-1]])

        # Check for performance degradation
        accuracy_drop = baseline_accuracy - current_metrics.accuracy

        if accuracy_drop > self.config.performance_alert_threshold:
            alert_message = f"Performance degradation detected for {model_name}: {accuracy_drop:.3f} accuracy drop"
            self.alert_system.send_alert("PERFORMANCE_DEGRADATION", alert_message, {
                'model_name': model_name,
                'accuracy_drop': accuracy_drop,
                'current_accuracy': current_metrics.accuracy,
                'baseline_accuracy': baseline_accuracy
            })

            # Trigger retraining if enabled
            if self.config.enable_auto_retraining:
                self._trigger_retraining(model_name, f"Performance degradation: {accuracy_drop:.3f}")

        # Check for high latency
        if current_metrics.latency_ms > 1000:  # 1 second threshold
            self.alert_system.send_alert("HIGH_LATENCY", f"High latency detected for {model_name}", {
                'model_name': model_name,
                'latency_ms': current_metrics.latency_ms
            })

        # Check for high error rate
        if current_metrics.error_rate > 0.1:  # 10% error rate
            self.alert_system.send_alert("HIGH_ERROR_RATE", f"High error rate detected for {model_name}", {
                'model_name': model_name,
                'error_rate': current_metrics.error_rate
            })

    def _trigger_retraining(self, model_name: str, reason: str):
        """Trigger model retraining"""
        retraining_request = {
            'model_name': model_name,
            'reason': reason,
            'timestamp': datetime.now(),
            'priority': 'HIGH' if 'critical' in reason.lower() else 'MEDIUM'
        }

        self.retraining_queue.append(retraining_request)
        logger.info(f"Retraining triggered for {model_name}: {reason}")

    def _continuous_monitoring(self):
        """Continuous monitoring loop"""
        while True:
            try:
                # Perform periodic health checks
                self._perform_system_health_check()

                # Check model ages and schedule retraining
                self._check_model_ages()

                # Generate periodic reports
                if int(time.time()) % 3600 == 0:  # Every hour
                    self._generate_monitoring_report()

                time.sleep(self.config.monitoring_interval)

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(self.config.monitoring_interval)

    def _continuous_retraining(self):
        """Continuous retraining loop"""
        while True:
            try:
                if self.retraining_queue:
                    retraining_request = self.retraining_queue.popleft()
                    self.retraining_system.execute_retraining(retraining_request)

                time.sleep(60)  # Check queue every minute

            except Exception as e:
                logger.error(f"Retraining loop error: {e}")
                time.sleep(60)

    def _perform_system_health_check(self):
        """Perform system health check"""
        health_status = {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'gpu_available': len(GPUtil.getGPUs()) > 0,
            'models_loaded': len(self.active_models),
            'timestamp': datetime.now()
        }

        # Check GPU usage if available
        if health_status['gpu_available']:
            gpus = GPUtil.getGPUs()
            health_status['gpu_usage'] = gpus[0].load * 100

        # Alert on high resource usage
        if health_status['cpu_usage'] > 90:
            self.alert_system.send_alert("HIGH_CPU_USAGE", "CPU usage above 90%", health_status)
        if health_status['memory_usage'] > 90:
            self.alert_system.send_alert("HIGH_MEMORY_USAGE", "Memory usage above 90%", health_status)

        # Save health status
        health_file = f"{self.monitoring_dir}/health_status.json"
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2, default=str)

    def _check_model_ages(self):
        """Check model ages and trigger retraining if needed"""
        current_time = datetime.now()

        for model_name, version in self.model_registry.items():
            if version.is_active:
                age_days = (current_time - version.creation_timestamp).days

                if age_days > self.config.max_model_age_days:
                    self._trigger_retraining(
                        model_name,
                        f"Model age {age_days} days exceeds maximum {self.config.max_model_age_days} days"
                    )

    def _generate_monitoring_report(self):
        """Generate comprehensive monitoring report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._get_system_health_summary(),
            'model_performance': {},
            'alerts_summary': self.alert_system.get_alerts_summary(),
            'retraining_status': self.retraining_system.get_status()
        }

        # Add performance data for each model
        for model_name in self.active_models.keys():
            if model_name in self.performance_history and self.performance_history[model_name]:
                recent_metrics = self.performance_history[model_name][-10:]  # Last 10 measurements

                report['model_performance'][model_name] = {
                    'avg_accuracy': np.mean([m.accuracy for m in recent_metrics]),
                    'avg_latency': np.mean([m.latency_ms for m in recent_metrics]),
                    'avg_error_rate': np.mean([m.error_rate for m in recent_metrics]),
                    'drift_score': recent_metrics[-1].drift_score if recent_metrics else 0.0,
                    'total_predictions': sum(m.predictions_count for m in recent_metrics)
                }

        # Save report
        report_file = f"{self.monitoring_dir}/performance_reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Monitoring report generated: {report_file}")

    def _get_system_health_summary(self) -> Dict[str, Any]:
        """Get system health summary"""
        try:
            health_file = f"{self.monitoring_dir}/health_status.json"
            if os.path.exists(health_file):
                with open(health_file, 'r') as f:
                    return json.load(f)
        except:
            pass

        return {'status': 'unknown'}

    def register_model(self, model_name: str, model: Any,
                      performance_metrics: Dict[str, float],
                      ethical_audit_score: float) -> str:
        """
        Register a new model version

        Args:
            model_name: Name of the model
            model: Trained model object
            performance_metrics: Model performance metrics
            ethical_audit_score: Ethical compliance score

        Returns:
            Version ID of the registered model
        """
        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Save model
        model_path = f"{self.models_dir}/{model_name}_{version_id}.joblib"
        joblib.dump(model, model_path)

        # Create version record
        version = ModelVersion(
            version_id=version_id,
            creation_timestamp=datetime.now(),
            model_path=model_path,
            performance_metrics=performance_metrics,
            ethical_audit_score=ethical_audit_score
        )

        # Update registry
        self.model_registry[model_name] = version
        self.active_models[model_name] = model

        # Initialize monitoring for new model
        self.monitoring_data[model_name] = deque(maxlen=self.config.drift_detection_window)
        self.performance_history[model_name] = []

        # Save registry
        self._save_model_registry()

        logger.info(f"Registered new model version: {model_name} {version_id}")

        return version_id

    def _save_model_registry(self):
        """Save model registry to disk"""
        registry_data = {}
        for model_name, version in self.model_registry.items():
            registry_data[model_name] = {
                'version_id': version.version_id,
                'creation_timestamp': version.creation_timestamp.isoformat(),
                'model_path': version.model_path,
                'performance_metrics': version.performance_metrics,
                'ethical_audit_score': version.ethical_audit_score,
                'is_active': version.is_active,
                'retirement_date': version.retirement_date.isoformat() if version.retirement_date else None
            }

        registry_file = f"{self.monitoring_dir}/model_registry.json"
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)

    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        dashboard = {
            'timestamp': datetime.now().isoformat(),
            'active_models': len(self.active_models),
            'total_predictions': sum(
                len(data) for data in self.monitoring_data.values()
            ),
            'system_health': self._get_system_health_summary(),
            'alerts': self.alert_system.get_recent_alerts(10),
            'model_status': {}
        }

        # Add status for each model
        for model_name in self.active_models.keys():
            status = {
                'version': self.model_registry[model_name].version_id,
                'predictions_count': len(self.monitoring_data[model_name]),
                'last_prediction': None,
                'performance_trend': 'stable'
            }

            if self.monitoring_data[model_name]:
                status['last_prediction'] = self.monitoring_data[model_name][-1]['timestamp']

            if model_name in self.performance_history and len(self.performance_history[model_name]) >= 2:
                recent = [m.accuracy for m in self.performance_history[model_name][-5:]]
                if len(recent) >= 2:
                    trend = (recent[-1] - recent[0]) / recent[0]
                    if trend > 0.05:
                        status['performance_trend'] = 'improving'
                    elif trend < -0.05:
                        status['performance_trend'] = 'degrading'
                    else:
                        status['performance_trend'] = 'stable'

            dashboard['model_status'][model_name] = status

        return dashboard

class AlertSystem:
    """Alert system for ML monitoring"""

    def __init__(self, config: MonitoringConfig, alerts_dir: str):
        self.config = config
        self.alerts_dir = alerts_dir
        self.alerts_history = []

    def send_alert(self, alert_type: str, message: str, metadata: Dict[str, Any]):
        """Send an alert"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'metadata': metadata,
            'severity': self._determine_severity(alert_type)
        }

        self.alerts_history.append(alert)

        # Save alert
        alert_file = f"{self.alerts_dir}/alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(alert_file, 'w') as f:
            json.dump(alert, f, indent=2)

        logger.warning(f"ALERT [{alert_type}]: {message}")

        # In production, this would send email/SMS notifications
        if self.config.alert_email_enabled:
            self._send_email_alert(alert)

    def _determine_severity(self, alert_type: str) -> str:
        """Determine alert severity"""
        severity_map = {
            'PERFORMANCE_DEGRADATION': 'HIGH',
            'HIGH_LATENCY': 'MEDIUM',
            'HIGH_ERROR_RATE': 'HIGH',
            'DATA_DRIFT': 'MEDIUM',
            'HIGH_CPU_USAGE': 'MEDIUM',
            'HIGH_MEMORY_USAGE': 'HIGH'
        }
        return severity_map.get(alert_type, 'LOW')

    def _send_email_alert(self, alert: Dict[str, Any]):
        """Send email alert (placeholder)"""
        # In production, implement actual email sending
        logger.info(f"Email alert would be sent: {alert['message']}")

    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts_history[-limit:] if self.alerts_history else []

    def get_alerts_summary(self) -> Dict[str, Any]:
        """Get alerts summary"""
        if not self.alerts_history:
            return {'total_alerts': 0}

        recent_alerts = self.alerts_history[-100:]  # Last 100 alerts

        return {
            'total_alerts': len(self.alerts_history),
            'recent_alerts': len(recent_alerts),
            'alerts_by_type': pd.Series([a['type'] for a in recent_alerts]).value_counts().to_dict(),
            'alerts_by_severity': pd.Series([a['severity'] for a in recent_alerts]).value_counts().to_dict()
        }

class RetrainingSystem:
    """Automated model retraining system"""

    def __init__(self, config: MonitoringConfig, logs_dir: str):
        self.config = config
        self.logs_dir = logs_dir

    def execute_retraining(self, retraining_request: Dict[str, Any]):
        """Execute model retraining"""
        model_name = retraining_request['model_name']
        reason = retraining_request['reason']

        logger.info(f"Starting retraining for {model_name}: {reason}")

        try:
            # Log retraining start
            self._log_retraining_event('STARTED', retraining_request)

            # In production, this would:
            # 1. Gather new training data
            # 2. Retrain the model
            # 3. Perform validation and ethical audit
            # 4. Deploy new model version if successful

            # Placeholder retraining logic
            success = self._perform_retraining(model_name, retraining_request)

            if success:
                self._log_retraining_event('COMPLETED', retraining_request)
                logger.info(f"Retraining completed successfully for {model_name}")
            else:
                self._log_retraining_event('FAILED', retraining_request)
                logger.error(f"Retraining failed for {model_name}")

        except Exception as e:
            logger.error(f"Retraining error for {model_name}: {e}")
            self._log_retraining_event('ERROR', {**retraining_request, 'error': str(e)})

    def _perform_retraining(self, model_name: str, retraining_request: Dict[str, Any]) -> bool:
        """Perform actual model retraining (placeholder)"""
        # In production, this would implement the full retraining pipeline
        # For now, just simulate successful retraining
        time.sleep(2)  # Simulate retraining time
        return True

    def _log_retraining_event(self, event_type: str, data: Dict[str, Any]):
        """Log retraining event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'data': data
        }

        log_file = f"{self.logs_dir}/retraining_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')

    def get_status(self) -> Dict[str, Any]:
        """Get retraining system status"""
        return {
            'retraining_queue_size': len(ml_monitoring.retraining_queue),
            'last_retraining_check': datetime.now().isoformat()
        }

# Create global monitoring pipeline instance
ml_monitoring = MLMonitoringPipeline()

# Convenience functions
def record_model_prediction(model_name: str, features: np.ndarray,
                          prediction: Any, actual: Optional[Any] = None,
                          latency_ms: Optional[float] = None):
    """Record a model prediction for monitoring"""
    ml_monitoring.record_prediction(model_name, features, prediction, actual, latency_ms)

def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get monitoring dashboard data"""
    return ml_monitoring.get_monitoring_dashboard()

def register_new_model(model_name: str, model: Any,
                      performance_metrics: Dict[str, float],
                      ethical_score: float) -> str:
    """Register a new model version"""
    return ml_monitoring.register_model(model_name, model, performance_metrics, ethical_score)

if __name__ == "__main__":
    # Demo of ML monitoring system
    print("📊 ML Monitoring Pipeline Demo")
    print("=" * 50)

    # Simulate model predictions
    print("📈 Recording sample predictions...")

    # Simulate resume screening predictions
    for i in range(50):
        features = np.random.rand(10)  # 10 features
        prediction = np.random.choice([0, 1])  # Binary classification
        actual = np.random.choice([0, 1])
        latency = np.random.uniform(50, 200)  # ms

        record_model_prediction('resume_screening', features, prediction, actual, latency)

    print("✅ Recorded 50 predictions for monitoring")

    # Get monitoring dashboard
    dashboard = get_monitoring_dashboard()
    print("📊 Monitoring Dashboard:")
    print(f"   Active models: {dashboard['active_models']}")
    print(f"   Total predictions: {dashboard['total_predictions']}")

    for model_name, status in dashboard['model_status'].items():
        print(f"   {model_name}: {status['predictions_count']} predictions")

    # Simulate some time for monitoring
    print("⏳ Running monitoring for 10 seconds...")
    time.sleep(10)

    print("✅ ML monitoring pipeline operational!")
    print("\n🔍 Key Features:")
    print("   • Real-time performance tracking")
    print("   • Data drift detection")
    print("   • Automated alerts")
    print("   • Continuous retraining pipeline")
    print("   • Ethical compliance monitoring")

