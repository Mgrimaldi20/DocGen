import os
import re
import sys
import multiprocessing

def extract_comments_and_signature(content):
    # Precompiled regex patterns
    comment_pattern = re.compile(
        r'/\*[\s\S]*?\*/',
        re.DOTALL
    )

    # List to store documentation entries
    docs = []

    # Find all comment blocks
    for comment_match in comment_pattern.finditer(content):
        comment_block = comment_match.group(0)
        # Start position after the comment block
        start_pos = comment_match.end()

        # Extract the function signature
        signature_lines = []
        pos = start_pos
        brace_or_semicolon_found = False
        while pos < len(content):
            line_end = content.find('\n', pos)
            if line_end == -1:
                line_end = len(content)
            line = content[pos:line_end].strip()
            pos = line_end + 1
            if not line:
                continue
            # Check for the presence of '{' or ';'
            if '{' in line or ';' in line:
                # Remove everything starting from '{' or ';'
                line = re.split(r'[{\;]', line)[0].rstrip()
                signature_lines.append(line)
                brace_or_semicolon_found = True
                break
            else:
                signature_lines.append(line)
        if brace_or_semicolon_found:
            signature = ' '.join(signature_lines)
            doc = parse_comment(comment_block)
            doc['signature'] = signature.strip()
            docs.append(doc)
    return docs

def parse_comment(comment_block):
    # Remove the comment delimiters
    comment_block = comment_block.strip()
    if comment_block.startswith('/*'):
        comment_block = comment_block[2:]
    if comment_block.endswith('*/'):
        comment_block = comment_block[:-2]
    # Split into lines
    lines = comment_block.strip().split('\n')

    # Initialize variables
    doc = {
        'function': '',
        'description': '',
        'params': [],
        'returns': '',
    }

    # Variables to keep track of the current section
    current_section = 'description'

    i = 0
    while i < len(lines):
        # Remove leading asterisks, whitespaces, and tabs
        line = lines[i].lstrip(' *\t')

        # Skip empty lines or lines that contain only an asterisk
        if line.strip() == '':
            i += 1
            continue

        # Check for section headers
        if line.startswith('Function:'):
            doc['function'] = line[len('Function:'):].strip()
            current_section = 'description'
        elif line.startswith('Returns:'):
            current_section = 'returns'
            doc['returns'] = line[len('Returns:'):].strip()
        elif re.match(r'\b\w+\b:', line):
            current_section = 'params'
            param_line = line
            # Handle multi-line parameter descriptions
            i += 1
            while i < len(lines):
                next_line = lines[i].lstrip(' *\t')
                if next_line.strip() == '':
                    i += 1
                    continue
                if re.match(r'\b\w+\b:', next_line) or next_line.startswith('Returns:'):
                    break
                param_line += ' ' + next_line.strip()
                i += 1
            doc['params'].append(param_line.strip())
            continue  # Skip the increment at the end
        else:
            if current_section == 'description':
                doc['description'] += line + ' '
            elif current_section == 'returns':
                doc['returns'] += ' ' + line
            elif current_section == 'params' and doc['params']:
                # Append to the last parameter description
                doc['params'][-1] += ' ' + line

        i += 1

    # Clean up fields
    doc['description'] = doc['description'].strip()
    doc['returns'] = doc['returns'].strip()
    doc['params'] = [param.strip() for param in doc['params']]

    return doc

def generate_html(docs):
    # Generate the sidebar index
    sidebar = '''<div class="sidebar">
    <h1>Navigation</h1>
    <ul>
'''

    content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Function Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; display: flex; height: 100vh; background: #f4f4f4; }
        .sidebar { width: 300px; padding: 20px; background: #f4f4f4; border-right: 1px solid #ccc; overflow-y: auto; height: 100%; }
        .bar2 { padding: 20px; background: #f4f4f4; height: 100%; width: 90% }
        .content { flex-grow: 1; padding: 20px; overflow-y: auto; }
        .function { margin-bottom: 50px; }
        .signature { font-family: monospace; background-color: #f0f0f0; padding: 10px; border-left: 4px solid #ccc; white-space: pre; }
        h1 { color: #2c3e50; }
        h2 { color: #2c3e50; }
        h3 { color: #34495e; }
        ul { list-style-type: disc; margin-left: 20px; }
        p { text-align: justify; }
        .function-name { margin: 0; padding: 0; }
    </style>
</head>
<body>
    <div class="bar2">
        <h1>Function Documentation</h1>
        <ul>
'''

    for doc in docs:
        func_id = doc.get('function', 'Unnamed Function').replace(' ', '-').lower()
        sidebar += f'            <li><a href="#{func_id}">{doc.get('function', 'Unnamed Function')}</a></li>\n'
        content += f'''
    <div class="function" id="{func_id}">
        <h2 class="function-name">{doc.get('function', 'Unnamed Function')}</h2>
        <pre class="signature">{doc.get('signature', 'Signature not found')}</pre>
'''
        if doc['description']:
            content += f'''
        <h3>Description:</h3>
        <p>{doc['description']}</p>
'''
        if doc['params']:
            content += '''
        <h3>Parameters:</h3>
        <ul>
'''
            for param in doc['params']:
                param_parts = param.split(':', 1)
                if len(param_parts) == 2:
                    param_name = param_parts[0].strip()
                    param_desc = param_parts[1].strip()
                    content += f'            <li><strong>{param_name}:</strong> {param_desc}</li>\n'
                else:
                    content += f'            <li>{param.strip()}</li>\n'
            content += '        </ul>\n'
        if doc['returns']:
            content += f'''
        <h3>Returns:</h3>
        <p>{doc['returns']}</p>
'''
        content += '    </div>\n'
    sidebar += '        </ul>\n    </div>\n'
    content += '    </div>\n</body>\n</html>'

    return sidebar + content

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        try:
            content = file.read()
            docs = extract_comments_and_signature(content)
            return docs
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []

def process_files_in_parallel(file_paths):
    pool = multiprocessing.Pool()
    results = pool.map(process_file, file_paths)
    pool.close()
    pool.join()

    # Flatten the list of lists
    all_docs = [doc for sublist in results for doc in sublist]
    return all_docs

def collect_file_paths(directory):
    excluded_dirs = {'libs', 'lib'}
    compatible_files = ('.c', '.h')
    file_paths = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for filename in files:
            if filename.endswith(compatible_files):
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)
    return file_paths

def main():
    if len(sys.argv) < 2:
        print('Usage: python generate_docs.py /path/to/your/c/code')
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f'Error: {directory} is not a valid directory.')
        sys.exit(1)

    print("Collecting file paths...")
    file_paths = collect_file_paths(directory)
    if not file_paths:
        print('No compatible files found.')
        sys.exit(0)

    print(f"Processing {len(file_paths)} files using {multiprocessing.cpu_count()} cores...")
    docs = process_files_in_parallel(file_paths)

    if not docs:
        print('No documentation comments found.')
        sys.exit(0)

    print("Generating HTML documentation...")
    html_content = generate_html(docs)
    with open('documentation.html', 'w', encoding='utf-8') as output_file:
        output_file.write(html_content)

    print('Documentation generated successfully in documentation.html')

if __name__ == '__main__':
    main()
    