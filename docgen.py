import os
import re
import sys

def extract_comments(file_content):
    # Pattern to match the comment block
    comment_pattern = re.compile(
        r'/\*[\s\S]*?\*/',
        re.DOTALL
    )
    matches = []
    for comment_match in comment_pattern.finditer(file_content):
        comment_block = comment_match.group(0)
        # Start position after the comment block
        start_pos = comment_match.end()
        # Extract the function signature
        signature_lines = []
        pos = start_pos
        brace_or_semicolon_found = False
        while pos < len(file_content):
            line_end = file_content.find('\n', pos)
            if line_end == -1:
                line_end = len(file_content)
            line = file_content[pos:line_end].strip()
            pos = line_end + 1
            if not line:
                continue
            # Check for the presence of '{' or ';' at the end of the line
            if '{' in line:
                # Remove everything starting from '{'
                line = line.split('{')[0].rstrip()
                signature_lines.append(line)
                brace_or_semicolon_found = True
                break
            elif ';' in line:
                signature_lines.append(line)
                brace_or_semicolon_found = True
                break
            else:
                signature_lines.append(line)
        if brace_or_semicolon_found:
            signature = ' '.join(signature_lines)
            matches.append((comment_block, signature.strip()))
    return matches

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
    html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Function Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { text-align: center; }
        .function { margin-bottom: 50px; }
        .signature { font-family: monospace; background-color: #f0f0f0; padding: 10px; border-left: 4px solid #ccc; white-space: pre; }
        h2 { color: #2c3e50; }
        h3 { color: #34495e; }
        ul { list-style-type: disc; margin-left: 20px; }
        p { text-align: justify; }
    </style>
</head>
<body>
    <h1>Function Documentation</h1>
'''
    for doc in docs:
        html += f'''
    <div class="function">
        <h2>{doc.get('function', 'Unnamed Function')}</h2>
        <pre class="signature">{doc.get('signature', 'Signature not found')}</pre>
'''
        if doc['description']:
            html += f'''
        <h3>Description:</h3>
        <p>{doc['description']}</p>
'''
        if doc['params']:
            html += '''
        <h3>Parameters:</h3>
        <ul>
'''
            for param in doc['params']:
                param_parts = param.split(':', 1)
                if len(param_parts) == 2:
                    param_name = param_parts[0].strip()
                    param_desc = param_parts[1].strip()
                    html += f'            <li><strong>{param_name}:</strong> {param_desc}</li>\n'
                else:
                    html += f'            <li>{param.strip()}</li>\n'
            html += '        </ul>\n'
        if doc['returns']:
            html += f'''
        <h3>Returns:</h3>
        <p>{doc['returns']}</p>
'''
        html += '    </div>\n'
    html += '''
</body>
</html>
'''
    return html

def process_files(directory):
    docs = []
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(('.c', '.h')):
                filepath = os.path.join(root, filename)
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    extracted = extract_comments(content)
                    for comment_block, signature in extracted:
                        doc = parse_comment(comment_block)
                        doc['signature'] = signature
                        docs.append(doc)
    return docs

def main():
    if len(sys.argv) < 2:
        print('Usage: python generate_docs.py /path/to/your/c/code')
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f'Error: {directory} is not a valid directory.')
        sys.exit(1)

    docs = process_files(directory)
    if not docs:
        print('No documentation comments found.')
        sys.exit(0)

    html_content = generate_html(docs)
    with open('documentation.html', 'w', encoding='utf-8') as output_file:
        output_file.write(html_content)

    print('Documentation generated successfully in documentation.html')

if __name__ == '__main__':
    main()
