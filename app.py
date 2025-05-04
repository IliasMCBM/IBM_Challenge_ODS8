import os
import gradio as gr
import re  # Añadido para expresiones regulares
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from advanced_features import (
    extract_key_requirements,
    create_cover_letter,
    cv_agent,
    generate_cv_from_agent_data
)
# Imports para PDF
import tempfile
from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright
import tempfile
import os
import markdown

# Load environment variables
load_dotenv()

# Get credentials from environment variables
api_key = os.getenv('WATSONX_API_KEY')
url = os.getenv('WATSONX_URL')
project_id = os.getenv('WATSONX_PROJECT_ID')

# Initialize WatsonX client
credentials = Credentials(
    url=url,
    api_key=api_key,
)
client = APIClient(credentials)

model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",
    api_client=client,
    project_id=project_id,
    params={
        "max_new_tokens": 2048,  # Aumentado significativamente a 2048
        "temperature": 0.7,
    }
)

# --- Función simplify_text (modificada para devolver tupla) ---
def simplify_text(text, action_type):
    print("--- Debug: simplify_text function entered!") 
    
    if not text.strip():
        print("--- Debug: simplify_text returning due to empty input.")
        return None, None 
    
    # Prompts revisados
    prompts = {
        "simplify": f"""**TAREA:** Reescribe el siguiente texto (puede ser una oferta de empleo o un CV) para que sea mucho más fácil de entender.
                      **OBJETIVO:** Que una persona sin conocimientos técnicos o experiencia en el sector pueda comprenderlo fácilmente.
                      **INSTRUCCIONES:**
                      1. Elimina toda la jerga técnica innecesaria.
                      2. Usa frases más cortas y lenguaje sencillo.
                      3. Mantén toda la información esencial (responsabilidades, requisitos clave, experiencia relevante).
                      4. No añadas información nueva.
                      
                      **TEXTO ORIGINAL:**
                      {text}
                      
                      **TEXTO SIMPLIFICADO:**""",
        
        "summarize": f"""**TAREA:** Crea un resumen muy conciso (2-3 frases o una lista de 3-5 puntos clave) del siguiente texto.
                      **INSTRUCCIONES:**
                      1. Extrae solo los puntos más importantes.
                      2. Usa lenguaje claro y directo.
                      
                      **TEXTO ORIGINAL:**
                      {text}
                      
                      **RESUMEN CONCISO (Empieza aquí tu respuesta):**""",
        
        # Prompt modificado para improve_cv: pedir reescritura directa
        "improve_cv": f"""Eres un experto en redacción de CVs. **Reescribe** la siguiente sección de un CV para hacerla más impactante y clara, manteniendo el idioma original.

                      **INSTRUCCIONES PARA LA REESCRITURA:**
                      1.  Empieza cada punto o descripción de tarea con un verbo de acción fuerte.
                      2.  Sé conciso y directo.
                      3.  Donde sea apropiado para mostrar impacto, añade un marcador como `[Quantify achievement/impact]` para indicar dónde se podría añadir una métrica real (no inventes números).
                      4.  El resultado debe ser **únicamente la sección del CV reescrita**, no una lista de sugerencias ni comentarios adicionales.

                      **SECCIÓN DE CV ORIGINAL:**
                      {text}

                      **SECCIÓN DE CV REESCRITA:**"""
    }
    
    prompt = prompts.get(action_type)
    if not prompt:
         print(f"--- Debug: Tipo de acción no válida: {action_type}")
         return "Tipo de acción no válida.", None 

    try:
        print(f"--- Debug: Iniciando llamada al modelo para action_type: {action_type}")
        response = model.generate_text(prompt)
        
        # Imprimir respuesta completa para depuración
        print(f"--- Debug: RESPUESTA COMPLETA DEL MODELO:")
        print(response)
        print(f"--- Debug: FIN DE RESPUESTA COMPLETA")

        if action_type == "improve_cv":
            print(f"--- Debug: Entrando en bloque improve_cv / generación PDF.")
            try:
                # Opción más simple: convertir directamente el texto a HTML preservando formato
                # En lugar de intentar procesar de manera compleja, preservamos el formato
                # y añadimos clases CSS básicas que ayuden con la presentación
                
                # Obtener el nombre del CV (primera línea)
                cv_name = text.split('\n')[0].strip() if text else "CV Mejorado"
                
                # Construir el HTML por partes para evitar problemas con f-strings
                cv_header = f'<div class="cv-header"><h1 class="name">{cv_name}</h1></div>'
                print(f'RESPONSE: {response}')
                # Procesar la respuesta del modelo a HTML
                processed_html = convertir_markdown_a_html(response)
                
                # Combinar todo el HTML
                cv_content_html = f'{cv_header}<div class="cv-content">{processed_html}</div>'
                
                # Configurar Jinja2
                env = Environment(loader=FileSystemLoader('.'))
                template = env.get_template('template.html')
                print(f"--- Debug: Plantilla HTML cargada.")

                # Renderizar HTML insertando el HTML procesado en la plantilla
                html_content = template.render(cv_content=cv_content_html)
                print(f"--- Debug: HTML generado (primeros 500 caracteres):")
                print(html_content[:500] + "...")
                print(f"--- Debug: HTML generado:")
                print(html_content)

                # Usar un nombre de archivo fijo en la raíz del proyecto
                pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_cv.pdf")
                print(f"--- Debug: Archivo PDF se guardará en: {pdf_path}")

                # Convertir HTML a PDF
                print(f"--- Debug: CSS cargado correctamente.")
                html_to_pdf_playwright(html_content, pdf_path)
                print(f"--- Debug: PDF generado con éxito en: {pdf_path}")
                
                # IMPORTANTE: Si estamos llegando hasta aquí pero el PDF no se muestra,
                # vamos a comprobar que el archivo existe
                if os.path.exists(pdf_path):
                    print(f"--- Debug: Verificación exitosa! El archivo PDF existe en {pdf_path} con tamaño {os.path.getsize(pdf_path)} bytes")
                else:
                    print(f"--- Debug: ERROR! El archivo PDF NO existe en {pdf_path}")
                
                # Devolvemos None para el TextArea, y la ruta para el File
                print(f"--- Debug: Devolviendo la ruta del PDF: {pdf_path}")
                return None, pdf_path

            except Exception as pdf_e:
                print(f"--- ERROR DETALLADO generando PDF: {type(pdf_e).__name__}: {pdf_e}")
                import traceback
                traceback.print_exc()
                return f"Error al generar PDF: {type(pdf_e).__name__}: {pdf_e}", None
        else:
            # Para otras acciones, devolver el texto para TextArea, None para File
            print(f"--- Debug: Devolviendo respuesta de texto para action_type: {action_type}")
            return response, None

    except Exception as e:
        print(f"--- ERROR procesando texto o llamando al modelo: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return f"Error al procesar el texto: {type(e).__name__}: {e}", None

def extract_requirements(text):
    """Wrapper function to extract key requirements"""
    return extract_key_requirements(text)

def generate_cover_letter(cv_text, job_description):
    """Wrapper function to create cover letter"""
    return create_cover_letter(cv_text, job_description)

# --- Función para actualizar visibilidad ---
def update_output_visibility(action):
    if action == "improve_cv":
        # Ocultar TextArea, Mostrar File
        return gr.update(visible=False), gr.update(visible=True)
    else:
        # Mostrar TextArea, Ocultar File
        return gr.update(visible=True), gr.update(visible=False)

def convertir_markdown_a_html(markdown_texto):
    html = markdown.markdown(markdown_texto, extensions=['extra', 'nl2br'])
    return html


def html_to_pdf_playwright(html_content: str, pdf_path: str):
    with open(file= 'tmp.html',mode= "w", encoding="utf-8") as tmp_html:
        tmp_html.write(html_content)
        tmp_html_path = tmp_html.name

    file_url = f"file://{os.path.abspath(tmp_html_path)}"
    print(f'RUTA DEL FILE TEMPORAL: {file_url}')

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(file_url)
        page.pdf(path=pdf_path, format="A4")
        browser.close()

    os.remove(tmp_html_path)


theme = gr.themes.Ocean(
    primary_hue="blue",
    neutral_hue="gray",
)

# --- Create Gradio interface --- 
with gr.Blocks(theme=theme, title="Asistente de Accesibilidad para Ofertas de Empleo y Currículums") as demo:
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
        with gr.TabItem("Funciones Básicas"):
            with gr.Row():
                with gr.Column():
                    input_text = gr.TextArea(label="Texto de entrada (oferta de empleo o sección de CV)", placeholder="Pega aquí el texto que deseas procesar...", lines=10)
                    action_type = gr.Radio(
                        ["simplify", "summarize", "improve_cv"],
                        label="Selecciona la acción a realizar",
                        value="simplify",
                        info="Elige qué quieres hacer con el texto. 'improve_cv' generará un PDF."
                    )
                    submit_btn = gr.Button("Procesar texto")
                
                with gr.Column():
                    # Componente para salida de TEXTO (inicialmente visible)
                    output_text_display = gr.TextArea(
                        label="Resultado (Texto)", 
                        lines=15, 
                        visible=True 
                    )
                    # Componente para salida de ARCHIVO (inicialmente oculto)
                    output_file_display = gr.File(
                        label="Descargar PDF Generado", 
                        visible=False
                    ) 
            
            # --- Conectar botón y cambio de acción --- 
            submit_btn.click(
                fn=simplify_text, # Llama directamente a simplify_text
                inputs=[input_text, action_type],
                # La salida es una lista con los dos componentes
                outputs=[output_text_display, output_file_display] 
            )
            
            # Cambiar visibilidad cuando cambia la acción seleccionada
            action_type.change(
                fn=update_output_visibility, 
                inputs=action_type, 
                outputs=[output_text_display, output_file_display]
            )
        
        with gr.TabItem("Extracción de Requisitos"):
            with gr.Row():
                with gr.Column():
                    job_description = gr.TextArea(label="Descripción del puesto", placeholder="Pega aquí la oferta de empleo...", lines=10)
                    extract_btn = gr.Button("Extraer requisitos")
                
                with gr.Column():
                    requirements_output = gr.TextArea(label="Requisitos extraídos", lines=10)
            
            extract_btn.click(
                fn=extract_requirements,
                inputs=job_description,
                outputs=requirements_output
            )
        
        with gr.TabItem("Carta de Presentación"):
            with gr.Row():
                with gr.Column():
                    cv_text = gr.TextArea(label="Tu CV", placeholder="Pega aquí tu currículum...", lines=10)
                    job_text = gr.TextArea(label="Oferta de empleo", placeholder="Pega aquí la oferta de empleo...", lines=10)
                    cover_letter_btn = gr.Button("Generar carta de presentación")
                
                with gr.Column():
                    cover_letter_output = gr.TextArea(label="Carta de presentación generada", lines=15)
            
            cover_letter_btn.click(
                fn=generate_cover_letter,
                inputs=[cv_text, job_text],
                outputs=cover_letter_output
            )
        
        with gr.TabItem("Asistente de CV"):
            with gr.Row():
                with gr.Column():
                    job_description_input = gr.TextArea(
                        label="Oferta de Empleo",
                        placeholder="Pega aquí la oferta de empleo para la que quieres crear tu CV...",
                        lines=10
                    )
                    user_input = gr.TextArea(
                        label="Tu respuesta",
                        placeholder="Escribe aquí tu respuesta a la pregunta del agente...",
                        lines=5
                    )
                    agent_btn = gr.Button("Iniciar / Responder")
                
                with gr.Column():
                    agent_output = gr.TextArea(
                        label="Asistente de CV",
                        lines=10,
                        value="Bienvenido al asistente de creación de CV. Para empezar, pega una oferta de empleo en el campo de la izquierda y haz clic en 'Iniciar'."
                    )
                    agent_cv_output = gr.File(
                        label="Descargar CV Generado",
                        visible=False
                    )
            
            # Estado oculto para mantener el contexto de la conversación
            agent_context = gr.State(None)
            
            # Función para procesar cada interacción con el agente
            def process_agent_interaction(job_desc, user_response, context):
                if not job_desc.strip():
                    return "Por favor, introduce primero una oferta de empleo.", context, gr.update(visible=False)
                
                # Llamar al agente
                message, new_context, cv_listo = cv_agent(job_desc, user_response, context)
                
                # Si el CV está listo, generarlo
                if cv_listo:
                    # Generar el CV
                    cv_text = generate_cv_from_agent_data(new_context)
                    
                    # Usar la misma función que simplify_text con improve_cv para generar el PDF
                    _, pdf_path = simplify_text(cv_text, "improve_cv")
                    
                    if pdf_path:
                        return message, new_context, gr.update(visible=True, value=pdf_path)
                    else:
                        return message + "\n\nHubo un problema al generar el PDF. Por favor, inténtalo de nuevo.", new_context, gr.update(visible=False)
                
                return message, new_context, gr.update(visible=False)
            
            # Conectar el botón a la función
            agent_btn.click(
                fn=process_agent_interaction,
                inputs=[job_description_input, user_input, agent_context],
                outputs=[agent_output, agent_context, agent_cv_output]
            )
    gr.Markdown("""
    ### Desarrollado como parte del IBM Challenge ODS8
    
    Este proyecto aborda el Objetivo de Desarrollo Sostenible 8: "Trabajo decente y crecimiento económico",
    facilitando el acceso al empleo mediante la reducción de barreras lingüísticas y de comprensión.
    """)

if __name__ == "__main__":
    demo.launch()