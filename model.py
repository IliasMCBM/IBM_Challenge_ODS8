import os
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

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

def model_response(prompt):
    return model.generate_text(prompt)