import json
import re
from bs4 import BeautifulSoup

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

def update_export_filename(filename):
    """
    Updates the export filename in script.js to the provided filename.
    
    Args:
        filename (str): The new filename to export annotations to
    """
    # Read the current script.js
    with open('scripts/script.js', 'r') as f:
        script_content = f.read()

    # Use regex to find and replace the filename
    
    pattern = r"a\.download = '[^']*'"
    replacement = f"a.download = '{filename}'"
    
    new_content = re.sub(pattern, replacement, script_content)
    
    # Write back to script.js
    with open('scripts/script.js', 'w') as f:
        f.write(new_content)
        
    print(f"Successfully updated export filename to: {filename}")


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
    
    pattern = r'<iframe src="[^"]*"'
    replacement = f'<iframe src="{new_src}"'
    
    new_content = re.sub(pattern, replacement, html_content)
    
    # Write back to index.html
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Successfully updated iframe src to: {new_src}")

def extract_sections_from_part(part_file):
    """
    Extract sections from a part XHTML file and return them as a dictionary.
    
    Args:
        part_file (str): Path to the part XHTML file
        
    Returns:
        dict: Dictionary containing section information with structure:
        {
            'section_id': {
                'number': 'section_number',
                'title': 'section_title',
                'content': 'section_content'
            }
        }
    """
    try:
        # Read the XHTML file
        with open(part_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the XHTML
        soup = BeautifulSoup(content, 'xml')
        
        # Initialize the sections dictionary
        sections = {}
        
        # Find all section anchors
        section_anchors = soup.find_all('a', class_='LegAnchorID', id=lambda x: x and x.startswith('section-'))
        
        for anchor in section_anchors:
            section_id = anchor.get('id')
            if not section_id:
                continue
                
            # Get the section number from the ID
            section_number = section_id.replace('section-', '')
            
            # Find the section content
            section_div = anchor.find_next('div', class_='LegSection')
            if not section_div:
                continue
                
            # Extract section title
            title_elem = section_div.find('h2', class_='LegSectionTitle')
            section_title = title_elem.text.strip() if title_elem else f"Section {section_number}"
            
            # Extract section content
            content_elem = section_div.find('div', class_='LegSectionContent')
            section_content = content_elem.text.strip() if content_elem else ""
            
            # Add to sections dictionary
            sections[section_id] = {
                'number': section_number,
                'title': section_title,
                'content': section_content
            }
        
        return sections
        
    except Exception as e:
        print(f"Error extracting sections from {part_file}: {str(e)}")
        return {}

if __name__ == "__main__":
    #update_script_js() 
    #update_iframe_src("processed_acts/2015_15.xhtml")
    print(extract_sections_from_part("packages/1989_41_part_1/acts/1989_41.xhtml"))