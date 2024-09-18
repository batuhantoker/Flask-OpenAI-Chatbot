# Import necessary libraries
from flask import Flask, render_template, request, redirect, session, url_for, flash
from openai import OpenAI
import os
import time
import json
import csv
import atexit
import secrets  # For generating a secure random key
import math
import datetime
import data_classes.mongo_setup as mongo_setup
import services.data_service as svc
from services.create_accounts_in_db import run_create_accounts
# from apscheduler.schedulers.background import BackgroundScheduler


# Connect with Mongo DB
mongo_setup.global_init()

# Make sure all userIds are loaded into DB
run_create_accounts()

# Load the config.json file
with open('config.json') as f:
    config = json.load(f)

# Access API key using the config dictionary
my_api_key = config['openai-api-key']

# Set the OpenAI API key
api_key = my_api_key
client = OpenAI(api_key=api_key)

# Set the default timer in seconds
TIMER_LIMIT = 30

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

# # Predefined valid user IDs
# valid_user_ids = ['12345', '67890', '11122', '33344']  # Example valid IDs

# Load the used and in-use user IDs from a JSON file
def load_used_ids():
    if os.path.exists('used_ids.json'):
        with open('used_ids.json', 'r') as f:
            return json.load(f)
    return {"used": [], "in_use": []}

# Save the used and in-use user IDs to a JSON file
def save_used_ids(used_ids):
    with open('used_ids.json', 'w') as f:
        json.dump(used_ids, f)

# Add the user ID to the "used" list after session completes
# def mark_user_id_as_used(user_id):
#     used_ids = load_used_ids()
#     used_ids['used'].append(user_id)
#     save_used_ids(used_ids)

# Mark a user ID as "in use" once logged in
# def mark_user_id_as_in_use(user_id):
#     used_ids = load_used_ids()
#     used_ids['in_use'].append(user_id)
#     save_used_ids(used_ids)

# Remove a user ID from the "in use" list when session ends
# def remove_user_id_from_in_use(user_id):
#     used_ids = load_used_ids()
#     used_ids['in_use'].remove(user_id)
#     save_used_ids(used_ids)

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
        writer.writerow(['User ID', 'User Prompt', 'GPT Chatbot'])
    
    return user_dir, csv_file

# A timer check helper function
def session_timeout():
    # Check if the session has a start time
    if 'start_time' in session:
        # Get the current time and the time when the session started
        current_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = session['start_time']
        
        # Calculate the elapsed time in seconds
        elapsed_time = math.floor((current_time - start_time).total_seconds())
        
        # If more than 5 minutes (300 seconds) have passed, end the session
        if elapsed_time > TIMER_LIMIT:
            flash('Your session has expired due to inactivity. Please log in again.')
            # Perform necessary cleanup, like saving session data
            save_user_session_data()
            # Clear the session
            session.clear()
            # Redirect to the login page
            # TODO Redirect to a logout page instead. 
            # maybe with instructions on how to ask for extra time
            # if needed
            return redirect(url_for('login'))
    return None  # Return None if the session is still valid


# Route for the login page
@application.route("/", methods=['GET', 'POST'])
def login():
    used_ids = load_used_ids()  # Load used IDs at the start
    
    if request.method == 'POST':
        user_id = request.form.get('password')  # Get the user ID from the form (stored in the "password" field)

        existing_user = svc.find_account_by_user_id(user_id)
        if existing_user: # and user_id not in used_ids['used'] and user_id not in used_ids['in_use']:
            # TODO Fix the mess of in_use, used, etc by the timer
            # TODO Add some kind of disclaimer that once logged in, timer will start and not pause.
            #       "Are you ready?" Kind of thing

            
            # Assuming, as soon as logged in, we start the timer (after disclaimer).
            
            # Check if already logged in:
            if existing_user.timer_is_running:
                start_time = existing_user.start_time
                # Check if start_time is naive (i.e., has no timezone info) 
                # (Usually while reading it looses tzinfo)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=datetime.timezone.utc)  
            else:
                start_time = svc.start_timer_by_User(existing_user)
            

            # Mark the user ID as "in use" immediately upon login
            # mark_user_id_as_in_use(user_id)

            # Generate a unique session token
            session['session_token'] = secrets.token_hex(16)
            
            # Store the valid user ID in the session and initialize their data
            session['user_id'] = user_id
            session['user_dir'], session['csv_file'] = initialize_user_data(user_id)   # returns paths 
            session['start_time'] = start_time  # Initialize start time when session begins
            session['chat_history'] = []  # Initialize chat history in session
            # TODO Known ISSUE new device would again activate login function, making all the session variables blank. Need to use DB to make it consistent!
            # TODO Can drop json and csv file. No longer needed.
            
            # Redirect to the chatbot page
            return redirect(url_for('chatbot'))
        else:
            # Invalid user ID or ID has already been used or is in use, show an error message
            flash('Invalid, already used, or in-use User ID! Please try again.')

    # If GET request, just show the login page
    return render_template('login.html')

