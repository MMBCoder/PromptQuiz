import streamlit as st
import pandas as pd
from openai import OpenAI
import os
from datetime import datetime
import smtplib
from email.message import EmailMessage

# Set page title
st.title("Prompt Writing Quiz")

# OpenAI API setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"

# Email configuration
EMAIL_ADDRESS = "mirza.22sept@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Gmail App Password

# Scenarios
scenarios = [
    "Design a prompt that instructs an AI to generate email creatives for an EMOB (email marketing onboarding) campaign targeting new tech users.",
    "Write a prompt for an AI to perform QA on a dataset used for email campaign segmentation and targeting.",
    "Create a prompt that instructs an AI to write and validate SAS code for cleaning and analyzing campaign performance data."
]

# Email function
def send_email(name, entry):
    msg = EmailMessage()
    msg['Subject'] = f"Prompt Quiz Submission - {name}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS

    body = f"""
Prompt Quiz Submission - {name}
Date: {entry['Date']}

Scenario 1:
Prompt: {entry['Scenario 1 Prompt']}
Score: {entry['Scenario 1 Score']}
LLM Likelihood: {entry['Scenario 1 LLM Likelihood']}

Scenario 2:
Prompt: {entry['Scenario 2 Prompt']}
Score: {entry['Scenario 2 Score']}
LLM Likelihood: {entry['Scenario 2 LLM Likelihood']}

Scenario 3:
Prompt: {entry['Scenario 3 Prompt']}
Score: {entry['Scenario 3 Score']}
LLM Likelihood: {entry['Scenario 3 LLM Likelihood']}
"""
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Collect user name
name = st.text_input("Enter your full name:")

if name:
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

        send_email(name, new_entry)
