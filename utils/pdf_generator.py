import os
import markdown
from xhtml2pdf import pisa
from datetime import datetime
try:
    from weasyprint import HTML
    _WEASY_AVAILABLE = True
except Exception:
    _WEASY_AVAILABLE = False

class PDFGenerator:
    """
    Generates PDF files from Markdown content using HTML templates.
    """
    
    def __init__(self, templates_dir=None):
        if templates_dir is None:
            # Default to 'utils/templates' relative to this file
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.templates_dir = os.path.join(base_dir, 'templates')
        else:
            self.templates_dir = templates_dir
            
    def generate_pdf(self, markdown_content, output_path, template_name='modern', header=None, sections=None):
        """
        Convert Markdown content to PDF using a specific template.
        
        Args:
            markdown_content (str): The CV content in Markdown format
            output_path (str): Path to save the generated PDF
            template_name (str): Name of the template to use (modern, professional, academic)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # 1. Convert Markdown to HTML
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
            
            # 2. Load Template
            template_file = f"{template_name.lower()}.html"
            template_path = os.path.join(self.templates_dir, template_file)
            
            if not os.path.exists(template_path):
                print(f"⚠️ Template '{template_name}' not found, falling back to modern.")
                template_path = os.path.join(self.templates_dir, 'modern.html')
                
                # Double fallback
                if not os.path.exists(template_path):
                     template_path = os.path.join(self.templates_dir, 'professional.html')
                
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()
                
            # 3. Inject Content
            # Simple string replacement for now. Jinja2 could be used for more complex needs.
            sidebar_html = ''
            main_html = html_content
            if isinstance(sections, dict):
                skills = sections.get('skills') or []
                if isinstance(skills, (list, tuple)) and skills:
                    skill_tags = ''.join([f"<span class='skill-tag'>{markdown.util.AtomicString(str(s))}</span>" for s in skills])
                    sidebar_html += f"<h2>Skills</h2><div>{skill_tags}</div>"
                summary = sections.get('summary')
                if isinstance(summary, str) and summary.strip():
                    summary_html = markdown.markdown(summary)
                    main_html = f"<h2>Summary</h2>{summary_html}" + main_html
                exp = sections.get('experience_html')
                if isinstance(exp, str) and exp:
                    main_html = f"<h2>Experience</h2>{exp}" + main_html
                projects = sections.get('projects_html')
                if isinstance(projects, str) and projects:
                    main_html = f"<h2>Projects</h2>{projects}" + main_html
                edu = sections.get('education_html')
                if isinstance(edu, str) and edu:
                    main_html = f"<h2>Education</h2>{edu}" + main_html
            full_html = template_html
            full_html = full_html.replace('{{ sidebar }}', sidebar_html)
            full_html = full_html.replace('{{ main }}', main_html)
            full_html = full_html.replace('{{ content }}', main_html)
            header = header or {}
            for key in ['name', 'title', 'email', 'phone', 'location', 'date']:
                full_html = full_html.replace(f'{{{{ {key} }}}}', str(header.get(key, '')))
            
            if _WEASY_AVAILABLE:
                try:
                    HTML(string=full_html).write_pdf(output_path)
                    print(f"✓ PDF generated (WeasyPrint): {output_path}")
                    return True
                except Exception as e:
                    print(f"⚠️ WeasyPrint failed: {e}, falling back to xhtml2pdf")
            with open(output_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    src=full_html,
                    dest=pdf_file,
                    encoding='utf-8'
                )
            if pisa_status.err:
                print(f"❌ PDF generation error: {pisa_status.err}")
                return False
            print(f"✓ PDF generated: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error generating PDF: {e}")
            return False

    def generate_html(self, markdown_content, template_name='modern', header=None, sections=None):
        try:
            html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
            template_file = f"{template_name.lower()}.html"
            template_path = os.path.join(self.templates_dir, template_file)
            if not os.path.exists(template_path):
                template_path = os.path.join(self.templates_dir, 'modern.html')
                if not os.path.exists(template_path):
                    template_path = os.path.join(self.templates_dir, 'professional.html')
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()

            sidebar_html = ''
            main_html = html_content
            if isinstance(sections, dict):
                skills = sections.get('skills') or []
                if isinstance(skills, (list, tuple)) and skills:
                    skill_tags = ''.join([f"<span class='skill-tag'>{markdown.util.AtomicString(str(s))}</span>" for s in skills])
                    sidebar_html += f"<h2>Skills</h2><div>{skill_tags}</div>"
                summary = sections.get('summary')
                if isinstance(summary, str) and summary.strip():
                    summary_html = markdown.markdown(summary)
                    main_html = f"<h2>Summary</h2>{summary_html}" + main_html
                exp = sections.get('experience_html')
                if isinstance(exp, str) and exp:
                    main_html = f"<h2>Experience</h2>{exp}" + main_html
                projects = sections.get('projects_html')
                if isinstance(projects, str) and projects:
                    main_html = f"<h2>Projects</h2>{projects}" + main_html
                edu = sections.get('education_html')
                if isinstance(edu, str) and edu:
                    main_html = f"<h2>Education</h2>{edu}" + main_html

            full_html = template_html
            full_html = full_html.replace('{{ sidebar }}', sidebar_html)
            full_html = full_html.replace('{{ main }}', main_html)
            full_html = full_html.replace('{{ content }}', main_html)
            header = header or {}
            for key in ['name', 'title', 'email', 'phone', 'location', 'date']:
                full_html = full_html.replace(f'{{{{ {key} }}}}', str(header.get(key, '')))
            return full_html
        except Exception as e:
            print(f"❌ Error generating HTML: {e}")
            return markdown.markdown(markdown_content)
