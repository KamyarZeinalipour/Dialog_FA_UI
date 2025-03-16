import argparse
import os
import re
import json
import difflib
import pandas as pd
import gradio as gr
import dialogues_gen

def clean_json_text(json_str):
    """
    Remove markdown fences if they exist.
    Expected markers: 
      - Leading "```json" (optionally with whitespace) 
      - Trailing "```"
    """
    if json_str.strip().startswith("```json"):
        json_str = re.sub(r"^```json\s*", "", json_str.strip())
    if json_str.strip().endswith("```"):
        json_str = re.sub(r"\s*```$", "", json_str.strip())
    return json_str

def highlight_dialogue(context, reference_conversation, selected_message, theme):
    """
    Find the corresponding dialogue text within the context and mark it.
    Uses a different highlighting style depending on the theme.
    """
    try:
        cleaned = clean_json_text(reference_conversation)
        conv = json.loads(cleaned)
        conv_messages = conv.get("conversation", [])
        idx = int(selected_message.split(":")[0]) if selected_message else None
        if idx is None or idx < 0 or idx >= len(conv_messages):
            return "Invalid conversation selection."

        conv_text = conv_messages[idx]["text"]
        
        # Set highlighting style based on theme.
        if theme.strip().lower() == "dark":
            # For dark theme: use an orange background and force text to black.
            mark_style = "background-color:orange; color:black"
        else:
            # For light theme: use yellow background with black text.
            mark_style = "background-color:yellow; color:black"
        
        pos = context.find(conv_text)
        if pos != -1:
            # If we find an exact match, highlight that substring
            highlighted = context.replace(conv_text, f"<mark style='{mark_style}'>{conv_text}</mark>", 1)
            return highlighted
        else:
            # Attempt approximate match per sentence
            sentences = re.split(r"(?<=[.!؟])\s+", context)
            best_ratio = 0
            best_sentence = None
            for sentence in sentences:
                ratio = difflib.SequenceMatcher(None, sentence, conv_text).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_sentence = sentence
            if best_sentence and best_ratio > 0.3:
                highlighted_sentence = f"<mark style='{mark_style}'>{best_sentence}</mark>"
                highlighted = context.replace(best_sentence, highlighted_sentence, 1)
                return highlighted
            else:
                return context
    except Exception as e:
        return f"Error during highlighting: {str(e)}"

def update_conversation_dropdown(reference_conversation):
    """
    Parse the JSON conversation and return a gr.update object (a dict) containing
    the choices for a dropdown.
    Each choice is a string with the conversation index and a short snippet of the dialogue.
    """
    try:
        cleaned = clean_json_text(reference_conversation)
        conv = json.loads(cleaned)
        conv_messages = conv.get("conversation", [])
        choices = []
        for i, entry in enumerate(conv_messages):
            # Take the first 30 characters of the text for a preview
            snippet = entry.get("text", "")[:30]
            snippet_display = f"{i}: {entry.get('speaker', 'Speaker?')} - {snippet}..."
            choices.append(snippet_display)
        # If there are messages, pick the first as default; otherwise None
        default_val = choices[0] if choices else None
        return gr.update(choices=choices, value=default_val)
    except:
        return gr.update(choices=[], value=None)

