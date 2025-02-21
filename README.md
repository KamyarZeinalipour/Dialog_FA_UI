# Annotation Tool

This repository contains two Python scripts designed to facilitate the annotation of generated conversations using Gradio-based user interfaces. These tools help annotators review and refine generated text to ensure accuracy and consistency.

## Overview of the Scripts

1. **`UI_eval_translate.py`**
   - This script is designed for annotating translated conversations from English to Farsi.
   - It allows users to review the generated translations, modify them if necessary, and mark whether a change was made.
   - The output is saved in a CSV file to track the annotation progress.

2. **`UI_Eval_wiki.py`**
   - This script is designed for annotating dialogues generated from Wikipedia information.
   - Annotators review and refine the generated conversations based on structured Wikipedia content.
   - The tool includes additional fields such as `title`, `selected_style`, and `selected_starter` to provide context for the generated dialogue.

## Features
- User-friendly Gradio interface for annotation.
- Supports resuming annotations from an existing CSV file.
- Tracks whether modifications were made (`modified_flag` column).
- Automatically saves progress after each annotation.
- Ensures required columns are present in the input CSV before starting the annotation process.

## Installation
Before running the scripts, ensure you have the necessary dependencies installed:

```bash
pip install pandas gradio argparse
```

## Usage
Each script requires three arguments:
1. **Annotator Name** – The name of the annotator (for reference).
2. **Input File Path** – Path to the CSV file containing the data to be annotated.
3. **Output File Path** – Path where the annotated data will be saved.

### Running `UI_eval_translate.py`
This script is used for reviewing and refining translated conversations:

```bash
python UI_eval_translate.py "Annotator_Name" path/to/input.csv 
```

### Running `UI_Eval_wiki.py`
This script is used for annotating dialogues generated from Wikipedia information:

```bash
python UI_Eval_wiki.py "Annotator_Name" path/to/input.csv path/to/output.csv
```

## Input CSV Format
Each script expects specific columns in the input CSV file:

### `UI_eval_translate.py` (Translation Annotation)
| Column Name                    | Description                                        |
|---------------------------------|----------------------------------------------------|
| `dialog`                        | Original dialog in English                        |
| `generated_conversation`        | Machine-translated conversation in Farsi         |

### `UI_Eval_wiki.py` (Wikipedia Dialogue Annotation)
| Column Name            | Description                                             |
|------------------------|---------------------------------------------------------|
| `text`                | The original Wikipedia information                     |
| `generated_conversation` | AI-generated dialogue from Wikipedia content         |
| `title`               | Title of the Wikipedia article                          |
| `selected_style`      | Style used for generating the dialogue                  |
| `selected_starter`    | Initial context for the generated conversation          |

## Output CSV Format
After annotation, the output CSV will contain the original data along with new columns:

| Column Name                          | Description                                  |
|--------------------------------------|----------------------------------------------|
| `generated_conversation_annotated`  | Annotator's revised conversation           |
| `modified_flag`                     | Indicates if the text was changed (`Changed` or `No Change`) |

## How It Works
1. The script loads the input CSV and checks for required columns.
2. If an output file exists, the tool resumes from the last annotated row.
3. The Gradio UI presents each row for annotation.
4. The annotator can modify the generated conversation and save the changes.
5. The tool moves to the next unannotated row until all rows are completed.

## Contribution
If you want to improve this annotation tool, feel free to submit pull requests or report issues.

## License
This project is licensed under the MIT License.

