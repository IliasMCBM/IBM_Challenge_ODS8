import os
import gradio as gr
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from advanced_features import (
    analyze_readability,
    extract_key_requirements,
    create_cover_letter,
    translate_to_simple_language
)

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

# Function to simplify text
def simplify_text(text, action_type):
    if not text.strip():
        return "Por favor, introduce algún texto para procesar."
    
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
                      
                      **TEXTO SIMPLIFICADO:**""", # Mantenido como estaba, parecía funcionar
        
        "identify_bias": f"""**TAREA:** Analiza el siguiente texto en busca de lenguaje potencialmente sesgado o excluyente (por género, edad, origen, etc.).
                           **INSTRUCCIONES:**
                           1. Si encuentras frases o palabras problemáticas, indícalas.
                           2. Explica brevemente por qué podrían ser sesgadas.
                           3. Sugiere una alternativa neutral e inclusiva para cada una.
                           4. Si no encuentras sesgos, indica claramente: "No se encontraron sesgos evidentes."
                           
                           **TEXTO A ANALIZAR:**
                           {text}
                           
                           **ANÁLISIS DE SESGOS (Empieza aquí tu respuesta):**""", # Eliminado formato de ejemplo
        
        "summarize": f"""**TAREA:** Crea un resumen muy conciso (2-3 frases o una lista de 3-5 puntos clave) del siguiente texto.
                      **INSTRUCCIONES:**
                      1. Extrae solo los puntos más importantes.
                      2. Usa lenguaje claro y directo.
                      
                      **TEXTO ORIGINAL:**
                      {text}
                      
                      **RESUMEN CONCISO (Empieza aquí tu respuesta):**""", # Simplificado
        
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
        return "Tipo de acción no válida."
    
    try:
        response = model.generate_text(prompt)
        return response
    except Exception as e:
        return f"Error al procesar el texto: {str(e)}"

def analyze_text(text):
    """Wrapper function to analyze readability"""
    return analyze_readability(text)

def extract_requirements(text):
    """Wrapper function to extract key requirements"""
    return extract_key_requirements(text)

def generate_cover_letter(cv_text, job_description):
    """Wrapper function to create cover letter"""
    return create_cover_letter(cv_text, job_description)

def simplify_by_level(text, level):
    """Wrapper function to translate to simple language by level"""
    return translate_to_simple_language(text, level)

# Create Gradio interface
with gr.Blocks(theme=gr.themes.Base(), title="Asistente de Accesibilidad para Ofertas de Empleo y Currículums") as demo:
    gr.Markdown("""
    # Asistente de Accesibilidad para Ofertas de Empleo y Currículums
    
    Esta herramienta ayuda a hacer más accesibles las ofertas de empleo y currículums mediante diversas funciones de procesamiento de texto.
    """)
    
    with gr.Tabs():
        with gr.TabItem("Funciones Básicas"):
            with gr.Row():
                with gr.Column():
                    input_text = gr.TextArea(label="Texto de entrada (oferta de empleo o sección de CV)", placeholder="Pega aquí el texto que deseas procesar...", lines=10)
                    action_type = gr.Radio(
                        ["simplify", "identify_bias", "summarize", "improve_cv"],
                        label="Selecciona la acción a realizar",
                        value="simplify",
                        info="Elige qué quieres hacer con el texto"
                    )
                    submit_btn = gr.Button("Procesar texto")
                
                with gr.Column():
                    output_text = gr.TextArea(label="Resultado", lines=10)
            
            submit_btn.click(
                fn=simplify_text,
                inputs=[input_text, action_type],
                outputs=output_text
            )
        
        with gr.TabItem("Análisis de Legibilidad"):
            with gr.Row():
                with gr.Column():
                    readability_input = gr.TextArea(label="Texto para analizar", placeholder="Pega aquí el texto que deseas analizar...", lines=10)
                    analyze_btn = gr.Button("Analizar legibilidad")
                
                with gr.Column():
                    readability_output = gr.TextArea(label="Análisis de legibilidad", lines=10)
            
            analyze_btn.click(
                fn=analyze_text,
                inputs=readability_input,
                outputs=readability_output
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
        
        with gr.TabItem("Simplificación por Nivel"):
            with gr.Row():
                with gr.Column():
                    complex_text = gr.TextArea(label="Texto complejo", placeholder="Pega aquí el texto que deseas simplificar...", lines=10)
                    level = gr.Radio(
                        ["básico", "intermedio", "avanzado"],
                        label="Nivel de simplificación",
                        value="intermedio",
                        info="Básico: para nivel educativo bajo, Intermedio: para público general, Avanzado: profesional pero simplificado"
                    )
                    simplify_btn = gr.Button("Simplificar texto")
                
                with gr.Column():
                    simplified_output = gr.TextArea(label="Texto simplificado", lines=10)
            
            simplify_btn.click(
                fn=simplify_by_level,
                inputs=[complex_text, level],
                outputs=simplified_output
            )
    
    gr.Markdown("""
    ### Desarrollado como parte del IBM Challenge ODS8
    
    Este proyecto aborda el Objetivo de Desarrollo Sostenible 8: "Trabajo decente y crecimiento económico",
    facilitando el acceso al empleo mediante la reducción de barreras lingüísticas y de comprensión.
    """)

if __name__ == "__main__":
    demo.launch()