import os
import re
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from difflib import SequenceMatcher
import string
from collections import defaultdict
import json
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from util import convert_to_html


# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

def getSectionUrl(section_id,url):
    if section_id:
        section_id = section_id.replace('-', '/')
        section_url = url+'/' + section_id
        return section_url
    else:
        return section_id

def read_file(file_path):
    """Read a file and return its content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def parse_annotations(file_path):
    """Parse annotations from a file and return a list of annotations."""
    content = read_file(file_path)
    # Split by the separator
    annotations = content.split('------------------------')
    # Remove empty annotations
    annotations = [annotation.strip() for annotation in annotations if annotation.strip()]
    return annotations

def parse_section(file_path):
    """Parse a section file and return its content."""
    content = read_file(file_path)
    # Extract section number from filename
    section_id = os.path.basename(file_path).replace('.txt', '')
    return {
        'section_id': section_id,
        'content': content
    }

def extract_section_range_from_filename(filename):
    """Extract section range from annotation filename."""
    # For files like "Sections 1-20.txt"
    sections_match = re.search(r'Sections\s+(\d+)-(\d+)', filename)
    if sections_match:
        start = int(sections_match.group(1))
        end = int(sections_match.group(2))
        return start, end, "section"
    
    # For files like "Artt. 101-120.txt"
    articles_match = re.search(r'Artt\.\s+(\d+)-(\d+)', filename)
    if articles_match:
        start = int(articles_match.group(1))
        end = int(articles_match.group(2))
        return start, end, "section"
    
    return None, None, None

def extract_annotation_parts(annotation):
    """Extract all parts from an annotation."""
    lines = annotation.split('\n')
    parts = {
        'type': '',
        'for': '',
        'to': '',
        'conditions': []
    }
    
    current_part = None
    
    for line in lines:
        if line.startswith('IT IS '):
            parts['type'] = line[6:].strip()
            current_part = None
        elif line.startswith('FOR '):
            parts['for'] = line[4:].strip()
            current_part = None
        elif line.startswith('TO '):
            parts['to'] = line[3:].strip()
            current_part = 'to'
        elif any(line.startswith(keyword) for keyword in ['WHEN/IF/WHERE', 'ONLY IF', 'BEFORE', 'AFTER', 'UNLESS']):
            # Extract the condition type and text
            for keyword in ['WHEN/IF/WHERE', 'ONLY IF', 'BEFORE', 'AFTER', 'UNLESS']:
                if line.startswith(keyword):
                    condition_text = line[len(keyword):].strip()
                    parts['conditions'].append({
                        'type': keyword,
                        'text': condition_text
                    })
                    current_part = f'condition_{len(parts["conditions"]) - 1}'
                    break
        elif current_part == 'to':
            parts['to'] += ' ' + line.strip()
        elif current_part and current_part.startswith('condition_'):
            condition_idx = int(current_part.split('_')[1])
            parts['conditions'][condition_idx]['text'] += ' ' + line.strip()
    
    return parts

def preprocess_text(text):
    """Preprocess text for better matching while preserving order."""
    # Lowercase
    text = text.lower()
    
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords but preserve order
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize but preserve order
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(token) for token in tokens]
    
    return tokens

def extract_ngrams(tokens, n=3):
    """Extract n-grams from tokens while preserving order."""
    ngrams = []
    
    for i in range(len(tokens) - n + 1):
        ngrams.append(' '.join(tokens[i:i+n]))
    
    return ngrams

def find_matching_sections(annotation_parts, sections, section_range, url):
    """
    Find sections that match the annotation parts, returning top 3 main sections
    and matching them with conditions.
    
    Modified to check each annotation part individually and add to the score instead
    of concatenating parts. Also embeds section information directly in conditions.
    """
    # Create section_dict from sections for easy lookup
    section_dict = {section['section_id']: section for section in sections}
    
    # Filter sections based on range
    filtered_sections = sections
    if section_range:
        start, end, section_type = section_range
        filtered_sections = [
            section for section in sections
            if section_type in section['section_id'] and
            any(str(num) in section['section_id'].split('-')[-1]
                for num in range(start, end + 1))
        ]
    
    if not filtered_sections:
        filtered_sections = sections
    
    # Store matches for main sections
    main_section_matches = defaultdict(int)
    
    # Process each annotation part individually
    for part_name in ['type', 'for', 'to']:
        if part_name in annotation_parts and annotation_parts[part_name]:
            part_text = annotation_parts[part_name]
            part_tokens = preprocess_text(part_text)
            
            # Create n-grams for this part
            part_3grams = extract_ngrams(part_tokens, 3)
            part_5grams = extract_ngrams(part_tokens, 5) if len(part_tokens) >= 5 else []
            part_7grams = extract_ngrams(part_tokens, 7) if len(part_tokens) >= 7 else []
            
            # Score sections based on this part
            for section in filtered_sections:
                section_tokens = preprocess_text(section['content'].lower())
                section_text = ' '.join(section_tokens)
                
                # Score based on n-gram matches with progressive weighting
                for ngram in part_3grams:
                    if ngram in section_text:
                        main_section_matches[section['section_id']] += 1
                for ngram in part_5grams:
                    if ngram in section_text:
                        main_section_matches[section['section_id']] += 2
                for ngram in part_7grams:
                    if ngram in section_text:
                        main_section_matches[section['section_id']] += 3
    
    # Get top 3 main sections
    top_main_sections = sorted(main_section_matches.items(), key=lambda x: x[1], reverse=True)[:3]
    top_main_sections = [section_id for section_id, score in top_main_sections if score > 0]
    
    # Process conditions and add section information directly to them
    updated_conditions = []
    
    # Process non-UNLESS conditions - assign all to the main section like in the old code
    non_unless_conditions = [c for c in annotation_parts['conditions'] if c['type'] != 'UNLESS']
    main_section = top_main_sections[0] if top_main_sections else None

    for condition in non_unless_conditions:
        # Create updated condition with section - all non-UNLESS conditions get the main section
        updated_condition = {
            'type': condition['type'],
            'text': condition['text'],
            'section': main_section#getSectionUrl(main_section, url) if main_section and url is not None else main_section
        }
        
        updated_conditions.append(updated_condition)
    
    # Process UNLESS conditions
    unless_conditions = [c for c in annotation_parts['conditions'] if c['type'] == 'UNLESS']
    for condition in unless_conditions:
        condition_tokens = preprocess_text(condition['text'])
        condition_3grams = extract_ngrams(condition_tokens, 3)
        
        best_match = None
        best_score = -1
        
        # Check each top main section first
        for main_section in top_main_sections:
            section_text = section_dict[main_section]['content'].lower()
            section_tokens = preprocess_text(section_text)
            score = sum(1 for ngram in condition_3grams if ngram in ' '.join(section_tokens))
            
            if score > best_score:
                best_score = score
                best_match = main_section
        
        # If no good match in main sections, check all sections
        if best_score == 0:
            for section in sections:
                section_text = section['content'].lower()
                section_tokens = preprocess_text(section_text)
                score = sum(1 for ngram in condition_3grams if ngram in ' '.join(section_tokens))
                
                if score > best_score:
                    best_score = score
                    best_match = section['section_id']
        
        # Create updated condition with section
        updated_condition = {
            'type': condition['type'],
            'text': condition['text'],
            'section': best_match#getSectionUrl(best_match, url) if best_match and url is not None else best_match
        }
        
        updated_conditions.append(updated_condition)
    
    return {
        
        'main_section': top_main_sections[0] if top_main_sections else None,
        'alternative_sections': top_main_sections[1:] if len(top_main_sections) > 1 else [],
        'conditions': updated_conditions
    }


def update_main_section(result):
    """
    Modifies the main_section if it satisfies the following conditions:
    1. main_section is not in any condition's section.
    2. Any condition's section is also in alternative_sections.
    
    Args:
        result (dict): The output of find_matching_sections containing:
            - main_section: The primary section identified.
            - alternative_sections: Secondary sections identified.
            - conditions: List of conditions with embedded section information.
    
    Returns:
        dict: Updated result with potentially modified main_section.
    """
    main_section = result.get('main_section')
    alternative_sections = result.get('alternative_sections', [])
    conditions = result.get('conditions', [])
    
    # Extract all condition sections
    condition_sections = [condition.get('section') for condition in conditions if condition.get('section')]
    
    # Condition 1: Check if main_section is not in condition_sections
    if main_section and main_section not in condition_sections:
        # Condition 2: Check if any condition_sections overlap with alternative_sections
        overlapping_sections = [
            section for section in condition_sections
            if section in alternative_sections
        ]
        
        if overlapping_sections:
            # Modify the main_section to the first overlapping section
            new_main_section = overlapping_sections[0]
            result['main_section'] = new_main_section
            
            # Remove the new main_section from alternative_sections
            result['alternative_sections'] = [
                section for section in alternative_sections
                if section != new_main_section
            ]
    
    return result


def main(url,annotation_dir,act_sections_dir,output_json_file_path, output_xml_file_path, mode):
    """
    Main function to process annotations and match them with sections.
    
    Args:
        output_json_file_path (str): Path to save the JSON output file
        output_xml_file_path (str): Path to save the XML output file
        mode (str): The mode to run in. Options are:
            - "debug": Include file_name and alternative_Sections_ids in the JSON output
            - "normal": Exclude file_name and alternative_Sections_ids from the JSON output
                        and also produce XML output
    """
    # Paths
    # Get the current file's directory
   
    
    # Get all annotation files
    annotation_files = [os.path.join(annotation_dir, f) for f in os.listdir(annotation_dir) 
                        if f.endswith('.txt') and not f.startswith('.')]
    
    # Get all section files
    section_files = []
    for f in os.listdir(act_sections_dir):
        if f.endswith('.txt'):
            section_files.append(os.path.join(act_sections_dir, f))
    
    # Parse sections
    sections = [parse_section(file) for file in section_files]
    
    # Create a dictionary to quickly look up sections by ID
    section_dict = {section['section_id']: section for section in sections}
    
    # Create a list to store results
    results = []
    
    # Process each annotation file
    for annotation_file in annotation_files:
        print(f"Processing {annotation_file}...")
        
        # Extract section range from filename
        filename = os.path.basename(annotation_file)
        section_range = extract_section_range_from_filename(filename)
        
        # Parse annotations from file
        annotations = parse_annotations(annotation_file)
        
        for annotation in annotations:
            # Extract parts from annotation
            annotation_parts = extract_annotation_parts(annotation)
            
            # Find matching sections
            matching_sections = find_matching_sections(annotation_parts, sections, section_range,url)
            
            # Step 2: Update main_section based on conditions
            matching_sections = update_main_section(matching_sections)

            main_section_id = matching_sections['main_section']
            updated_conditions = matching_sections['conditions']
            alternative_Sections_ids = matching_sections['alternative_sections']
            
            # Update the annotation_parts with the updated conditions that include section info
            annotation_parts['conditions'] = updated_conditions
            
            # Combine all section IDs
            all_section_ids = []
            if main_section_id:
                all_section_ids.append(main_section_id)
            all_section_ids.extend([c.get('section') for c in updated_conditions if c.get('section')])


            
            if main_section_id:
                # Get the content of the main matching section for display
                primary_section = section_dict[main_section_id]
                
                conditions = annotation_parts['conditions']
                for condition in conditions:
                    condition['section'] = getSectionUrl(condition.get('section'),url)
                
                # Create result dictionary based on mode
                result_dict = {
                    'main_section': getSectionUrl(main_section_id,url),
                    'type': annotation_parts['type'],
                    'for': annotation_parts['for'],
                    'to': annotation_parts['to'],
                    'conditions': conditions#annotation_parts['conditions'],
                }
                
                # Include additional fields in debug mode
                if mode == "debug":
                    result_dict['file_name'] = filename
                    result_dict['alternative_Sections_ids'] = alternative_Sections_ids
                
                results.append(result_dict)
           
    
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Convert DataFrame to dictionary/JSON format
    json_data = df.to_dict(orient='records')

    # Save to JSON file
    with open(output_json_file_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(results)} records to {output_json_file_path}")
    
    # Generate XML output in normal mode
    if mode == "normal":
        # Create root element
        root = ET.Element("annotations")
        
        for item in json_data:
            # Create annotation element
            annotation = ET.SubElement(root, "annotation")
            
            # Add section info
            section = ET.SubElement(annotation, "section")
            section.text = item['main_section']
            
            # Add type info with HTML conversion
            type_elem = ET.SubElement(annotation, "type")
            type_elem.text = item['type']
            #type_html = ET.SubElement(annotation, "type_html")
            
            
            # Add for info with HTML conversion
            for_elem = ET.SubElement(annotation, "for")
            #for_elem.text = item['for']
            #for_html = ET.SubElement(annotation, "for_html")
            
            # Safely convert to HTML with error handling
            #try:
            for_html_str = convert_to_html(item['for'],for_elem)
            
            #for_elem.append(for_html_str)
            # except Exception as e:
            #     print(f"Error converting 'for' to HTML: {e}")
            #     for_html.text = item['for']  # Fallback to plain text
            
            # Add to info with HTML conversion
            to_elem = ET.SubElement(annotation, "to")
            #to_elem.text = item['to']
            #to_html = ET.SubElement(annotation, "to_html")
            
            # Safely convert to HTML with error handling
            #try:
            to_html_str = convert_to_html(item['to'],to_elem)
            print(to_html_str)
            #to_elem.append(to_html_str)
            # except Exception as e:
            #     print(f"Error converting 'to' to HTML: {e}")
            #     to_html.text = item['to']  # Fallback to plain text
            
            # Add conditions with embedded section information
            conditions_elem = ET.SubElement(annotation, "conditions")
            for condition in item.get('conditions', []):
                condition_elem = ET.SubElement(conditions_elem, "condition")
                
                condition_type = ET.SubElement(condition_elem, "type")
                condition_type.text = condition['type']
                
                #condition_text = ET.SubElement(condition_elem, "text")
                #condition_text.text = condition['text']
                
                #condition_html = ET.SubElement(condition_elem, "html")
                
                # Safely convert to HTML with error handling
                #try:
                condition_html_str = convert_to_html(condition['text'],condition_elem)
                #condition_text.append(condition_html_str)
                # except Exception as e:
                #     print(f"Error converting condition to HTML: {e}")
                #     condition_html.text = condition['text']  # Fallback to plain text
                
                # Add section information directly to the condition
                if 'section' in condition and condition['section']:
                    condition_section = ET.SubElement(condition_elem, "section")
                    condition_section.text = condition['section']
        
        # Create XML string with pretty formatting
        xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        
        # Save XML to file
        with open(output_xml_file_path, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        print(f"Saved XML output to {output_xml_file_path}")
        

if __name__ == "__main__":
    import argparse
    
    # parser = argparse.ArgumentParser(description='Process annotations and match them with sections.')
    # parser.add_argument('--mode', type=str, choices=['debug', 'normal'], default='normal',
    #                     help='Mode to run in: debug or normal (default: normal)')
    # parser.add_argument('--json', type=str, default='equalty_act_annotations_police.json',
    #                     help='Path to save the JSON output file')
    # parser.add_argument('--xml', type=str, default='equalty_act_annotations_police.xml',
    #                     help='Path to save the XML output file')
    
    # args = parser.parse_args()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct paths relative to current directory
    annotation_dir = os.path.join(current_dir, 'data/Equality Act 2010')
    act_sections_dir = os.path.join(current_dir, 'data/2010/15')
    url='https://www.legislation.gov.uk/ukpga/2010/15'
    output_json_file_path = os.path.join(current_dir,'outputs/Equality_Act_2010.json')
    output_xml_file_path = os.path.join(current_dir,'outputs/Equality_Act_2010.xml')
    mode = 'normal'


   
    main(url,annotation_dir,act_sections_dir,output_json_file_path, output_xml_file_path, mode)
