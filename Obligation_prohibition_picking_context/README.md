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

