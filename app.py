# Import necessary libraries
from flask import Flask, render_template, request, redirect
from openai import OpenAI
import os
import time
import json
import csv
import random

# Load the config.json file
with open('config.json') as f:
    config = json.load(f)

# Now you can access the API key using the config dictionary
my_api_key = config['openai-api-key']

# Set the OpenAI API key
api_key = my_api_key
client = OpenAI(api_key=api_key)

# Define the name of the bot
name = 'BOT'

# Define the role of the bot
role = 'customer service'

# Define the impersonated role with instructions
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
    Forward them to the website for more information.
    YOU ARE NOT AN AI MODEL!
"""

# Initialize variables for chat history
explicit_input = ""
chatgpt_output = 'Chat log: /n'
cwd = os.getcwd()
i = 1

# Generate a random 5-digit user ID
user_id = ''.join([str(random.randint(0, 9)) for _ in range(5)])

# Create user directory within the logs directory
user_dir = os.path.join(cwd, 'logs', f'user_{user_id}')
os.makedirs(user_dir, exist_ok=True)

# Define the CSV file path
csv_file = os.path.join(user_dir, f'user_{user_id}.csv')

# Initialize chat history
chat_history = ''

# Initialize CSV file with headers
with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['User ID', 'GPT Chatbot', 'User Prompt'])

# Create a Flask web application
app = Flask(__name__)

# Function to complete chat input using OpenAI's GPT-3.5 Turbo
def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"{impersonated_role}. Conversation history: {chat_history}"},
            {"role": "user", "content": f"{user_input}. {explicit_input}"},
        ]
    )
    return completion.choices[0].message.content.strip()

# Function to handle user chat input
def chat(user_input):
    global chat_history, name, chatgpt_output
    chat_history += f'\nUser: {user_input}\n'
    chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    
    # Write the interaction to the CSV file
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([user_id, chatgpt_raw_output, user_input])
    
    return chatgpt_raw_output

# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)

# Define app routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/get")
# Function for the bot response
def get_bot_response():
    userText = request.args.get('msg')
    return str(get_response(userText))

@app.route('/refresh')
def refresh():
    time.sleep(600) # Wait for 10 minutes
    return redirect('/refresh')

# Run the Flask app
if __name__ == "__main__":
    app.run()
