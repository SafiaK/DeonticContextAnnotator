import json
import re
from bs4 import BeautifulSoup
import os

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

def extract_sections_from_part(part_file, output_file=None):
    """
    Extract sections from a part XHTML file and return them as a dictionary.
    If output_file is provided, save the JSON there. Otherwise, use the default naming logic.
    """
    try:
        print(f"Opening file: {part_file}")
        # Read the XHTML file
        with open(part_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("File read successfully")
        # Parse the XHTML
        soup = BeautifulSoup(content, 'xml')
        print("BeautifulSoup parsing complete")
        
        # Initialize the sections dictionary
        sections = {}
        
        # Find all section anchors with IDs starting with 'section-'
        section_anchors = soup.find_all('a', id=lambda x: x and x.startswith('section-'))
        print(f"Found {len(section_anchors)} section anchors")
        
        for anchor in section_anchors:
            section_id = anchor.get('id')
            print(f"\nProcessing section: {section_id}")
            
            # Find the next h3 element which contains the section info
            section_header = anchor.find_next(['h3', 'h4'])
            if not section_header:
                print(f"No header found for section {section_id}")
                continue
            print(f"Found header for section {section_id}")
            
            # Get section number from the section ID
            section_number = section_id.replace('section-', '')
            print(f"Section number: {section_number}")
            
            # Get section title - look for any span with text within the header
            title_spans = section_header.find_all('span')
            title_text = []
            for span in title_spans:
                text = span.get_text(strip=True)
                if text and text != section_number and 'E+W' not in text:
                    title_text.append(text)
            
            section_title = ' '.join(title_text) if title_text else f"Section {section_number}"
            print(f"Section title: {section_title}")
            
            # Get section content by collecting all relevant paragraphs
            content = []
            current = section_header.find_next_sibling()
            
            # Keep going until we hit the next section or run out of siblings
            while current and not (current.name in ['h3', 'h4'] or current.find('a', id=lambda x: x and x.startswith('section-'))):
                # Look for paragraph text
                if current.name == 'p':
                    text = current.get_text(strip=True)
                    if text and 'E+W' not in text:
                        content.append(text)
                current = current.find_next_sibling()
            
            section_content = '\n'.join(content)
            print(f"Content length: {len(section_content)} characters")
            
            # Add to sections dictionary
            sections[section_id] = {
                'number': section_number,
                'title': section_title,
                'content': section_content
            }
            print(f"Added section {section_id} to dictionary")
        
        print(f"\nTotal sections processed: {len(sections)}")
        
        # Save to JSON file using the provided output_file or the part directory name
        if output_file is None:
            part_dir = os.path.basename(os.path.dirname(part_file))
            output_file = os.path.join(os.path.dirname(part_file), f"{part_dir}_sections.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=4, ensure_ascii=False)
        print(f"Saved sections to {output_file}")
        
        return sections
        
    except Exception as e:
        print(f"Error extracting sections from {part_file}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}

if __name__ == "__main__":
    #update_script_js() 
    #update_iframe_src("processed_acts/2015_15.xhtml")
    part_file = "packages/2014_6_part_1/acts/2014_6.xhtml"
    output_file = "packages/2014_6_part_1/acts/2014_6_part_1_sections.json"
    print(extract_sections_from_part(part_file, output_file))