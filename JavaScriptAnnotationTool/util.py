import json

def update_script_js(file_name):
    # Read the sections from section_list.json
    with open(file_name, 'r') as f:
        sections = json.load(f)
    
    # Read the current script.js
    with open('scripts/script.js', 'r') as f:
        script_content = f.read()

    # Create the sections array string 
    sections_str = 'const sections = ' + json.dumps(sections, indent=4) + ';\n'

    # Find and remove existing sections array if it exists
    start = script_content.find('const sections =')
    if start != -1:
        end = script_content.find('];', start) + 2
        script_content = script_content[end:].lstrip()

    # Find where to insert the sections
    insert_point = script_content.find('function populateSectionDropdowns()')
    
    # Create the new content
    new_content = sections_str + script_content
    
    # Write back to script.js
    with open('scripts/script.js', 'w') as f:
        f.write(new_content)
    
    print("Successfully updated script.js with sections from section_list.json")
def update_iframe_src(new_src,filename):
    """
    Updates the iframe src attribute in index.html with the provided new source path.
    
    Args:
        new_src (str): The new source path for the iframe
    """
    # Read the current index.html
    with open(filename, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Use regex to find and replace the iframe src
    import re
    pattern = r'<iframe src="[^"]*"'
    replacement = f'<iframe src="{new_src}"'
    
    new_content = re.sub(pattern, replacement, html_content)
    
    # Write back to index.html
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Successfully updated iframe src to: {new_src}")

if __name__ == "__main__":
    update_script_js() 
    update_iframe_src("processed_acts/2015_15.xhtml")