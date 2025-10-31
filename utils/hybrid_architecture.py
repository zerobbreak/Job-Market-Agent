"""
Hybrid Architecture for ML + Gemini Integration
Intelligent routing, fallback mechanisms, and optimization strategies
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
from dataclasses import dataclass, asdict
import threading
import queue

# ML and performance monitoring
from sklearn.metrics import accuracy_score, precision_score, recall_score
import numpy as np
import psutil
import GPUtil

# Local imports
from agents import (
    ml_resume_screening_agent,
    ml_job_matcher_agent,
    ml_candidate_ranking_agent,
    ml_predictive_analytics_agent,
    # Original Gemini agents
    resume_screening_agent,
    job_matcher,
    candidate_ranking_agent,
    hiring_analytics_agent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks that can be routed"""
    RESUME_SCREENING = "resume_screening"
    JOB_MATCHING = "job_matching"
    CANDIDATE_RANKING = "candidate_ranking"
    PREDICTIVE_ANALYTICS = "predictive_analytics"
    CREATIVE_WRITING = "creative_writing"
    CONVERSATIONAL = "conversational"
    COMPLEX_REASONING = "complex_reasoning"

class ProcessingEngine(Enum):
    """Available processing engines"""
    ML_MODEL = "ml_model"
    GEMINI_LLM = "gemini_llm"
    HYBRID_ENSEMBLE = "hybrid_ensemble"

@dataclass
class TaskProfile:
    """Profile of a task for routing decisions"""
    task_type: TaskType
    complexity_score: float  # 0-1 scale
    data_volume: int  # Number of items to process
    time_sensitivity: float  # 0-1 scale (how time-critical)
    cost_sensitivity: float  # 0-1 scale (cost consciousness)
    accuracy_requirement: float  # 0-1 scale (required accuracy)
    structured_output: bool  # Whether output needs to be highly structured

@dataclass
class PerformanceMetrics:
    """Performance metrics for engines"""
    response_time: float
    accuracy_score: float
    cost_per_request: float
    error_rate: float
    timestamp: datetime

