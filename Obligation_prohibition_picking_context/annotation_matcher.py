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

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

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
def find_matching_sections(annotation_parts, sections, section_range=None):
    """
    Find sections that match the annotation parts, returning top 3 main sections
    and matching them with conditions.
    
    Modified to check each annotation part individually and add to the score instead
    of concatenating parts.
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
    
    # Process non-UNLESS conditions individually
    non_unless_conditions = [c for c in annotation_parts['conditions'] if c['type'] != 'UNLESS']
    for condition in non_unless_conditions:
        condition_text = condition['text']
        condition_tokens = preprocess_text(condition_text)
        
        # Create n-grams for this condition
        condition_3grams = extract_ngrams(condition_tokens, 3)
        condition_5grams = extract_ngrams(condition_tokens, 5) if len(condition_tokens) >= 5 else []
        condition_7grams = extract_ngrams(condition_tokens, 7) if len(condition_tokens) >= 7 else []
        
        # Score sections based on this condition
        for section in filtered_sections:
            section_tokens = preprocess_text(section['content'].lower())
            section_text = ' '.join(section_tokens)
            
            # Score based on n-gram matches with progressive weighting
            for ngram in condition_3grams:
                if ngram in section_text:
                    main_section_matches[section['section_id']] += 1
            for ngram in condition_5grams:
                if ngram in section_text:
                    main_section_matches[section['section_id']] += 2
            for ngram in condition_7grams:
                if ngram in section_text:
                    main_section_matches[section['section_id']] += 3
    
    # Get top 3 main sections
    top_main_sections = sorted(main_section_matches.items(), key=lambda x: x[1], reverse=True)[:3]
    top_main_sections = [section_id for section_id, score in top_main_sections if score > 0]
    
    # Process UNLESS conditions separately
    unless_conditions = [c for c in annotation_parts['conditions'] if c['type'] == 'UNLESS']
    condition_sections = {}
    
    # For each UNLESS condition, find best matching section among top main sections
    for i, condition in enumerate(unless_conditions):
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
        
        if best_match:
            condition_sections[f"unless_{i}"] = best_match
    
    # Add non-UNLESS conditions to the return object with their corresponding main sections
    for i, condition in enumerate(non_unless_conditions):
        condition_type = condition['type'].lower()
        condition_sections[f"{condition_type}_{i}"] = top_main_sections[0] if top_main_sections else None
    
    return {
        'main_section': top_main_sections[0] if top_main_sections else None,
        'alternative_sections': top_main_sections[1:] if len(top_main_sections) > 1 else [],
        'condition_sections': condition_sections
    }

def update_main_section(result):
    """
    Modifies the main_section if it satisfies the following conditions:
    1. main_section is not in condition_sections.
    2. Any condition_sections are also in alternative_sections.
    
    Args:
        result (dict): The output of find_matching_sections containing:
            - main_section: The primary section identified.
            - alternative_sections: Secondary sections identified.
            - condition_sections: Sections related to conditions.
    
    Returns:
        dict: Updated result with potentially modified main_section.
    """
    main_section = result.get('main_section')
    alternative_sections = result.get('alternative_sections', [])
    condition_sections = result.get('condition_sections', {})
    
    # Condition 1: Check if main_section is not in condition_sections
    if main_section and main_section not in condition_sections.values():
        # Condition 2: Check if any condition_sections overlap with alternative_sections
        overlapping_sections = [
            section for section in condition_sections.values()
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
def find_matching_sections_backup(annotation_parts, sections, section_range=None):
    """
    Find sections that match the annotation parts, returning top 3 main sections
    and matching them with conditions.
    
    Improved to incorporate non-UNLESS condition text into the main matching text.
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
        
    # Process main parts and incorporate non-UNLESS conditions
    #main_text = annotation_parts['type'] + ' ' + annotation_parts['for'] + ' ' + annotation_parts['to']

    main_text = annotation_parts['for'] + ' ' + annotation_parts['to']
    
    # Add text from non-UNLESS conditions to the main text
    non_unless_conditions = [c for c in annotation_parts['conditions']if c['type'] != 'UNLESS']
    for condition in non_unless_conditions:
        main_text += ' ' + condition['text']
    
    main_tokens = preprocess_text(main_text)
        
    # Create n-grams
    main_3grams = extract_ngrams(main_tokens, 3)
    main_5grams = extract_ngrams(main_tokens, 5) if len(main_tokens) >= 5 else []
    main_7grams = extract_ngrams(main_tokens, 7) if len(main_tokens) >= 7 else []
        
    # Store matches for main sections
    main_section_matches = defaultdict(int)
        
    # Score main sections with improved weighting
    for section in filtered_sections:
        section_tokens = preprocess_text(section['content'].lower())
        section_text = ' '.join(section_tokens)
                
        # Score based on n-gram matches with progressive weighting
        for ngram in main_3grams:
            if ngram in section_text:
                main_section_matches[section['section_id']] += 1
        for ngram in main_5grams:
            if ngram in section_text:
                main_section_matches[section['section_id']] += 2
        for ngram in main_7grams:
            if ngram in section_text:
                main_section_matches[section['section_id']] += 3
        
    # Get top 3 main sections
    top_main_sections = sorted(main_section_matches.items(), key=lambda x: x[1], reverse=True)[:3]
    top_main_sections = [section_id for section_id, score in top_main_sections if score > 0]
        
    # Process UNLESS conditions separately
    unless_conditions = [c for c in annotation_parts['conditions'] if c['type'] == 'UNLESS']
    condition_sections = {}
        
    # For each UNLESS condition, find best matching section among top main sections
    for i, condition in enumerate(unless_conditions):
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
                
        if best_match:
            condition_sections[f"unless_{i}"] = best_match
        
    # Add non-UNLESS conditions to the return object with their corresponding main sections
    for i, condition in enumerate(non_unless_conditions):
        condition_type = condition['type'].lower()
        condition_sections[f"{condition_type}_{i}"] = top_main_sections[0] if top_main_sections else None
        
    return {
        'main_section': top_main_sections[0] if top_main_sections else None,
        'alternative_sections': top_main_sections[1:] if len(top_main_sections) > 1 else [],
        'condition_sections': condition_sections
    }
