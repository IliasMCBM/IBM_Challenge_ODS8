import re # Asegúrate de tener esta importación al principio del archivo
import os
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

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
        "max_new_tokens": 1024,  # Aumentado a 1024
        "temperature": 0.6, # Reducido ligeramente para mayor coherencia
    }
)

# Ajustar parámetros del modelo - un poco más de flexibilidad
model.params = {
    "max_new_tokens": 1024,
    "temperature": 0.6, # Ligeramente aumentado
    "top_k": 50,
    "top_p": 0.95
    # Considerar añadir repetition_penalty si está disponible y el problema persiste
}

# Advanced text processing functions

def analyze_readability(text):
    """
    Analyzes the readability level of a text and suggests improvements
    to make it more accessible.
    """
    prompt = f"""Analiza el nivel de legibilidad del siguiente texto. 
    Proporciona una puntuación del 1 al 10 (donde 1 es muy difícil de entender y 10 es muy fácil).
    Identifica las partes más complejas y sugiere cómo simplificarlas sin perder información importante:
    
    {text}
    """
    
    try:
        response = model.generate_text(prompt)
        return response
    except Exception as e:
        return f"Error al analizar la legibilidad: {str(e)}"

def extract_key_requirements(text):
    """
    Extracts and lists the key skills, qualifications, and requirements
    from a job posting in a clear, structured format.
    """
    prompt = f"""Extrae y lista las habilidades clave, calificaciones y requisitos
    de la siguiente oferta de empleo en un formato claro y estructurado:
    
    {text}
    
    Formato de salida:
    - Habilidades técnicas: [lista]
    - Habilidades blandas: [lista]
    - Formación académica: [lista]
    - Experiencia requerida: [lista]
    - Idiomas: [lista]
    - Otros requisitos: [lista]
    """
    
    try:
        response = model.generate_text(prompt)
        return response
    except Exception as e:
        return f"Error al extraer requisitos clave: {str(e)}"

