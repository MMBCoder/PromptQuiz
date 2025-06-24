import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from datetime import datetime
import requests
from io import BytesIO
import base64
import json

# Set page title
st.title("Prompt Writing Quiz")

# OpenAI API setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set this as a secret in your environment
REPO_OWNER = "MMBCoder"
REPO_NAME = "PromptQuiz"
FILE_PATH = "scores.xlsx"

# Load Excel file from GitHub
def load_excel():
    url = f'https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/main/{FILE_PATH}'
    try:
        resp = requests.get(url)
        df = pd.read_excel(BytesIO(resp.content), engine='openpyxl')
        if 'Name' not in df.columns:
            raise ValueError("Missing 'Name' column")
        return df
    except Exception:
        st.warning("Starting fresh: Excel file missing or invalid.")
        return pd.DataFrame(columns=[
            'Name', 'Date',
            'Scenario 1 Prompt', 'Scenario 1 Score', 'Scenario 1 LLM Likelihood',
            'Scenario 2 Prompt', 'Scenario 2 Score', 'Scenario 2 LLM Likelihood',
            'Scenario 3 Prompt', 'Scenario 3 Score', 'Scenario 3 LLM Likelihood'
        ])

# Save to GitHub using GitHub API
def save_to_excel(df):
    excel_bytes = BytesIO()
    df.to_excel(excel_bytes, index=False, engine='openpyxl')
    excel_bytes.seek(0)
    content = base64.b64encode(excel_bytes.read()).decode('utf-8')

    # Get the current file's SHA if it exists
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github+json'
    }
    sha = None
    get_url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}'
    response = requests.get(get_url, headers=headers)
    if response.status_code == 200:
        sha = response.json().get('sha')

    # Push updated file
    data = {
        "message": "Append new quiz submission",
        "content": content,
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    put_response = requests.put(get_url, headers=headers, data=json.dumps(data))
    if put_response.status_code in [200, 201]:
        st.success("Your responses have been recorded and pushed to GitHub.")
    else:
        st.error("Failed to update GitHub. Check token and permissions.")

# Scenarios
scenarios = [
    "Design a prompt that instructs an AI to generate email creatives for an EMOB (email marketing onboarding) campaign targeting new tech users.",
    "Write a prompt for an AI to perform QA on a dataset used for email campaign segmentation and targeting.",
    "Create a prompt that instructs an AI to write and validate SAS code for cleaning and analyzing campaign performance data."
]

# Collect user name
name = st.text_input("Enter your full name:")

if name:
    df_existing = load_excel()

    if name in df_existing['Name'].values:
        st.error("Duplicate entry not allowed.")
    else:
        prompts = []
        scores = []
        llm_flags = []

        for idx, scenario in enumerate(scenarios, 1):
            st.subheader(f"Scenario {idx}")
            st.write(scenario)
            prompt = st.text_area(f"Enter your prompt for scenario {idx}:", key=f"prompt_{idx}")
            prompts.append(prompt)

        if st.button("Submit"):
            for prompt in prompts:
                quality_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "Score the clarity and usefulness of this prompt from 1 (poor) to 10 (excellent). Reply only with a number."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1,
                    temperature=0
                )
                quality_score = quality_response.choices[0].message.content.strip()
                scores.append(quality_score)

                llm_check_response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "Is this likely written by AI or a human? Reply with 'AI' or 'Human'."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1,
                    temperature=0
                )
                llm_flag = llm_check_response.choices[0].message.content.strip()
                llm_flags.append(llm_flag)

            for idx in range(3):
                st.write(f"Scenario {idx+1} Score: {scores[idx]}/10 - Likely written by: {llm_flags[idx]}")

            new_entry = {
                'Name': name,
                'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Scenario 1 Prompt': prompts[0],
                'Scenario 1 Score': scores[0],
                'Scenario 1 LLM Likelihood': llm_flags[0],
                'Scenario 2 Prompt': prompts[1],
                'Scenario 2 Score': scores[1],
                'Scenario 2 LLM Likelihood': llm_flags[1],
                'Scenario 3 Prompt': prompts[2],
                'Scenario 3 Score': scores[2],
                'Scenario 3 LLM Likelihood': llm_flags[2]
            }
            df_existing = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)
            save_to_excel(df_existing)
