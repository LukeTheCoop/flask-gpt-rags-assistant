from flask import Flask, request, jsonify
from openai import OpenAI
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
dotenv_path = '.env'
load_dotenv(dotenv_path)

# Access environment variables
OPENAI_API_KEY = os.getenv('API_KEY')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

'''
FILE MANAGEMENT

.env : Located in main directory. This is our env file for api keys.
Can hard code api key into variable if wanted. (E.X. OPENAI_API_KEY = "key here")

assistant_instructions: Located in the util folder. This is the system instructions for our agent.

what_they_ask: Located in the data folder. This is all the messages exchanged with our agent.

'''

#Not Recommended, can hard code api key into variable if wanted. (E.X. OPENAI_API_KEY = "key here")
OPENAI_API_KEY = os.getenv('API_KEY')
EMAIL_APP_PASSWORD = os.getenv('EMAIL_APP_PASSWORD')

with open('util/assistant_instructions.txt', 'r') as file:
    assistant_instructions = file.read()

LOG_FILE_PATH = 'data/what_they_ask.txt'

def log_input_message(message):
    try:
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as file:
            timestamp = datetime.utcnow().isoformat()
            file.write(f"{timestamp} - {message}\n")
    except Exception as e:
        print(f"Failed to log input message: {e}")

'''
How to obtain key :

    To send emails from a Python script using Gmail's SMTP server, you'll need to generate an App Password if your account has 2-Step Verification enabled. This App Password allows your script to access your Gmail account securely. Here's how to set it up:

    Enable 2-Step Verification:

    Sign in to your Google Account.
    Navigate to the Security tab.
    Under "Signing in to Google", select 2-Step Verification and follow the prompts to set it up.
    Generate an App Password:

    After enabling 2-Step Verification, return to the Security tab.
    Under "Signing in to Google", click on App Passwords. You might need to sign in again.
    In the "Select app" dropdown, choose Mail.
    In the "Select device" dropdown, select the device you're using or choose Other (Custom name) to label it appropriately.
    Click Generate. A 16-character App Password will appear. Note this password; you'll use it in your Python script.

'''
def send_email(name, email, subject, content):
    to_email = "example@gmail.com" #Email from google account used for API Key. INSTRUCTIONS ABOVE
    from_email = "example@gmail.com"
    content = content + f"\n\nClient's Email: {email}"
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, EMAIL_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")
    finally:
        server.quit()
        return 'Sent'

# Initialize assistant and other OpenAI components
assistant = client.beta.assistants.create(
    name="Assistant Name",
    instructions=assistant_instructions,
    model="gpt-4o-mini",
    tools=[{"type": "file_search"}, {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email. Name, email, subject, and content are required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The user's name that is trying to contact"},
                    "email": {"type": "string", "description": "The user's email that is trying to contact"},
                    "subject": {"type": "string", "description": "The subject of the email"},
                    "content": {"type": "string", "description": "The content of the email"},
                },
                "required": ["name", "email", "subject", "content"]
            }
        }
    }],
)

#Create Thread for Assistant
thread = client.beta.threads.create()

#Init a vector store to place our document.
vector_store = client.beta.vector_stores.create(name="Example Document")

# Ready the files for upload to OpenAI
file_paths = ["documents/example.pdf"]
file_streams = [open(path, "rb") for path in file_paths]

#Store the document into the vector store
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
    vector_store_id=vector_store.id, files=file_streams
)

print(f'The file is {file_batch.status}')
print(file_batch.file_counts)

#Update vectorstore into the assistant
assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

def call_message(user_message):
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=user_message,
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )

    if run.status == 'requires_action':
        print('CAUGHT ACTION')
        tool_outputs = []
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name == "send_email":
                print('CAUGHT SEND_EMAIL()')
                print(json.loads(tool.function.arguments))
                response = json.loads(tool.function.arguments)
                output = send_email(response['name'], response['email'], response['subject'], response['content'])
                print(f'OUTPUT: {output}')
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": output
                })

        if tool_outputs:
            try:
                run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                print("Tool outputs submitted successfully.")
                while run.status == "queued" or run.status == "in_progress":
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id,
                    )
            except Exception as e:
                print("Failed to submit tool outputs:", e)
        else:
            print("No tool outputs to submit.")

    data = client.beta.threads.messages.list(thread_id=thread.id)

    for m in data:
        return m.content[0].text.value

app = Flask(__name__)

@app.route('/process', methods=['POST', 'OPTIONS'])
def process_text():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.json
        input_text = data.get('text', '')

        if not input_text:
            return jsonify({'error': 'No input text provided'}), 400

        log_input_message(("USER |" + input_text))
        processed_text = call_message(input_text)
        log_input_message(("AGENT |" + processed_text))

        return jsonify({'result': processed_text})
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'}), 500

if __name__ == '__main__':
    input = 'What is the secret word and the secret phrase from our example document?'
    print(f'User input: {input}')
    print(call_message(input))
    app.run(debug=True)
