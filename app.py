import streamlit as st
import pandas as pd
import openai
import os
from datetime import datetime
import requests
from io import BytesIO

# Set page title
st.title("Prompt Writing Quiz")

# OpenAI API setup
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

# Load Excel file from GitHub
def load_excel():
    url = 'https://github.com/MMBCoder/PromptQuiz/raw/main/scores.xlsx'
    resp = requests.get(url)
    return pd.read_excel(BytesIO(resp.content), engine='openpyxl')

# Save Excel file locally (manual upload needed for GitHub)
def save_to_excel(df):
    df.to_excel('scores.xlsx', index=False)

# Scenarios
scenarios = [
    "Write a prompt to generate creative ad concepts for a new tech gadget.",
    "Write a prompt to conduct QA for an email marketing campaign dataset.",
    "Write a prompt to create and validate SAS code for data analysis."
]

# Collect user name
name = st.text_input("Enter your full name:")

if name:
    df_existing = load_excel()

    if name in df_existing['Name'].values:
        st.error("Duplicate entry not allowed.")
    else:
        prompts = []
        ai_assistance = []

        for idx, scenario in enumerate(scenarios, 1):
            st.subheader(f"Scenario {idx}")
            st.write(scenario)

            prompt = st.text_area(f"Enter your prompt for scenario {idx}:", key=f"prompt_{idx}")
            ai_help = st.radio(f"Did you write this yourself or use an LLM?", ('Self-written', 'LLM-assisted'), key=f"ai_{idx}")

            prompts.append(prompt)
            ai_assistance.append(ai_help)

        if st.button("Submit"):
            scores = []
            for scenario, prompt in zip(scenarios, prompts):
                response = openai.ChatCompletion.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": f"Rate the quality of the prompt on a scale of 1 (lowest) to 10 (highest), strictly based on clarity, specificity, and effectiveness for the following scenario: '{scenario}'. Only respond with the number."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1,
                    temperature=0
                )
                score = response.choices[0].message.content.strip()
                scores.append(score)

            # Display scores
            for idx, score in enumerate(scores, 1):
                st.write(f"Scenario {idx} Score: {score}/10")

            # Record data to Excel
            new_entry = {
                'Name': name,
                'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Scenario 1 Prompt': prompts[0],
                'Scenario 1 AI Assistance': ai_assistance[0],
                'Scenario 1 Score': scores[0],
                'Scenario 2 Prompt': prompts[1],
                'Scenario 2 AI Assistance': ai_assistance[1],
                'Scenario 2 Score': scores[1],
                'Scenario 3 Prompt': prompts[2],
                'Scenario 3 AI Assistance': ai_assistance[2],
                'Scenario 3 Score': scores[2]
            }
            df_existing = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)
            save_to_excel(df_existing)

            st.success("Your responses have been recorded successfully!")
