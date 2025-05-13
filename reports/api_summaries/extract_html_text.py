import os
from bs4 import BeautifulSoup

# Directory containing the HTML files
HTML_DIR = 'VmbPy_Function_Reference'

# List all files in the directory
for filename in os.listdir(HTML_DIR):
    if filename.endswith('.html'):
        html_path = os.path.join(HTML_DIR, filename)
        txt_path = os.path.join(HTML_DIR, os.path.splitext(filename)[0] + '.txt')
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            # Extract all visible text, including code and tables
            text = soup.get_text(separator='\n', strip=True)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
print('Extraction complete. .txt files saved in', HTML_DIR) 