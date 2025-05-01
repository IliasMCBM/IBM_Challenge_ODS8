import os
import gradio as gr
import re  # Añadido para expresiones regulares
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from advanced_features import (
    analyze_readability,
    extract_key_requirements,
    create_cover_letter,
    translate_to_simple_language,
    cv_agent,
    generate_cv_from_agent_data
)
# Imports para PDF
import tempfile
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

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

# Nueva función para procesar la salida del modelo en formato CV y convertirla en HTML estructurado
def process_cv_output_to_html(raw_text):
    """
    Convierte el texto generado por el modelo (con asteriscos para negrita)
    en HTML estructurado con clases CSS para un CV profesional.
    """
    print("--- Debug: Procesando salida del modelo a HTML estructurado")
    
    # Divido el texto por líneas para procesarlo
    lines = raw_text.strip().split('\n')
    
    # Extraigo información básica (nombre, título, contacto)
    name = ""
    title = ""
    contact_info = ""
    
    # Buscar nombre (generalmente la primera línea con asteriscos)
    for i, line in enumerate(lines):
        if re.search(r'\*\*([^*]+)\*\*', line):
            name = re.search(r'\*\*([^*]+)\*\*', line).group(1).strip()
            lines[i] = ""  # Elimino esta línea del original
            break
    
    # Buscar título/profesión (generalmente en las primeras líneas)
    for i, line in enumerate(lines):
        if re.search(r'\*\*([^*|]+)\|([^*]+)\*\*', line):
            # Formato típico: **Profesión | Ubicación**
            match = re.search(r'\*\*([^*|]+)\|([^*]+)\*\*', line)
            title = match.group(1).strip()
            lines[i] = ""
            break
        elif name and line and '**' in line and i < 5:
            # Si no encuentro el formato exacto, uso la siguiente línea con asteriscos
            title = line.replace('*', '').strip()
            lines[i] = ""
            break
    
    # Buscar información de contacto
    for i, line in enumerate(lines):
        if 'Contact:' in line or 'contact:' in line or '+' in line or '@' in line:
            contact_info = line.replace('**Contact:**', '').replace('**', '').strip()
            lines[i] = ""
            break
    
    # Construyo el HTML estructurado
    html = f"""
    <div class="cv-header">
        <h1 class="name">{name}</h1>
        <h2 class="title">{title}</h2>
        <div class="contact-info">
            {contact_info}
        </div>
    </div>
    """
    
    # Procesamiento de secciones
    current_section = None
    section_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detecto secciones importantes (EDUCATION, EXPERIENCE, etc.)
        if re.match(r'\*\*(EDUCATION|EXPERIENCE|SKILLS|KNOWLEDGE|CERTIFICATIONS|AWARDS|PROJECTS)\*\*', line, re.IGNORECASE):
            # Si hay una sección en proceso, la cierro
            if current_section:
                html += process_section(current_section, section_content)
                section_content = []
            
            # Inicio una nueva sección
            current_section = re.match(r'\*\*(.*?)\*\*', line).group(1).upper()
            continue
            
        # Añado línea al contenido de la sección actual
        if current_section:
            section_content.append(line)
    
    # Proceso la última sección
    if current_section and section_content:
        html += process_section(current_section, section_content)
    
    return html

def process_section(section_name, content_lines):
    """
    Procesa una sección específica del CV y genera el HTML correspondiente.
    """
    html = f'<div class="cv-section">\n'
    html += f'<h2 class="section-title">{section_name}</h2>\n'
    
    if section_name in ["EDUCATION", "EXPERIENCE"]:
        html += process_entries(content_lines)
    elif section_name in ["KNOWLEDGE", "SKILLS"]:
        html += process_skills(content_lines)
    elif section_name in ["CERTIFICATIONS", "AWARDS"]:
        html += process_certifications(content_lines)
    else:
        # Para otras secciones, procesar como contenido genérico
        html += '<div class="section-content">\n'
        for line in content_lines:
            # Reemplazo asteriscos con etiquetas de énfasis
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            html += f'<p>{processed_line}</p>\n'
        html += '</div>\n'
    
    html += '</div>\n'
    return html

