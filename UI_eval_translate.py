import argparse
import os
import pandas as pd
import gradio as gr

def main(annotator_name, input_file_path):
    # Determine output file path.
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    output_file_path = f"{base_filename}annotated{annotator_name}.csv"

    # Load the input CSV file.
    if not os.path.isfile(input_file_path):
        print(f"Input file {input_file_path} does not exist.")
        return

    df_input = pd.read_csv(input_file_path)
    df_output = df_input.copy()

    # Check if the output file exists to resume annotations.
    if os.path.isfile(output_file_path):
        df_output = pd.read_csv(output_file_path)
        print(f"Resuming annotations using existing output file {output_file_path}.")
    else:
        # Add a new column for annotated conversations if not present.
        if 'generated_conversation_annotated' not in df_output.columns:
            df_output['generated_conversation_annotated'] = pd.NA  
        # Add the modified_flag column if not present
        if 'modified_flag' not in df_output.columns:
            df_output['modified_flag'] = pd.NA  

    # Verify required columns exist.
    required_columns = {'dialog', 'generated_conversation'}
    if not required_columns.issubset(df_input.columns):
        print(f"Error: Input CSV must contain the columns {required_columns}")
        return

    total_rows = len(df_output)
    # Count already annotated examples.
    annotated_count = df_output['generated_conversation_annotated'].notna().sum()

    # Determine the starting index:
    # If there are any unannotated rows, start with the first unannotated.
    unannotated_indices = df_output[df_output['generated_conversation_annotated'].isna()].index.tolist()
    if unannotated_indices:
        current_idx = unannotated_indices[0]
    else:
        current_idx = total_rows - 1

    # Helper function: load a row's values for display.
    def load_row(index):
        row = df_output.loc[index]
        dialog_text = row['dialog']
        # The original generated conversation is kept as reference.
        gen_conv_text = row['generated_conversation']
        # For annotated conversation, if already saved, use it; otherwise, use the original.
        annotated_text = row['generated_conversation_annotated']
        if pd.isna(annotated_text):
            annotated_text = gen_conv_text
        return dialog_text, gen_conv_text, annotated_text

    # Get initial values for the determined starting row.
    initial_dialog, initial_generated, initial_annotated = load_row(current_idx)

    # Define function for saving current annotation and moving forward.
    def save_and_next(annotated_text):
        nonlocal current_idx
        # Retrieve original generated conversation for comparison.
        original_text = df_output.loc[current_idx, 'generated_conversation']
        # Save the current annotation.
        df_output.loc[current_idx, 'generated_conversation_annotated'] = annotated_text
        if annotated_text == original_text:
            df_output.loc[current_idx, 'modified_flag'] = 'No Change'
        else:
            df_output.loc[current_idx, 'modified_flag'] = 'Changed'
            
        # Save the CSV file.
        df_output.to_csv(output_file_path, index=False)

        # Update count of annotated examples.
        annotated_count = df_output['generated_conversation_annotated'].notna().sum()
        # Refresh the list of unannotated indices.
        unannotated_indices = df_output[df_output['generated_conversation_annotated'].isna()].index.tolist()
        
        # Move to next unannotated row if available.
        if unannotated_indices:
            current_idx = unannotated_indices[0]
            dialog_text, gen_conv_text, annotated_text = load_row(current_idx)
            return (
                gr.update(value=dialog_text, visible=True),
                gr.update(value=gen_conv_text, visible=True),
                gr.update(value=annotated_text, visible=True),
                f"Annotation saved. {annotated_count} of {total_rows} annotated."
            )
        else:
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                f"Annotation complete! All {total_rows} rows have been annotated."
            )

    # Define function to navigate back.
    def go_previous():
        nonlocal current_idx
        if current_idx > 0:
            current_idx -= 1
        dialog_text, gen_conv_text, annotated_text = load_row(current_idx)
        return (
            gr.update(value=dialog_text, visible=True),
            gr.update(value=gen_conv_text, visible=True),
            gr.update(value=annotated_text, visible=True),
            f"Moved to previous item (Row {current_idx + 1} of {total_rows})."
        )

    # Build the Gradio interface.
    with gr.Blocks() as demo:
        gr.Markdown(f"# CSV Annotation Tool - Annotator: {annotator_name}")

        with gr.Row():
            with gr.Column():
            # Display the "dialog" for context (non-editable).
             dialog_box = gr.Textbox(value=initial_dialog, label="Dialog", interactive=False, lines=10)
            with gr.Column():
            # Non-editable box showing the original generated conversation.
              generated_conv_box = gr.Textbox(value=initial_generated, label="Generated Conversation (Reference)", interactive=False, lines=10)
            with gr.Column():
            # Editable text box for annotation (prefilled with previously saved annotation or original value).
              annotated_conv_box = gr.Textbox(value=initial_annotated, label="Annotated Conversation (Editable)", lines=10)
        with gr.Row():
            prev_button = gr.Button("← Previous")
            next_button = gr.Button("Save & Next")
        with gr.Row():
            # Status now shows the current number of annotated examples.
            status = gr.Textbox(value=f"{annotated_count} of {total_rows} annotated.", interactive=False, label="Status")

        # Connect button events.
        next_button.click(
            save_and_next,
            inputs=annotated_conv_box,
            outputs=[dialog_box, generated_conv_box, annotated_conv_box, status]
        )
        prev_button.click(
            go_previous,
            inputs=None,
            outputs=[dialog_box, generated_conv_box, annotated_conv_box, status]
        )

    demo.launch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV Annotation Tool")
    parser.add_argument("annotator_name", help="Name of the annotator")
    parser.add_argument("input_file_path", help="Path to the input CSV file")
    args = parser.parse_args()
    main(args.annotator_name, args.input_file_path)
