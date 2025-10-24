"""
Ethical Guidelines for AI-Powered Career Assistance
Ensuring responsible, transparent, and compliant AI usage
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import json

class EthicalGuidelines:
    """
    Comprehensive ethical framework for AI career assistance
    """

    def __init__(self):
        self.guidelines = {
            'cv_optimization': {
                'rule': 'NEVER fabricate experience',
                'approach': 'Reframe existing experience, highlight transferable skills',
                'transparency': 'Disclose AI assistance if asked',
                'validation': 'Cross-reference with provided CV content only'
            },
            'interview_assistance': {
                'rule': 'Copilot provides guidance, not answers',
                'limit': 'Bullet points only, student must respond authentically',
                'disclosure': 'Consider disclosing AI practice to employers',
                'ethical_boundary': 'Enhance preparation, do not provide unfair advantage'
            },
            'application_automation': {
                'rule': 'Quality over quantity',
                'limit': 'Only apply to genuinely good matches (score 70+)',
                'personalization': 'Each application must be meaningfully customized',
                'responsible_volume': 'Maximum 10 applications per day to avoid spam'
            },
            'data_privacy': {
                'encryption': 'End-to-end encryption for student data',
                'consent': 'Explicit consent for data usage',
                'compliance': 'POPIA (SA) and GDPR compliant',
                'data_minimization': 'Collect only necessary information'
            },
            'ai_transparency': {
                'disclosure': 'Inform users when AI is involved',
                'bias_awareness': 'Monitor for algorithmic bias',
                'accountability': 'Clear responsibility attribution',
                'continuous_review': 'Regular ethical audits'
            }
        }

        self.consent_records = {}
        self.ethical_audit_log = []

    def validate_cv_optimization(self, original_cv: str, optimized_cv: str, student_consent: bool = False) -> Dict[str, Any]:
        """
        Validate CV optimization adheres to ethical guidelines
        """
        validation_result = {
            'ethical_compliant': True,
            'warnings': [],
            'recommendations': [],
            'consent_required': True,
            'disclosure_advised': True
        }

        # Check for fabrication
        original_words = set(original_cv.lower().split())
        optimized_words = set(optimized_cv.lower().split())

        # Allow reasonable expansion (up to 30% new content for rephrasing)
        expansion_ratio = len(optimized_words - original_words) / len(original_words)

        if expansion_ratio > 0.3:
            validation_result['warnings'].append(
                f"Content expansion ratio ({expansion_ratio:.1%}) exceeds ethical threshold (30%)"
            )
            validation_result['recommendations'].append(
                "Reduce content expansion - focus on rephrasing existing experience"
            )

        # Check for common fabrication patterns
        fabrication_indicators = [
            'years of experience' in optimized_cv.lower() and 'years of experience' not in original_cv.lower(),
            'led a team' in optimized_cv.lower() and not any(phrase in original_cv.lower() for phrase in ['team', 'group', 'led']),
            'managed budget' in optimized_cv.lower() and 'budget' not in original_cv.lower()
        ]

        if any(fabrication_indicators):
            validation_result['ethical_compliant'] = False
            validation_result['warnings'].append("Potential experience fabrication detected")
            validation_result['recommendations'].append("Only reframe existing experience - do not invent new achievements")

        # Check consent
        if not student_consent:
            validation_result['warnings'].append("Student consent required for CV optimization")
            validation_result['recommendations'].append("Obtain explicit consent before proceeding")

        # Log ethical check
        self._log_ethical_check('cv_optimization', validation_result)

        return validation_result

    def validate_interview_assistance(self, question: str, copilot_response: str) -> Dict[str, Any]:
        """
        Validate interview copilot response adheres to ethical boundaries
        """
        validation_result = {
            'ethical_compliant': True,
            'warnings': [],
            'recommendations': [],
            'response_type': 'guidance_only',
            'disclosure_recommended': True
        }

        # Check response format (should be bullet points, not complete answers)
        lines = copilot_response.strip().split('\n')
        bullet_lines = [line for line in lines if line.strip().startswith(('•', '-', '*'))]

        if len(bullet_lines) == 0:
            validation_result['warnings'].append("Response should use bullet points for guidance only")
            validation_result['recommendations'].append("Convert to bullet-point format focusing on structure and keywords")

        # Check for complete answer patterns
        complete_answer_indicators = [
            'my answer would be' in copilot_response.lower(),
            'you should say' in copilot_response.lower(),
            'tell them that' in copilot_response.lower(),
            copilot_response.count('.') > 5  # Too many complete sentences
        ]

        if any(complete_answer_indicators):
            validation_result['ethical_compliant'] = False
            validation_result['warnings'].append("Copilot response appears to provide complete answers")
            validation_result['recommendations'].append("Provide structure guidance and keywords only - not complete responses")

        # Check response length (should be brief guidance)
        if len(copilot_response.split()) > 50:
            validation_result['warnings'].append("Copilot response too detailed")
            validation_result['recommendations'].append("Limit to 3-5 brief bullet points maximum")

        # Log ethical check
        self._log_ethical_check('interview_assistance', validation_result)

        return validation_result

    def validate_application_submission(self, job_match_score: float, application_count_today: int,
                                      customization_level: str) -> Dict[str, Any]:
        """
        Validate application submission meets ethical criteria
        """
        validation_result = {
            'can_submit': True,
            'warnings': [],
            'recommendations': [],
            'quality_assessment': 'high' if job_match_score >= 80 else 'medium' if job_match_score >= 70 else 'low'
        }

        # Check match quality threshold
        if job_match_score < 70:
            validation_result['can_submit'] = False
            validation_result['warnings'].append(f"Job match score ({job_match_score:.1f}) below ethical threshold (70)")
            validation_result['recommendations'].append("Only apply to jobs with strong match scores to maintain quality")

        # Check application volume
        if application_count_today >= 10:
            validation_result['can_submit'] = False
            validation_result['warnings'].append(f"Daily application limit reached ({application_count_today}/10)")
            validation_result['recommendations'].append("Focus on quality applications rather than quantity")

        # Check customization
        if customization_level not in ['high', 'medium']:
            validation_result['warnings'].append("Application customization level insufficient")
            validation_result['recommendations'].append("Ensure each application is meaningfully customized for the specific role")

        # Log ethical check
        self._log_ethical_check('application_automation', validation_result)

        return validation_result

    def manage_data_consent(self, student_id: str, data_types: List[str], purpose: str,
                           retention_period: str = "2 years") -> str:
        """
        Manage data consent and generate consent record
        """
        consent_id = hashlib.sha256(f"{student_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]

        consent_record = {
            'consent_id': consent_id,
            'student_id': student_id,
            'data_types': data_types,
            'purpose': purpose,
            'granted_at': datetime.now().isoformat(),
            'retention_period': retention_period,
            'consent_withdrawn': False,
            'compliance': ['POPIA', 'GDPR'],
            'data_processing_details': {
                'encryption': 'AES-256',
                'storage_location': 'South Africa',
                'access_control': 'Role-based',
                'audit_trail': 'Enabled'
            }
        }

        self.consent_records[consent_id] = consent_record

        # Log consent
        self._log_ethical_check('data_privacy', {
            'action': 'consent_granted',
            'consent_id': consent_id,
            'student_id': student_id
        })

        return consent_id

    def withdraw_consent(self, consent_id: str) -> bool:
        """
        Withdraw data consent and mark for deletion
        """
        if consent_id in self.consent_records:
            self.consent_records[consent_id]['consent_withdrawn'] = True
            self.consent_records[consent_id]['withdrawn_at'] = datetime.now().isoformat()

            self._log_ethical_check('data_privacy', {
                'action': 'consent_withdrawn',
                'consent_id': consent_id
            })

            return True

        return False

    def generate_ethical_disclosure(self, service_type: str, student_name: str = "Student") -> str:
        """
        Generate appropriate ethical disclosure statement
        """
        disclosures = {
            'cv_optimization': f"{student_name} acknowledges that CV optimization suggestions were generated with AI assistance to improve presentation while maintaining complete accuracy of all information.",

            'interview_practice': f"{student_name} has practiced interview responses using AI-powered guidance tools to improve communication skills and response structure.",

            'job_matching': f"Job recommendations were enhanced using AI algorithms to identify suitable opportunities based on skills and preferences.",

            'general': f"This career assistance service uses AI technology to provide guidance and recommendations while ensuring all information remains accurate and authentic."
        }

        return disclosures.get(service_type, disclosures['general'])

    def get_ethical_audit_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate ethical audit report for specified period
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        recent_logs = [
            log for log in self.ethical_audit_log
            if datetime.fromisoformat(log['timestamp']).timestamp() > cutoff_date
        ]

        report = {
            'period_days': days,
            'total_checks': len(recent_logs),
            'compliance_rate': 0.0,
            'warnings_count': 0,
            'critical_issues': 0,
            'category_breakdown': {},
            'recommendations': []
        }

        if recent_logs:
            compliant_checks = sum(1 for log in recent_logs if log.get('ethical_compliant', True))
            report['compliance_rate'] = (compliant_checks / len(recent_logs)) * 100

            report['warnings_count'] = sum(len(log.get('warnings', [])) for log in recent_logs)
            report['critical_issues'] = sum(1 for log in recent_logs if not log.get('ethical_compliant', True))

            # Category breakdown
            for log in recent_logs:
                category = log.get('category', 'unknown')
                if category not in report['category_breakdown']:
                    report['category_breakdown'][category] = 0
                report['category_breakdown'][category] += 1

        # Generate recommendations
        if report['compliance_rate'] < 95:
            report['recommendations'].append("Review and strengthen ethical validation processes")

        if report['critical_issues'] > 0:
            report['recommendations'].append("Address critical ethical compliance issues immediately")

        if report['warnings_count'] > len(recent_logs) * 0.1:
            report['recommendations'].append("Investigate high warning frequency and improve user guidance")

        return report

    def _log_ethical_check(self, category: str, result: Dict[str, Any]):
        """
        Log ethical compliance check
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'ethical_compliant': result.get('ethical_compliant', True),
            'warnings': result.get('warnings', []),
            'recommendations': result.get('recommendations', []),
            'details': result
        }

        self.ethical_audit_log.append(log_entry)

        # Keep only last 1000 entries
        if len(self.ethical_audit_log) > 1000:
            self.ethical_audit_log = self.ethical_audit_log[-1000:]

    def get_guideline_summary(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of ethical guidelines
        """
        if category:
            return self.guidelines.get(category, {})

        return {
            'guidelines': self.guidelines,
            'active_consents': len([c for c in self.consent_records.values() if not c.get('consent_withdrawn', False)]),
            'total_audits': len(self.ethical_audit_log),
            'last_updated': datetime.now().isoformat()
        }

# Global ethical guidelines instance
ethical_guidelines = EthicalGuidelines()