def main(annotator_name, input_file_path):
    if not os.path.isfile(input_file_path):
        print(f"Input file {input_file_path} does not exist.")
        return

    file_name, file_ext = os.path.splitext(os.path.basename(input_file_path))
    output_file_path = f"{file_name}_annotated_{annotator_name}{file_ext}"

    df_input = pd.read_csv(input_file_path)
    required_columns = ['title', 'text', 'selected_style', 'selected_starter', 'generated_conversation']
    for col in required_columns:
        if col not in df_input.columns:
            print(f"Column '{col}' is missing in the input CSV.")
            return

    # Create a copy of the input and ensure extra columns exist
    df_output = df_input.copy()
    for new_col in ['generated_conversation_annotated', 'modified_flag']:
        if new_col not in df_output.columns:
            df_output[new_col] = pd.NA

    # If there's an existing output file, load it to resume
    if os.path.isfile(output_file_path):
        df_existing = pd.read_csv(output_file_path)
        # If the existing file is missing any columns, add them
        for col in df_output.columns:
            if col not in df_existing.columns:
                df_existing[col] = df_output[col]
        df_output = df_existing
        print(f"Resuming annotations using existing output file: {output_file_path}")
    else:
        df_output.to_csv(output_file_path, index=False)

    total_items = len(df_output)

    # Find the first row that has no annotation; if none, start at 0
    first_not_annotated = df_output[df_output['generated_conversation_annotated'].isna()].index
    current_index = first_not_annotated[0] if len(first_not_annotated) > 0 else 0

    # For storing newly generated conversations
    generated_conversation_storage = {}

    # -------------
    # Helper function to count how many are done
    # -------------
    def count_annotated():
        return df_output['generated_conversation_annotated'].notna().sum()

    # -------------
    # Load a row from the dataframe by index
    # -------------
    def load_item(index):
        if index < 0 or index >= total_items:
            return None

        row = df_output.iloc[index]
        title_val = row['title']
        context_val = row['text']
        style_val = row['selected_style']
        starter_val = row['selected_starter']
        reference_val = row['generated_conversation']

        # If no annotation saved yet, default to the reference
        annotated_val = row['generated_conversation_annotated']
        if pd.isna(annotated_val):
            annotated_val = reference_val

        # Nothing in new_generated_conversation by default
        new_gen_val = ""

        # Status text
        done = int(count_annotated())
        status_val = f"Row {index+1} of {total_items} — {done} annotated so far."

        return [
            gr.update(value=title_val),          # title
            gr.update(value=context_val),        # context
            gr.update(value=style_val),          # style
            gr.update(value=starter_val),        # starter
            gr.update(value=annotated_val),      # annotated textbox
            gr.update(value=reference_val),      # reference textbox
            gr.update(value=new_gen_val),        # newly generated conversation
            gr.update(value=status_val),         # status
        ]

    # -------------
    # Save the current row's annotation
    # -------------
    def save_annotation(annotated_conversation):
        nonlocal current_index

        original_conv = df_output.at[current_index, 'generated_conversation']
        if annotated_conversation.strip() == original_conv.strip():
            df_output.at[current_index, 'modified_flag'] = "No Change"
        else:
            df_output.at[current_index, 'modified_flag'] = "Changed"

        df_output.at[current_index, 'generated_conversation_annotated'] = annotated_conversation
        df_output.to_csv(output_file_path, index=False)

        # Reload the same row so the user remains on it
        return load_item(current_index)

    # -------------
    # Move to next row
    # -------------
    def go_next():
        nonlocal current_index
        if current_index < total_items - 1:
            current_index += 1
        return load_item(current_index)

    # -------------
    # Move to previous row
    # -------------
    def go_back():
        nonlocal current_index
        if current_index > 0:
            current_index -= 1
        return load_item(current_index)

    # -------------
    # Generate a new conversation (optional feature)
    # -------------
    def generate_new_conversation():
        nonlocal current_index
        row = df_output.iloc[current_index]
        new_conversation = dialogues_gen.generate_conversation(
            row['text'],
            row['title'],
            row['selected_style'],
            row['selected_starter']
        )
        generated_conversation_storage[current_index] = new_conversation
        return gr.update(value=new_conversation)

    # Prepare the initial data for the current index
    init_load = load_item(current_index)
    first_ref = df_output.at[current_index, 'generated_conversation']

    # Prepare the initial dropdown for the reference conversation
    init_dropdown = update_conversation_dropdown(first_ref)

    with gr.Blocks() as demo:
        gr.Markdown(f"# CSV Annotation Tool — Annotator: {annotator_name}")

        with gr.Row():
            with gr.Column(scale=1.5):
                title = gr.Textbox(label="Title", interactive=False)
                context = gr.Textbox(label="Context", interactive=False, lines=5)
                selected_style = gr.Textbox(label="Selected Style", interactive=False)
                selected_starter = gr.Textbox(label="Selected Starter", interactive=False)
            with gr.Column(scale=1.5):
                annotated_conversation = gr.Textbox(
                    label="Generated Conversation (JSON format) - Annotated",
                    lines=5
                )
                generate_button = gr.Button("Generate New Conversation")
                new_generated_conversation = gr.Textbox(
                    label="New Conversation (Generated Realtime)", 
                    interactive=False
                )                 
                 
        

        theme_selector = gr.Radio(
                    choices=["light", "dark"], 
                    value="light", 
                    label="Theme"
                )  

        conversation_selector = gr.Dropdown(
                label="Select Dialogue Message",
                choices=init_dropdown["choices"], 
                value=init_dropdown["value"]
            )
        highlighted_context = gr.HTML(label="Highlighted Context")                
  


          



        with gr.Row():
            save_button = gr.Button("Save Annotation")
            prev_button = gr.Button("Previous")
            next_button = gr.Button("Next")

        status = gr.Textbox(label="Status", interactive=False)
        reference_conversation = gr.Textbox(
                    label="Generated Conversation (JSON format) - Reference",
                    interactive=False,
                    lines=5
                )  

        # When the reference conversation changes, update the dropdown
        reference_conversation.change(
            update_conversation_dropdown, 
            inputs=[reference_conversation], 
            outputs=[conversation_selector]
        )

        # When the user selects a message, highlight it
        conversation_selector.change(
            highlight_dialogue,
            inputs=[context, reference_conversation, conversation_selector, theme_selector],
            outputs=[highlighted_context]
        )

        # Button clicks
        save_button.click(
            save_annotation,
            inputs=[annotated_conversation],
            outputs=[title, context, selected_style, selected_starter,
                     annotated_conversation, reference_conversation,
                     new_generated_conversation, status]
        )
        next_button.click(
            go_next,
            outputs=[title, context, selected_style, selected_starter,
                     annotated_conversation, reference_conversation,
                     new_generated_conversation, status]
        )
        prev_button.click(
            go_back,
            outputs=[title, context, selected_style, selected_starter,
                     annotated_conversation, reference_conversation,
                     new_generated_conversation, status]
        )
        generate_button.click(
            generate_new_conversation,
            outputs=[new_generated_conversation]
        )

        # Initialize UI from current row data
        if init_load:
            (title.value, 
             context.value, 
             selected_style.value, 
             selected_starter.value,
             annotated_conversation.value,
             reference_conversation.value, 
             new_generated_conversation.value,
             status.value) = [x["value"] for x in init_load]

    demo.launch(debug=True)

if __name__ == "__main__":  
    parser = argparse.ArgumentParser(description="CSV Annotation Tool")
    parser.add_argument("annotator_name", type=str, help="Name of the annotator")
    parser.add_argument("input_file_path", type=str, help="Path to the input CSV file")
    args = parser.parse_args()

    main(args.annotator_name, args.input_file_path)