def process_entries(content_lines):
    """
    Procesa entradas de educación o experiencia laboral.
    """
    html = ""
    current_entry = {}
    entries = []
    
    for line in content_lines:
        if '|' in line and '**' in line:
            # Si hay una entrada en proceso, la guardamos
            if current_entry:
                entries.append(current_entry)
                current_entry = {}
            
            # Formato típico: **Organización | Fecha**
            match = re.search(r'\*\*([^*|]+)\|([^*]+)\*\*', line)
            if match:
                current_entry["organization"] = match.group(1).strip()
                current_entry["date"] = match.group(2).strip()
                current_entry["descriptions"] = []
            else:
                # Si no coincide exactamente, intentamos extraer lo que podamos
                org_name = re.search(r'\*\*(.*?)\*\*', line)
                if org_name:
                    current_entry["organization"] = org_name.group(1).strip()
                    # Intentar extraer fecha si existe
                    date_match = re.search(r'(\w+\s+\d{4}\s*-\s*\w*\s*\d*)', line)
                    current_entry["date"] = date_match.group(1).strip() if date_match else ""
                    current_entry["descriptions"] = []
        
        elif line.startswith('**') and ':' in line:
            # Formato: **Título:** Descripción
            parts = line.split(':', 1)
            title = parts[0].replace('**', '').strip()
            desc = parts[1].strip() if len(parts) > 1 else ""
            
            if "title" not in current_entry:
                current_entry["title"] = title
            
            if desc:
                current_entry["descriptions"].append(desc)
        
        elif line.startswith('**'):
            # Podría ser un título
            title = line.replace('**', '').strip()
            if "title" not in current_entry:
                current_entry["title"] = title
        
        elif line.startswith('•') or line.startswith('-'):
            # Punto de una lista
            desc = line.replace('•', '').replace('-', '').strip()
            if current_entry and "descriptions" in current_entry:
                current_entry["descriptions"].append(desc)
        
        else:
            # Descripción general
            if current_entry and "descriptions" in current_entry:
                current_entry["descriptions"].append(line)
    
    # Añadir la última entrada
    if current_entry:
        entries.append(current_entry)
    
    # Generar HTML para cada entrada
    for entry in entries:
        html += '<div class="entry">\n'
        
        if "organization" in entry:
            html += f'<div class="entry-organization">{entry["organization"]}</div>\n'
        
        if "title" in entry:
            html += f'<div class="entry-title">{entry["title"]}</div>\n'
        
        if "date" in entry:
            html += f'<div class="entry-date">{entry["date"]}</div>\n'
        
        if "descriptions" in entry and entry["descriptions"]:
            html += '<div class="entry-description">\n<ul>\n'
            for desc in entry["descriptions"]:
                html += f'<li>{desc}</li>\n'
            html += '</ul>\n</div>\n'
        
        html += '</div>\n'
    
    return html

def process_skills(content_lines):
    """
    Procesa secciones de habilidades y conocimientos.
    """
    html = '<div class="skills-section">\n'
    current_category = None
    category_skills = []
    categories = []
    
    for line in content_lines:
        if line.startswith('**') and line.endswith(':**'):
            # Nueva categoría de habilidad
           
            
            current_category = line.replace('**', '').replace(':', '')
        elif current_category and line:
            # Habilidad dentro de categoría
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Quitar asteriscos
            category_skills.append(clean_line)
    
    # Añadir la última categoría
    if current_category and category_skills:
        categories.append({"name": current_category, "skills": category_skills})
    
    # Generar HTML para cada categoría
    for category in categories:
        html += f'<div class="skill-category">\n'
        html += f'<h3 class="skill-category-title">{category["name"]}</h3>\n'
        html += '<ul class="skill-list">\n'
        
        for skill in category["skills"]:
            html += f'<li>{skill}</li>\n'
        
        html += '</ul>\n</div>\n'
    
    html += '</div>\n'
    return html

def process_certifications(content_lines):
    """
    Procesa secciones de certificaciones y premios.
    """
    html = '<div class="certifications">\n<ul>\n'
    
    for line in content_lines:
        clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Quitar asteriscos
        if clean_line:
            html += f'<li>{clean_line}</li>\n'
    
    html += '</ul>\n</div>\n'
    return html

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
        
        "identify_bias": f"""**TAREA:** Analiza el siguiente texto en busca de lenguaje potencialmente sesgado o excluyente (por género, edad, origen, etc.).
                           **INSTRUCCIONES:**
                           1. Si encuentras frases o palabras problemáticas, indícalas.
                           2. Explica brevemente por qué podrían ser sesgadas.
                           3. Sugiere una alternativa neutral e inclusiva para cada una.
                           4. Si no encuentras sesgos, indica claramente: "No se encontraron sesgos evidentes."
                           
                           **TEXTO A ANALIZAR:**
                           {text}
                           
                           **ANÁLISIS DE SESGOS (Empieza aquí tu respuesta):**""",
        
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
                
                # Procesar la respuesta del modelo a HTML
                processed_html = process_cv_text_to_html(response)
                
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

                # Usar un nombre de archivo fijo en la raíz del proyecto
                pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_cv.pdf")
                print(f"--- Debug: Archivo PDF se guardará en: {pdf_path}")

                # Convertir HTML a PDF
                css = CSS(filename='style.css')
                print(f"--- Debug: CSS cargado correctamente.")
                HTML(string=html_content, base_url='.').write_pdf(pdf_path, stylesheets=[css])
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

