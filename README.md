# Flask-OpenAI-Chatbot
A Flask chatbot application that can impersonate multiple characters and is powered by OpenAI's GPT-3.5 Turbo. This chatbot allows users to interact with different characters, each with their unique backgrounds and personalities. Additionally, it features a user-friendly chatbot UI written in HTML.

![Python Version](https://img.shields.io/badge/Python-3.7%20%7C%203.8%20%7C%203.9-blue)
![Flask Version](https://img.shields.io/badge/Flask-2.0.1-green)
![OpenAI GPT Version](https://img.shields.io/badge/OpenAI%20GPT-3.5%20Turbo-yellow)


## Features

- Impersonate various characters with distinct backgrounds and personalities.
- Utilize OpenAI's GPT-3.5 Turbo for intelligent responses.
- User-friendly chatbot interface built with HTML and Flask.
- Store chat history for each character in separate text files.
- Easy-to-configure character profiles.

## Getting Started

### Prerequisites

- Python 3.7+ installed on your system.
- Flask 2.0.1 and OpenAI Python SDK installed.
- Set up your OpenAI API key.

### Installation

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/your-username/multi-character-chatbot.git
    ```

2. 2. Navigate to the project directory:
bash
Copy code
cd multi-character-chatbot
3. Install the required Python packages:
bash
Copy code
pip install -r requirements.txt
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
d. Save the changes to the app.py file and exit the text editor.
With these steps completed, your chatbot application is now set up to use OpenAI's GPT-3.5 Turbo and is ready to be launched.

5. Usage
Now that you've completed the setup, you can use your Chatbot App:

![Screenshot 2023-10-03 at 19 32 54](https://github.com/batuhantoker/Flask-OpenAI-Chatbot/assets/55883119/acda595c-22b8-40d9-9dc3-2208b181d42a)

a. Start the Flask app:
```bash
python app.py
```
b. Open your web browser and go to http://localhost:5000 to interact with the chatbot.
c. Choose a character to impersonate from the character selection menu.
d. Engage in conversations with the chatbot and experience different personalities and backgrounds.
Your chatbot app is now fully configured and ready for use. You can customize character profiles and the chatbot UI as needed to create engaging and interactive conversations.

