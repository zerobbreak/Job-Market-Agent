"""
CV Templates Module
Defines the structural templates for different CV types.
"""

class CVTemplates:
    """
    Collection of CV templates with structural definitions.
    """
    
    MODERN = """
    # [Name]
    [Contact Info: Email | Phone | LinkedIn | Portfolio]
    
    ## SUMMARY
    [Concise, impactful summary highlighting key skills and career goals]
    
    ## SKILLS
    - **Languages:** [List]
    - **Frameworks:** [List]
    - **Tools:** [List]
    - **Soft Skills:** [List]
    
    ## TECHNICAL PROJECTS
    **[Project Name]** | [Role]
    [Link if available]
    - [Impact-driven bullet point]
    - [Tech stack used]
    
    ## PROFESSIONAL EXPERIENCE
    **[Role]** | [Company] | [Dates]
    - [Action verb] [Context] [Result/Metric]
    - [Action verb] [Context] [Result/Metric]
    
    ## EDUCATION
    **[Degree]** | [Institution] | [Year]
    - [Relevant Coursework/Honors]
    """
    
    PROFESSIONAL = """
    # [Name]
    [Contact Info: Email | Phone | LinkedIn]
    
    ## PROFESSIONAL SUMMARY
    [Formal summary of experience, leadership, and value proposition]
    
    ## PROFESSIONAL EXPERIENCE
    **[Role]** | [Company] | [Location] | [Dates]
    - [Action verb] [Context] [Result/Metric]
    - [Action verb] [Context] [Result/Metric]
    - [Action verb] [Context] [Result/Metric]
    
    ## EDUCATION
    **[Degree]** | [Institution] | [Year]
    
    ## SKILLS & CERTIFICATIONS
    - [Skill Category]: [List]
    - [Certification Name] ([Year])
    """
    
    ACADEMIC = """
    # [Name]
    [Contact Info: Email | Phone | LinkedIn | Google Scholar]
    
    ## EDUCATION
    **[Degree]** | [Institution] | [Year]
    - Thesis: [Title]
    - Advisor: [Name]
    
    ## RESEARCH EXPERIENCE
    **[Role]** | [Institution] | [Dates]
    - [Research focus and outcomes]
    
    ## PUBLICATIONS
    - [Citation format]
    
    ## TEACHING EXPERIENCE
    **[Role]** | [Institution] | [Dates]
    - [Course Name]
    
    ## PROFESSIONAL EXPERIENCE
    **[Role]** | [Company] | [Dates]
    - [Description]
    
    ## SKILLS
    - [List]
    """

    @staticmethod
    def get_template(template_name):
        """Returns the requested template structure."""
        template_name = template_name.upper()
        if hasattr(CVTemplates, template_name):
            return getattr(CVTemplates, template_name)
        return CVTemplates.PROFESSIONAL  # Default
