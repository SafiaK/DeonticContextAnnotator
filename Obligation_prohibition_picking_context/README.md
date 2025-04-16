# Equality Act 2010 Annotation Analysis

This project provides tools to analyze and automate the annotation of the Equality Act 2010 according to specific guidelines. The repository contains scripts to match existing annotations with their corresponding sections and to automate the annotation process using large language models.

## Project Structure

- `data/2010/15/`: Contains individual sections and parts of the Equality Act 2010
- `data/Equality Act 2010/`: Contains annotated data according to the guidelines
- `annotation_matcher.py`: Script to match annotations with their corresponding sections
- `annotation_automator.py`: Script to automate the annotation process using LLMs
- `LegislationHandler.py`: Script to download and parse legislation from legislation.gov.uk

## Annotation Format

The annotations follow this format:
```
IT IS [OBLIGATORY/PROHIBITED/PERMITTED]
FOR [someone]
TO [do something]
[WHEN/IF/WHERE/ONLY IF/BEFORE/AFTER/UNLESS] [some conditions apply]
```

The slots IT IS, FOR, and TO are mandatory, while conditions are optional.

## Usage

### Matching Annotations with Sections

To match existing annotations with their corresponding sections and create an Excel sheet:

```bash
python annotation_matcher.py
```

This will:
1. Parse the annotated files in `data/Equality Act 2010/`
2. Parse the section files in `data/2010/15/`
3. Match annotations to their corresponding sections using NLP techniques
4. Create an Excel file `equality_act_annotations.xlsx` with columns:
   - `act_section`: The section ID(s) that match the annotation
   - `content_text`: The content of the primary matching section
   - `annotation`: The full annotation text
   - `annotation_type`: The type of annotation (OBLIGATORY/PROHIBITED/PERMITTED)
   - `annotation_for`: The subject of the annotation
   - `annotation_to`: The action part of the annotation
   - `annotation_conditions`: The conditions of the annotation

### Automating Annotation

To automate the annotation process using large language models:

```bash
python annotation_automator.py --api_key YOUR_OPENAI_API_KEY
```

Optional arguments:
- `--sections_dir`: Directory containing section files (default: "data/2010/15")
- `--output`: Base path for output files (default: "automated_annotations")
- `--model`: Model to use for annotation (default: "gpt-4")
- `--sample`: Process only a sample of N sections (default: 0, which means all)

Example to process just 5 sections:
```bash
python annotation_automator.py --api_key YOUR_OPENAI_API_KEY --sample 5
```

This will:
1. Process the specified section files
2. Use the OpenAI API to generate annotations according to the guidelines
3. Save the results to Excel and JSON files

## Automation Approach

The automation approach uses large language models (specifically GPT-4) to analyze legislative text and extract obligations, prohibitions, and permissions according to the annotation guidelines. The process involves:

1. **Text Chunking**: Breaking down long sections into manageable chunks that fit within the model's context window
2. **Prompt Engineering**: Crafting detailed prompts that explain the annotation format and guidelines
3. **Annotation Extraction**: Using the model to identify and format the relevant norms
4. **Post-processing**: Combining and formatting the results into the required structure

This approach leverages the language model's ability to understand legal text and extract structured information, making it suitable for annotating large volumes of legislative content.

## Requirements

- Python 3.7+
- pandas
- nltk
- openai
- tqdm
- difflib

Install the required packages:
```bash
pip install pandas nltk openai tqdm
```

## Future Improvements

1. **Enhanced Matching**: Improve the matching algorithm to better handle complex cases
2. **Validation**: Add validation steps to ensure the quality of automated annotations
3. **Batch Processing**: Implement batch processing to handle large volumes of text more efficiently
4. **Fine-tuning**: Fine-tune the language model on legal annotation tasks for better performance
5. **User Interface**: Develop a user interface for easier interaction with the annotation tools
