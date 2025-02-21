import argparse
import os
import pandas as pd
import gradio as gr

def main(annotator_name, input_file_path):
    # Determine output file path
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
    output_file_path = f"{base_filename}_annotated_{annotator_name}.csv"

    # Load the input CSV file
    if not os.path.isfile(input_file_path):
        print(f"Input file {input_file_path} does not exist.")
        return

    df_input = pd.read_csv(input_file_path)
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

    required_columns = {'dialog', 'generated_conversation'}
    if not required_columns.issubset(df_input.columns):
        print(f"Error: Input CSV must contain the columns {required_columns}")
        return  

    total_rows = len(df_output)
    
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

        # Get the number of annotated rows
        annotated_count = total_rows - len(unannotated_indices) + 1

        # Move to the next unannotated index
        unannotated_indices = df_output[df_output['generated_conversation_annotated'].isna()].index.tolist()

        if unannotated_indices:
            current_index = unannotated_indices[0]
            next_dialog = df_output.at[current_index, 'dialog']
            next_generated_conversation = df_output.at[current_index, 'generated_conversation']
            return (
                gr.update(value=next_dialog),
                gr.update(value=next_generated_conversation),
                f"Annotation saved. {annotated_count} of {total_rows} annotated. Proceed to the next item."
            )
        else:
            # All rows have been annotated
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                f"Annotation complete! All {total_rows} rows have been annotated."
            )

    # Get the initial dialog and generated conversation
    initial_dialog = df_output.at[current_index, 'dialog']
    initial_generated_conversation = df_output.at[current_index, 'generated_conversation']

    # Create the Gradio interface
    with gr.Blocks() as demo:
        gr.Markdown(f"# CSV Annotation Tool - Annotator: {annotator_name}")

        with gr.Row():
            dialog_box = gr.Textbox(
                value=initial_dialog, label="dialog", interactive=False, lines=10
            )
            generated_conversation_box = gr.Textbox(
                value=initial_generated_conversation,
                label="Generated Conversation (Editable)",
                lines=10
            )

        submit_button = gr.Button("Save Annotation")
        status = gr.Textbox(value=f"0 of {total_rows} annotated.", interactive=False, label="Status")

        submit_button.click(
            annotate,
            inputs=generated_conversation_box,
            outputs=[dialog_box, generated_conversation_box, status]
        )

    demo.launch()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV Annotation Tool")
    parser.add_argument("annotator_name", help="Name of the annotator")
    parser.add_argument("input_file_path", help="Path to the input CSV file")

    args = parser.parse_args()

    main(args.annotator_name, args.input_file_path)
