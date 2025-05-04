import os
import markdown
from model import model_response
from playwright.sync_api import sync_playwright
from jinja2 import Environment, FileSystemLoader

# =============================================================================
# MAIN FUNCTION: action_manager
# =============================================================================
def action_manager(text, action_type):
    """
    Manages text processing actions such as simplification, summarization, or CV improvement.

    Parameters:
        text (str): The text to be processed.
        action_type (str): The type of action to perform ('simplify', 'summarize', 'improve_cv').

    Returns:
        Tuple[str | None, str | None]: The processed text or the path to the generated PDF file,
        depending on the action type.
    """
    if not text.strip():
        return None, None 
    
    prompts = {
      
        "summarize": f"""**TASK:** Create a very concise summary (2-3 sentences or a list of 3-5 key points) of the following text.
                      **INSTRUCTIONS:**
                      1. Extract only the most important points.
                      2. Use clear and direct language.
                      
                      **ORIGINAL TEXT:**
                      {text}
                      
                      **CONCISE SUMMARY (Start your answer here):**""",
        
        "improve_cv": f"""You are an expert in CV writing. **Rewrite** the following CV section to make it more impactful and clear, preserving the original language.

                      **REWRITING INSTRUCTIONS:**
                      1. Start each bullet point or task description with a strong action verb.
                      2. Be concise and to the point.
                      3. Where appropriate, add a placeholder like `[Quantify achievement/impact]` to indicate where a real metric could be inserted (do not make up numbers).
                      4. The result should be **only the rewritten CV section**, not a list of suggestions or additional comments.

                      **ORIGINAL CV SECTION:**
                      {text}

                      **REWRITTEN CV SECTION:**"""
    }
    
    prompt = prompts.get(action_type)
    if not prompt:
        return "Invalid action type.", None 

    try:
        response = model_response(prompt)

        if action_type == "improve_cv":
            try:
                cv_name = text.split('\n')[0].strip() if text else "Improved CV"
                cv_header = f'<div class="cv-header"><h1 class="name">{cv_name}</h1></div>'
                processed_html = convert_markdown_to_html(response)
                cv_content_html = f'{cv_header}<div class="cv-content">{processed_html}</div>'

                env = Environment(loader=FileSystemLoader('.'))
                template = env.get_template('template.html')
                html_content = template.render(cv_content=cv_content_html)

                pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_cv.pdf")
                html_to_pdf_playwright(html_content, pdf_path)

                if os.path.exists(pdf_path):
                    return None, pdf_path
                else:
                    return "Error: PDF file was not generated successfully.", None

            except Exception as pdf_e:
                import traceback
                traceback.print_exc()
                return f"Error generating PDF: {type(pdf_e).__name__}: {pdf_e}", None
        else:
            return response, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error processing text: {type(e).__name__}: {e}", None



# =============================================================================
# HELPER FUNCTION: convert_markdown_to_html
# =============================================================================
def convert_markdown_to_html(markdown_text):
    """
    Converts Markdown-formatted text to HTML.

    Parameters:
        markdown_text (str): The input text in Markdown format.

    Returns:
        str: The HTML-converted text.
    """
    return markdown.markdown(markdown_text, extensions=['extra', 'nl2br'])



# =============================================================================
# HELPER FUNCTION: html_to_pdf_playwright
# =============================================================================
def html_to_pdf_playwright(html_content: str, pdf_path: str):
    """
    Generates a PDF file from HTML content using Playwright.

    Parameters:
        html_content (str): HTML content to render.
        pdf_path (str): Path where the generated PDF will be saved.
    """
    with open(file='tmp.html', mode="w", encoding="utf-8") as tmp_html:
        tmp_html.write(html_content)
        tmp_html_path = tmp_html.name

    file_url = f"file://{os.path.abspath(tmp_html_path)}"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(file_url)
        page.pdf(path=pdf_path, format="A4")
        browser.close()

    os.remove(tmp_html_path)
