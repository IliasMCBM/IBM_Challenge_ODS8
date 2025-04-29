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
print(api_key, url, project_id)
print("Setting up credentials...")
credentials = Credentials(
    url=url,
    api_key=api_key,
)

print("Creating API client...")
client = APIClient(credentials)

print("Initializing model...")
model = ModelInference(
    model_id="ibm/granite-3-8b-instruct",
    api_client=client,
    project_id=project_id,
    params={
        "max_new_tokens": 100
    }
)

print("Testing model with a sample prompt...")
prompt = 'Si tengo 5 manzanas y me quitan dos, cuantas me quedan?'
print(f"Prompt: {prompt}")
print("Response:")
print(model.generate_text(prompt))
print("\nConnection test complete!")