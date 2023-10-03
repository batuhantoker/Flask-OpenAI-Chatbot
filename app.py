#imports
from flask import Flask, render_template, request, redirect
import openai,os,time



global chat_history,name
openai.api_key = "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"

name = 'BOT' # Name of the bot 

role=f'''To behave as a person called Batuhan Toker. You have mechanical engineering bachelors, mechatronics master. You spent 1 year teaching in computer science at TUM and you were doing a phd but dropped out.
        Your skills relies on AI and robotics. You studied haptics, vibration control, network synthesis and analysis. You need to behave as
        '''
impersonated_role = f"""
                    From now on you are going to act as {name}. Your role is {role}.
                    You are a true impersonation of {name} and you reply all request with I pronoun. You never give unknow information. forward them to {website} for more information.
                    YOU ARE NOT AN AI MODEL! """
explicit_input = ""
chatgpt_output = 'Chat log: /n'
cwd = os.getcwd()
i = 1
while os.path.exists(os.path.join(cwd, f'chat_history{i}.txt')):
    i += 1
history_file = os.path.join(cwd, f'chat_history{i}.txt')
with open(history_file, 'w') as f:
    f.write( '\n')
    f.close()

chat_history = ''

app = Flask(__name__)
#create chatbot


def chatcompletion(user_input, impersonated_role, explicit_input, chat_history):
  output = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-0301",
    temperature=1,
    presence_penalty=0,
    frequency_penalty=0,
    max_tokens=2000,
    messages=[
      {"role": "system", "content": f"{impersonated_role}. Conversation history: {chat_history}"},
      {"role": "user", "content": f"{user_input}. {explicit_input}"},
    ]
  )

  for item in output['choices']:
    chatgpt_output = item['message']['content']

  return chatgpt_output


def chat(user_input):
    global chat_history,name,chatgpt_output
    current_day = time.strftime("%d/%m", time.localtime())
    current_time = time.strftime("%H:%M:%S", time.localtime())
    chat_history += f'\nUser: {user_input}\n'
    chatgpt_raw_output = chatcompletion(user_input, impersonated_role, explicit_input, chat_history).replace(f'{name}:', '')
    chatgpt_output = f'{name}: {chatgpt_raw_output}'
    chat_history += chatgpt_output + '\n'
    with open(history_file, 'a') as f:
      f.write('\n'+ current_day+ ' '+ current_time+ ' User: ' +user_input +' \n' + current_day+ ' ' + current_time+  ' ' +  chatgpt_output + '\n')
      f.close()
    #save_chat_history(chatgpt_output + '\n')
    return chatgpt_raw_output






def get_response(userText):
    return (chat(userText))


#define app routes
@app.route("/")
def index():

    return render_template("index.html")
@app.route("/get")
#function for the bot response
def get_bot_response():

    userText = request.args.get('msg')

    return str(get_response(userText))

@app.route('/refresh')
def refresh():
    time.sleep(600) # Wait for 10 minutes

    return redirect('/refresh')

if __name__ == "__main__":
    app.run()
