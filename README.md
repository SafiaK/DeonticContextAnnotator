# Legal Document Annotation and Context Matching System

This project consists of two main components that work together to process and analyze legal documents:

1. **JavaScript Annotation Tool** - A pipeline for downloading, processing, and packaging legal acts
2. **Annotation Context Matcher** - A system for matching annotations with their relevant legal contexts

## 1. JavaScript Annotation Tool

Located in the `JavaScriptAnnotationTool` directory, this component provides a pipeline for processing legal documents. It includes:

### Key Features
- Downloads legal acts from specified URLs
- Processes and cleans downloaded documents
- Splits acts into manageable sections
- Creates annotation packages for review

### Main Components
- `pipeline.py`: Main pipeline script for processing acts
- `split_legislation.py`: Handles splitting of legal documents into sections
- `CleanDownloadedAct.py`: Cleans and processes downloaded acts
- `LegislationHandler.py`: Core functionality for handling legal documents
- `util.py`: Utility functions for document processing

### Directory Structure
- `downloaded_acts/`: Stores raw downloaded legal documents
- `processed_acts/`: Contains processed and cleaned documents
- `split_acts/`: Stores split sections of legal documents
- `packages/`: Contains final annotation packages
- `guidelines/`: Documentation and guidelines for annotation

## 2. Annotation Context Matcher

The `annotation_matcher.py` script is responsible for matching annotations with their relevant legal contexts. It uses natural language processing techniques to:

### Key Features
- Processes annotations from text files
- Matches annotations with relevant legal sections
- Identifies conditions and their contexts
- Generates both JSON and XML outputs

### Main Functionality
- Preprocesses text using NLTK
- Extracts n-grams for matching
- Identifies main sections and alternative sections
- Processes conditions (WHEN/IF/WHERE, ONLY IF, BEFORE, AFTER, UNLESS)
- Generates structured output in JSON and XML formats

## Usage

### JavaScript Annotation Tool
1. Place URLs of legal acts in the input directory
2. Run the pipeline:
   ```bash
   cd JavaScriptAnnotationTool
   python pipeline.py
   ```
3. Access the annotation interface through `index.html`

### Annotation Context Matcher
1. Prepare annotation files in the correct format
2. Run the matcher:
   ```bash
   python annotation_matcher.py
   ```
3. Output files will be generated in the specified output directory


## Output Formats

The system generates two types of output:

1. **JSON Output**
   - Contains structured annotation data
   - Includes main sections, conditions, and context information
   - Can be used for further processing or analysis

2. **XML Output**
   - Provides a hierarchical view of annotations
   - Includes HTML-converted text for better display
   - Suitable for integration with other systems