def main():
    # Paths
    annotation_dir = 'data/Police, Crime, Sentencing and Courts Act 2022'
    section_dir = 'data/2022/32'
    
    # Get all annotation files
    annotation_files = [os.path.join(annotation_dir, f) for f in os.listdir(annotation_dir) 
                        if f.endswith('.txt') and not f.startswith('.')]
    
    # Get all section files
    section_files = []
    for f in os.listdir(section_dir):
        if f.endswith('.txt'):
            section_files.append(os.path.join(section_dir, f))
    
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
            matching_sections = find_matching_sections(annotation_parts, sections, section_range)
            
            # Step 2: Update main_section based on conditions
            matching_sections = update_main_section(matching_sections)

            main_section_id = matching_sections['main_section']
            condition_section_ids = matching_sections['condition_sections']
            alternative_Sections_ids = matching_sections['alternative_sections']
            
            # Combine all section IDs
            all_section_ids = []
            if main_section_id:
                all_section_ids.append(main_section_id)
            all_section_ids.extend(condition_section_ids.values())
            
            if main_section_id:
                # Get the content of the main matching section for display
                primary_section = section_dict[main_section_id]
                
                results.append({
                    'file_name': filename,
                    'act_section': main_section_id,
                    'condition_sections': condition_section_ids,#', '.join(condition_section_ids.values()) if condition_section_ids else '',
                    #'content_text': primary_section['content'],
                    'annotation_type': annotation_parts['type'],
                    'annotation_for': annotation_parts['for'],
                    'annotation_to': annotation_parts['to'],
                    'annotation_conditions': annotation_parts['conditions'],
                    'alternative_Sections_ids': alternative_Sections_ids
                })
            else:
                # Only append if required fields are not empty
                if (annotation_parts['type'].strip() and 
                    annotation_parts['for'].strip() and 
                    annotation_parts['to'].strip()):
                    results.append({
                        'file_name': filename,
                        'act_section': 'Unknown',
                        'condition_sections': '',
                        'annotation_type': annotation_parts['type'],
                        'annotation_for': annotation_parts['for'],
                        'annotation_to': annotation_parts['to'],
                        'annotation_conditions': annotation_parts['conditions']
                    })
    
    
    # Create DataFrame
    df = pd.DataFrame(results)
    

    # Convert DataFrame to dictionary/JSON format
    json_data = df.to_dict(orient='records')

    # Save to JSON file
    with open('equalty_act_annotations_police.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)


    # Save to Excel
    print(f"Saved {len(results)} equalty_act_annotations_police.json")

if __name__ == "__main__":
    main()
