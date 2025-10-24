import fitz

try:
    cv_text = ""
    with fitz.open('CV.pdf') as doc:
        print(f"Opened PDF with {len(doc)} pages")
        for page_num, page in enumerate(doc, 1):
            cv_text += page.get_text()
            print(f"Read page {page_num}")
        print(f"Total text length: {len(cv_text)}")
        print("PDF reading successful!")
        print(f"First 200 characters: {cv_text[:200]}")
except Exception as e:
    print(f"Error reading PDF: {e}")
