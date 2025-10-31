"""
ML Model Evaluation Framework
Comprehensive evaluation of ML models for accuracy, bias detection, fairness, and ethical AI compliance
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import numpy as np
import pandas as pd
from collections import defaultdict

# ML and statistical imports
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, mean_absolute_error,
    mean_squared_error, r2_score, roc_auc_score, roc_curve
)
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
from imblearn.metrics import classification_report_imbalanced
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLEvaluationFramework:
    """
    Comprehensive framework for evaluating ML models used in hiring systems.
    Includes accuracy metrics, bias detection, fairness analysis, and ethical AI safeguards.
    """

    def __init__(self, results_dir: str = "ml_evaluation_results"):
        """
        Initialize the ML Evaluation Framework

        Args:
            results_dir: Directory to store evaluation results and reports
        """
        self.results_dir = results_dir
        self.evaluation_history = []

        # Create results directory
        os.makedirs(results_dir, exist_ok=True)

        # Initialize bias and fairness detectors
        self.bias_detectors = {
            'demographic_parity': self._check_demographic_parity,
            'equal_opportunity': self._check_equal_opportunity,
            'disparate_impact': self._check_disparate_impact,
            'predictive_equality': self._check_predictive_equality
        }

        # Ethical AI thresholds
        self.ethical_thresholds = {
            'max_bias_ratio': 1.5,  # Maximum allowed bias ratio
            'min_fairness_score': 0.8,  # Minimum fairness score required
            'max_disparate_impact': 0.8,  # Maximum disparate impact ratio
            'min_transparency_score': 0.7  # Minimum explainability score
        }

    def evaluate_model_comprehensive(self, model, X_test: np.ndarray, y_test: np.ndarray,
                                   model_name: str, model_type: str = 'classification',
                                   sensitive_features: Optional[Dict[str, np.ndarray]] = None,
                                   feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive model evaluation including accuracy, bias, and fairness

        Args:
            model: Trained ML model
            X_test: Test features
            y_test: Test labels
            model_name: Name of the model for reporting
            model_type: 'classification' or 'regression'
            sensitive_features: Dictionary of sensitive features for bias analysis
            feature_names: Names of features for interpretability

        Returns:
            Comprehensive evaluation report
        """
        evaluation_report = {
            'model_name': model_name,
            'model_type': model_type,
            'timestamp': datetime.now().isoformat(),
            'performance_metrics': {},
            'bias_analysis': {},
            'fairness_metrics': {},
            'ethical_compliance': {},
            'recommendations': []
        }

        try:
            # Get model predictions
            y_pred = model.predict(X_test)
            if hasattr(model, 'predict_proba'):
                y_pred_proba = model.predict_proba(X_test)
            else:
                y_pred_proba = None

            # 1. Performance Metrics
            evaluation_report['performance_metrics'] = self._calculate_performance_metrics(
                y_test, y_pred, y_pred_proba, model_type
            )

            # 2. Cross-validation stability
            evaluation_report['cross_validation'] = self._perform_cross_validation(model, X_test, y_test)

            # 3. Bias and Fairness Analysis
            if sensitive_features:
                evaluation_report['bias_analysis'] = self._analyze_bias(
                    y_test, y_pred, sensitive_features
                )
                evaluation_report['fairness_metrics'] = self._calculate_fairness_metrics(
                    y_test, y_pred, sensitive_features
                )

            # 4. Feature Importance Analysis
            if hasattr(model, 'feature_importances_') and feature_names:
                evaluation_report['feature_importance'] = self._analyze_feature_importance(
                    model, feature_names
                )

            # 5. Ethical AI Compliance Check
            evaluation_report['ethical_compliance'] = self._check_ethical_compliance(
                evaluation_report
            )

            # 6. Generate Recommendations
            evaluation_report['recommendations'] = self._generate_evaluation_recommendations(
                evaluation_report
            )

            # Store evaluation in history
            self.evaluation_history.append(evaluation_report)

            # Save detailed report
            self._save_evaluation_report(evaluation_report)

            logger.info(f"✅ Comprehensive evaluation completed for {model_name}")

        except Exception as e:
            logger.error(f"❌ Evaluation failed for {model_name}: {e}")
            evaluation_report['error'] = str(e)

        return evaluation_report

    def _calculate_performance_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                                     y_pred_proba: Optional[np.ndarray],
                                     model_type: str) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        metrics = {}

        if model_type == 'classification':
            # Basic classification metrics
            metrics['accuracy'] = float(accuracy_score(y_true, y_pred))
            metrics['precision'] = float(precision_score(y_true, y_pred, average='weighted', zero_division=0))
            metrics['recall'] = float(recall_score(y_true, y_pred, average='weighted', zero_division=0))
            metrics['f1_score'] = float(f1_score(y_true, y_pred, average='weighted', zero_division=0))

            # Confusion matrix
            cm = confusion_matrix(y_true, y_pred)
            metrics['confusion_matrix'] = cm.tolist()

            # Detailed classification report
            report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
            metrics['detailed_report'] = report

            # ROC-AUC if probabilities available
            if y_pred_proba is not None and y_pred_proba.shape[1] == 2:
                try:
                    metrics['roc_auc'] = float(roc_auc_score(y_true, y_pred_proba[:, 1]))
                except Exception:
                    metrics['roc_auc'] = None

        elif model_type == 'regression':
            metrics['mae'] = float(mean_absolute_error(y_true, y_pred))
            metrics['mse'] = float(mean_squared_error(y_true, y_pred))
            metrics['rmse'] = float(np.sqrt(mean_squared_error(y_true, y_pred)))
            metrics['r2_score'] = float(r2_score(y_true, y_pred))

            # Additional regression metrics
            metrics['mean_absolute_percentage_error'] = float(
                np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 1e-10))) * 100
            )

        return metrics

    def _perform_cross_validation(self, model, X: np.ndarray, y: np.ndarray,
                                cv_folds: int = 5) -> Dict[str, Any]:
        """Perform cross-validation to assess model stability"""
        try:
            kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

            if hasattr(model, 'predict_proba'):
                scoring = ['accuracy', 'precision_weighted', 'recall_weighted', 'f1_weighted']
            else:
                scoring = ['neg_mean_absolute_error', 'neg_mean_squared_error', 'r2']

            cv_results = {}
            for metric in scoring:
                try:
                    scores = cross_val_score(model, X, y, cv=kf, scoring=metric)
                    cv_results[metric] = {
                        'mean': float(scores.mean()),
                        'std': float(scores.std()),
                        'scores': scores.tolist()
                    }
                except Exception as e:
                    cv_results[metric] = {'error': str(e)}

            return cv_results

        except Exception as e:
            return {'error': str(e)}

    def _analyze_bias(self, y_true: np.ndarray, y_pred: np.ndarray,
                     sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Analyze potential bias in model predictions"""
        bias_analysis = {}

        for feature_name, feature_values in sensitive_features.items():
            feature_bias = {}

            # Get unique groups in sensitive feature
            unique_groups = np.unique(feature_values)

            if len(unique_groups) >= 2:
                for group in unique_groups:
                    group_mask = feature_values == group
                    if np.sum(group_mask) > 0:  # Ensure group has samples
                        group_true = y_true[group_mask]
                        group_pred = y_pred[group_mask]

                        # Calculate group-specific metrics
                        group_metrics = {
                            'sample_size': int(np.sum(group_mask)),
                            'accuracy': float(accuracy_score(group_true, group_pred)) if len(group_true) > 0 else 0,
                            'precision': float(precision_score(group_true, group_pred, average='weighted', zero_division=0)) if len(group_true) > 0 else 0,
                            'recall': float(recall_score(group_true, group_pred, average='weighted', zero_division=0)) if len(group_true) > 0 else 0,
                            'f1_score': float(f1_score(group_true, group_pred, average='weighted', zero_division=0)) if len(group_true) > 0 else 0
                        }

                        feature_bias[f'group_{group}'] = group_metrics

                # Calculate bias ratios between groups
                if len(feature_bias) >= 2:
                    groups = list(feature_bias.keys())
                    base_group = feature_bias[groups[0]]

                    for group in groups[1:]:
                        current_group = feature_bias[group]

                        bias_ratios = {}
                        for metric in ['accuracy', 'precision', 'recall', 'f1_score']:
                            if base_group[metric] > 0:
                                bias_ratios[f'{metric}_ratio'] = current_group[metric] / base_group[metric]
                            else:
                                bias_ratios[f'{metric}_ratio'] = 0

                        feature_bias[f'{group}_vs_{groups[0]}_bias'] = bias_ratios

            bias_analysis[feature_name] = feature_bias

        return bias_analysis

    def _calculate_fairness_metrics(self, y_true: np.ndarray, y_pred: np.ndarray,
                                  sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Calculate fairness metrics for different protected groups"""
        fairness_metrics = {}

        for detector_name, detector_func in self.bias_detectors.items():
            try:
                fairness_metrics[detector_name] = detector_func(y_true, y_pred, sensitive_features)
            except Exception as e:
                fairness_metrics[detector_name] = {'error': str(e)}

        return fairness_metrics

    def _check_demographic_parity(self, y_true: np.ndarray, y_pred: np.ndarray,
                                sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Check demographic parity (equal acceptance rates across groups)"""
        results = {}

        for feature_name, feature_values in sensitive_features.items():
            unique_groups = np.unique(feature_values)

            if len(unique_groups) >= 2:
                group_rates = {}
                for group in unique_groups:
                    group_mask = feature_values == group
                    if np.sum(group_mask) > 0:
                        group_pred = y_pred[group_mask]
                        acceptance_rate = np.mean(group_pred)
                        group_rates[f'group_{group}'] = float(acceptance_rate)

                # Check if rates are within acceptable range
                rates = list(group_rates.values())
                if len(rates) >= 2:
                    max_rate = max(rates)
                    min_rate = min(rates)
                    ratio = max_rate / min_rate if min_rate > 0 else float('inf')

                    results[feature_name] = {
                        'group_rates': group_rates,
                        'max_min_ratio': ratio,
                        'demographic_parity_violation': ratio > self.ethical_thresholds['max_bias_ratio']
                    }

        return results

    def _check_equal_opportunity(self, y_true: np.ndarray, y_pred: np.ndarray,
                               sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Check equal opportunity (equal true positive rates across groups)"""
        results = {}

        for feature_name, feature_values in sensitive_features.items():
            unique_groups = np.unique(feature_values)

            if len(unique_groups) >= 2:
                group_tpr = {}  # True Positive Rate

                for group in unique_groups:
                    group_mask = feature_values == group
                    if np.sum(group_mask) > 0:
                        group_true = y_true[group_mask]
                        group_pred = y_pred[group_mask]

                        # Calculate True Positive Rate (TPR)
                        tp = np.sum((group_true == 1) & (group_pred == 1))
                        fn = np.sum((group_true == 1) & (group_pred == 0))
                        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
                        group_tpr[f'group_{group}'] = float(tpr)

                # Check TPR equality
                tpr_values = list(group_tpr.values())
                if len(tpr_values) >= 2:
                    max_tpr = max(tpr_values)
                    min_tpr = min(tpr_values)
                    ratio = max_tpr / min_tpr if min_tpr > 0 else float('inf')

                    results[feature_name] = {
                        'group_tpr': group_tpr,
                        'max_min_ratio': ratio,
                        'equal_opportunity_violation': ratio > self.ethical_thresholds['max_bias_ratio']
                    }

        return results

    def _check_disparate_impact(self, y_true: np.ndarray, y_pred: np.ndarray,
                              sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Check disparate impact (80% rule - selection rate ratio)"""
        results = {}

        for feature_name, feature_values in sensitive_features.items():
            unique_groups = np.unique(feature_values)

            if len(unique_groups) >= 2:
                selection_rates = {}

                for group in unique_groups:
                    group_mask = feature_values == group
                    if np.sum(group_mask) > 0:
                        group_pred = y_pred[group_mask]
                        selection_rate = np.mean(group_pred)
                        selection_rates[f'group_{group}'] = float(selection_rate)

                # Apply 80% rule (4/5ths rule)
                rates = list(selection_rates.values())
                if len(rates) >= 2:
                    highest_rate = max(rates)
                    lowest_rate = min(rates)
                    impact_ratio = lowest_rate / highest_rate if highest_rate > 0 else 0

                    results[feature_name] = {
                        'selection_rates': selection_rates,
                        'disparate_impact_ratio': impact_ratio,
                        'passes_80_percent_rule': impact_ratio >= 0.8,  # 80% rule
                        'severe_disparity': impact_ratio < self.ethical_thresholds['max_disparate_impact']
                    }

        return results

    def _check_predictive_equality(self, y_true: np.ndarray, y_pred: np.ndarray,
                                 sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Check predictive equality (equal false positive rates across groups)"""
        results = {}

        for feature_name, feature_values in sensitive_features.items():
            unique_groups = np.unique(feature_values)

            if len(unique_groups) >= 2:
                group_fpr = {}  # False Positive Rate

                for group in unique_groups:
                    group_mask = feature_values == group
                    if np.sum(group_mask) > 0:
                        group_true = y_true[group_mask]
                        group_pred = y_pred[group_mask]

                        # Calculate False Positive Rate (FPR)
                        fp = np.sum((group_true == 0) & (group_pred == 1))
                        tn = np.sum((group_true == 0) & (group_pred == 0))
                        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
                        group_fpr[f'group_{group}'] = float(fpr)

                # Check FPR equality
                fpr_values = list(group_fpr.values())
                if len(fpr_values) >= 2:
                    max_fpr = max(fpr_values)
                    min_fpr = min(fpr_values)
                    ratio = max_fpr / min_fpr if min_fpr > 0 else float('inf')

                    results[feature_name] = {
                        'group_fpr': group_fpr,
                        'max_min_ratio': ratio,
                        'predictive_equality_violation': ratio > self.ethical_thresholds['max_bias_ratio']
                    }

        return results

    def _analyze_feature_importance(self, model, feature_names: List[str]) -> Dict[str, Any]:
        """Analyze feature importance for model interpretability"""
        if not hasattr(model, 'feature_importances_'):
            return {'error': 'Model does not support feature importance analysis'}

        importance_scores = model.feature_importances_
        feature_importance = {}

        # Sort features by importance
        sorted_indices = np.argsort(importance_scores)[::-1]

        for i, idx in enumerate(sorted_indices):
            feature_importance[feature_names[idx]] = {
                'importance_score': float(importance_scores[idx]),
                'rank': i + 1,
                'percentage': float(importance_scores[idx] * 100)
            }

        return feature_importance

    def _check_ethical_compliance(self, evaluation_report: Dict[str, Any]) -> Dict[str, Any]:
        """Check if model meets ethical AI standards"""
        compliance = {
            'overall_compliant': True,
            'issues': [],
            'recommendations': []
        }

        # Check performance thresholds
        performance = evaluation_report.get('performance_metrics', {})
        if performance.get('accuracy', 0) < 0.7:
            compliance['issues'].append('Low model accuracy')
            compliance['overall_compliant'] = False

        # Check bias metrics
        bias_analysis = evaluation_report.get('bias_analysis', {})
        fairness_metrics = evaluation_report.get('fairness_metrics', {})

        for feature_name, feature_bias in bias_analysis.items():
            for bias_type, bias_data in feature_bias.items():
                if '_vs_' in bias_type and '_bias' in bias_type:
                    ratios = bias_data
                    for ratio_name, ratio_value in ratios.items():
                        if isinstance(ratio_value, (int, float)) and ratio_value > self.ethical_thresholds['max_bias_ratio']:
                            compliance['issues'].append(f'Bias detected in {feature_name}: {ratio_name} = {ratio_value:.2f}')
                            compliance['overall_compliant'] = False

        # Check disparate impact
        for detector_name, detector_results in fairness_metrics.items():
            if detector_name == 'disparate_impact':
                for feature_name, impact_data in detector_results.items():
                    if not impact_data.get('passes_80_percent_rule', True):
                        compliance['issues'].append(f'Disparate impact violation in {feature_name}')
                        compliance['overall_compliant'] = False

        # Generate recommendations
        if not compliance['overall_compliant']:
            compliance['recommendations'].extend([
                'Consider bias mitigation techniques (re-sampling, re-weighting)',
                'Review training data for representation issues',
                'Implement fairness-aware algorithms',
                'Add more diverse training data',
                'Consider human oversight for high-stakes decisions'
            ])

        return compliance

    def _generate_evaluation_recommendations(self, evaluation_report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on evaluation results"""
        recommendations = []

        # Performance-based recommendations
        performance = evaluation_report.get('performance_metrics', {})
        if performance.get('accuracy', 0) < 0.8:
            recommendations.append('Model accuracy needs improvement - consider more features or different algorithm')

        if performance.get('f1_score', 0) < 0.75:
            recommendations.append('Consider addressing class imbalance or improving feature engineering')

        # Bias and fairness recommendations
        ethical = evaluation_report.get('ethical_compliance', {})
        if not ethical.get('overall_compliant', True):
            recommendations.append('Address identified bias and fairness issues before deployment')

        # Stability recommendations
        cv_results = evaluation_report.get('cross_validation', {})
        for metric, scores in cv_results.items():
            if isinstance(scores, dict) and 'std' in scores:
                if scores['std'] > 0.1:  # High variance
                    recommendations.append(f'High variance in {metric} - consider regularization or more data')

        return recommendations

    def _save_evaluation_report(self, evaluation_report: Dict[str, Any]):
        """Save detailed evaluation report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{evaluation_report['model_name']}_evaluation_{timestamp}.json"

        filepath = os.path.join(self.results_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(evaluation_report, f, indent=2, default=str)
            logger.info(f"Evaluation report saved: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save evaluation report: {e}")

    def generate_evaluation_dashboard(self, evaluation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        """Generate HTML dashboard summarizing evaluation results"""
        if evaluation_history is None:
            evaluation_history = self.evaluation_history

        if not evaluation_history:
            return "<h3>No evaluation data available</h3>"

        # Create summary statistics
        latest_eval = evaluation_history[-1]

        html_content = f"""
        <html>
        <head>
            <title>ML Model Evaluation Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric {{ background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                .compliant {{ color: green; }}
                .non-compliant {{ color: red; }}
                .warning {{ color: orange; }}
            </style>
        </head>
        <body>
            <h1>🤖 ML Model Evaluation Dashboard</h1>
            <p><strong>Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <h2>📊 Latest Model Performance</h2>
            <div class="metric">
                <h3>{latest_eval.get('model_name', 'Unknown Model')}</h3>
                <p><strong>Type:</strong> {latest_eval.get('model_type', 'Unknown')}</p>
                <p><strong>Accuracy:</strong> {latest_eval.get('performance_metrics', {}).get('accuracy', 'N/A')}</p>
                <p><strong>F1 Score:</strong> {latest_eval.get('performance_metrics', {}).get('f1_score', 'N/A')}</p>
            </div>

            <h2>⚖️ Ethical AI Compliance</h2>
            <div class="metric {'compliant' if latest_eval.get('ethical_compliance', {}).get('overall_compliant') else 'non-compliant'}">
                <h3>Overall Compliance: {'✅ PASS' if latest_eval.get('ethical_compliance', {}).get('overall_compliant') else '❌ FAIL'}</h3>
                <ul>
        """

        # Add compliance issues
        issues = latest_eval.get('ethical_compliance', {}).get('issues', [])
        if issues:
            for issue in issues:
                html_content += f"<li>{issue}</li>"
        else:
            html_content += "<li>No compliance issues detected</li>"

        html_content += """
                </ul>
            </div>

            <h2>💡 Recommendations</h2>
            <div class="metric">
                <ul>
        """

        recommendations = latest_eval.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                html_content += f"<li>{rec}</li>"
        else:
            html_content += "<li>No specific recommendations</li>"

        html_content += """
                </ul>
            </div>
        </body>
        </html>
        """

        return html_content

    def get_evaluation_summary(self) -> Dict[str, Any]:
        """Get summary of all evaluations"""
        if not self.evaluation_history:
            return {'message': 'No evaluations performed yet'}

        latest_eval = self.evaluation_history[-1]

        summary = {
            'total_evaluations': len(self.evaluation_history),
            'latest_model': latest_eval.get('model_name'),
            'latest_performance': latest_eval.get('performance_metrics'),
            'ethical_compliance': latest_eval.get('ethical_compliance', {}).get('overall_compliant'),
            'issues_count': len(latest_eval.get('ethical_compliance', {}).get('issues', [])),
            'recommendations_count': len(latest_eval.get('recommendations', []))
        }

        return summary

# Create singleton instance
ml_evaluation_framework = MLEvaluationFramework()

# Utility functions for quick evaluation
def evaluate_model_quick(model, X_test: np.ndarray, y_test: np.ndarray,
                        model_name: str, model_type: str = 'classification') -> Dict[str, Any]:
    """
    Quick model evaluation with basic metrics

    Args:
        model: Trained ML model
        X_test: Test features
        y_test: Test labels
        model_name: Model name
        model_type: 'classification' or 'regression'

    Returns:
        Basic evaluation metrics
    """
    return ml_evaluation_framework.evaluate_model_comprehensive(
        model, X_test, y_test, model_name, model_type
    )

def check_model_bias_quick(y_true: np.ndarray, y_pred: np.ndarray,
                          sensitive_features: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Quick bias check for model predictions

    Args:
        y_true: True labels
        y_pred: Predicted labels
        sensitive_features: Dictionary of sensitive features

    Returns:
        Bias analysis results
    """
    return ml_evaluation_framework._analyze_bias(y_true, y_pred, sensitive_features)

if __name__ == "__main__":
    # Example usage
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification

    # Generate sample data
    X, y = make_classification(n_samples=1000, n_features=20, n_informative=10,
                              n_redundant=10, n_classes=2, random_state=42)

    # Split data
    X_train, X_test = X[:800], X[800:]
    y_train, y_test = y[:800], y[800:]

    # Train sample model
    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)

    # Evaluate model
    evaluation = evaluate_model_quick(model, X_test, y_test, "Sample_RF_Model")

    print("Model Evaluation Results:")
    print(f"Accuracy: {evaluation['performance_metrics']['accuracy']:.3f}")
    print(f"F1 Score: {evaluation['performance_metrics']['f1_score']:.3f}")
    print(f"Ethical Compliance: {evaluation['ethical_compliance']['overall_compliant']}")

    if evaluation['recommendations']:
        print("\nRecommendations:")
        for rec in evaluation['recommendations']:
            print(f"- {rec}")

