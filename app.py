# Import necessary libraries
from flask import Flask, render_template, request, redirect, session, url_for, flash
from openai import OpenAI
import os
import time
import json
import csv
import pandas as pd
import random
import atexit
import secrets  # For generating a secure random key
import math
import datetime
import data_classes.mongo_setup as mongo_setup
import services.data_service as svc
from services.create_accounts_in_db import run_create_accounts
# from apscheduler.schedulers.background import BackgroundScheduler
from data_classes.survey import SurveyResponse


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
TIMER_LIMIT = 300

# Define the name of the bot
name = 'Assitant'

# Define the role of the bot
role = 'Helpful Chatbot'

# Define the impersonated role with instructions @girma_terfa
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}."""
# """
#     You are an AI model specialized in detecting spam emails.
#     You must help users identify if an email is spam or not.
#     You will help the user identify potential red flags and help them determine if the email may or may not be spam based on suspicious characteristics.
#     You will also explain to the user why you think something may or may not be spam so they are not tricked into being scammed.
#     Elaborate with details on why you think so based on evidence and common tactics used by spammers.
#     You should help them be safe, but conversly if an email seems legitmate you should inform them why you think so.
# """

initial_message = 'Hello, I am a ChatBot. I am designed to help you with identifying spam emails. Please feel free to ask me anything! Your UserID is '

cwd = os.getcwd()

# Create a Flask web application
application = Flask(__name__)

# Set the secret key using a securely generated random key
application.secret_key = secrets.token_hex(16)

# Global variable to store session data outside the request context
user_sessions = {}


# Save the used and in-use user IDs to a JSON file
def save_used_ids(used_ids):
    with open('used_ids.json', 'w') as f:
        json.dump(used_ids, f)


# Function to initialize user directory and files
def initialize_user_data(user_id):
    # Ensure the user_id is always treated as a string
    user_id_str = str(user_id).zfill(5)
    
    # Create user directory within the logs directory
    user_dir = os.path.join(cwd, 'logs', f'user_{user_id_str}')
    os.makedirs(user_dir, exist_ok=True)
    
    # Define the CSV file path
    csv_file = os.path.join(user_dir, f'user_{user_id_str}.csv')
    
    # Initialize CSV file with headers
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)  # Ensure all data is quoted
        writer.writerow(['User ID', 'User Prompt', 'GPT Chatbot', 'Email Subject', 'Email Content', 'Dataset', 'Type'])
    
    return user_dir, csv_file


# A timer check helper function
def session_timeout():
    # Check if the session has a start time
    if 'start_time' in session:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        start_time = session['start_time']
        
        elapsed_time = math.floor((current_time - start_time).total_seconds())

        # If the timer limit has been exceeded, end the session and redirect
        if elapsed_time > TIMER_LIMIT:
            return redirect(url_for('end_session'))
    
    return None
    


