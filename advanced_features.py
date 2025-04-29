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

# Ajustar parámetros del modelo - más restrictivos
model.params = {
    "max_new_tokens": 1024,
    "temperature": 0.4, # Aún más bajo
    "top_k": 40,
    "top_p": 0.9
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

def cv_agent(job_description, user_input="", context=None):
    """
    Actúa como un agente conversacional que recopila información del usuario para crear un CV
    basado en una oferta de empleo. Mantiene el contexto de la conversación y va haciendo
    preguntas específicas según la fase en que se encuentre.
    
    Args:
        job_description: La oferta de empleo completa
        user_input: La respuesta del usuario a la pregunta anterior
        context: Diccionario con el contexto de la conversación (estado, datos recopilados, etc.)
    
    Returns:
        Tuple: (mensaje_para_usuario, contexto_actualizado, cv_listo)
            - mensaje_para_usuario: La siguiente pregunta o mensaje para el usuario
            - contexto_actualizado: El contexto actualizado con la nueva información
            - cv_listo: Boolean indicando si el CV está listo para ser generado
    """
    # Si es la primera interacción, inicializar contexto
    if not context:
        # Analizar la oferta de empleo para extraer requisitos clave
        prompt = f"""Analiza esta oferta de empleo y extrae:
        1. El título del puesto
        2. Las habilidades técnicas clave requeridas (lista de 3-5)
        3. La experiencia mínima requerida (en años si se especifica)
        
        Oferta de empleo:
        {job_description}
        
        Responde en formato JSON así:
        {{
            "titulo": "Título del puesto",
            "habilidades": ["habilidad1", "habilidad2", "..."],
            "experiencia_requerida": "X años en..."
        }}
        """
        
        try:
            job_analysis = model.generate_text(prompt)
            # Convertir el análisis a estructura, pero como no podemos usar json.loads,
            # usamos un enfoque simplificado extrayendo la información con regex
            import re
            
            titulo_match = re.search(r'"titulo":\s*"([^"]+)"', job_analysis)
            titulo = titulo_match.group(1) if titulo_match else "puesto ofertado"
            
            # Inicializar contexto para la primera pregunta
            context = {
                "estado": "datos_personales",
                "datos": {
                    "oferta": {
                        "titulo": titulo,
                        "descripcion": job_description
                    },
                    "personales": {},
                    "experiencia": [],
                    "educacion": [],
                    "habilidades": []
                },
                "preguntas_hechas": 0
            }
            
            # Primera pregunta sobre datos personales
            return (
                f"Hola, voy a ayudarte a crear un CV adaptado para la oferta de '{titulo}'. "
                f"Para empezar, necesito algunos datos personales básicos. "
                f"¿Podrías proporcionarme tu nombre completo, correo electrónico y número de teléfono?",
                context,
                False
            )
        except Exception as e:
            return f"Error al analizar la oferta de empleo: {str(e)}", None, False
    
    # Procesar la respuesta del usuario según el estado
    if context["estado"] == "datos_personales":
        # Extraer datos personales de la respuesta usando peticiones individuales para cada dato
        try:
            print("\n----- PROCESAMIENTO DE DATOS PERSONALES -----")
            print(f"ENTRADA DE USUARIO: '{user_input}'")
            
            # Extraer nombre
            prompt_nombre = f"""Lee el siguiente texto y extrae SOLO el nombre completo de la persona:
            
            Texto: "{user_input}"
            
            Responde SOLO con el nombre completo, sin añadir ningún otro texto ni explicaciones.
            """
            try:
                nombre = model.generate_text(prompt_nombre)
                nombre = nombre.strip()
                print(f"NOMBRE EXTRAÍDO: '{nombre}'")
                context["datos"]["personales"]["nombre"] = nombre
            except Exception as e:
                print(f"ERROR AL EXTRAER NOMBRE: {str(e)}")
                context["datos"]["personales"]["nombre"] = "Usuario"
                
            # Extraer email
            prompt_email = f"""Lee el siguiente texto y extrae SOLO la dirección de correo electrónico:
            
            Texto: "{user_input}"
            
            Responde SOLO con la dirección de email, sin añadir ningún otro texto ni explicaciones.
            """
            try:
                email = model.generate_text(prompt_email)
                email = email.strip()
                print(f"EMAIL EXTRAÍDO: '{email}'")
                context["datos"]["personales"]["email"] = email
            except Exception as e:
                print(f"ERROR AL EXTRAER EMAIL: {str(e)}")
                context["datos"]["personales"]["email"] = ""
                
            # Extraer teléfono
            prompt_telefono = f"""Lee el siguiente texto y extrae SOLO el número de teléfono:
            
            Texto: "{user_input}"
            
            Responde SOLO con el número de teléfono, sin añadir ningún otro texto ni explicaciones.
            """
            try:
                telefono = model.generate_text(prompt_telefono)
                telefono = telefono.strip()
                print(f"TELÉFONO EXTRAÍDO: '{telefono}'")
                context["datos"]["personales"]["telefono"] = telefono
            except Exception as e:
                print(f"ERROR AL EXTRAER TELÉFONO: {str(e)}")
                context["datos"]["personales"]["telefono"] = ""
            
            # Imprimir datos finales extraídos
            print("\nDATOS PERSONALES EXTRAÍDOS:")
            print(f"Nombre: '{context['datos']['personales'].get('nombre')}'")
            print(f"Email: '{context['datos']['personales'].get('email')}'")
            print(f"Teléfono: '{context['datos']['personales'].get('telefono')}'")
            
            # Verificar si se obtuvieron los datos mínimos necesarios
            if context["datos"]["personales"].get("nombre") and context["datos"]["personales"].get("email"):
                # Actualizar estado para pasar a experiencia laboral
                context["estado"] = "experiencia_laboral"
                print("\nDATO EXTRAÍDOS CORRECTAMENTE - Pasando a experiencia laboral")
                
                # Pregunta sobre experiencia laboral
                return (
                    f"Gracias, {context['datos']['personales'].get('nombre')}. "
                    f"Ahora, cuéntame sobre tu experiencia laboral relevante para el puesto de {context['datos']['oferta']['titulo']}. "
                    f"Por favor, menciona el nombre de la empresa, tu cargo, fechas y una breve descripción de tus responsabilidades.",
                    context,
                    False
                )
            else:
                # Si aún no se pudieron extraer los datos mínimos
                print("\nNO SE PUDIERON EXTRAER TODOS LOS DATOS NECESARIOS")
                return "No he podido identificar claramente todos tus datos. Por favor, proporcióname tu información así:\n\nNombre: Ilias Amchichou\nEmail: iliasamchichou@gmail.com\nTeléfono: 657514688", context, False
                
        except Exception as e:
            import traceback
            print(f"\nERROR GENERAL EN PROCESAMIENTO DE DATOS: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            return "Lo siento, ha ocurrido un error al procesar tus datos. Por favor, proporcióname tu información así:\n\nNombre: Ilias Amchichou\nEmail: iliasamchichou@gmail.com\nTeléfono: 657514688", context, False
    
    elif context["estado"] == "experiencia_laboral":
        # Extraer experiencia laboral de la respuesta
        print("\n----- PROCESAMIENTO DE EXPERIENCIA LABORAL -----")
        print(f"ENTRADA DE USUARIO: '{user_input}'")
        
        try:
            # Primero, guardamos la experiencia en el contexto independientemente del análisis
            context["datos"]["experiencia"].append(user_input)
            context["preguntas_hechas"] += 1
            print(f"Experiencia guardada. Preguntas hechas hasta ahora: {context['preguntas_hechas']}")
            
            # Analizamos la experiencia para ver si necesita más detalles
            prompt = f"""Analiza esta experiencia laboral:
            {user_input}
            
            Identifica:
            1. Si es suficientemente detallada o necesita más información
            2. Si es relevante para el puesto: {context['datos']['oferta']['titulo']}
            3. Si menciona duración o años de experiencia
            
            Responde en el siguiente formato:
            {{
                "es_completa": true/false,
                "es_relevante": true/false,
                "experiencia_total_anios": X,
                "necesita_mas_detalles": true/false
            }}
            """
            
            try:
                print("Solicitando análisis de experiencia al modelo...")
                analisis = model.generate_text(prompt)
                print(f"ANÁLISIS RECIBIDO: '{analisis}'")
                
                # Extraer análisis con regex de forma más flexible
                es_completa = "true" in re.search(r'"es_completa":\s*(true|false)', analisis, re.IGNORECASE).group(1) if re.search(r'"es_completa":\s*(true|false)', analisis, re.IGNORECASE) else False
                es_relevante = "true" in re.search(r'"es_relevante":\s*(true|false)', analisis, re.IGNORECASE).group(1) if re.search(r'"es_relevante":\s*(true|false)', analisis, re.IGNORECASE) else True
                necesita_detalles = "true" in re.search(r'"necesita_mas_detalles":\s*(true|false)', analisis, re.IGNORECASE).group(1) if re.search(r'"necesita_mas_detalles":\s*(true|false)', analisis, re.IGNORECASE) else False
                
                print(f"ANÁLISIS DE LA EXPERIENCIA:")
                print(f"- ¿Es completa? {es_completa}")
                print(f"- ¿Es relevante? {es_relevante}")
                print(f"- ¿Necesita más detalles? {necesita_detalles}")
                
            except Exception as e:
                print(f"Error en el análisis de experiencia: {e}")
                print("Asumiendo valores por defecto para continuar")
                # En caso de error, asumimos valores por defecto para no interrumpir el flujo
                es_completa = True
                es_relevante = True
                necesita_detalles = False
            
            # Si necesita más detalles y no hemos hecho muchas preguntas, pedir más información
            if necesita_detalles and context["preguntas_hechas"] < 4:
                print("Solicitando más detalles sobre la experiencia")
                return (
                    "Gracias por la información sobre tu experiencia en NWorld. ¿Podrías proporcionar más detalles "
                    "sobre tus proyectos específicos con Databricks y Spark en Scala? Por ejemplo, "
                    "¿qué tipo de análisis de datos realizabas o qué problemas resolvías?",
                    context,
                    False
                )
            else:
                # Pasar a educación
                print("Pasando a la etapa de educación")
                context["estado"] = "educacion"
                return (
                    "Gracias por compartir tu experiencia con Databricks y Spark. Ahora, ¿podrías indicarme tu formación académica? "
                    "Incluye títulos, instituciones y años de graduación.",
                    context,
                    False
                )
        except Exception as e:
            import traceback
            print(f"\nERROR GENERAL EN PROCESAMIENTO DE EXPERIENCIA: {type(e).__name__}: {str(e)}")
            print(traceback.format_exc())
            
            # En caso de error, guardar la experiencia y continuar con educación
            if user_input:
                context["datos"]["experiencia"].append(user_input)
                context["preguntas_hechas"] += 1
                context["estado"] = "educacion"
                return (
                    "He registrado tu experiencia. Ahora, ¿podrías indicarme tu formación académica? "
                    "Incluye títulos, instituciones y años de graduación.",
                    context,
                    False
                )
            else:
                return "Lo siento, ha ocurrido un error. Por favor, resume brevemente tu experiencia laboral mencionando empresa, cargo y tecnologías utilizadas.", context, False
    
    elif context["estado"] == "educacion":
        # Guardar educación
        context["datos"]["educacion"].append(user_input)
        
        # Pasar a habilidades
        context["estado"] = "habilidades"
        return (
            "Perfecto. Por último, ¿qué habilidades técnicas y blandas consideras que te hacen "
            f"idóneo/a para el puesto de {context['datos']['oferta']['titulo']}?",
            context,
            False
        )
    
    elif context["estado"] == "habilidades":
        # Guardar habilidades
        context["datos"]["habilidades"].append(user_input)
        
        # Finalizar recopilación
        context["estado"] = "finalizado"
        return (
            "¡Genial! He recopilado toda la información necesaria para crear tu CV adaptado a "
            f"la oferta de {context['datos']['oferta']['titulo']}. Ahora generaré un CV profesional "
            "basado en tus datos y optimizado para esta oferta específica.",
            context,
            True  # Indicar que el CV está listo para ser generado
        )
    
    elif context["estado"] == "finalizado":
        # Ya hemos terminado, generar el CV
        return "Tu CV ya está listo para ser generado.", context, True
    
    else:
        return "Ha ocurrido un error en el proceso. Por favor, inténtalo de nuevo.", None, False

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

def generate_cv_from_agent_data(context):
    """
    Genera un CV en formato de texto a partir de los datos recopilados por el agente.
    
    Args:
        context: Diccionario con el contexto completo de la conversación, incluyendo todos los datos recopilados
    
    Returns:
        String: CV formateado listo para ser convertido a PDF
    """
    if not context or "datos" not in context:
        return "Error: No hay suficientes datos para generar el CV."
    
    datos = context["datos"]
    
    # Extraer los datos personales
    nombre = datos["personales"].get("nombre", "")
    email = datos["personales"].get("email", "")
    telefono = datos["personales"].get("telefono", "")
    
    # Crear prompt para generar el CV
    prompt = f"""**TAREA:** Crea un CV profesional y efectivo basado en la siguiente información.

**DATOS DEL CANDIDATO:**
- Nombre: {nombre}
- Email: {email}
- Teléfono: {telefono}

**EXPERIENCIA LABORAL:**
{' '.join(datos["experiencia"])}

**EDUCACIÓN:**
{' '.join(datos["educacion"])}

**HABILIDADES:**
{' '.join(datos["habilidades"])}

**OFERTA DE EMPLEO A LA QUE APLICA:**
{datos["oferta"]["descripcion"]}

**INSTRUCCIONES:**
1. Crea un CV profesional y bien estructurado adaptado específicamente para esta oferta.
2. Usa formato Markdown con asteriscos para marcar las secciones principales en negrita.
3. Destaca las experiencias y habilidades más relevantes para la posición.
4. Asegúrate de que el CV sea conciso pero completo.
5. Incluye las siguientes secciones: **DATOS PERSONALES**, **EXPERIENCIA**, **EDUCACIÓN**, **HABILIDADES**.
6. Utiliza viñetas (•) para listar elementos en cada sección.
7. Formato de experiencia: **Empresa | Período**
8. Si hay información faltante importante, complétala de forma razonable.

Genera ÚNICAMENTE el texto del CV, sin comentarios adicionales:
"""

    try:
        # Generar el CV usando el modelo
        cv_text = model.generate_text(prompt)
        return cv_text
    except Exception as e:
        return f"Error al generar el CV: {str(e)}"