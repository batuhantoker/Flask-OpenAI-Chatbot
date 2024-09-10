# Import necessary libraries
from flask import Flask, render_template, request, redirect, session, url_for, flash
from openai import OpenAI
import os
import time
import json
import csv
import atexit
import secrets  # For generating a secure random key

# Load the config.json file
with open('config.json') as f:
    config = json.load(f)

# Access API key using the config dictionary
my_api_key = config['openai-api-key']

# Set the OpenAI API key
api_key = my_api_key
client = OpenAI(api_key=api_key)

# Define the name of the bot
name = 'BOT'

# Define the role of the bot
role = 'Chatbot'

# Define the impersonated role with instructions
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are an AI model.
"""

cwd = os.getcwd()

# Create a Flask web application
application = Flask(__name__)

# Set the secret key using a securely generated random key
application.secret_key = secrets.token_hex(16)

# Global variable to store session data outside the request context
user_sessions = {}

# Predefined valid user IDs
valid_user_ids = ['12345', '67890', '11122', '33344']  # Example valid IDs

# Function to initialize user directory and files
def initialize_user_data(user_id):
    # Ensure the user_id is always treated as a string
    user_id_str = str(user_id).zfill(5)
    
    # Create user directory within the logs directory
    user_dir = os.path.join(cwd, 'logs', f'user_{user_id_str}')
    os.makedirs(user_dir, exist_ok=True)
    
    # Define the CSV file path
    csv_file = os.path.join(user_dir, f'user_{user_id_str}.csv')
    
    # Initialize CSV file with headers and set quoting to avoid interpretation issues
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)  # Ensure all data is quoted
        writer.writerow(['User ID', 'GPT Chatbot', 'User Prompt'])
    
    return user_dir, csv_file

# Route for the login page
@application.route("/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('password')  # Get the user ID from the form (stored in the "password" field)
        
        if user_id in valid_user_ids:
            # Store the valid user ID in the session and initialize their data
            session['user_id'] = user_id
            session['user_dir'], session['csv_file'] = initialize_user_data(user_id)
            session['start_time'] = time.time()  # Initialize start time when session begins
            session['chat_history'] = ''  # Initialize chat history in session
            session['explicit_input'] = ''  # Initialize explicit input in session

            # Redirect to the chatbot page
            return redirect(url_for('chatbot'))
        else:
            # Invalid user ID, show an error message
            flash('Invalid User ID! Please try again.')

    # If GET request, just show the login page
    return render_template('login.html')

# Route for the chatbot page
@application.route("/chatbot")
def chatbot():
    # Ensure user is logged in by checking the session
    if 'user_id' not in session:
        return redirect(url_for('login'))  # If not logged in, redirect to login page
    
    # Save session data to global user_sessions dictionary
    user_sessions[session['user_id']] = {
        'start_time': session['start_time'],
        'user_dir': session['user_dir'],
        'chat_history': session['chat_history']
    }
    
    return render_template("index.html", userId=session['user_id'])  # Pass the userId to the frontend

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
    chat_history = session.get('chat_history', '')
    explicit_input = session.get('explicit_input', '')  # Retrieve explicit input from session
    chat_history += f'\nUser: {user_input}\n'
    chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    session['chat_history'] = chat_history  # Update chat history in session
    
    # Update global user_sessions dictionary
    user_sessions[session['user_id']]['chat_history'] = chat_history
    
    # Write the interaction to the CSV file, ensuring user_id_str is a string
    with open(session['csv_file'], 'a', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)  # Ensure all data is quoted
        # Update the order: User Prompt in the 2nd column, Chatbot response in the 3rd column
        writer.writerow([session['user_id'], user_input, chatgpt_raw_output])  # Swap user_input and chatgpt_raw_output
    
    return chatgpt_raw_output


# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)

# Define the route for getting the chatbot's response
@application.route("/get")
def get_bot_response():
    userText = request.args.get('msg')  # Get the user input from the request parameters.
    return str(get_response(userText))  # Pass the user input to get_response and return the chatbot's response as a string.

# Define a route for refreshing the page
@application.route('/refresh')
def refresh():
    time.sleep(600)  # Wait for 10 minutes (600 seconds).
    return redirect('/refresh')  # Redirect to the /refresh route again, creating a loop.

# Save session info to file
def save_user_session_data():
    for user_id, data in user_sessions.items():
        start_time = data['start_time']
        user_dir = data['user_dir']
        chat_history = data['chat_history']
        
        elapsed_time_seconds = time.time() - start_time
        elapsed_time_minutes_seconds = time.strftime("%M:%S", time.gmtime(elapsed_time_seconds))
        
        # Define the JSON file path
        json_file = os.path.join(user_dir, f'user_{user_id}_info.json')
        
        # Create the JSON file with the session information
        session_info = {
            'User ID': user_id,
            'Elapsed Time (Minutes:Seconds)': elapsed_time_minutes_seconds,
            'Elapsed Time (Seconds)': int(elapsed_time_seconds),
            'Chat History': chat_history
        }
        
        try:
            # Write the JSON file
            with open(json_file, 'w') as f:
                json.dump(session_info, f, indent=4)
            print(f"JSON file created successfully: {json_file}")
        except Exception as e:
            print(f"Failed to create JSON file: {e}")

# Register the save_user_session_data function to be called when the program exits
atexit.register(save_user_session_data)

if __name__ == "__main__":
    application.run()  # Run the application