def create_cover_letter(cv_text, job_text):
    """
    Creates a tailored cover letter based on a CV and job description,
    highlighting relevant experience and skills.
    """
    if not cv_text.strip() or not job_text.strip():
        return "Error: Necesitas proporcionar tanto tu CV como la descripción del puesto."

    print(f"--- Debug: CV Text Received (first 100 chars): {cv_text[:100]}...")
    print(f"--- Debug: Job Text Received (first 100 chars): {job_text[:100]}...")

    # Intento simple de extraer el nombre del candidato del CV
    candidate_name = "El/La Candidato/a" # Valor por defecto
    try:
        # Buscar líneas que probablemente contengan el nombre (ej. la primera línea no vacía)
        lines = cv_text.split('\\n') # Asumiendo que \n puede ser el separador
        if not lines or len(lines) <= 1:
             lines = cv_text.split('\n') # Probar con newline estándar

        for line in lines:
            line = line.strip()
            # Heurística: línea corta, sin caracteres especiales comunes de contacto/dirección
            if line and '|' not in line and '@' not in line and ':' not in line and len(line.split()) < 5:
                 candidate_name = line
                 print(f"--- Debug: Possible candidate name extracted: {candidate_name}")
                 break
        # Si no se encontró, intentar extraer del email si existe
        if candidate_name == "El/La Candidato/a":
             match = re.search(r'Email:\s*([\w.-]+)@', cv_text, re.IGNORECASE)
             if match:
                 name_part = match.group(1).replace('.', ' ').replace('-', ' ').title()
                 # Comprobar si parece un nombre
                 if len(name_part.split()) <= 3 and not any(kw in name_part.lower() for kw in ['info', 'contact', 'admin', 'cv', 'resume']):
                     candidate_name = name_part
                     print(f"--- Debug: Possible candidate name extracted from email: {candidate_name}")

    except Exception as e:
        print(f"--- Debug: Error extracting name, using default: {e}")
        candidate_name = "El/La Candidato/a"


    # Prompt modificado para evitar placeholders y usar el nombre extraído
    prompt = f"""**TAREA OBLIGATORIA:** Escribe **SOLO EL CUERPO** de una carta de presentación formal **EN ESPAÑOL**.

**REGLAS ESTRICTAS:**
*   **NO** repitas la oferta de empleo.
*   **NO** incluyas encabezados (direcciones, fechas, datos del receptor).
*   **NO** uses placeholders genéricos como `[Tu Nombre]`, `[Receptor]`, `[Fecha]`, etc.
*   Empieza directamente con el saludo formal (ej. "Estimado/a equipo de contratación,").
*   Termina directamente con la despedida formal (ej. "Atentamente,") seguida por el nombre del candidato: **{candidate_name}**.

**INSTRUCCIONES:**
1.  Lee el **CV DEL CANDIDATO** para entender su perfil.
2.  Lee la **OFERTA DE EMPLEO** para entender los requisitos.
3.  Escribe el cuerpo de la carta **EN ESPAÑOL**, explicando cómo la experiencia y habilidades del **CV DEL CANDIDATO** (cuyo nombre es {candidate_name}) son adecuadas para la **OFERTA DE EMPLEO**. Conecta el CV con la oferta.

**CV DEL CANDIDATO:**
---
{cv_text}
---

**OFERTA DE EMPLEO (SOLO PARA CONTEXTO, NO COPIAR):**
---
{job_text}
---

**CUERPO DE LA CARTA DE PRESENTACIÓN GENERADO (EN ESPAÑOL, SIN ENCABEZADOS/PLACEHOLDERS, USANDO '{candidate_name}' AL FINAL):**
"""

    try:
        response = model.generate_text(prompt)
        print(f"--- Debug: Raw Model Response (before potential cleanup): {response}")

        # Limpieza adicional por si el modelo aún incluye placeholders (menos ideal)
        response_cleaned = response.strip()
        # Eliminar líneas de encabezado/pie si aún aparecen (heurística)
        lines = response_cleaned.split('\n')
        final_lines = []
        in_body = False
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.lower().startswith(("estimado", "estimada", "a la atención")):
                in_body = True
            if in_body and not (stripped_line.startswith('[') and stripped_line.endswith(']')):
                 # Evitar añadir líneas que sean solo placeholders
                 if stripped_line or final_lines: # Mantener líneas vacías dentro del cuerpo si existen
                    final_lines.append(line) # Mantener indentación original si es relevante

        response_cleaned = '\n'.join(final_lines).strip()

        # Reemplazar placeholder final si aún existe y tenemos un nombre
        if candidate_name != "El/La Candidato/a":
             response_cleaned = response_cleaned.replace("[Tu Nombre]", candidate_name)
             # Considerar reemplazar también variaciones como [Nombre] si aparecen

        print(f"--- Debug: Cleaned Model Response: {response_cleaned}")


        # Validaciones sobre la respuesta LIMPIA
        if not response_cleaned.lower().startswith(("estimado", "estimada", "a la atención")):
             print("--- Debug: Cleaned response does not seem to start like a formal Spanish letter body.")
             if job_text[:50].strip() in response_cleaned[:200]:
                 print("--- Debug: Cleaned response might be repeating the job description again.")
             if "[Tu Nombre]" in response_cleaned or "[Receptor]" in response_cleaned:
                 print("--- Debug: Cleaned response still contains placeholders.")
             # Devolver la respuesta limpia para inspección incluso si falla el inicio
             return response_cleaned

        if job_text[100:200].strip() in response_cleaned:
            print("--- Debug: Warning - Cleaned response might contain parts of the job description.")

        return response_cleaned
    except Exception as e:
        return f"Error al crear la carta de presentación: {str(e)}"

def translate_to_simple_language(text, target_level="básico"):
    """
    Translates technical or complex text into simpler language at a specified level.
    Levels: básico, intermedio, avanzado
    """
    level_mapping = {
        "básico": "muy simple y accesible, apto para personas con bajo nivel educativo o discapacidades cognitivas",
        "intermedio": "moderadamente simple, evitando tecnicismos innecesarios pero manteniendo cierta complejidad",
        "avanzado": "profesional pero claro, simplificando solo los tecnicismos más especializados"
    }
    
    level_description = level_mapping.get(target_level, level_mapping["básico"])
    
    prompt = f"""Traduce el siguiente texto a un lenguaje {level_description}.
    Mantén toda la información importante pero simplifica la estructura y vocabulario:
    
    {text}
    """
    
    try:
        response = model.generate_text(prompt)
        return response
    except Exception as e:
        return f"Error al traducir a lenguaje simple: {str(e)}"