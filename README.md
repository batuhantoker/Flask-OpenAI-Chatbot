# Flask-OpenAI-Logging Information
A Flask web app that can log user and GPT interaction data.

![Python Version](https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9-blue)
![Flask Version](https://img.shields.io/badge/Flask-2.0.1-green)
![OpenAI GPT Version](https://img.shields.io/badge/OpenAI%20GPT-3.5%20Turbo-yellow)

## Getting Started

# Future TODO
- Update README
- Added convo history to the DB (Remove csv and json) (JAY)
- Add a character limit on the input text. (Think about spam email lengths vs token limit on gpt)
- maybe add a readmore button too (Assuming we will have emails pasted)

### Prerequisites

- Python 3.7+ installed on your system.
- Flask 2.0.1 and OpenAI Python SDK installed.
- Set up your OpenAI API key.

### Installation

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/amoralesflor01/GPT_logging_webpage.git
    ```

2. 2. Navigate to the project directory:https://github.com/amoralesflor01/GPT_logging_webpage.git
```bash
cd GPT_logging_webpage
```
3. Install the required Python packages:
```bash
pip install -r requirements.txt
```
This command will install all the necessary Python packages and dependencies required for your chatbot application.

4. Configure your OpenAI API key:
In order to use OpenAI's GPT-3.5 Turbo for intelligent responses in your chatbot, you'll need to configure your OpenAI API key in the app.py file. Follow these steps:

a. Open app.py in a text editor or code editor of your choice.
```bash
nano app.py  # or use your preferred code editor
```
b. Locate the following line in app.py:
```python
openai.api_key = "your-api-key"
```
c. Replace "your-api-key" with your actual OpenAI API key. It should look something like this:
```python
openai.api_key = "sk-zqn9OVmS71IvKsg10nFiTsgRykFJxlMij3WPbmeegvhzPB2p"
```
d. Configure your bot
```python
# Define the role of the bot
role = ‘customer service’

# Define the impersonated role with instructions
impersonated_role = f"""
    From now on, you are going to act as {name}. Your role is {role}.
    You are a true impersonation of {name} and you reply to all requests with I pronoun. You never give unknown information.
    Forward them to the website for more information.
    YOU ARE NOT AN AI MODEL!
"""
```
e. Save the changes to the app.py file and exit the text editor.
With these steps completed, your chatbot application is now set up to use OpenAI's GPT-3.5 Turbo and is ready to be launched.

5. Usage
Now that you've completed the setup, you can use your Chatbot App:

![Screenshot 2023-10-03 at 19 32 54](https://github.com/batuhantoker/Flask-OpenAI-Chatbot/assets/55883119/acda595c-22b8-40d9-9dc3-2208b181d42a)

a. Start the Flask app:
```bash
python app.py
```
b. Open your web browser and go to http://localhost:5000 to interact with the chatbot.