# --- Función para actualizar visibilidad ---
def update_output_visibility(action):
    if action == "improve_cv":
        # Ocultar TextArea, Mostrar File
        return gr.update(visible=False), gr.update(visible=True)
    else:
        # Mostrar TextArea, Ocultar File
        return gr.update(visible=True), gr.update(visible=False)

def process_cv_text_to_html(text):
    """
    Convierte el texto de CV (posiblemente con marcado de Markdown o asteriscos) 
    en HTML estructurado, preservando el formato y mejorando la presentación.
    Enfoque flexible que funciona con cualquier estructura de CV.
    """
    if not text:
        return ""
    
    # Separar por líneas para mejor procesamiento
    lines = text.strip().split('\n')
    html_parts = []
    
    # Variables para detectar secciones
    current_section = None
    
    # Definir patrones de expresión regular fuera de f-strings
    date_pattern = r'\d{4}[-—–]\d{4}|\d{4}[-—–]Present|[A-Za-z]+\s+\d{4}'
    
    # Procesar línea por línea
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            html_parts.append("<br>")
            continue
        
        # Detectar encabezados/secciones (líneas en mayúsculas o con **)
        if line.isupper() or (line.startswith('**') and line.endswith('**')):
            # Es un encabezado de sección
            clean_heading = line.replace('*', '').strip()
            if current_section:
                # Si ya estábamos en una sección, cerramos la div
                html_parts.append("</div>")
            
            current_section = clean_heading
            html_parts.append(f'<div class="cv-section">')
            html_parts.append(f'<h2 class="section-title">{clean_heading}</h2>')
            continue
        
        # Detectar datos de contacto (email, teléfono, etc.)
        if '@' in line or '+' in line or ('http' in line and 'linkedin' in line.lower()):
            html_parts.append(f'<div class="contact-info">{line}</div>')
            continue
            
        # Detectar experiencias/elementos con fechas
        if re.search(date_pattern, line):
            # Es probable que sea un elemento con fecha (experiencia/educación)
            # Si contiene '|' probablemente sea "Posición | Fechas"
            if '|' in line:
                parts = line.split('|')
                position = parts[0].replace('*', '').strip()
                date = parts[1].replace('*', '').strip()
                html_parts.append(f'<div class="entry">')
                html_parts.append(f'<div class="entry-title">{position}</div>')
                html_parts.append(f'<div class="entry-date">{date}</div>')
            else:
                # Si no tiene formato estándar, lo ponemos como está
                html_parts.append(f'<div class="entry">')
                html_parts.append(f'<div class="entry-organization">{line.replace("*", "")}</div>')
            continue
        
        # Detectar elementos de lista (puntos con • o -)
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            entry_text = line[1:].strip()
            if html_parts and len(html_parts) > 0 and html_parts[-1].endswith('</ul>'):
                # Ya tenemos una lista abierta, simplemente añadimos el elemento
                html_parts[-1] = html_parts[-1][:-5]  # Quitar el cierre </ul>
                html_parts.append(f'<li>{entry_text}</li>')
                html_parts.append('</ul>')
            else:
                # Nueva lista
                html_parts.append('<ul class="skill-list">')
                html_parts.append(f'<li>{entry_text}</li>')
                html_parts.append('</ul>')
            continue
            
        # Procesar formato en negrita (** **)
        processed_line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)
            
        # Línea de texto normal (quizás con alguna marca)
        html_parts.append(f'<p>{processed_line}</p>')
    
    # Cerrar última sección si existe
    if current_section:
        html_parts.append("</div>")
        
    return '\n'.join(html_parts)

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
                        ["simplify", "identify_bias", "summarize", "improve_cv"],
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