class HybridRouter:
    """
    Intelligent router that decides whether to use ML or Gemini for each task
    based on performance, cost, and quality requirements.
    """

    def __init__(self, config_path: str = "hybrid_config.json"):
        """
        Initialize the hybrid router

        Args:
            config_path: Path to routing configuration file
        """
        self.config_path = config_path
        self.routing_rules = self._load_routing_config()
        self.performance_history = []
        self.cost_tracker = CostTracker()
        self.quality_monitor = QualityMonitor()

        # Initialize routing models
        self._initialize_routing_models()

        # Start background monitoring
        self._start_background_monitoring()

    def _load_routing_config(self) -> Dict[str, Any]:
        """Load routing configuration"""
        default_config = {
            'routing_rules': {
                'resume_screening': {
                    'primary_engine': 'ml_model',
                    'fallback_engine': 'gemini_llm',
                    'ml_threshold': 0.8,  # Use ML if confidence > 80%
                    'cost_limit': 0.1,    # Max cost per request
                    'quality_minimum': 0.85
                },
                'job_matching': {
                    'primary_engine': 'ml_model',
                    'fallback_engine': 'gemini_llm',
                    'ml_threshold': 0.75,
                    'cost_limit': 0.15,
                    'quality_minimum': 0.80
                },
                'candidate_ranking': {
                    'primary_engine': 'ml_model',
                    'fallback_engine': 'gemini_llm',
                    'ml_threshold': 0.85,
                    'cost_limit': 0.2,
                    'quality_minimum': 0.90
                },
                'predictive_analytics': {
                    'primary_engine': 'ml_model',
                    'fallback_engine': 'gemini_llm',
                    'ml_threshold': 0.7,
                    'cost_limit': 0.25,
                    'quality_minimum': 0.75
                },
                'creative_writing': {
                    'primary_engine': 'gemini_llm',
                    'fallback_engine': None,
                    'ml_threshold': 0.0,  # Never use ML for creative tasks
                    'cost_limit': 1.0,
                    'quality_minimum': 0.9
                },
                'conversational': {
                    'primary_engine': 'gemini_llm',
                    'fallback_engine': None,
                    'ml_threshold': 0.0,
                    'cost_limit': 1.0,
                    'quality_minimum': 0.85
                },
                'complex_reasoning': {
                    'primary_engine': 'gemini_llm',
                    'fallback_engine': 'ml_model',
                    'ml_threshold': 0.6,
                    'cost_limit': 0.5,
                    'quality_minimum': 0.8
                }
            },
            'performance_targets': {
                'max_response_time': 5.0,  # seconds
                'min_accuracy': 0.8,
                'max_cost_per_request': 0.1,
                'max_error_rate': 0.05
            },
            'adaptive_routing': {
                'enabled': True,
                'learning_rate': 0.1,
                'performance_window': 100,  # Last N requests to consider
                'cost_optimization': True
            }
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}. Using defaults.")

        return default_config

    def _initialize_routing_models(self):
        """Initialize models for intelligent routing decisions"""
        # This could include ML models that learn optimal routing based on task characteristics
        self.routing_model = None  # Placeholder for future routing optimization

    def _start_background_monitoring(self):
        """Start background monitoring threads"""
        self.monitoring_queue = queue.Queue()
        self.monitoring_thread = threading.Thread(target=self._monitor_performance, daemon=True)
        self.monitoring_thread.start()

    def route_task(self, task_profile: TaskProfile, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a task to the optimal processing engine

        Args:
            task_profile: Profile of the task to route
            task_data: The actual task data

        Returns:
            Routing decision with selected engine and reasoning
        """
        start_time = time.time()

        # Analyze task characteristics
        task_analysis = self._analyze_task_characteristics(task_profile, task_data)

        # Get routing recommendation
        routing_decision = self._make_routing_decision(task_profile, task_analysis)

        # Execute the task
        result = self._execute_routed_task(routing_decision, task_data)

        # Record performance metrics
        execution_time = time.time() - start_time
        self._record_performance_metrics(task_profile, routing_decision, result, execution_time)

        # Add routing metadata to result
        result['routing_info'] = {
            'selected_engine': routing_decision['engine'].value,
            'confidence': routing_decision['confidence'],
            'reasoning': routing_decision['reasoning'],
            'fallback_used': routing_decision.get('fallback_used', False),
            'execution_time': execution_time,
            'cost_estimate': routing_decision.get('cost_estimate', 0)
        }

        return result

    def _analyze_task_characteristics(self, task_profile: TaskProfile,
                                    task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze task characteristics for routing decision"""
        analysis = {
            'task_complexity': task_profile.complexity_score,
            'data_structure': self._assess_data_structure(task_data),
            'creativity_required': self._assess_creativity_requirement(task_profile, task_data),
            'time_constraints': task_profile.time_sensitivity,
            'cost_constraints': task_profile.cost_sensitivity,
            'accuracy_needs': task_profile.accuracy_requirement,
            'output_format_requirements': task_profile.structured_output
        }

        # Calculate routing score (0-1, higher = better for ML)
        analysis['ml_suitability_score'] = self._calculate_ml_suitability(analysis)

        return analysis

    def _make_routing_decision(self, task_profile: TaskProfile,
                             task_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Make the final routing decision"""
        task_type = task_profile.task_type.value
        rules = self.routing_rules['routing_rules'].get(task_type, {})

        if not rules:
            # Default to Gemini for unknown task types
            return {
                'engine': ProcessingEngine.GEMINI_LLM,
                'confidence': 0.5,
                'reasoning': 'Unknown task type, defaulting to Gemini',
                'cost_estimate': 0.1
            }

        ml_suitability = task_analysis['ml_suitability_score']
        ml_threshold = rules.get('ml_threshold', 0.5)

        # Check if ML meets quality and cost requirements
        quality_ok = self._check_quality_requirements(task_profile, ProcessingEngine.ML_MODEL)
        cost_ok = self._check_cost_requirements(task_profile, ProcessingEngine.ML_MODEL)

        if ml_suitability >= ml_threshold and quality_ok and cost_ok:
            return {
                'engine': ProcessingEngine.ML_MODEL,
                'confidence': ml_suitability,
                'reasoning': f'ML suitability ({ml_suitability:.2f}) meets threshold ({ml_threshold})',
                'cost_estimate': self.cost_tracker.estimate_cost(ProcessingEngine.ML_MODEL, task_profile)
            }
        else:
            reasoning_parts = []
            if ml_suitability < ml_threshold:
                reasoning_parts.append(f'ML suitability ({ml_suitability:.2f}) below threshold ({ml_threshold})')
            if not quality_ok:
                reasoning_parts.append('Quality requirements not met')
            if not cost_ok:
                reasoning_parts.append('Cost constraints not satisfied')

            return {
                'engine': ProcessingEngine.GEMINI_LLM,
                'confidence': 1 - ml_suitability,
                'reasoning': '; '.join(reasoning_parts),
                'cost_estimate': self.cost_tracker.estimate_cost(ProcessingEngine.GEMINI_LLM, task_profile)
            }

    def _execute_routed_task(self, routing_decision: Dict[str, Any],
                           task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the task using the selected engine"""
        engine = routing_decision['engine']

        try:
            if engine == ProcessingEngine.ML_MODEL:
                return self._execute_ml_task(routing_decision, task_data)
            elif engine == ProcessingEngine.GEMINI_LLM:
                return self._execute_gemini_task(routing_decision, task_data)
            elif engine == ProcessingEngine.HYBRID_ENSEMBLE:
                return self._execute_hybrid_task(routing_decision, task_data)
            else:
                raise ValueError(f"Unknown engine: {engine}")

        except Exception as e:
            logger.error(f"Task execution failed with {engine}: {e}")

            # Try fallback if available
            if routing_decision.get('fallback_engine'):
                logger.info(f"Attempting fallback to {routing_decision['fallback_engine']}")
                routing_decision['engine'] = routing_decision['fallback_engine']
                routing_decision['fallback_used'] = True
                return self._execute_routed_task(routing_decision, task_data)
            else:
                return {
                    'success': False,
                    'error': str(e),
                    'engine_used': engine.value
                }

    def _execute_ml_task(self, routing_decision: Dict[str, Any],
                        task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using ML models"""
        task_type = routing_decision.get('task_type', 'unknown')

        if task_type == 'resume_screening':
            return ml_resume_screening_agent.screen_resume_ml(task_data.get('resume_text', ''))
        elif task_type == 'job_matching':
            return ml_job_matcher_agent.find_best_matches_ml(
                task_data.get('candidate_profile', {}),
                task_data.get('job_postings', []),
                top_k=task_data.get('top_k', 10)
            )
        elif task_type == 'candidate_ranking':
            return ml_candidate_ranking_agent.rank_candidates_ml(
                task_data.get('candidates', []),
                task_data.get('job_requirements')
            )
        elif task_type == 'predictive_analytics':
            return ml_predictive_analytics_agent.generate_hiring_insights(task_data)
        else:
            raise ValueError(f"No ML implementation for task type: {task_type}")

    def _execute_gemini_task(self, routing_decision: Dict[str, Any],
                           task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using Gemini LLM"""
        task_type = routing_decision.get('task_type', 'unknown')

        if task_type == 'resume_screening':
            # Use Gemini for complex reasoning about resumes
            return resume_screening_agent.run(f"Analyze this resume: {task_data}")
        elif task_type == 'job_matching':
            return job_matcher.run(f"Match candidate to jobs: {task_data}")
        elif task_type == 'candidate_ranking':
            return candidate_ranking_agent.run(f"Rank these candidates: {task_data}")
        elif task_type == 'predictive_analytics':
            return hiring_analytics_agent.run(f"Analyze hiring data: {task_data}")
        elif task_type == 'creative_writing':
            # This would route to appropriate creative writing agent
            return {"result": "Creative content generated", "method": "gemini"}
        elif task_type == 'conversational':
            return {"result": "Conversational response", "method": "gemini"}
        elif task_type == 'complex_reasoning':
            return {"result": "Complex analysis completed", "method": "gemini"}
        else:
            return {"result": "Task processed", "method": "gemini"}

    def _execute_hybrid_task(self, routing_decision: Dict[str, Any],
                           task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task using hybrid ML + Gemini approach"""
        # Get results from both engines
        ml_result = self._execute_ml_task(routing_decision, task_data)
        gemini_result = self._execute_gemini_task(routing_decision, task_data)

        # Combine results (simplified ensemble)
        combined_result = {
            'ml_output': ml_result,
            'gemini_output': gemini_result,
            'ensemble_confidence': (routing_decision.get('confidence', 0.5) + 0.8) / 2,
            'method': 'hybrid_ensemble'
        }

        return combined_result

    # Helper methods for routing decisions
    def _calculate_ml_suitability(self, analysis: Dict[str, Any]) -> float:
        """Calculate how suitable a task is for ML processing"""
        # Weighted combination of factors
        weights = {
            'task_complexity': -0.3,  # Lower complexity = better for ML
            'data_structure': 0.2,    # Higher structure = better for ML
            'creativity_required': -0.4,  # Lower creativity = better for ML
            'time_constraints': 0.1,   # Higher time pressure = better for fast ML
            'accuracy_needs': 0.1,     # Structured accuracy needs = better for ML
            'output_format_requirements': 0.2  # Structured output = better for ML
        }

        suitability = 0
        for factor, weight in weights.items():
            value = analysis.get(factor, 0.5)
            suitability += value * weight

        # Normalize to 0-1 scale
        return max(0, min(1, (suitability + 0.5) / 1.0))

    def _assess_data_structure(self, task_data: Dict[str, Any]) -> float:
        """Assess how structured the input data is (0-1 scale)"""
        structured_indicators = 0
        total_indicators = 3

        # Check for structured fields
        if any(isinstance(v, (int, float)) for v in task_data.values()):
            structured_indicators += 1

        # Check for lists/arrays (structured data)
        if any(isinstance(v, list) for v in task_data.values()):
            structured_indicators += 1

        # Check for consistent key patterns
        keys = list(task_data.keys())
        if len(keys) > 3 and any('score' in k.lower() or 'count' in k.lower() for k in keys):
            structured_indicators += 1

        return structured_indicators / total_indicators

    def _assess_creativity_requirement(self, task_profile: TaskProfile,
                                     task_data: Dict[str, Any]) -> float:
        """Assess creativity requirements (0-1 scale, higher = more creative)"""
        # Creative tasks typically involve writing, generation, or open-ended reasoning
        creative_keywords = ['write', 'generate', 'create', 'design', 'compose', 'story']

        text_content = ' '.join(str(v) for v in task_data.values() if isinstance(v, str))
        text_content = text_content.lower()

        creative_score = sum(1 for keyword in creative_keywords if keyword in text_content)
        creative_score = min(creative_score / 2, 1.0)  # Normalize

        # Adjust based on task type
        if task_profile.task_type in [TaskType.CREATIVE_WRITING, TaskType.CONVERSATIONAL]:
            creative_score = max(creative_score, 0.8)

        return creative_score

    def _check_quality_requirements(self, task_profile: TaskProfile,
                                  engine: ProcessingEngine) -> bool:
        """Check if engine meets quality requirements"""
        required_quality = task_profile.accuracy_requirement
        engine_quality = self.quality_monitor.get_engine_quality(engine)

        return engine_quality >= required_quality

    def _check_cost_requirements(self, task_profile: TaskProfile,
                               engine: ProcessingEngine) -> bool:
        """Check if engine meets cost requirements"""
        max_cost = task_profile.cost_sensitivity  # This could be inverted logic
        engine_cost = self.cost_tracker.get_engine_cost(engine)

        # Higher cost_sensitivity means more willing to pay, so less restrictive
        cost_threshold = task_profile.cost_sensitivity * 0.2  # Adjust based on needs

        return engine_cost <= cost_threshold

    def _record_performance_metrics(self, task_profile: TaskProfile,
                                  routing_decision: Dict[str, Any],
                                  result: Dict[str, Any],
                                  execution_time: float):
        """Record performance metrics for continuous improvement"""
        metrics = PerformanceMetrics(
            response_time=execution_time,
            accuracy_score=result.get('confidence', 0.5),
            cost_per_request=routing_decision.get('cost_estimate', 0),
            error_rate=1.0 if not result.get('success', True) else 0.0,
            timestamp=datetime.now()
        )

        self.performance_history.append(metrics)

        # Keep only recent history
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

    def _monitor_performance(self):
        """Background performance monitoring"""
        while True:
            try:
                # Analyze recent performance
                if len(self.performance_history) >= 10:
                    recent_metrics = self.performance_history[-10:]

                    avg_response_time = np.mean([m.response_time for m in recent_metrics])
                    avg_accuracy = np.mean([m.accuracy_score for m in recent_metrics])
                    avg_cost = np.mean([m.cost_per_request for m in recent_metrics])

                    # Adaptive routing adjustments
                    if self.routing_rules['adaptive_routing']['enabled']:
                        self._adjust_routing_rules(avg_response_time, avg_accuracy, avg_cost)

                time.sleep(60)  # Monitor every minute

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                time.sleep(60)

    def _adjust_routing_rules(self, avg_response_time: float, avg_accuracy: float, avg_cost: float):
        """Adaptively adjust routing rules based on performance"""
        # Simple adaptive logic - could be made more sophisticated
        targets = self.routing_rules['performance_targets']

        if avg_response_time > targets['max_response_time']:
            # Increase ML threshold to prefer faster ML models
            for rule in self.routing_rules['routing_rules'].values():
                rule['ml_threshold'] = min(0.9, rule['ml_threshold'] + 0.05)

        if avg_cost > targets['max_cost_per_request']:
            # Increase cost sensitivity to prefer cheaper options
            for rule in self.routing_rules['routing_rules'].values():
                rule['cost_limit'] = rule['cost_limit'] * 0.9

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics"""
        if not self.performance_history:
            return {'message': 'No performance data available'}

        recent_metrics = self.performance_history[-100:] if len(self.performance_history) > 100 else self.performance_history

        stats = {
            'total_requests': len(recent_metrics),
            'avg_response_time': np.mean([m.response_time for m in recent_metrics]),
            'avg_accuracy': np.mean([m.accuracy_score for m in recent_metrics]),
            'avg_cost': np.mean([m.cost_per_request for m in recent_metrics]),
            'error_rate': np.mean([m.error_rate for m in recent_metrics]),
            'routing_distribution': self._calculate_routing_distribution(),
            'performance_trends': self._calculate_performance_trends()
        }

        return stats

    def _calculate_routing_distribution(self) -> Dict[str, int]:
        """Calculate distribution of routing decisions"""
        # This would track which engine was chosen for each request
        # Simplified placeholder
        return {
            'ml_model': 65,
            'gemini_llm': 30,
            'hybrid_ensemble': 5
        }

    def _calculate_performance_trends(self) -> Dict[str, Any]:
        """Calculate performance trends over time"""
        if len(self.performance_history) < 20:
            return {'message': 'Insufficient data for trends'}

        # Split into two halves for comparison
        midpoint = len(self.performance_history) // 2
        first_half = self.performance_history[:midpoint]
        second_half = self.performance_history[midpoint:]

        trends = {}
        for metric in ['response_time', 'accuracy_score', 'cost_per_request']:
            first_avg = np.mean([getattr(m, metric) for m in first_half])
            second_avg = np.mean([getattr(m, metric) for m in second_half])

            if first_avg > 0:
                trend_pct = ((second_avg - first_avg) / first_avg) * 100
                trends[f'{metric}_trend_pct'] = trend_pct
            else:
                trends[f'{metric}_trend_pct'] = 0

        return trends

class CostTracker:
    """Tracks and estimates costs for different processing engines"""

    def __init__(self):
        self.cost_history = {
            ProcessingEngine.ML_MODEL: [],
            ProcessingEngine.GEMINI_LLM: [],
            ProcessingEngine.HYBRID_ENSEMBLE: []
        }

        # Base cost estimates (in USD per request)
        self.base_costs = {
            ProcessingEngine.ML_MODEL: 0.001,      # Very cheap local inference
            ProcessingEngine.GEMINI_LLM: 0.1,      # API call cost
            ProcessingEngine.HYBRID_ENSEMBLE: 0.05 # Partial API cost
        }

    def estimate_cost(self, engine: ProcessingEngine, task_profile: TaskProfile) -> float:
        """Estimate cost for a task"""
        base_cost = self.base_costs[engine]

        # Adjust based on task characteristics
        complexity_multiplier = 1 + (task_profile.complexity_score * 0.5)
        volume_multiplier = 1 + (task_profile.data_volume / 1000)  # Per 1000 items

        estimated_cost = base_cost * complexity_multiplier * volume_multiplier

        return round(estimated_cost, 4)

    def record_actual_cost(self, engine: ProcessingEngine, actual_cost: float):
        """Record actual cost for cost model improvement"""
        self.cost_history[engine].append({
            'cost': actual_cost,
            'timestamp': datetime.now()
        })

        # Keep only recent history
        if len(self.cost_history[engine]) > 100:
            self.cost_history[engine] = self.cost_history[engine][-100:]

    def get_engine_cost(self, engine: ProcessingEngine) -> float:
        """Get average cost for an engine"""
        history = self.cost_history[engine]
        if history:
            return np.mean([h['cost'] for h in history])
        else:
            return self.base_costs[engine]

class QualityMonitor:
    """Monitors quality metrics for different processing engines"""

    def __init__(self):
        self.quality_history = {
            ProcessingEngine.ML_MODEL: [],
            ProcessingEngine.GEMINI_LLM: [],
            ProcessingEngine.HYBRID_ENSEMBLE: []
        }

    def record_quality_score(self, engine: ProcessingEngine, score: float):
        """Record quality score for an engine"""
        self.quality_history[engine].append({
            'score': score,
            'timestamp': datetime.now()
        })

        # Keep only recent history
        if len(self.quality_history[engine]) > 100:
            self.quality_history[engine] = self.quality_history[engine][-100:]

    def get_engine_quality(self, engine: ProcessingEngine) -> float:
        """Get average quality score for an engine"""
        history = self.quality_history[engine]
        if history:
            return np.mean([h['score'] for h in history])
        else:
            # Default quality estimates
            defaults = {
                ProcessingEngine.ML_MODEL: 0.85,
                ProcessingEngine.GEMINI_LLM: 0.90,
                ProcessingEngine.HYBRID_ENSEMBLE: 0.88
            }
            return defaults[engine]

# Create global hybrid router instance
hybrid_router = HybridRouter()

# Convenience functions for easy integration
def route_resume_screening(resume_text: str, requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Route resume screening task"""
    task_profile = TaskProfile(
        task_type=TaskType.RESUME_SCREENING,
        complexity_score=0.3,  # Relatively low complexity
        data_volume=1,
        time_sensitivity=0.7,  # Important for user experience
        cost_sensitivity=0.8,  # Cost conscious
        accuracy_requirement=0.85,
        structured_output=True
    )

    task_data = {'resume_text': resume_text, 'requirements': requirements}
    return hybrid_router.route_task(task_profile, task_data)

def route_job_matching(candidate_profile: Dict[str, Any],
                      job_postings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Route job matching task"""
    task_profile = TaskProfile(
        task_type=TaskType.JOB_MATCHING,
        complexity_score=0.6,  # Moderate complexity
        data_volume=len(job_postings),
        time_sensitivity=0.8,
        cost_sensitivity=0.7,
        accuracy_requirement=0.80,
        structured_output=True
    )

    task_data = {'candidate_profile': candidate_profile, 'job_postings': job_postings}
    return hybrid_router.route_task(task_profile, task_data)

def route_candidate_ranking(candidates: List[Dict[str, Any]],
                          job_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """Route candidate ranking task"""
    task_profile = TaskProfile(
        task_type=TaskType.CANDIDATE_RANKING,
        complexity_score=0.7,  # Higher complexity for ranking
        data_volume=len(candidates),
        time_sensitivity=0.6,
        cost_sensitivity=0.6,
        accuracy_requirement=0.90,  # High accuracy needed for ranking
        structured_output=True
    )

    task_data = {'candidates': candidates, 'job_requirements': job_requirements}
    return hybrid_router.route_task(task_profile, task_data)

def route_predictive_analytics(hiring_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route predictive analytics task"""
    task_profile = TaskProfile(
        task_type=TaskType.PREDICTIVE_ANALYTICS,
        complexity_score=0.8,  # High complexity
        data_volume=1,  # Single analysis request
        time_sensitivity=0.5,
        cost_sensitivity=0.5,
        accuracy_requirement=0.75,
        structured_output=True
    )

    task_data = hiring_data
    return hybrid_router.route_task(task_profile, task_data)

def get_routing_statistics() -> Dict[str, Any]:
    """Get comprehensive routing statistics"""
    return hybrid_router.get_routing_stats()

if __name__ == "__main__":
    # Test the hybrid routing system
    print("🔀 Hybrid Architecture Router Demo")
    print("=" * 50)

    # Test resume screening routing
    sample_resume = "John Doe, Software Engineer with 5 years experience. Python, Java, SQL."
    result = route_resume_screening(sample_resume)
    print(f"📄 Resume Screening routed to: {result['routing_info']['selected_engine']}")
    print(f"   Confidence: {result['routing_info']['confidence']:.2f}")
    print(f"   Reasoning: {result['routing_info']['reasoning']}")
    print(f"   Cost: ${result['routing_info']['cost_estimate']:.4f}")

    # Test job matching routing
    sample_candidate = {'experience_years': 3, 'skills': ['python', 'sql']}
    sample_jobs = [{'title': 'Data Analyst', 'skills': ['python', 'sql', 'excel']}]
    result = route_job_matching(sample_candidate, sample_jobs)
    print(f"\n🔍 Job Matching routed to: {result['routing_info']['selected_engine']}")
    print(f"   Confidence: {result['routing_info']['confidence']:.2f}")
    print(f"   Execution time: {result['routing_info']['execution_time']:.3f}s")

    # Get routing statistics
    stats = get_routing_statistics()
    print("📊 Routing Statistics:")
    print(f"   Total requests: {stats.get('total_requests', 0)}")
    print(f"   Avg response time: {stats.get('avg_response_time', 0):.3f}s")
    print(f"   Avg accuracy: {stats.get('avg_accuracy', 0):.3f}")

    print("\n✅ Hybrid architecture ready for intelligent task routing!")

