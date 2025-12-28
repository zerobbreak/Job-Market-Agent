import os
import markdown
from xhtml2pdf import pisa
from datetime import datetime

try:
    from weasyprint import HTML
    _WEASY_AVAILABLE = True
except Exception:
    _WEASY_AVAILABLE = False

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except Exception:
    _PLAYWRIGHT_AVAILABLE = False

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
            # 1. Generate HTML Content
            full_html = self.generate_html(markdown_content, template_name, header, sections)
            
            # 2. Try Playwright (Best Quality - Chrome Rendering)
            if _PLAYWRIGHT_AVAILABLE:
                try:
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        page = browser.new_page()
                        page.set_content(full_html)
                        # Add some wait to ensure fonts/styles load
                        page.wait_for_load_state('networkidle', timeout=3000) 
                        page.pdf(
                            path=output_path, 
                            format='A4', 
                            print_background=True, 
                            margin={'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'}
                        )
                        browser.close()
                    print(f"✓ PDF generated (Playwright): {output_path}")
                    return True
                except Exception as e:
                    print(f"⚠️ Playwright failed: {e}, falling back to WeasyPrint/xhtml2pdf")

            # 3. Try WeasyPrint (Good Quality - CSS Paged Media)
            if _WEASY_AVAILABLE:
                try:
                    HTML(string=full_html).write_pdf(output_path)
                    print(f"✓ PDF generated (WeasyPrint): {output_path}")
                    return True
                except Exception as e:
                    print(f"⚠️ WeasyPrint failed: {e}, falling back to xhtml2pdf")
            
            # 4. Fallback to xhtml2pdf (Basic Quality)
            with open(output_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    src=full_html,
                    dest=pdf_file,
                    encoding='utf-8'
                )
            if pisa_status.err:
                print(f"❌ PDF generation error: {pisa_status.err}")
                return False
            print(f"✓ PDF generated (xhtml2pdf): {output_path}")
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
                    if 'summary</h2>' not in main_html.lower():
                        main_html = f"<h2>Summary</h2>{summary_html}\n" + main_html
                exp = sections.get('experience_html')
                if isinstance(exp, str) and exp:
                    if 'experience</h2>' not in main_html.lower():
                        main_html = f"<h2>Experience</h2>{exp}\n" + main_html
                projects = sections.get('projects_html')
                if isinstance(projects, str) and projects:
                    if 'projects</h2>' not in main_html.lower():
                        main_html = f"<h2>Projects</h2>{projects}\n" + main_html
                edu = sections.get('education_html')
                if isinstance(edu, str) and edu:
                    if 'education</h2>' not in main_html.lower():
                        main_html = f"<h2>Education</h2>{edu}\n" + main_html

            full_html = template_html
            full_html = full_html.replace('{{ sidebar }}', sidebar_html)
            full_html = full_html.replace('{{ main }}', main_html)
            full_html = full_html.replace('{{ content }}', main_html)
            header = header or {}
            contact_extra = ''
            try:
                base_keys = {'name','title','email','phone','location','date'}
                items = []
                for k, v in header.items():
                    if k in base_keys:
                        continue
                    val = str(v).strip()
                    if not val:
                        continue
                    label = k.replace('_',' ').title()
                    if val.startswith('http'):
                        items.append(f"<div><strong>{markdown.util.AtomicString(label)}</strong> <a href='{markdown.util.AtomicString(val)}'>{markdown.util.AtomicString(val)}</a></div>")
                    else:
                        items.append(f"<div><strong>{markdown.util.AtomicString(label)}</strong> {markdown.util.AtomicString(val)}</div>")
                contact_extra = ''.join(items)
            except Exception:
                contact_extra = ''
            full_html = full_html.replace('{{ contact_extra }}', contact_extra)
            for key in ['name', 'title', 'email', 'phone', 'location', 'date']:
                full_html = full_html.replace(f'{{{{ {key} }}}}', str(header.get(key, '')))
            return full_html
        except Exception as e:
            print(f"❌ Error generating HTML: {e}")
            return markdown.markdown(markdown_content)
