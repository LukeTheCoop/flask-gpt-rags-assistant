# Flask-GPT-RAGS-Assistant

`flask-gpt-rags-assistant` is a Flask-based API framework that integrates with OpenAI's GPT models to provide an assistant capable of processing user queries, sending emails, and interacting with documents stored in a vector database. This project demonstrates a practical implementation of AI-powered conversational agents combined with additional functionalities like file management and email integration.

---

## Features
1. **Text Processing**:
   - Accepts user input and processes it using an OpenAI GPT model.
   - Logs all user and agent interactions to a file for tracking.

2. **Email Integration**:
   - Supports sending emails via Gmail using App Passwords.
   - Handles structured email content through OpenAI tools.

3. **Document Processing**:
   - Uses OpenAI's vector database to store and retrieve document data.
   - Updates the assistant with document-based knowledge.

4. **Environment Configuration**:
   - Environment variables for secure API and email configurations.
   - Easy-to-edit `.env` file for keys and sensitive data.

5. **Asynchronous Tools**:
   - Dynamically handles OpenAI-required tools like email functionality.

---

## Installation

### Prerequisites
- Python 3.7 or later.
- A Gmail account with [App Password](https://support.google.com/accounts/answer/185833?hl=en) configured.
- OpenAI API Key from [OpenAI](https://platform.openai.com/signup).

### Clone the Repository
```bash
git clone https://github.com/LukeTheCoop/flask-gpt-rags-assistant.git
cd flask-gpt-rags-assistant
