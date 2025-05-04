import gradio as gr
from advanced_features import extract_key_requirements, create_cover_letter, cv_agent, generate_cv_from_agent_data
from basic_functions import action_manager

# =============================================================================
# FUNCTION: update_output_visibility
# =============================================================================
def update_output_visibility(action):
    """
    Updates the visibility of output components depending on the selected action.

    Args:
        action (str): The selected action (e.g., "improve_cv").

    Returns:
        Tuple: Gradio component visibility updates.
    """
    if action == "improve_cv":
        return gr.update(visible=False), gr.update(visible=True)
    else:
        return gr.update(visible=True), gr.update(visible=False)

# =============================================================================
# THEME CONFIGURATION
# =============================================================================
theme = gr.themes.Ocean(
    primary_hue="blue",
    neutral_hue="gray",
)

# =============================================================================
# GRADIO INTERFACE SETUP
# =============================================================================
with gr.Blocks(theme=theme, title="Accessibility Assistant for Job Offers and CVs") as demo:
    gr.Markdown("""
    <div style="display: flex; align-items: center; gap: 20px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg" alt="IBM Logo" width="120" />
        <div>
            <h1>Accessibility Assistant for Job Offers and CVs</h1>
            <p>This tool helps make job offers and CVs more accessible through various text processing functions.</p>
        </div>
    </div>
    """)

    with gr.Tabs():
        # =============================================================================
        # TAB: Basic Functions
        # =============================================================================
        with gr.TabItem("Basic Functions"):
            with gr.Row():
                with gr.Column():
                    input_text = gr.TextArea(
                        label="Input Text (job offer or CV section)", 
                        placeholder="Paste the text you want to process here...", 
                        lines=10
                    )
                    action_type = gr.Radio(
                        ["summarize", "improve_cv"],
                        label="Select Action",
                        value="summarize",
                        info="'improve_cv' will generate a downloadable PDF."
                    )
                    submit_btn = gr.Button("Process Text")

                with gr.Column():
                    output_text_display = gr.TextArea(
                        label="Result (Text)", 
                        lines=15, 
                        visible=True
                    )
                    output_file_display = gr.File(
                        label="Download Generated PDF", 
                        visible=False
                    )

            submit_btn.click(
                fn=action_manager,
                inputs=[input_text, action_type],
                outputs=[output_text_display, output_file_display]
            )

            action_type.change(
                fn=update_output_visibility,
                inputs=action_type,
                outputs=[output_text_display, output_file_display]
            )
        # =============================================================================
        # TAB: Key Requirements Extraction
        # =============================================================================
        with gr.TabItem("Key Requirements Extraction"):
            with gr.Row():
                with gr.Column():
                    job_description = gr.TextArea(
                        label="Job Description", 
                        placeholder="Paste the job posting here...", 
                        lines=10
                    )
                    extract_btn = gr.Button("Extract Requirements")
                
                with gr.Column():
                    requirements_output = gr.TextArea(
                        label="Extracted Requirements", 
                        lines=10
                    )
            
            extract_btn.click(
                fn=extract_key_requirements,
                inputs=job_description,
                outputs=requirements_output
            )
        
        # =============================================================================
        # TAB: CV Assistant Agent
        # =============================================================================
        with gr.TabItem("CV Assistant"):
            with gr.Row():
                with gr.Column():
                    job_description_input = gr.TextArea(
                        label="Job Posting",
                        placeholder="Paste the job posting you want to tailor your CV for...",
                        lines=10
                    )
                    user_input = gr.TextArea(
                        label="Your Response",
                        placeholder="Type your response to the assistant's question here...",
                        lines=5
                    )
                    agent_btn = gr.Button("Start / Respond")

                with gr.Column():
                    agent_output = gr.TextArea(
                        label="CV Assistant",
                        lines=10,
                        value="Welcome to the CV creation assistant. To begin, paste a job posting and click 'Start'."
                    )
                    agent_cv_output = gr.File(
                        label="Download Generated CV",
                        visible=False
                    )

            # State to maintain conversation context
            agent_context = gr.State(None)

            def process_agent_interaction(job_desc, user_response, context):
                if not job_desc.strip():
                    return "Please provide a job posting first.", context, gr.update(visible=False)

                message, new_context, cv_ready = cv_agent(job_desc, user_response, context)

                #print(f'MESSAGE:\n{message}')
                #print(f'NEW CONTEXT:\n{new_context}')

                if cv_ready:
                    cv_text = generate_cv_from_agent_data(new_context)
                    print(f'CV TEXT:\n{cv_text}')
                    _, pdf_path = action_manager(cv_text, "improve_cv")

                    if pdf_path:
                        return message, new_context, gr.update(visible=True, value=pdf_path)
                    else:
                        return message + "\n\nAn error occurred while generating the PDF. Please try again.", new_context, gr.update(visible=False)

                return message, new_context, gr.update(visible=False)

            agent_btn.click(
                fn=process_agent_interaction,
                inputs=[job_description_input, user_input, agent_context],
                outputs=[agent_output, agent_context, agent_cv_output]
            )

        # =============================================================================
        # TAB: Cover Letter Generator
        # =============================================================================
        with gr.TabItem("Cover Letter"):
            with gr.Row():
                with gr.Column():
                    cv_text = gr.TextArea(
                        label="Your CV", 
                        placeholder="Paste your CV here...", 
                        lines=10
                    )
                    job_text = gr.TextArea(
                        label="Job Posting", 
                        placeholder="Paste the job posting here...", 
                        lines=10
                    )
                    cover_letter_btn = gr.Button("Generate Cover Letter")
                
                with gr.Column():
                    cover_letter_output = gr.TextArea(
                        label="Generated Cover Letter", 
                        lines=15
                    )
            
            cover_letter_btn.click(
                fn=create_cover_letter,
                inputs=[cv_text, job_text],
                outputs=cover_letter_output
            )


    # =============================================================================
    # FOOTER
    # =============================================================================
    gr.Markdown("""
    ### Developed for the IBM Challenge SDG8

    This project contributes to Sustainable Development Goal 8: "Decent Work and Economic Growth",
    by improving access to employment through clearer and more inclusive language.
    """)

# =============================================================================
# RUN APP
# =============================================================================
if __name__ == "__main__":
    demo.launch()
