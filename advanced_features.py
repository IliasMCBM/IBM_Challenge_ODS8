import re
from model import model_response

# =============================================================================
# FUNCTION: extract_key_requirements
# =============================================================================

def extract_key_requirements(text):
    """
    Extracts and lists the key skills, qualifications, and requirements
    from a job posting in a clear, structured format.

    Args:
        text (str): Full job posting text.

    Returns:
        str: A structured list of categorized requirements or an error message.
    """
    prompt = f"""Extract and list the key skills, qualifications, and requirements
from the following job posting in a clear and structured format:

{text}

Output format:
- Technical skills: [list]
- Soft skills: [list]
- Education: [list]
- Required experience: [list]
- Languages: [list]
- Other requirements: [list]
"""
    try:
        response = model_response(prompt)
        return response
    except Exception as e:
        return f"Error while extracting key requirements: {str(e)}"




# =============================================================================
# FUNCTION: create_cover_letter
# =============================================================================

def extract_key_requirements(text):
    """
    Extracts and lists the key skills, qualifications, and requirements
    from a job posting in a clear, structured format.

    Args:
        text (str): Full job posting text.

    Returns:
        str: A structured list of categorized requirements or an error message.
    """
    prompt = f"""Extract and list the key skills, qualifications, and requirements
from the following job posting in a clear and structured format:

{text}

Output format:
- Technical skills: [list]
- Soft skills: [list]
- Education: [list]
- Required experience: [list]
- Languages: [list]
- Other requirements: [list]
"""
    try:
        response = model_response(prompt)
        return response
    except Exception as e:
        return f"Error while extracting key requirements: {str(e)}"


# =============================================================================
# FUNCTION: create_cover_letter
# =============================================================================

def create_cover_letter(cv_text, job_text):
    """
    Generates a tailored cover letter body in English using a given CV and job description.
    Ensures the letter starts and ends formally and does not include placeholders or headers.

    Args:
        cv_text (str): The candidate's CV content.
        job_text (str): The job posting to respond to.

    Returns:
        str: A formal English cover letter body or an error message.
    """
    if not cv_text.strip() or not job_text.strip():
        return "Error: Both your CV and the job description are required."

    candidate_name = "The Candidate"  # Default fallback name

    try:
        lines = cv_text.split('\n') if '\\n' not in cv_text else cv_text.split('\\n')
        for line in lines:
            line = line.strip()
            if line and '|' not in line and '@' not in line and ':' not in line and len(line.split()) < 5:
                candidate_name = line
                break

        if candidate_name == "The Candidate":
            match = re.search(r'Email:\s*([\w.-]+)@', cv_text, re.IGNORECASE)
            if match:
                name_part = match.group(1).replace('.', ' ').replace('-', ' ').title()
                if len(name_part.split()) <= 3 and not any(kw in name_part.lower() for kw in ['info', 'contact', 'admin', 'cv', 'resume']):
                    candidate_name = name_part

    except Exception:
        candidate_name = "The Candidate"

    prompt = f"""**TASK:** Write **ONLY THE BODY** of a formal English cover letter.

**STRICT RULES:**
* Do **NOT** repeat the job posting.
* Do **NOT** include headers (addresses, dates, recipient info).
* Do **NOT** use generic placeholders like [Your Name], [Recipient], [Date], etc.
* Start directly with a formal greeting (e.g., "Dear Hiring Team,").
* End directly with a formal closing (e.g., "Sincerely,") followed by the candidate's name: **{candidate_name}**.

**INSTRUCTIONS:**
1. Read the **CANDIDATE CV** to understand their background.
2. Read the **JOB POSTING** to understand requirements.
3. Write the letter body **IN ENGLISH**, explaining how the experience and skills from the **CANDIDATE CV** (named {candidate_name}) are a good fit for the **JOB POSTING**.

**CANDIDATE CV:**
---
{cv_text}
---

**JOB POSTING (FOR CONTEXT ONLY, DO NOT COPY):**
---
{job_text}
---

**GENERATED COVER LETTER BODY (IN ENGLISH, NO HEADERS/PLACEHOLDERS, USE '{candidate_name}' AT THE END):**
"""
    try:
        response = model_response(prompt).strip()
        lines = response.split('\n')

        final_lines = []
        in_body = False
        for line in lines:
            stripped = line.strip()
            if stripped.lower().startswith(("dear", "to the attention")):
                in_body = True
            if in_body and not (stripped.startswith('[') and stripped.endswith(']')):
                if stripped or final_lines:
                    final_lines.append(line)

        response_cleaned = '\n'.join(final_lines).strip()

        if candidate_name != "The Candidate":
            response_cleaned = response_cleaned.replace("[Your Name]", candidate_name)

        return response_cleaned

    except Exception as e:
        return f"Error generating cover letter: {str(e)}"