# Route for the chatbot page
@application.route("/chatbot")
def chatbot():
    # Ensure user is logged in and has a valid session token
    if 'user_id' not in session or 'session_token' not in session:
        return redirect(url_for('login'))  # If not logged in, redirect to login page

    # Checking if the session has expired
    timeout_redirect = session_timeout()
    if timeout_redirect:
        return timeout_redirect  # If session has timed out, redirect to login
    
    end_time = session['start_time'] + datetime.timedelta(seconds=TIMER_LIMIT)
    current_time = datetime.datetime.now(datetime.timezone.utc)
    time_left = math.ceil((end_time - current_time).total_seconds())

    # Save session data to global user_sessions dictionary
    user_sessions[session['user_id']] = {
        'start_time': session['start_time'],
        'user_dir': session['user_dir'],
        'chat_history': session['chat_history'],
        'session_token': session['session_token'],
    }

    return render_template("index.html", userId=session['user_id'], TIMER_LIMIT=time_left)  # Pass the userId to the frontend

# Function to complete chat input using OpenAI's GPT-3.5 Turbo
def chatcompletion(conversation_history):

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=conversation_history
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "Failed to generate, please try again!"

# Function to handle user chat input
def chat(user_input):
    conversation_history = session.get('chat_history',[])
    
    # If empty, add initial System instruction
    if conversation_history == [] or conversation_history == '':
        conversation_history = []
        tmp = {
            "role": "system",
            "content": impersonated_role
        }
        conversation_history.append(tmp)

    # Sometimes flask sends the session stuff as a string instead. Weird.    
    if type(conversation_history) == str:
        conversation_history = eval(conversation_history)
    
    # Add user input
    conversation_history.append({"role": "user", "content": user_input})
    # Call GPT
    chatgpt_raw_output = chatcompletion(conversation_history)
    # Add GPT Response
    conversation_history.append({"role": "assistant", "content": chatgpt_raw_output})

    
    session['chat_history'] = conversation_history  # Update chat history in session
    
    # Update global user_sessions dictionary
    user_sessions[session['user_id']]['chat_history'] = conversation_history
    
    # Write the interaction to the CSV file, ensuring user_id_str is a string
    with open(session['csv_file'], 'a', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)  # Ensure all data is quoted
        # User ID, User Input, GPT Response
        writer.writerow([session['user_id'], user_input, chatgpt_raw_output])
    
    return chatgpt_raw_output


# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)

# Define the route for getting the chatbot's response
@application.route("/get")
def get_bot_response():

    # Checking if server logged out! (Due to tab sync issues) (Can't be fixed until UI timer and Python timer are exactly the same)
    if 'user_id' not in session or 'session_token' not in session:
        return redirect(url_for('login'))  # If not logged in, redirect to login page
    
    # Checking if the session has expired
    timeout_redirect = session_timeout()
    if timeout_redirect:
        return timeout_redirect  # If session has timed out, redirect to login
    
    userText = request.args.get('msg')  # Get the user input from the request parameters.
    return str(get_response(userText))  # Pass the user input to get_response and return the chatbot's response as a string.

# Define a route for refreshing the page
@application.route('/refresh')
def refresh():
    time.sleep(600)  # Wait for 10 minutes (600 seconds).
    return redirect('/refresh')  # Redirect to the /refresh route again, creating a loop.

@application.template_filter('timer_format')
def timer_format(value_in_seconds):
    return f"{math.floor(value_in_seconds/60):02}:{(value_in_seconds%60):02}"

# Save session info to file and clean up the "in use" list
def save_user_session_data():
    for user_id, data in user_sessions.items():
        start_time = data['start_time']
        user_dir = data['user_dir']
        chat_history = data['chat_history']

        elapsed_time_seconds = math.floor((datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds())
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

        # # Mark the user ID as used
        # mark_user_id_as_used(user_id)
        # # Remove the user ID from the "in use" list
        # remove_user_id_from_in_use(user_id)


# Function that will end the session for the user, either button was pressed or 
# time is over.
@application.route("/end-session", methods=['POST'])
def end_session():
    # Save session data and clean up
    save_user_session_data()
    
    # Clear the session
    session.clear()

    return 'Session Ended', 200



# Register the save_user_session_data function to be called when the program exits
atexit.register(save_user_session_data)
# atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    application.run()  # Run the application
