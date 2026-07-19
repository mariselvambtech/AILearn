import glob
import os

docstring = '''"""
Test suite for the WebAI Playwright Client.

This module contains tests verifying the functionality of the Playwright 
integration, CDP accessibility tree extraction, and AI command execution.
"""\n'''

for file in glob.glob('test_*.py'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    if not content.startswith('"""'):
        with open(file, 'w', encoding='utf-8') as f:
            f.write(docstring + content)
        print(f'Updated {file}')
