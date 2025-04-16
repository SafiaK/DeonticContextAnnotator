import os
import re
import pandas as pd
import json
import argparse
from tqdm import tqdm
import openai
import nltk
from nltk.tokenize import sent_tokenize
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("annotation_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class AnnotationAutomator:
    """
    A class to automate the annotation of legislative text using large language models.
    """
    
    def __init__(self, api_key=None, model="gpt-4"):
        """
        Initialize the automator with API key and model.
        
        Args:
            api_key (str): OpenAI API key. If None, will try to get from environment variable.
            model (str): The model to use for annotation.
        """
        # Set OpenAI API key
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            
        if not openai.api_key:
            raise ValueError("OpenAI API key is required. Please provide it as an argument or set the OPENAI_API_KEY environment variable.")
            
        self.model = model
        
    def read_file(self, file_path):
        """Read a file and return its content."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
            
    def chunk_text(self, text, max_tokens=4000):
        """
        Split text into chunks that fit within token limits.
        
        Args:
            text (str): The text to chunk.
            max_tokens (int): Maximum tokens per chunk.
            
        Returns:
            list: List of text chunks.
        """
        # Simple approximation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        # Split text into sentences
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed the limit, start a new chunk
            if len(current_chunk) + len(sentence) > max_chars:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def annotate_text(self, text):
        """
        Use LLM to annotate legislative text according to the guidelines.
        
        Args:
            text (str): The legislative text to annotate.
            
        Returns:
            list: List of annotations in the required format.
        """
        # Chunk the text if it's too long
        chunks = self.chunk_text(text)
        all_annotations = []
        
        for chunk in chunks:
            prompt = f"""
            You are an expert legal annotator. Your task is to extract obligations, prohibitions, and permissions from the following legislative text and format them according to these guidelines:

            Format:
            IT IS [OBLIGATORY/PROHIBITED/PERMITTED]
            FOR [someone]
            TO [do something]
            [WHEN/IF/WHERE/ONLY IF/BEFORE/AFTER/UNLESS] [some conditions apply]

            The slots IT IS, FOR, and TO are mandatory (they occur in every annotation), while conditions are optional.
            Each condition is identified by either keyword WHEN/IF/WHERE, ONLY IF, BEFORE, AFTER, or UNLESS.

            Important rules:
            1. Only annotate regulative norms (obligations, permissions, prohibitions), not constitutive norms (definitions).
            2. Keep the text as close as possible to the original wording.
            3. The final annotations must read grammatically and fluently.
            4. Separate multiple annotations with a line of dashes: ------------------------

            Here is the legislative text to annotate:

            {chunk}

            Extract all obligations, prohibitions, and permissions from this text and format them according to the guidelines.
            """
            
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert legal annotator who extracts and formats obligations, prohibitions, and permissions from legislative text."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=4000
                )
                
                annotations_text = response.choices[0].message.content.strip()
                
                # Split the annotations
                chunk_annotations = annotations_text.split("------------------------")
                chunk_annotations = [a.strip() for a in chunk_annotations if a.strip()]
                
                all_annotations.extend(chunk_annotations)
                
                # Sleep to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error annotating chunk: {e}")
                continue
                
        return all_annotations
        
    def process_section(self, section_path):
        """
        Process a single section file.
        
        Args:
            section_path (str): Path to the section file.
            
        Returns:
            dict: Dictionary with section ID, content, and annotations.
        """
        # Extract section ID from filename
        section_id = os.path.basename(section_path).replace('.txt', '')
        
        # Read section content
        content = self.read_file(section_path)
        
        # Annotate the section
        logger.info(f"Annotating section {section_id}...")
        annotations = self.annotate_text(content)
        
        return {
            'section_id': section_id,
            'content': content,
            'annotations': annotations
        }
        
    def process_all_sections(self, sections_dir, output_path):
        """
        Process all section files in a directory.
        
        Args:
            sections_dir (str): Directory containing section files.
            output_path (str): Path to save the results.
        """
        # Get all section files
        section_files = [os.path.join(sections_dir, f) for f in os.listdir(sections_dir) 
                        if f.endswith('.txt') and not f.startswith('.')]
        
        results = []
        
        for section_file in tqdm(section_files, desc="Processing sections"):
            try:
                result = self.process_section(section_file)
                results.append(result)
                
                # Save intermediate results
                self.save_results(results, output_path)
                
            except Exception as e:
                logger.error(f"Error processing {section_file}: {e}")
                continue
                
        logger.info(f"Processed {len(results)} sections. Results saved to {output_path}")
        
    def save_results(self, results, output_path):
        """
        Save results to Excel and JSON.
        
        Args:
            results (list): List of dictionaries with section data.
            output_path (str): Base path for output files.
        """
        # Create flattened data for Excel
        excel_data = []
        
        for result in results:
            for annotation in result['annotations']:
                excel_data.append({
                    'act_section': result['section_id'],
                    'content_text': result['content'],
                    'annotation': annotation
                })
                
        # Save to Excel
        df = pd.DataFrame(excel_data)
        df.to_excel(f"{output_path}.xlsx", index=False)
        
        # Save to JSON (for backup and further processing)
        with open(f"{output_path}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Automate annotation of legislative text using LLMs")
    parser.add_argument("--sections_dir", type=str, default="legislation/ukpga/2010", 
                        help="Directory containing section files")
    parser.add_argument("--output", type=str, default="automated_annotations", 
                        help="Base path for output files")
    parser.add_argument("--api_key", type=str, help="OpenAI API key")
    parser.add_argument("--model", type=str, default="gpt-4", 
                        help="Model to use for annotation")
    parser.add_argument("--sample", type=int, default=0, 
                        help="Process only a sample of N sections (0 for all)")
    
    args = parser.parse_args()
    
    automator = AnnotationAutomator(api_key=args.api_key, model=args.model)
    
    # Process all sections or a sample
    if args.sample > 0:
        section_files = [os.path.join(args.sections_dir, f) for f in os.listdir(args.sections_dir) 
                        if f.endswith('.txt') and not f.startswith('.')]
        section_files = section_files[:args.sample]
        
        results = []
        for section_file in tqdm(section_files, desc="Processing sample sections"):
            try:
                result = automator.process_section(section_file)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {section_file}: {e}")
                continue
                
        automator.save_results(results, args.output)
        logger.info(f"Processed {len(results)} sample sections. Results saved to {args.output}")
    else:
        automator.process_all_sections(args.sections_dir, args.output)

if __name__ == "__main__":
    main()