# Route for the login page
@application.route("/", methods=['GET', 'POST'])
def login():
    # Check if already logged in, direct redirect
    if 'user_id' in session or 'session_token' in session:
        return redirect(url_for('chatbot'))
    

    if request.method == 'POST':
        user_id = request.form.get('password')  # Get the user ID from the form (stored in the "password" field)

        existing_user = svc.find_account_by_user_id(user_id)
        if existing_user: # and user_id not in used_ids['used'] and user_id not in used_ids['in_use']:
            # TODO Fix the mess of in_use, used, etc by the timer
            # TODO Add some kind of disclaimer that once logged in, timer will start and not pause.
            #       "Are you ready?" Kind of thing

            
            # Assuming, as soon as logged in, we start the timer (after disclaimer).
            
            # If survey is completed, the user should not be allowed to login again
            if existing_user.survey_completed:
                flash('Survey already completed. You cannot login again.')
                return redirect(url_for('login'))
            
            # Check if the timer is running; if not, start it
            # if not existing_user.timer_is_running:
            #     start_time = svc.start_timer_by_User(existing_user)
            start_time = existing_user.start_time
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=datetime.timezone.utc)
                
            
            # If no conversation history, initiate with a welcome message
            if not existing_user.conversation_history:
                svc.append_conversation(user_id, is_bot=True, content=initial_message + user_id)
            

            # Mark the user ID as "in use" immediately upon login
            # mark_user_id_as_in_use(user_id)

            # Generate a unique session token
            session['session_token'] = secrets.token_hex(16)
            
            # Store the valid user ID in the session and initialize their data
            session['user_id'] = user_id
            session["email_id"] = existing_user.email_id
            session['user_dir'], session['csv_file'] = initialize_user_data(user_id)   # returns paths 
            # session['start_time'] = start_time  # Initialize start time when session begins
            session['chat_history'] = []  # Initialize chat history in session
            # TODO Known ISSUE new device would again activate login function, making all the session variables blank. Need to use DB to make it consistent!
            # TODO Can drop json and csv file. No longer needed.
            
            # Redirect to the chatbot page
            return redirect(url_for('consent'))
        else:
            # Invalid user ID or ID has already been used or is in use, show an error message
            flash('Invalid, already used, or in-use User ID! Please try again.')

    # If GET request, just show the login page
    return render_template('login.html')


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
    conversation_history = session.get('chat_history', [])
    
    # If empty, add initial System instruction
    if conversation_history == [] or conversation_history == '':
        conversation_history = []
        tmp = {
            "role": "system",
            "content": impersonated_role
        }
        conversation_history.append(tmp)

    # Sometimes Flask sends the session stuff as a string instead. Weird.
    if type(conversation_history) == str:
        conversation_history = eval(conversation_history)
    
    # Add user input to the conversation
    conversation_history.append({"role": "user", "content": user_input})
    svc.append_conversation(session['user_id'], is_bot=False, content=user_input)
    
    # Call GPT-3.5 Turbo to get a response
    chatgpt_raw_output = chatcompletion(conversation_history)
    
    # Add GPT response to the conversation
    conversation_history.append({"role": "assistant", "content": chatgpt_raw_output})
    svc.append_conversation(session['user_id'], is_bot=True, content=chatgpt_raw_output)
    
    # Save the conversation history in the session
    session['chat_history'] = conversation_history
    
    # Ensure the user_sessions entry exists
    if session['user_id'] not in user_sessions:
        user_sessions[session['user_id']] = {}

    # Update the global user_sessions dictionary
    user_sessions[session['user_id']]['chat_history'] = conversation_history
    
    return chatgpt_raw_output


# Function to get a response from the chatbot
def get_response(userText):
    return chat(userText)


# Modify the chatbot route to pass email data to the template
@application.route("/chatbot")
def chatbot():
    # Ensure user is logged in and has a valid session token
    if 'user_id' not in session or 'session_token' not in session:
        return redirect(url_for('login'))

    # Checking if the session has expired
    timeout_redirect = session_timeout()
    if timeout_redirect:
        return timeout_redirect  # If session has timed out, redirect to login

    # Fetch the user's start_time and ensure it's timezone-aware
    existing_user = svc.find_account_by_user_id(session['user_id'])
    start_time = existing_user.start_time

    # Ensure start_time is timezone-aware
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=datetime.timezone.utc)

    # Make current_time timezone-aware
    current_time = datetime.datetime.now(datetime.timezone.utc)

    # Calculate remaining time only after the timer has started
    if existing_user.timer_is_running:
        end_time = start_time + datetime.timedelta(seconds=TIMER_LIMIT)
        time_left = max(0, math.ceil((end_time - current_time).total_seconds()))
    else:
        time_left = TIMER_LIMIT  # If the timer hasn't started, show full time

    # Fetch email to display
    email = svc.getEmailRecordByUuid(session["email_id"])

    email_sender = email["From"].values[0]
    email_subject = email["Subject"].values[0]
    email_content = email["Email Content"].values[0]

    return render_template(
        "index.html", 
        userId=session['user_id'],
        user_id_int=int(session['user_id']),
        TIMER_LIMIT=time_left,
        email_sender=email_sender,
        email_subject=email_subject,
        email_content=email_content,
        convo_history=existing_user.conversation_history
    )

#######################################################

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


@application.template_filter('message_side_format')
def message_side_format(is_bot):
    return "left" if is_bot else "right"


# Save session info to file and clean up the "in use" list
def save_user_session_data():
    for user_id, data in user_sessions.items():
        if 'start_time' not in data:
            print(f"User {user_id} is missing start_time")
            continue  # Skip saving if start_time is missing
        
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


