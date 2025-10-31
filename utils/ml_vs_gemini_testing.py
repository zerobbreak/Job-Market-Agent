"""
ML vs Gemini Comparative Testing Framework
Comprehensive performance comparison between ML-enhanced and Gemini-only agents
"""

import os
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ThreadPoolExecutor, as_completed

# Local imports
from utils.hybrid_architecture import hybrid_router
from utils.ml_evaluation import ml_evaluation_framework
from utils.ethical_ai_safeguards import ethical_safeguards

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Individual test case definition"""
    test_id: str
    agent_type: str
    task_description: str
    input_data: Dict[str, Any]
    expected_output_type: str
    quality_criteria: Dict[str, Any]

@dataclass
class TestResult:
    """Result of a single test execution"""
    test_id: str
    approach: str  # 'ml', 'gemini', or 'hybrid'
    execution_time: float
    cost_estimate: float
    output_quality_score: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComparativeTestSuite:
    """Complete test suite comparing ML vs Gemini approaches"""
    suite_name: str
    test_cases: List[TestCase] = field(default_factory=list)
    results: List[TestResult] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)

class MLvsGeminiTestingFramework:
    """
    Comprehensive testing framework for comparing ML-enhanced agents
    against Gemini-only versions across performance, cost, and quality metrics.
    """

    def __init__(self, results_dir: str = "testing_results"):
        """
        Initialize the testing framework

        Args:
            results_dir: Directory to store test results and reports
        """
        self.results_dir = results_dir
        self.test_suites = {}

        # Create results directory
        os.makedirs(results_dir, exist_ok=True)
        os.makedirs(f"{results_dir}/reports", exist_ok=True)
        os.makedirs(f"{results_dir}/visualizations", exist_ok=True)
        os.makedirs(f"{results_dir}/detailed_results", exist_ok=True)

        # Initialize test configurations
        self._initialize_test_configurations()

    def _initialize_test_configurations(self):
        """Initialize test configurations for different agent types"""
        self.test_configurations = {
            'resume_screening': {
                'sample_size': 100,
                'quality_metrics': ['qualification_accuracy', 'entity_extraction', 'processing_speed'],
                'cost_weight': 0.4,
                'quality_weight': 0.4,
                'speed_weight': 0.2
            },
            'candidate_ranking': {
                'sample_size': 50,
                'quality_metrics': ['ranking_accuracy', 'fairness_score', 'consistency'],
                'cost_weight': 0.3,
                'quality_weight': 0.5,
                'speed_weight': 0.2
            },
            'job_matching': {
                'sample_size': 80,
                'quality_metrics': ['match_accuracy', 'semantic_similarity', 'relevance_score'],
                'cost_weight': 0.35,
                'quality_weight': 0.45,
                'speed_weight': 0.2
            },
            'predictive_analytics': {
                'sample_size': 30,
                'quality_metrics': ['prediction_accuracy', 'forecast_precision', 'trend_detection'],
                'cost_weight': 0.25,
                'quality_weight': 0.5,
                'speed_weight': 0.25
            }
        }

    def create_comprehensive_test_suite(self, suite_name: str = "ml_vs_gemini_comparison") -> ComparativeTestSuite:
        """
        Create a comprehensive test suite comparing ML vs Gemini approaches

        Args:
            suite_name: Name of the test suite

        Returns:
            Configured test suite
        """
        suite = ComparativeTestSuite(suite_name=suite_name)

        # Generate test cases for each agent type
        for agent_type, config in self.test_configurations.items():
            test_cases = self._generate_test_cases_for_agent(agent_type, config['sample_size'])
            suite.test_cases.extend(test_cases)

        self.test_suites[suite_name] = suite
        logger.info(f"Created test suite '{suite_name}' with {len(suite.test_cases)} test cases")

        return suite

    def _generate_test_cases_for_agent(self, agent_type: str, sample_size: int) -> List[TestCase]:
        """Generate test cases for a specific agent type"""
        test_cases = []

        if agent_type == 'resume_screening':
            # Generate diverse resume test cases
            for i in range(sample_size):
                test_case = TestCase(
                    test_id=f"resume_screening_{i:03d}",
                    agent_type=agent_type,
                    task_description="Screen resume and provide qualification assessment",
                    input_data={
                        'resume_text': self._generate_test_resume(i),
                        'job_requirements': self._generate_job_requirements(i % 5)
                    },
                    expected_output_type='qualification_assessment',
                    quality_criteria={
                        'qualification_consistency': True,
                        'entity_extraction_completeness': 0.8,
                        'processing_time_under_5s': True
                    }
                )
                test_cases.append(test_case)

        elif agent_type == 'candidate_ranking':
            # Generate candidate ranking test cases
            for i in range(sample_size):
                test_case = TestCase(
                    test_id=f"candidate_ranking_{i:03d}",
                    agent_type=agent_type,
                    task_description="Rank candidates based on job fit",
                    input_data={
                        'candidates': self._generate_candidate_pool(5),
                        'job_requirements': self._generate_job_requirements(i % 3)
                    },
                    expected_output_type='ranked_list',
                    quality_criteria={
                        'ranking_consistency': True,
                        'top_candidate_quality': 0.8,
                        'ranking_logic_coherence': True
                    }
                )
                test_cases.append(test_case)

        elif agent_type == 'job_matching':
            # Generate job matching test cases
            for i in range(sample_size):
                test_case = TestCase(
                    test_id=f"job_matching_{i:03d}",
                    agent_type=agent_type,
                    task_description="Find best job matches for candidate",
                    input_data={
                        'candidate_profile': self._generate_candidate_profile(i),
                        'available_jobs': self._generate_job_pool(10)
                    },
                    expected_output_type='job_matches',
                    quality_criteria={
                        'match_relevance': 0.75,
                        'semantic_accuracy': 0.8,
                        'diversity_score': 0.6
                    }
                )
                test_cases.append(test_case)

        elif agent_type == 'predictive_analytics':
            # Generate predictive analytics test cases
            for i in range(sample_size):
                test_case = TestCase(
                    test_id=f"predictive_analytics_{i:03d}",
                    agent_type=agent_type,
                    task_description="Analyze hiring patterns and predict outcomes",
                    input_data={
                        'historical_data': self._generate_historical_hiring_data(),
                        'prediction_targets': ['time_to_hire', 'retention_probability', 'performance_rating']
                    },
                    expected_output_type='analytics_report',
                    quality_criteria={
                        'prediction_accuracy': 0.7,
                        'trend_insights': True,
                        'actionable_recommendations': True
                    }
                )
                test_cases.append(test_case)

        return test_cases

    def execute_test_suite(self, suite: ComparativeTestSuite,
                          approaches: List[str] = ['ml', 'gemini', 'hybrid'],
                          max_workers: int = 4) -> ComparativeTestSuite:
        """
        Execute a complete test suite comparing different approaches

        Args:
            suite: Test suite to execute
            approaches: Approaches to test ('ml', 'gemini', 'hybrid')
            max_workers: Maximum concurrent workers

        Returns:
            Test suite with results populated
        """
        logger.info(f"Executing test suite '{suite.suite_name}' with {len(suite.test_cases)} test cases")

        # Execute tests using thread pool for parallelism
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_test = {}

            # Submit all test combinations
            for test_case in suite.test_cases:
                for approach in approaches:
                    future = executor.submit(self._execute_single_test, test_case, approach)
                    future_to_test[future] = (test_case, approach)

            # Collect results as they complete
            for future in as_completed(future_to_test):
                test_case, approach = future_to_test[future]
                try:
                    result = future.result()
                    suite.results.append(result)
                except Exception as e:
                    logger.error(f"Test execution failed for {test_case.test_id} ({approach}): {e}")
                    # Add failed result
                    failed_result = TestResult(
                        test_id=test_case.test_id,
                        approach=approach,
                        execution_time=0.0,
                        cost_estimate=0.0,
                        output_quality_score=0.0,
                        success=False,
                        error_message=str(e)
                    )
                    suite.results.append(failed_result)

        # Generate summary statistics
        suite.summary_stats = self._generate_test_summary(suite, approaches)

        # Save detailed results
        self._save_test_results(suite)

        logger.info(f"Test suite execution completed. Results: {suite.summary_stats}")

        return suite

    def _execute_single_test(self, test_case: TestCase, approach: str) -> TestResult:
        """Execute a single test case with specified approach"""
        start_time = time.time()

        try:
            # Route task based on approach
            if approach == 'ml':
                # Force ML-only execution
                result = self._execute_ml_only(test_case)
            elif approach == 'gemini':
                # Force Gemini-only execution
                result = self._execute_gemini_only(test_case)
            elif approach == 'hybrid':
                # Use intelligent hybrid routing
                from utils.hybrid_architecture import TaskProfile, TaskType
                task_profile = self._convert_test_case_to_task_profile(test_case)
                result = hybrid_router.route_task(task_profile, test_case.input_data)
            else:
                raise ValueError(f"Unknown approach: {approach}")

            execution_time = time.time() - start_time

            # Evaluate output quality
            quality_score = self._evaluate_output_quality(result, test_case.quality_criteria)

            # Estimate cost
            cost_estimate = self._estimate_execution_cost(result, approach, execution_time)

            test_result = TestResult(
                test_id=test_case.test_id,
                approach=approach,
                execution_time=execution_time,
                cost_estimate=cost_estimate,
                output_quality_score=quality_score,
                success=True,
                metadata={
                    'agent_type': test_case.agent_type,
                    'output_length': len(str(result)) if result else 0,
                    'routing_info': result.get('routing_info', {}) if isinstance(result, dict) else {}
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            test_result = TestResult(
                test_id=test_case.test_id,
                approach=approach,
                execution_time=execution_time,
                cost_estimate=0.0,
                output_quality_score=0.0,
                success=False,
                error_message=str(e)
            )

        return test_result

    def _execute_ml_only(self, test_case: TestCase) -> Any:
        """Execute test using ML-only approach"""
        agent_type = test_case.agent_type

        if agent_type == 'resume_screening':
            from agents import ml_resume_screening_agent
            return ml_resume_screening_agent.screen_resume_ml(
                test_case.input_data.get('resume_text', '')
            )
        elif agent_type == 'candidate_ranking':
            from agents import ml_candidate_ranking_agent
            return ml_candidate_ranking_agent.rank_candidates_ml(
                test_case.input_data.get('candidates', []),
                test_case.input_data.get('job_requirements', {})
            )
        elif agent_type == 'job_matching':
            from agents import ml_job_matcher_agent
            return ml_job_matcher_agent.find_best_matches_ml(
                test_case.input_data.get('candidate_profile', {}),
                test_case.input_data.get('available_jobs', []),
                top_k=5
            )
        elif agent_type == 'predictive_analytics':
            from agents import ml_predictive_analytics_agent
            return ml_predictive_analytics_agent.generate_hiring_insights(
                test_case.input_data.get('historical_data', {})
            )
        else:
            raise ValueError(f"No ML implementation for agent type: {agent_type}")

    def _execute_gemini_only(self, test_case: TestCase) -> Any:
        """Execute test using Gemini-only approach"""
        agent_type = test_case.agent_type

        if agent_type == 'resume_screening':
            from agents import resume_screening_agent
            return resume_screening_agent.run(
                f"Screen this resume: {test_case.input_data.get('resume_text', '')}"
            )
        elif agent_type == 'candidate_ranking':
            from agents import candidate_ranking_agent
            return candidate_ranking_agent.run(
                f"Rank these candidates: {test_case.input_data}"
            )
        elif agent_type == 'job_matching':
            from agents import job_matcher
            return job_matcher.run(
                f"Find job matches: {test_case.input_data}"
            )
        elif agent_type == 'predictive_analytics':
            from agents import hiring_analytics_agent
            return hiring_analytics_agent.run(
                f"Analyze hiring data: {test_case.input_data}"
            )
        else:
            return {"result": "Processed with Gemini", "method": "gemini_only"}

    def _convert_test_case_to_task_profile(self, test_case: TestCase):
        """Convert test case to task profile for hybrid routing"""
        from utils.hybrid_architecture import TaskProfile, TaskType

        # Map agent type to TaskType
        task_type_map = {
            'resume_screening': TaskType.RESUME_SCREENING,
            'candidate_ranking': TaskType.CANDIDATE_RANKING,
            'job_matching': TaskType.JOB_MATCHING,
            'predictive_analytics': TaskType.PREDICTIVE_ANALYTICS
        }

        task_type = task_type_map.get(test_case.agent_type, TaskType.RESUME_SCREENING)

        return TaskProfile(
            task_type=task_type,
            complexity_score=0.5,  # Medium complexity for testing
            data_volume=len(str(test_case.input_data)),
            time_sensitivity=0.7,
            cost_sensitivity=0.6,
            accuracy_requirement=0.8,
            structured_output=True
        )

    def _evaluate_output_quality(self, result: Any, quality_criteria: Dict[str, Any]) -> float:
        """Evaluate the quality of test output"""
        if not result or not isinstance(result, dict):
            return 0.0

        quality_score = 0.0
        criteria_count = len(quality_criteria)

        for criterion, expected_value in quality_criteria.items():
            if criterion in result:
                actual_value = result[criterion]
                if isinstance(expected_value, (int, float)):
                    # Numeric comparison
                    if isinstance(actual_value, (int, float)):
                        if actual_value >= expected_value:
                            quality_score += 1.0
                        else:
                            quality_score += actual_value / expected_value
                elif isinstance(expected_value, bool):
                    # Boolean comparison
                    if actual_value == expected_value:
                        quality_score += 1.0
                else:
                    # String/other comparison
                    if str(actual_value).lower() == str(expected_value).lower():
                        quality_score += 1.0

        return quality_score / criteria_count if criteria_count > 0 else 0.5

    def _estimate_execution_cost(self, result: Any, approach: str, execution_time: float) -> float:
        """Estimate the cost of test execution"""
        base_costs = {
            'ml': 0.001,      # Very cheap local inference
            'gemini': 0.1,    # API call cost
            'hybrid': 0.05    # Partial API cost
        }

        base_cost = base_costs.get(approach, 0.1)

        # Add time-based cost component
        time_multiplier = min(execution_time / 1.0, 5.0)  # Cap at 5x for very slow executions

        return base_cost * time_multiplier

    def _generate_test_summary(self, suite: ComparativeTestSuite,
                             approaches: List[str]) -> Dict[str, Any]:
        """Generate comprehensive test summary with statistical analysis"""
        summary = {
            'total_tests': len(suite.results),
            'successful_tests': len([r for r in suite.results if r.success]),
            'approaches_tested': approaches,
            'performance_comparison': {},
            'cost_analysis': {},
            'quality_analysis': {},
            'statistical_significance': {},
            'recommendations': []
        }

        # Group results by approach
        approach_results = {}
        for approach in approaches:
            approach_results[approach] = [r for r in suite.results if r.approach == approach and r.success]

        # Performance comparison
        summary['performance_comparison'] = self._analyze_performance_comparison(approach_results)

        # Cost analysis
        summary['cost_analysis'] = self._analyze_cost_comparison(approach_results)

        # Quality analysis
        summary['quality_analysis'] = self._analyze_quality_comparison(approach_results)

        # Statistical significance testing
        summary['statistical_significance'] = self._perform_statistical_tests(approach_results)

        # Generate recommendations
        summary['recommendations'] = self._generate_test_recommendations(summary)

        return summary

    def _analyze_performance_comparison(self, approach_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Analyze performance differences between approaches"""
        performance_stats = {}

        for approach, results in approach_results.items():
            if results:
                execution_times = [r.execution_time for r in results]
                performance_stats[approach] = {
                    'mean_time': np.mean(execution_times),
                    'median_time': np.median(execution_times),
                    'std_time': np.std(execution_times),
                    'min_time': np.min(execution_times),
                    'max_time': np.max(execution_times),
                    'p95_time': np.percentile(execution_times, 95)
                }

        return performance_stats

    def _analyze_cost_comparison(self, approach_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Analyze cost differences between approaches"""
        cost_stats = {}

        for approach, results in approach_results.items():
            if results:
                costs = [r.cost_estimate for r in results]
                cost_stats[approach] = {
                    'total_cost': np.sum(costs),
                    'mean_cost': np.mean(costs),
                    'cost_per_test': np.mean(costs),
                    'cost_efficiency': 1.0 / np.mean(costs) if np.mean(costs) > 0 else 0
                }

        # Calculate cost savings
        if 'ml' in cost_stats and 'gemini' in cost_stats:
            ml_cost = cost_stats['ml']['mean_cost']
            gemini_cost = cost_stats['gemini']['mean_cost']
            if gemini_cost > 0:
                cost_stats['cost_savings'] = {
                    'ml_vs_gemini_percent': ((gemini_cost - ml_cost) / gemini_cost) * 100,
                    'absolute_savings_per_test': gemini_cost - ml_cost
                }

        return cost_stats

    def _analyze_quality_comparison(self, approach_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Analyze quality differences between approaches"""
        quality_stats = {}

        for approach, results in approach_results.items():
            if results:
                qualities = [r.output_quality_score for r in results]
                quality_stats[approach] = {
                    'mean_quality': np.mean(qualities),
                    'median_quality': np.median(qualities),
                    'std_quality': np.std(qualities),
                    'quality_consistency': 1.0 - (np.std(qualities) / np.mean(qualities)) if np.mean(qualities) > 0 else 0
                }

        return quality_stats

    def _perform_statistical_tests(self, approach_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """Perform statistical significance tests between approaches"""
        statistical_results = {}

        if 'ml' in approach_results and 'gemini' in approach_results:
            ml_times = [r.execution_time for r in approach_results['ml']]
            gemini_times = [r.execution_time for r in approach_results['gemini']]

            if len(ml_times) > 1 and len(gemini_times) > 1:
                # T-test for performance difference
                t_stat, p_value = stats.ttest_ind(ml_times, gemini_times)
                statistical_results['performance_t_test'] = {
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant_difference': p_value < 0.05,
                    'ml_faster': np.mean(ml_times) < np.mean(gemini_times)
                }

                # Cost comparison
                ml_costs = [r.cost_estimate for r in approach_results['ml']]
                gemini_costs = [r.cost_estimate for r in approach_results['gemini']]
                cost_t_stat, cost_p_value = stats.ttest_ind(ml_costs, gemini_costs)
                statistical_results['cost_t_test'] = {
                    't_statistic': cost_t_stat,
                    'p_value': cost_p_value,
                    'significant_difference': cost_p_value < 0.05,
                    'ml_cheaper': np.mean(ml_costs) < np.mean(gemini_costs)
                }

        return statistical_results

    def _generate_test_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        perf_comparison = summary.get('performance_comparison', {})
        cost_analysis = summary.get('cost_analysis', {})
        quality_analysis = summary.get('quality_analysis', {})
        stat_sig = summary.get('statistical_significance', {})

        # Performance recommendations
        if 'ml' in perf_comparison and 'gemini' in perf_comparison:
            ml_time = perf_comparison['ml']['mean_time']
            gemini_time = perf_comparison['gemini']['mean_time']
            if ml_time < gemini_time * 0.5:  # ML is much faster
                recommendations.append("ML approach significantly outperforms Gemini in speed - consider ML-first routing")

        # Cost recommendations
        cost_savings = cost_analysis.get('cost_savings', {})
        savings_pct = cost_savings.get('ml_vs_gemini_percent', 0)
        if savings_pct > 50:
            recommendations.append(f"ML approach provides {savings_pct:.1f}% cost savings - implement cost-based routing")

        # Quality recommendations
        if 'ml' in quality_analysis and 'gemini' in quality_analysis:
            ml_quality = quality_analysis['ml']['mean_quality']
            gemini_quality = quality_analysis['gemini']['quality_analysis']['mean_quality']
            if ml_quality >= gemini_quality * 0.9:  # ML quality is comparable
                recommendations.append("ML quality is comparable to Gemini - safe for production deployment")

        # Statistical significance
        perf_sig = stat_sig.get('performance_t_test', {})
        cost_sig = stat_sig.get('cost_t_test', {})
        if perf_sig.get('significant_difference') and cost_sig.get('significant_difference'):
            recommendations.append("Statistically significant improvements in both performance and cost - proceed with ML implementation")

        if not recommendations:
            recommendations.append("Continue testing - insufficient data for definitive recommendations")

        return recommendations

    def _save_test_results(self, suite: ComparativeTestSuite):
        """Save detailed test results and generate visualizations"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Save detailed results
        results_file = f"{self.results_dir}/detailed_results/{suite.suite_name}_{timestamp}.json"
        results_data = {
            'suite_name': suite.suite_name,
            'execution_timestamp': timestamp,
            'test_cases': [vars(tc) for tc in suite.test_cases],
            'results': [vars(tr) for tr in suite.results],
            'summary_stats': suite.summary_stats
        }

        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        # Generate visualizations
        self._generate_test_visualizations(suite, timestamp)

        # Generate HTML report
        self._generate_html_report(suite, timestamp)

        logger.info(f"Test results saved to {results_file}")

    def _generate_test_visualizations(self, suite: ComparativeTestSuite, timestamp: str):
        """Generate comparative visualizations"""
        try:
            # Create DataFrame for plotting
            results_df = pd.DataFrame([vars(r) for r in suite.results if r.success])

            if len(results_df) > 0:
                # Performance comparison plot
                plt.figure(figsize=(12, 8))

                plt.subplot(2, 2, 1)
                sns.boxplot(data=results_df, x='approach', y='execution_time')
                plt.title('Execution Time by Approach')
                plt.ylabel('Time (seconds)')

                plt.subplot(2, 2, 2)
                sns.boxplot(data=results_df, x='approach', y='cost_estimate')
                plt.title('Cost by Approach')
                plt.ylabel('Cost (USD)')

                plt.subplot(2, 2, 3)
                sns.boxplot(data=results_df, x='approach', y='output_quality_score')
                plt.title('Quality Score by Approach')
                plt.ylabel('Quality Score')

                plt.subplot(2, 2, 4)
                success_rates = results_df.groupby('approach')['success'].mean()
                success_rates.plot(kind='bar')
                plt.title('Success Rate by Approach')
                plt.ylabel('Success Rate')

                plt.tight_layout()
                plt.savefig(f"{self.results_dir}/visualizations/{suite.suite_name}_{timestamp}.png", dpi=300, bbox_inches='tight')
                plt.close()

        except Exception as e:
            logger.warning(f"Failed to generate visualizations: {e}")

    def _generate_html_report(self, suite: ComparativeTestSuite, timestamp: str):
        """Generate comprehensive HTML test report"""
        summary = suite.summary_stats

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ML vs Gemini Comparative Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .success {{ color: green; }}
                .warning {{ color: orange; }}
                .danger {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>🤖 ML vs Gemini Comparative Testing Report</h1>
            <p><strong>Test Suite:</strong> {suite.suite_name}</p>
            <p><strong>Execution Date:</strong> {timestamp}</p>
            <p><strong>Total Tests:</strong> {summary.get('total_tests', 0)}</p>
            <p><strong>Successful Tests:</strong> {summary.get('successful_tests', 0)}</p>

            <h2>📊 Performance Comparison</h2>
            <div class="metric">
                <h3>Execution Time Analysis</h3>
        """

        # Add performance data
        perf_comp = summary.get('performance_comparison', {})
        for approach, metrics in perf_comp.items():
            html_content += f"""
                <p><strong>{approach.upper()}:</strong>
                Mean: {metrics.get('mean_time', 0):.3f}s,
                Median: {metrics.get('median_time', 0):.3f}s,
                P95: {metrics.get('p95_time', 0):.3f}s</p>
            """

        html_content += """
            </div>

            <h2>💰 Cost Analysis</h2>
            <div class="metric">
        """

        # Add cost data
        cost_analysis = summary.get('cost_analysis', {})
        for approach, metrics in cost_analysis.items():
            if approach != 'cost_savings':
                html_content += f"""
                <p><strong>{approach.upper()}:</strong>
                Total: ${metrics.get('total_cost', 0):.3f},
                Per Test: ${metrics.get('cost_per_test', 0):.4f}</p>
                """

        cost_savings = cost_analysis.get('cost_savings', {})
        if cost_savings:
            savings_pct = cost_savings.get('ml_vs_gemini_percent', 0)
            html_content += f"""
                <p class="success"><strong>Cost Savings:</strong> {savings_pct:.1f}% reduction with ML approach</p>
            """

        html_content += """
            </div>

            <h2>🎯 Quality Analysis</h2>
            <div class="metric">
        """

        # Add quality data
        quality_analysis = summary.get('quality_analysis', {})
        for approach, metrics in quality_analysis.items():
            html_content += f"""
            <p><strong>{approach.upper()}:</strong>
            Mean Quality: {metrics.get('mean_quality', 0):.3f},
            Consistency: {metrics.get('quality_consistency', 0):.3f}</p>
            """

        html_content += """
            </div>

            <h2>📈 Statistical Significance</h2>
            <div class="metric">
        """

        # Add statistical test results
        stat_sig = summary.get('statistical_significance', {})
        perf_test = stat_sig.get('performance_t_test', {})
        cost_test = stat_sig.get('cost_t_test', {})

        if perf_test.get('significant_difference'):
            ml_faster = perf_test.get('ml_faster')
            html_content += f'<p class="success">⚡ Performance difference is statistically significant (p={perf_test.get("p_value", 1):.4f})</p>'
            html_content += f'<p>ML is {"faster" if ml_faster else "slower"} than Gemini</p>'

        if cost_test.get('significant_difference'):
            ml_cheaper = cost_test.get('ml_cheaper')
            html_content += f'<p class="success">💰 Cost difference is statistically significant (p={cost_test.get("p_value", 1):.4f})</p>'
            html_content += f'<p>ML is {"cheaper" if ml_cheaper else "more expensive"} than Gemini</p>'

        html_content += """
            </div>

            <h2>💡 Recommendations</h2>
            <div class="metric">
                <ul>
        """

        # Add recommendations
        recommendations = summary.get('recommendations', [])
        for rec in recommendations:
            html_content += f"<li>{rec}</li>"

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """

        # Save HTML report
        report_file = f"{self.results_dir}/reports/{suite.suite_name}_{timestamp}.html"
        with open(report_file, 'w') as f:
            f.write(html_content)

        logger.info(f"HTML test report saved to {report_file}")

    # Helper methods for test data generation (simplified)
    def _generate_test_resume(self, index: int) -> str:
        """Generate synthetic resume for testing"""
        return f"John Doe {index}, Software Engineer with {index+1} years experience. Python, SQL, AWS."

    def _generate_job_requirements(self, index: int) -> Dict[str, Any]:
        """Generate job requirements for testing"""
        return {'experience_years': index + 1, 'skills': ['python', 'sql']}

    def _generate_candidate_pool(self, size: int) -> List[Dict[str, Any]]:
        """Generate candidate pool for testing"""
        return [{'id': f'cand_{i}', 'experience_years': i+1} for i in range(size)]

    def _generate_candidate_profile(self, index: int) -> Dict[str, Any]:
        """Generate candidate profile for testing"""
        return {'experience_years': index % 5 + 1, 'skills': ['python']}

    def _generate_job_pool(self, size: int) -> List[Dict[str, Any]]:
        """Generate job pool for testing"""
        return [{'title': f'Job {i}', 'skills': ['python']} for i in range(size)]

    def _generate_historical_hiring_data(self) -> Dict[str, Any]:
        """Generate historical hiring data for testing"""
        return {'time_to_hire': [30, 45, 60], 'retention': [0.8, 0.9, 0.7]}

# Create global testing framework instance
ml_testing_framework = MLvsGeminiTestingFramework()

# Convenience functions
def run_comprehensive_comparison(suite_name: str = "automated_comparison") -> Dict[str, Any]:
    """Run comprehensive ML vs Gemini comparison"""
    suite = ml_testing_framework.create_comprehensive_test_suite(suite_name)
    completed_suite = ml_testing_framework.execute_test_suite(suite)
    return completed_suite.summary_stats

def get_latest_test_results() -> Dict[str, Any]:
    """Get results from most recent test run"""
    # This would return the most recent test results
    return {"message": "Test results would be returned here"}

if __name__ == "__main__":
    # Demo of the testing framework
    print("=" * 60)

    suite = ml_testing_framework.create_comprehensive_test_suite("demo_comparison")

    # For demo, just run a small subset to show functionality
    demo_test_cases = suite.test_cases[:5]  # Just 5 test cases for demo
    demo_suite = ComparativeTestSuite(suite_name="demo_subset", test_cases=demo_test_cases)

    # Execute demo tests
    try:
        completed_demo = ml_testing_framework.execute_test_suite(
            demo_suite, approaches=['ml', 'gemini'], max_workers=2
        )

        print("📊 Sample Results:"        summary = completed_demo.summary_stats

        perf_comp = summary.get('performance_comparison', {})
        if perf_comp:
            for approach, metrics in perf_comp.items():
                print(f"   {approach.upper()} - Mean time: {metrics.get('mean_time', 0):.3f}s")

        cost_analysis = summary.get('cost_analysis', {})
        cost_savings = cost_analysis.get('cost_savings', {})
        if cost_savings:
            savings_pct = cost_savings.get('ml_vs_gemini_percent', 0)
            print(f"   Cost savings: {savings_pct:.1f}% with ML approach")

    except Exception as e:
        print(f"❌ Demo execution failed: {e}")
        print("💡 This is expected if ML models aren't fully trained yet")

    print("   • Cost-benefit analysis")
    print("   • Comprehensive reporting")
    print("   • Performance visualization")

