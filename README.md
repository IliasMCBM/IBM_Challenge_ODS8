# Accessibility Assistant for Job Offers and CVs

This project is part of the IBM Challenge ODS8, focused on Sustainable Development Goal 8: "Decent work and economic growth."

## Description

This tool uses generative AI (IBM Granite) to make job offers and CVs more accessible, addressing language barriers that hinder access to employment for various groups, such as people with different educational levels, non-native speakers, or people with certain cognitive disabilities.

## Features

The application allows users (recruiters or candidates) to paste text from job offers or CV sections to:

1. **Simplify technical language**: Converts complex terminology into more accessible expressions.
2. **Identify biased language**: Detects and suggests alternatives for potentially exclusionary expressions.
3. **Generate summaries**: Creates concise and easy-to-understand versions.
4. **Improve CV sections**: Helps draft content in clear and effective language.

## Installation

1. Clone this repository:
```
git clone https://github.com/IliasMCBM/IBM_Challenge_ODS8
```

2. Install dependencies by running the file corresponding to your OS (Linux/Mac or Windows):
- On Linux or MacOS:
```
cd repository_name
./bash.sh
```
- On Windows:
```
cd repository_name
install.bat
```

3. Configure the `.env` file with your IBM WatsonX credentials:
```
WATSONX_API_KEY=your_api_key
WATSONX_URL=your_url
WATSONX_PROJECT_ID=your_project_id
```

## Usage

1. Run the application:
```
python app.py
```

2. Access the web interface through the provided local URL.
3. Paste the text you want to process and select the desired action.
4. Click on "Process text" to get results.

## Technologies used

- Python
- Gradio (for the user interface)
- IBM WatsonX AI (with the Granite-13B model)
- LangChain

## Contribution to SDG 8

This project contributes to SDG 8 by:
- Facilitating access to formal employment for vulnerable groups
- Reducing language barriers in recruitment processes
- Promoting more inclusive hiring practices
- Improving employability through more effective communication