# =============================================================================
# FUNCTION: cv_agent
# =============================================================================

def cv_agent(job_description, user_input="", context=None):
    """
    Conversational agent that collects information to generate a customized CV
    based on a job posting and user responses over multiple turns.

    Args:
        job_description (str): The job posting text.
        user_input (str): User response to the previous question.
        context (dict | None): Dictionary storing the conversation state and collected data.

    Returns:
        tuple: (next_user_message, updated_context, cv_ready)
            - next_user_message (str): Message/question to ask the user next.
            - updated_context (dict): Updated context with stored information.
            - cv_ready (bool): Whether the CV is ready to be generated.
    """
    # Initialize context if it's the first interaction
    if not context:
        prompt = f"""Analyze the following job posting and extract:
1. The job title
2. 3-5 key technical skills required
3. Minimum experience required (in years, if specified)

Job posting:
{job_description}

Respond in this JSON format:
{{
    "title": "Job Title",
    "skills": ["skill1", "skill2", "..."],
    "required_experience": "X years in..."
}}
"""
        try:
            job_analysis = model_response(prompt)

            import re
            title_match = re.search(r'"title":\s*"([^"]+)"', job_analysis)
            title = title_match.group(1) if title_match else "target role"

            context = {
                "state": "personal_info",
                "data": {
                    "job_posting": {
                        "title": title,
                        "description": job_description
                    },
                    "personal": {},
                    "experience": [],
                    "education": [],
                    "skills": []
                },
                "questions_asked": 0
            }

            return (
                f"Hi! I'm going to help you create a tailored CV for the '{title}' position. "
                f"Let's start with some basic personal information. "
                f"Can you provide your full name, email address, and phone number?",
                context,
                False
            )
        except Exception as e:
            return f"Error analyzing job posting: {str(e)}", None, False

    
    elif context["state"] == "personal_info":
        try:
            # Extract full name
            prompt_name = f"""Read the following text and extract ONLY the person's full name:

Text: "{user_input}"

Respond ONLY with the full name. Do not include any other text or explanation.
"""
            try:
                name = model_response(prompt_name).strip()
                context["data"]["personal"]["name"] = name
            except Exception:
                context["data"]["personal"]["name"] = "User"

            # Extract email
            prompt_email = f"""Read the following text and extract ONLY the email address:

Text: "{user_input}"

Respond ONLY with the email address. Do not include any other text or explanation.
"""
            try:
                email = model_response(prompt_email).strip()
                context["data"]["personal"]["email"] = email
            except Exception:
                context["data"]["personal"]["email"] = ""

            # Extract phone number
            prompt_phone = f"""Read the following text and extract ONLY the phone number:

Text: "{user_input}"

Respond ONLY with the phone number. Do not include any other text or explanation.
"""
            try:
                phone = model_response(prompt_phone).strip()
                context["data"]["personal"]["phone"] = phone
            except Exception:
                context["data"]["personal"]["phone"] = ""

            if context["data"]["personal"].get("name") and context["data"]["personal"].get("email"):
                context["state"] = "work_experience"
                return (
                    f"Thank you, {context['data']['personal'].get('name')}. "
                    f"Now, please tell me about your relevant work experience for the position of {context['data']['job_posting']['title']}. "
                    f"Include the company name, your role, dates, and a brief description of your responsibilities.",
                    context,
                    False
                )
            else:
                return (
                    "I couldn't clearly identify all your personal info. "
                    "Please provide your information like this:\n\n"
                    "Name: John Doe\nEmail: john@example.com\nPhone: +123456789",
                    context,
                    False
                )

        except Exception as e:
            return (
                "Sorry, something went wrong while processing your personal information. "
                "Please provide your information like this:\n\n"
                "Name: John Doe\nEmail: john@example.com\nPhone: +123456789",
                context,
                False
            )
    
    elif context["state"] == "work_experience":
        try:
            # Save the raw experience text
            context["data"]["experience"].append(user_input)
            context["questions_asked"] += 1

            # Analyze the experience to determine relevance and completeness
            prompt = f"""Analyze this work experience description:
{user_input}

Identify:
1. Whether it's detailed enough
2. Whether it's relevant to the role: {context['data']['job_posting']['title']}
3. Whether it includes duration or years of experience

Respond in the following JSON format:
{{
    "is_complete": true/false,
    "is_relevant": true/false,
    "total_experience_years": X,
    "needs_more_details": true/false
}}
"""
            try:
                analysis = model_response(prompt)

                import re
                complete_match = re.search(r'"is_complete":\s*(true|false)', analysis, re.IGNORECASE)
                relevant_match = re.search(r'"is_relevant":\s*(true|false)', analysis, re.IGNORECASE)
                detail_match = re.search(r'"needs_more_details":\s*(true|false)', analysis, re.IGNORECASE)

                is_complete = complete_match.group(1).lower() == "true" if complete_match else True
                is_relevant = relevant_match.group(1).lower() == "true" if relevant_match else True
                needs_more_details = detail_match.group(1).lower() == "true" if detail_match else False

            except Exception:
                # Fallback values if analysis fails
                is_complete = True
                is_relevant = True
                needs_more_details = False

            if needs_more_details and context["questions_asked"] < 4:
                return (
                    "Thanks for sharing. Could you please provide more details about that role? "
                    "For example, what kind of projects did you work on, or what impact did you have?",
                    context,
                    False
                )
            else:
                # Proceed to next phase
                context["state"] = "education"
                return (
                    "Great. Now, could you tell me about your educational background? "
                    "Include degrees, institutions, and graduation years.",
                    context,
                    False
                )

        except Exception:
            if user_input:
                context["data"]["experience"].append(user_input)
                context["questions_asked"] += 1
                context["state"] = "education"
                return (
                    "Thanks for sharing your experience. Now, please tell me about your education — "
                    "degrees, institutions, and graduation years.",
                    context,
                    False
                )
            else:
                return (
                    "Something went wrong. Please briefly describe your work experience — "
                    "including company, role, dates, and technologies used.",
                    context,
                    False
                )
    
    elif context["state"] == "education":
        # Store the user's education information
        context["data"]["education"].append(user_input)

        # Proceed to the next phase: skills
        context["state"] = "skills"
        return (
            f"Perfect. Lastly, what technical and soft skills do you believe make you "
            f"a strong candidate for the position of {context['data']['job_posting']['title']}?",
            context,
            False
        )

    elif context["state"] == "skills":
        # Store the user's skills
        context["data"]["skills"].append(user_input)

        # Mark as completed
        context["state"] = "finalized"
        return (
            f"Great! I have collected all the necessary information to generate your tailored CV "
            f"for the position of {context['data']['job_posting']['title']}. Now I will generate a professional CV "
            f"based on your details and optimized for this specific job.",
            context,
            True  # CV is ready to be generated
        )

    elif context["state"] == "finalized":
        # The agent has completed the data collection
        return "Your CV is ready to be generated.", context, True

    else:
        return "An unexpected error occurred in the process. Please try again.", None, False




