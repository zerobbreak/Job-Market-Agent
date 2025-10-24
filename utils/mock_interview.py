"""
Mock Interview Simulator
Conduct realistic mock interviews with AI interviewer and real-time feedback
"""

import os
from datetime import datetime
from .scraping import extract_job_keywords
from agents import interview_prep_agent


class MockInterviewSimulator:
    """
    Conduct realistic mock interviews with AI interviewer
    """
    def __init__(self, job_role, company, student_profile=None):
        self.role = job_role
        self.company = company
        self.student_profile = student_profile or {}
        self.questions = []
        self.responses = []
        self.feedback = []
        self.session_start = None
        self.session_end = None

    def start_interview(self, student_name):
        """
        Begin mock interview session
        """
        self.session_start = datetime.now()

        greeting = f"Hello {student_name}, thank you for interviewing with {self.company} for the {self.role} position. Let's begin."

        # Generate dynamic questions based on role and company
        self.questions = self._generate_interview_questions()

        print("\n" + "="*80)
        print("🎭 MOCK INTERVIEW SESSION STARTED")
        print("="*80)
        print(greeting)
        print(f"\n📋 Interview for: {self.role} at {self.company}")
        print(f"👤 Candidate: {student_name}")
        print(f"❓ Questions prepared: {len(self.questions)}")
        print("="*80)

        return greeting

    def conduct_interview(self, get_response_callback=None):
        """
        Conduct the full interview session
        """
        if not get_response_callback:
            # Default to console input
            get_response_callback = self._get_console_response

        for i, question in enumerate(self.questions, 1):
            print(f"\n🎯 Question {i}/{len(self.questions)}:")
            print(f"   {question}")

            # Get student response
            response = get_response_callback(question)
            self.responses.append({
                'question_number': i,
                'question': question,
                'response': response,
                'timestamp': datetime.now()
            })

            # Real-time feedback
            print("\n💬 Analyzing your response...")
            instant_feedback = self.analyze_response(question, response)
            self.feedback.append(instant_feedback)

            print("\n📊 INSTANT FEEDBACK:")
            print("-" * 40)
            print(f"Overall Score: {instant_feedback.get('overall_score', 'N/A')}/50")
            print(f"Strengths: {instant_feedback.get('strengths', 'N/A')}")
            print(f"Improvements: {instant_feedback.get('improvements', 'N/A')}")

            # Optional: AI asks follow-up question
            if instant_feedback.get('needs_followup', False):
                followup = self._generate_followup(question, response)
                print(f"\n🔄 Follow-up Question:")
                print(f"   {followup}")

                followup_response = get_response_callback(followup)
                self.responses.append({
                    'question_number': f"{i}f",
                    'question': followup,
                    'response': followup_response,
                    'timestamp': datetime.now()
                })

                print("✅ Follow-up response recorded.")

        self.session_end = datetime.now()
        return self.generate_final_report()

    def analyze_response(self, question, response):
        """
        Provide instant AI feedback on answer quality
        """
        try:
            # For now, use a simplified analysis due to API limits
            # In production, this would use the interview_prep_agent
            analysis = self._analyze_response_fallback(question, response)
            return analysis
        except Exception as e:
            print(f"Error analyzing response: {e}")
            return self._analyze_response_fallback(question, response)

    def _analyze_response_fallback(self, question, response):
        """
        Fallback response analysis when API is unavailable
        """
        # Simple heuristic analysis
        response_length = len(response.split())
        has_specifics = any(word in response.lower() for word in ['specific', 'example', 'project', 'team', 'learned', 'challenge'])
        has_structure = any(phrase in response.lower() for phrase in ['situation', 'task', 'action', 'result', 'first', 'then', 'finally'])

        # Calculate scores
        relevance_score = 8 if len(response) > 50 else 5
        structure_score = 9 if has_structure else 6
        specificity_score = 9 if has_specifics else 6
        confidence_score = 8 if len([w for w in response.lower().split() if w in ['um', 'uh', 'like', 'you know']]) < 3 else 5
        completeness_score = 8 if response_length > 30 else 5

        overall_score = relevance_score + structure_score + specificity_score + confidence_score + completeness_score

        return {
            'overall_score': overall_score,
            'breakdown': {
                'relevance': relevance_score,
                'structure': structure_score,
                'specificity': specificity_score,
                'confidence': confidence_score,
                'completeness': completeness_score
            },
            'strengths': self._identify_strengths(response, response_length, has_specifics, has_structure),
            'improvements': self._identify_improvements(response, response_length, has_specifics, has_structure),
            'needs_followup': overall_score < 30,
            'filler_words_detected': len([w for w in response.lower().split() if w in ['um', 'uh', 'like', 'you know']])
        }

    def _identify_strengths(self, response, length, has_specifics, has_structure):
        """Identify what the candidate did well"""
        strengths = []
        if length > 50:
            strengths.append("Good response length - provided sufficient detail")
        if has_specifics:
            strengths.append("Used specific examples and concrete details")
        if has_structure:
            strengths.append("Well-structured answer with clear progression")
        if length > 30 and not any(word in response.lower() for word in ['um', 'uh']):
            strengths.append("Confident delivery with minimal filler words")

        return strengths if strengths else ["Clear and direct communication"]

    def _identify_improvements(self, response, length, has_specifics, has_structure):
        """Suggest areas for improvement"""
        improvements = []
        if length < 30:
            improvements.append("Add more detail and specific examples")
        if not has_specifics:
            improvements.append("Include concrete examples from your experience")
        if not has_structure:
            improvements.append("Use STAR method: Situation-Task-Action-Result")
        if any(word in response.lower() for word in ['um', 'uh', 'like']):
            improvements.append("Reduce filler words (um, uh, like) for more confident delivery")

        return improvements if improvements else ["Practice delivering responses more concisely"]

    def _generate_followup(self, original_question, response):
        """Generate follow-up questions based on response"""
        if len(response.split()) < 20:
            return "Can you elaborate on that answer with a specific example?"

        if "team" in response.lower():
            return "Can you tell me more about your specific role in that team?"

        if "project" in response.lower():
            return "What was the most challenging aspect of that project for you?"

        return "That's interesting. Can you give me a specific example of how you applied what you learned?"

    def _generate_interview_questions(self):
        """Generate interview questions for this role"""
        # Create a mock job posting for question generation
        mock_job = {
            'title': self.role,
            'company': self.company,
            'description': f"""
            We are looking for a {self.role} to join our team at {self.company}.
            The ideal candidate will have relevant experience in their field and strong communication skills.
            """
        }

        try:
            # Try to use the interview prep agent
            questions_text = interview_prep_agent.run(f"""
            Generate 8-10 interview questions for a {self.role} position at {self.company}:

            Include:
            - 3 Technical/Skills questions
            - 3 Behavioral questions (STAR method)
            - 2 Company-specific questions
            - 2 Situational questions

            Return as a numbered list.
            """)

            if hasattr(questions_text, 'content'):
                questions_text = questions_text.content

            # Parse the questions
            lines = questions_text.split('\n')
            questions = [line.strip() for line in lines if line.strip() and (line[0].isdigit() or line.startswith('-'))]
            questions = [q.lstrip('0123456789.- ').strip() for q in questions if q]

            if len(questions) >= 5:
                return questions[:8]  # Limit to 8 questions

        except Exception as e:
            print(f"Error generating questions with AI: {e}")

        # Fallback questions
        return self._generate_fallback_questions()

    def _generate_fallback_questions(self):
        """Generate basic fallback questions"""
        return [
            f"Can you tell me about yourself and your background in {self.role}?",
            f"What interests you about working at {self.company}?",
            f"Can you describe a challenging project you worked on and how you handled it?",
            f"How do you approach problem-solving in your work?",
            f"Tell me about a time when you worked effectively in a team.",
            f"What are your strengths and areas for development?",
            f"Where do you see yourself in 3-5 years?",
            f"Do you have any questions for us about the role or {self.company}?"
        ]

    def _get_console_response(self, question):
        """Get response from console input"""
        print("\n💭 Your Response (type your answer, press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "" and lines:  # Empty line and we have content
                break
            lines.append(line)

        response = " ".join(lines).strip()
        if not response:
            response = "I need more time to think about this question."

        return response

    def generate_final_report(self):
        """
        Comprehensive interview performance report
        """
        duration = None
        if self.session_start and self.session_end:
            duration = self.session_end - self.session_start

        report_data = {
            'session_duration': str(duration) if duration else "Unknown",
            'questions_asked': len(self.questions),
            'responses_given': len(self.responses),
            'feedback_items': len(self.feedback),
            'average_score': sum(f.get('overall_score', 0) for f in self.feedback) / len(self.feedback) if self.feedback else 0
        }

        # Generate comprehensive report
        try:
            # Simplified report generation due to API limits
            report = self._generate_final_report_fallback(report_data)
            return report
        except Exception as e:
            print(f"Error generating final report: {e}")
            return self._generate_final_report_fallback(report_data)

    def _generate_final_report_fallback(self, report_data):
        """Generate fallback final report"""
        avg_score = report_data['average_score']
        performance_level = "Excellent" if avg_score >= 40 else "Good" if avg_score >= 30 else "Needs Improvement"

        report = f"""
🎭 MOCK INTERVIEW PERFORMANCE REPORT
{"="*50}

📊 SESSION SUMMARY
   Duration: {report_data['session_duration']}
   Questions Answered: {report_data['responses_given']}
   Average Score: {avg_score:.1f}/50 ({performance_level})

🏆 OVERALL PERFORMANCE: {performance_level}

💪 STRENGTHS:
"""
        # Add strengths based on feedback
        all_strengths = []
        for feedback in self.feedback:
            strengths = feedback.get('strengths', [])
            all_strengths.extend(strengths)

        # Get unique strengths
        unique_strengths = list(set(all_strengths))
        for strength in unique_strengths[:3]:
            report += f"   ✓ {strength}\n"

        report += "\n🎯 AREAS FOR IMPROVEMENT:\n"
        all_improvements = []
        for feedback in self.feedback:
            improvements = feedback.get('improvements', [])
            all_improvements.extend(improvements)

        unique_improvements = list(set(all_improvements))
        for improvement in unique_improvements[:3]:
            report += f"   → {improvement}\n"

        report += f"""

📋 RECOMMENDATIONS:
   • Practice using the STAR method for behavioral questions
   • Prepare specific examples from your work experience
   • Work on reducing filler words for more confident delivery
   • Research the company and role thoroughly before interviews
   • Practice answering questions out loud to improve fluency

🎯 NEXT STEPS:
   • Review the questions you found challenging
   • Practice mock interviews regularly
   • Focus on improving your {unique_improvements[0] if unique_improvements else 'response structure'}
   • Consider recording yourself to analyze body language

{"="*50}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report
