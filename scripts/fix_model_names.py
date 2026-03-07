import os

def replace_in_file(filepath, old_str, new_str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if old_str in content:
            new_content = content.replace(old_str, new_str)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated: {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")

def main():
    backend_dir = r"c:\Users\uthac\OneDrive\Documents\programing\Python\Job-Market-Agent\backend"
    for root, dirs, files in os.walk(backend_dir):
        if '.venv' in root or '__pycache__' in root or '.git' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                replace_in_file(os.path.join(root, file), 'gemini-2.0-flash', 'gemini-2.5-flash')

if __name__ == "__main__":
    main()