# =============================================================================
# FUNCTION: generate_cv_from_agent_data
# =============================================================================

def generate_cv_from_agent_data(context):
    """
    Generates a formatted CV text (in Markdown) from the conversation context
    gathered by the cv_agent.

    Args:
        context (dict): Conversation context with all collected user data.

    Returns:
        str: A complete Markdown-formatted CV, or an error message.
    """
    if not context or "data" not in context:
        return "Error: Not enough data to generate the CV."

    data = context["data"]
    print(f'EXPERIENCE: \n{" ".join(data["experience"])}')
    print(f'EDUCATION: \n{"" "".join(data["education"])}')
    print(f'SKILLS: \n{"" "".join(data["skills"])}')

    # Extract personal information
    name = data["personal"].get("name", "")
    email = data["personal"].get("email", "")
    phone = data["personal"].get("phone", "")

    # Construct the prompt to send to the model
    prompt = f"""**TASK:** Create a professional and effective CV based on the following information.

**CANDIDATE DETAILS:**
- Name: {name}
- Email: {email}
- Phone: {phone}

**WORK EXPERIENCE:**
{' '.join(data["experience"])}

**EDUCATION:**
{' '.join(data["education"])}

**SKILLS:**
{' '.join(data["skills"])}

**INSTRUCTIONS:**
1. Create a well-structured, professional CV tailored to the job posting.
2. Use Markdown format. Use asterisks to mark section titles (e.g., **EXPERIENCE**).
3. Emphasize the most relevant experience and skills.
4. Keep it concise but complete.
5. Include the following sections: **PERSONAL INFORMATION**, **EXPERIENCE**, **EDUCATION**, **SKILLS**.
6. Use bullet points (•) to list items in each section.
7. Experience format: **Company | Period**

Generate ONLY the CV text, without any extra explanations or comments.
"""

    try:
        cv_text = model_response(prompt)
        return cv_text
    except Exception as e:
        return f"Error generating CV: {str(e)}"
