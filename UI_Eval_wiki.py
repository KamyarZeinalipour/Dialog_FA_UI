import argparse
import os
import pandas as pd
import gradio as gr

def main(annotator_name, input_file_path, output_file_path):
    # Load the input CSV file
    if not os.path.isfile(input_file_path):
        print(f"Input file {input_file_path} does not exist.")
        return

    # Read the CSV with fallback for missing columns
    df_input = pd.read_csv(input_file_path)

    # Ensure required columns are present
    required_columns = ['text', 'generated_conversation', 'title', 'selected_style', 'selected_starter']
    for col in required_columns:
        if col not in df_input.columns:
            print(f"Column '{col}' is missing in the input CSV.")
            return

    df_output = df_input.copy()

    # Check if the output file exists to resume annotations
    if os.path.isfile(output_file_path):
        df_output = pd.read_csv(output_file_path)
        print(f"Resuming annotations using existing output file {output_file_path}.")
    else:
        # Add a new column for annotated conversations if not present
        if 'generated_conversation_annotated' not in df_output.columns:
            df_output['generated_conversation_annotated'] = pd.NA  # Initialize with NaNs

        # Add the modified_flag column
        if 'modified_flag' not in df_output.columns:
            df_output['modified_flag'] = pd.NA  # Initialize with NaNs

    # Find the indices of unannotated rows
    unannotated_indices = df_output[df_output['generated_conversation_annotated'].isna()].index.tolist()
    if not unannotated_indices:
        print("All rows have been annotated.")
        return

    # Initialize current index
    current_index = unannotated_indices[0]

    # Define the annotation function
    def annotate(generated_conversation_annotated):
        nonlocal current_index, unannotated_indices

        # Original generated_conversation
        original_conversation = df_output.at[current_index, 'generated_conversation']

        # Save the annotation
        df_output.at[current_index, 'generated_conversation_annotated'] = generated_conversation_annotated

        # Check if the user made changes
        if generated_conversation_annotated == original_conversation:
            df_output.at[current_index, 'modified_flag'] = 'No Change'
        else:
            df_output.at[current_index, 'modified_flag'] = 'Changed'

        # Save the output CSV after the modification
        df_output.to_csv(output_file_path, index=False)

        # Move to the next unannotated index
        unannotated_indices = df_output[df_output['generated_conversation_annotated'].isna()].index.tolist()

        if unannotated_indices:
            current_index = unannotated_indices[0]
            next_text = df_output.at[current_index, 'text']
            next_generated_conversation = df_output.at[current_index, 'generated_conversation']
            next_title = df_output.at[current_index, 'title']
            next_selected_style = df_output.at[current_index, 'selected_style']
            next_selected_starter = df_output.at[current_index, 'selected_starter']
            return (
                gr.update(value=next_text),
                gr.update(value=next_generated_conversation),
                gr.update(value=next_title),
                gr.update(value=next_selected_style),
                gr.update(value=next_selected_starter),
                "Annotation saved. Proceed to the next item."
            )
        else:
            # All rows have been annotated
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                "Annotation complete! All rows have been annotated."
            )

    # Get the initial values
    initial_text = df_output.at[current_index, 'text']
    initial_generated_conversation = df_output.at[current_index, 'generated_conversation']
    initial_title = df_output.at[current_index, 'title']
    initial_selected_style = df_output.at[current_index, 'selected_style']
    initial_selected_starter = df_output.at[current_index, 'selected_starter']

    # Create the Gradio interface
    with gr.Blocks() as demo:
        gr.Markdown(f"# CSV Annotation Tool - Annotator: {annotator_name}")

        with gr.Column():
            title_box = gr.Textbox(
                value=initial_title, label="title", interactive=False, lines=1
            )
            with gr.Row():
                    with gr.Column():
                            text_box = gr.Textbox(
                                value=initial_text, label="Text", interactive=False, lines=5
                            )
                            selected_style_box = gr.Textbox(
                value=initial_selected_style, label="Selected Style", interactive=False, lines=1
            )
                            selected_starter_box = gr.Textbox(
                                value=initial_selected_starter, label="Selected Starter", interactive=False, lines=1
                            )
                    generated_conversation_box = gr.Textbox(
                        value=initial_generated_conversation,
                        label="Generated Conversation (Editable)",
                        lines=5
                    )


        submit_button = gr.Button("Save Annotation")
        status = gr.Textbox(value="", interactive=False, label="Status")

        submit_button.click(
            annotate,
            inputs=generated_conversation_box,
            outputs=[
                text_box,
                generated_conversation_box,
                title_box,
                selected_style_box,
                selected_starter_box,
                status
            ]
        )

    demo.launch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV Annotation Tool")
    parser.add_argument("annotator_name", help="Name of the annotator")
    parser.add_argument("input_file_path", help="Path to the input CSV file")
    parser.add_argument("output_file_path", help="Path to the output CSV file")

    args = parser.parse_args()

    main(args.annotator_name, args.input_file_path, args.output_file_path)