# Function that will end the session for the user, either button was pressed or 
# time is over.
@application.route("/end-session")
def end_session():
    user_id = session.get('user_id')

    if user_id:
        # Save user session data
        save_user_session_data()
        
        # Fetch the user record
        user = svc.find_account_by_user_id(user_id)
        if user:
            if not user.survey_completed:
                user.timer_is_running = False  # Stop the timer
                user.save()

        # Store user_id temporarily to link with survey
        session['temp_user_id'] = user_id

    # Clear the session except for temp_user_id
    temp_user_id = session.get('temp_user_id')
    temp_email_id = session.get("email_id")
    session.clear()
    session['temp_user_id'] = temp_user_id
    session["temp_email_id"] = temp_email_id

    # Redirect to survey page
    return redirect(url_for('survey', user_id=temp_user_id))


@application.route("/survey", methods=['GET', 'POST'])
def survey():
    user_id = session.get('temp_user_id') or request.args.get('user_id')

    if not user_id:
        flash("Session has expired. Please log in again.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve survey responses and handle multiple selections
        survey_responses = {
            key: ", ".join(request.form.getlist(key)) if len(request.form.getlist(key)) > 1 else request.form[key]
            for key in request.form.keys()
        }

        # Retrieve survey responses from the form
        #survey_response = request.form.to_dict()
        # Collect multiple checkbox values for 'user-email-action' field
        #survey_response['user-email-action'] = request.form.getlist('user-email-action')
        
        #survey_response['features'] = request.form.getlist('features')

        # Find the user and update survey responses
        user = svc.find_account_by_user_id(user_id)
        if user:
            user.survey_responses = survey_responses
            user.survey_completed = True  # Mark survey as completed
            user.timer_is_running = False  # Ensure the timer is stopped
            user.save()

        flash("Survey responses saved successfully. Session ended.")
        session.clear()  # Clear the session fully after survey is completed

        # Render a template with a redirect script
        return render_template("redirect_after_submit.html", redirect_url="https://docs.google.com/document/d/1dqDm4nkdzaRoT9GOtNfQEzQODbYUvxOMkugTin3n48c/edit?tab=t.0")

        #return redirect(url_for('login'))

    # Fetch email to display
    email = svc.getEmailRecordByUuid(session["temp_email_id"])
    email_sender = email["From"].values[0]
    email_subject = email["Subject"].values[0]
    email_content = email["Email Content"].values[0]


    return render_template(
        'survey.html', 
        email_sender=email_sender,
        email_subject=email_subject,
        email_content=email_content,
        user_id_int=int(user_id)
    )



@application.route("/consent", methods=['GET', 'POST'])
def consent():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Ensure the user is logged in
    
    if request.method == 'POST':
        consent_given = request.form.get('consent')
        
        if consent_given != 'yes':
            flash("You must give consent to proceed.")
            return redirect(url_for('consent'))
        
        # Proceed to pre-survey after consent is given
        return redirect(url_for('pre_survey'))

    return render_template('consent.html')  # Ensure you create this template



@application.route("/pre-survey", methods=['GET', 'POST'])
def pre_survey():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Save pre-survey responses to DB
        pre_survey_responses = {
            key: ", ".join(request.form.getlist(key)) if len(request.form.getlist(key)) > 1 else request.form[key]
            for key in request.form.keys()
        }

        # Save pre-survey responses to DB
        #pre_survey_responses = request.form.to_dict()
        # Collect multiple checkbox values for 'computer-literacy' field
        #pre_survey_responses['computer-literacy'] = request.form.getlist('computer-literacy')
        
        #pre_survey_responses['features'] = request.form.getlist('features')
        
        # Save pre-survey responses in the user's document
        svc.store_survey_response(session['user_id'], pre_survey_responses, is_pre_survey=True)
        
        # Redirect to instructions page
        return redirect(url_for('instructions'))

    return render_template('pre_survey.html', user_id = int(session['user_id']))



@application.route("/instructions", methods=['GET'])
def instructions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('instructions.html', user_id = int(session['user_id']))



@application.route("/start-timer", methods=['POST'])
def start_timer():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Start the timer only when the "Next" button is clicked on the instructions page
    svc.start_timer_by_User(svc.find_account_by_user_id(session['user_id']))

    # Redirect to chatbot
    return redirect(url_for('chatbot'))



# Register the save_user_session_data function to be called when the program exits
atexit.register(save_user_session_data)
# atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000)  # Run the application
