import os
import markdown
from xhtml2pdf import pisa
from datetime import datetime

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
            
    def generate_pdf(self, markdown_content, output_path, template_name='professional'):
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
                print(f"⚠️ Template '{template_name}' not found, falling back to professional.")
                template_path = os.path.join(self.templates_dir, 'professional.html')
                
            with open(template_path, 'r', encoding='utf-8') as f:
                template_html = f.read()
                
            # 3. Inject Content
            # Simple string replacement for now. Jinja2 could be used for more complex needs.
            full_html = template_html.replace('{{ content }}', html_content)
            
            # 4. Generate PDF
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
