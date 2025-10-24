"""
South African Customizations for Job Market AI Agent
Tailored for SA youth unemployment realities
"""

from typing import Dict, List, Any, Optional
from .knowledge_base import knowledge_base

class SACustomizations:
    """
    South African specific customizations for job market system
    """

    def __init__(self):
        self.customizations = {
            'transport_consideration': {
                'calculate_commute_cost': True,
                'prefer_remote_jobs': True,
                'transport_subsidy_jobs': 'prioritize',
                'commute_zones': {
                    'Johannesburg': {'cost_range': 'R800-1,500', 'reliability': 'medium'},
                    'Cape Town': {'cost_range': 'R400-800', 'reliability': 'medium'},
                    'Pretoria': {'cost_range': 'R300-600', 'reliability': 'high'},
                    'Durban': {'cost_range': 'R300-700', 'reliability': 'medium'}
                }
            },
            'skills_gap_programs': {
                'recommend_learnerships': True,
                'seta_programs': True,  # Skills Education Training Authorities
                'yes_initiative': True,  # Youth Employment Service
                'programs': {
                    'learnerships': {
                        'banking_seta': 'R3,500/month',
                        'services_seta': 'R3,000/month',
                        'manufacturing_seta': 'R4,000/month',
                        'duration': '12-24 months',
                        'benefits': ['paid training', 'work experience', 'NQF qualification']
                    },
                    'yes_initiative': {
                        'target': 'graduates under 35',
                        'salary_range': 'R6,000-12,000/month',
                        'companies': ['Standard Bank', 'Nedbank', 'FNB', 'Government departments'],
                        'benefits': ['subsidized employment', 'training', 'permanent placement potential']
                    }
                }
            },
            'salary_expectations': {
                'entry_level_range': 'R8,000 - R15,000',  # Realistic for SA
                'include_benefits': ['transport allowance', 'medical aid', 'provident fund', 'leave days'],
                'regional_adjustments': {
                    'johannesburg': {'multiplier': 1.2, 'reason': 'higher living costs'},
                    'cape_town': {'multiplier': 1.1, 'reason': 'higher living costs'},
                    'pretoria': {'multiplier': 1.0, 'reason': 'baseline'},
                    'other_cities': {'multiplier': 0.9, 'reason': 'lower cost of living'}
                }
            },
            'languages': {
                'support': ['English', 'Afrikaans', 'Zulu', 'Xhosa', 'Sotho', 'Tswana', 'Tsonga', 'Venda', 'Ndebele'],
                'multilingual_interface': True,
                'workplace_languages': {
                    'english': {'usage': 'universal', 'proficiency_required': 'business'},
                    'afrikaans': {'usage': 'western_cape, northern_cape', 'proficiency_required': 'conversational'},
                    'zulu': {'usage': 'kzn, gauteng', 'proficiency_required': 'conversational'},
                    'xhosa': {'usage': 'eastern_cape, western_cape', 'proficiency_required': 'conversational'},
                    'sotho': {'usage': 'free_state, gauteng', 'proficiency_required': 'conversational'}
                }
            },
            'first_job_focus': {
                'emphasize_learnerships': True,
                'internship_opportunities': True,
                'graduate_programs': True,
                'entry_points': {
                    'learnerships': {
                        'duration': '12-24 months',
                        'salary_range': 'R3,000-4,500/month',
                        'benefits': ['paid training', 'work experience', 'NQF qualification', 'permanent job potential'],
                        'target': 'school leavers, TVET graduates'
                    },
                    'internships': {
                        'duration': '12-24 months',
                        'salary_range': 'R6,000-12,000/month',
                        'benefits': ['structured development', 'mentorship', 'permanent placement', 'market salary'],
                        'target': 'university graduates'
                    },
                    'graduate_programs': {
                        'duration': '12-24 months',
                        'salary_range': 'R8,000-15,000/month',
                        'benefits': ['fast-tracked career', 'leadership development', 'networking', 'permanent role'],
                        'target': 'high-performing graduates'
                    }
                }
            }
        }

    def get_transport_considerations(self, location: str = None) -> Dict[str, Any]:
        """Get transport-related recommendations for job matching"""
        transport_data = self.customizations['transport_consideration']

        if location and location.lower() in transport_data['commute_zones']:
            city_data = transport_data['commute_zones'][location.lower()]
            return {
                'location': location,
                'commute_cost': city_data['cost_range'],
                'reliability': city_data['reliability'],
                'recommendations': [
                    'Prioritize remote/hybrid positions',
                    'Look for transport allowance benefits',
                    'Consider accommodation closer to workplace',
                    'Check company shuttle services'
                ],
                'savings_potential': 'R500-1,000/month with remote work'
            }

        return {
            'general_advice': 'Transport costs 15-25% of salary in major cities',
            'recommendations': [
                'Prioritize remote work opportunities',
                'Calculate commute costs before accepting offers',
                'Negotiate transport allowance in salary discussions'
            ]
        }

    def get_skills_development_recommendations(self, student_profile: Dict) -> Dict[str, Any]:
        """Get skills development program recommendations"""
        programs = self.customizations['skills_gap_programs']['programs']

        recommendations = {
            'eligible_programs': [],
            'salary_expectations': {},
            'next_steps': []
        }

        # Check learnership eligibility (typically for TVET/school leavers)
        if student_profile.get('education_level') in ['matric', 'tvet', 'nqf_4']:
            recommendations['eligible_programs'].append('learnerships')
            recommendations['salary_expectations']['learnerships'] = programs['learnerships']
            recommendations['next_steps'].append('Apply for SETA learnerships through company websites')

        # Check internship eligibility (university graduates)
        if student_profile.get('education_level') in ['degree', 'diploma', 'honours']:
            recommendations['eligible_programs'].extend(['internships', 'yes_initiative'])
            recommendations['salary_expectations']['internships'] = programs['yes_initiative']
            recommendations['next_steps'].extend([
                'Apply for YES internships at major banks',
                'Check company graduate programs',
                'Register on YES initiative portal'
            ])

        return recommendations

    def adjust_salary_expectations(self, base_salary: str, location: str = None) -> Dict[str, Any]:
        """Adjust salary expectations based on SA market realities"""
        salary_config = self.customizations['salary_expectations']

        adjusted = {
            'original_range': base_salary,
            'adjusted_range': salary_config['entry_level_range'],
            'benefits_to_include': salary_config['include_benefits'],
            'location_adjustment': None,
            'realistic_expectations': [
                'Entry-level positions: R8,000-15,000/month',
                'Include benefits in total compensation',
                'Negotiate based on cost of living',
                'Consider learnerships for experience building'
            ]
        }

        # Apply regional adjustments
        if location:
            location_key = location.lower().replace(' ', '_')
            if location_key in salary_config['regional_adjustments']:
                adjustment = salary_config['regional_adjustments'][location_key]
                adjusted['location_adjustment'] = adjustment
                adjusted['regional_notes'] = f"{location}: {adjustment['reason']}"

        return adjusted

    def get_language_recommendations(self, student_profile: Dict) -> Dict[str, Any]:
        """Get language-related recommendations for SA workplace"""
        language_config = self.customizations['languages']

        recommendations = {
            'primary_language': 'English (required for most professional roles)',
            'additional_languages': [],
            'proficiency_levels': {},
            'cultural_tips': [
                'Code-switching is common in SA workplaces',
                'Show cultural awareness and adaptability',
                'English is sufficient for most tech/finance roles'
            ]
        }

        # Recommend languages based on target regions
        target_regions = student_profile.get('preferred_regions', ['gauteng'])
        for region in target_regions:
            region = region.lower()
            for lang, details in language_config['workplace_languages'].items():
                if region in details['usage'] or details['usage'] == 'universal':
                    if lang not in recommendations['additional_languages']:
                        recommendations['additional_languages'].append(lang)
                        recommendations['proficiency_levels'][lang] = details['proficiency_required']

        return recommendations

    def get_first_job_strategy(self, student_profile: Dict) -> Dict[str, Any]:
        """Develop first job strategy for recent graduates"""
        first_job_config = self.customizations['first_job_focus']

        strategy = {
            'recommended_pathways': [],
            'timeline': '6-12 months to first job',
            'action_plan': [],
            'salary_progression': {}
        }

        # Determine education level and recommend appropriate pathways
        education_level = student_profile.get('education_level', 'degree')

        if education_level in ['matric', 'tvet']:
            strategy['recommended_pathways'].append('learnerships')
            strategy['action_plan'].extend([
                'Apply for SETA learnerships immediately',
                'Consider TVET college for skills upgrade',
                'Build practical experience through volunteering'
            ])
            strategy['salary_progression'] = {
                'starting': 'R3,000-4,500/month',
                'after_12_months': 'R6,000-8,000/month',
                'after_24_months': 'R8,000-12,000/month'
            }

        elif education_level in ['degree', 'diploma']:
            strategy['recommended_pathways'].extend(['internships', 'graduate_programs'])
            strategy['action_plan'].extend([
                'Apply for YES internships at major corporations',
                'Target graduate programs with fast-track potential',
                'Network through university career fairs',
                'Customize CV for graduate positions'
            ])
            strategy['salary_progression'] = {
                'starting': 'R8,000-12,000/month',
                'after_12_months': 'R12,000-18,000/month',
                'after_24_months': 'R18,000-25,000/month'
            }

        return strategy

    def enhance_job_matching(self, job: Dict, student_profile: Dict) -> Dict:
        """Enhance job matching with SA-specific considerations"""
        enhanced_job = job.copy()

        # Add transport considerations
        transport_info = self.get_transport_considerations(job.get('location', ''))
        enhanced_job['transport_considerations'] = transport_info

        # Add salary reality check
        salary_info = self.adjust_salary_expectations(
            job.get('salary_range', 'R8,000-15,000'),
            job.get('location', '')
        )
        enhanced_job['salary_realism'] = salary_info

        # Add first job suitability
        if student_profile.get('is_recent_graduate', True):
            first_job_strategy = self.get_first_job_strategy(student_profile)
            enhanced_job['first_job_suitability'] = first_job_strategy

        # Calculate SA-specific match score adjustments
        sa_score_adjustments = []

        # Remote work bonus
        if job.get('remote_work') or job.get('hybrid_work'):
            sa_score_adjustments.append({'factor': 'remote_work', 'adjustment': 10, 'reason': 'Transport savings'})

        # Learnership/Internship bonus for graduates
        if any(keyword in job.get('title', '').lower() for keyword in ['learnership', 'internship', 'graduate']):
            sa_score_adjustments.append({'factor': 'graduate_program', 'adjustment': 15, 'reason': 'First job opportunity'})

        # Transport allowance bonus
        if job.get('benefits') and any(benefit.lower().find('transport') >= 0 for benefit in job.get('benefits', [])):
            sa_score_adjustments.append({'factor': 'transport_allowance', 'adjustment': 8, 'reason': 'Transport support'})

        enhanced_job['sa_score_adjustments'] = sa_score_adjustments

        return enhanced_job

    def get_market_insights(self, student_profile: Dict) -> Dict[str, Any]:
        """Get comprehensive SA market insights for student"""
        insights = {
            'transport_reality': self.get_transport_considerations(),
            'salary_expectations': self.adjust_salary_expectations('R8,000-15,000'),
            'skills_development': self.get_skills_development_recommendations(student_profile),
            'language_considerations': self.get_language_recommendations(student_profile),
            'first_job_strategy': self.get_first_job_strategy(student_profile),
            'key_challenges': [
                '45.5% youth unemployment rate',
                'High transport costs (15-25% of salary)',
                'Competition for entry-level positions',
                'Need for work experience to get first job'
            ],
            'success_factors': [
                'Start with learnerships/internships',
                'Prioritize remote work opportunities',
                'Network through university connections',
                'Be realistic about salary expectations',
                'Focus on building experience over high salary'
            ]
        }

        return insights

# Global SA customizations instance
sa_customizations = SACustomizations()
