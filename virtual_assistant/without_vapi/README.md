# TWILIO CALL HANDLER

## Project Overview

This is a Python web application built using the FastAPI framework, served by the Uvicorn ASGI server. The application is designed to be highly performant, scalable, and easy to maintain. It provides a robust set of APIs for managing conversations, speech-to-text, and text-to-speech functionality.

## Getting Started

-----------------

### Prerequisites

* Python 3.8+
* Uvicorn 0.14.0+
* FastAPI 0.63.0+
* Pydantic 1.8.2+
* OpenAPI 3.0.2+
* Loguru 0.5.3+
* Pytest 6.2.5+
* Black 20.8b1+
* Isort 5.10.1+
* Mypy 0.910+

### Installation

1. Clone the repository: `git clone <remote-url>`
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (on Linux/Mac) or `venv\Scripts\activate` (on Windows)
4. Install dependencies: `pip install -r requirements.txt`

### Running the Application

To start the application, run the following command:

```bash
uvicorn --host 0.0.0.0 --reload --port 8080 main:app
```

This will start the Uvicorn server on port 8080, with automatic reloading enabled.

## Project Structure

-----------------

The project is organized into the following directories:

* `app`: Contains the FastAPI application code
  * `main.py`: The main application file
  * `routes`: Defines the API routes and endpoints
    * `conversation.py`: Conversation-related endpoints
    * `speech_to_text.py`: Speech-to-text endpoints
    * `text_to_speech.py`: Text-to-speech endpoints
  * `models`: Defines the data models used by the application
    * `conversation.py`: Conversation data model
    * `speech_to_text.py`: Speech-to-text data model
    * `text_to_speech.py`: Text-to-speech data model
  * `services`: Contains business logic and utility functions
    * `conversation_service.py`: Conversation-related business logic
    * `speech_to_text_service.py`: Speech-to-text business logic
    * `text_to_speech_service.py`: Text-to-speech business logic
  * `tests`: Contains unit tests and integration tests
    * `test_conversation.py`: Conversation-related tests
    * `test_speech_to_text.py`: Speech-to-text tests
    * `test_text_to_speech.py`: Text-to-speech tests
* `config`: Contains configuration files
  * `config.py`: Application-wide configuration
  * `logging_config.py`: Logging configuration
* `logs`: Contains log files
* `requirements`: Contains dependency files
  * `requirements.txt`: Dependencies required by the application

## API Endpoints

-----------------

The API endpoints are defined in the `routes` directory. Each endpoint is documented using OpenAPI specifications.

### Conversation Endpoints

* `POST /call/inbound/receive/<bot_id>`: Create a new conversation connection
* `wss /ws/<bot_id>/audio/stream`: Answer an inbound call

## Configuration

-----------------

The application configuration is stored in the `config.py` file. This file contains settings for the database, logging, and other application-wide settings.

### Logging Configuration

* `LOG_LEVEL`: The log level (e.g. DEBUG, INFO, WARNING, ERROR)
* `LOG_FORMAT`: The log format

## Best Practices

-----------------

This project follows best practices for Python development, including:

* Using type hints and docstrings for code readability
* Following PEP 8 guidelines for code style
* Using a consistent naming convention
* Writing unit tests and integration tests
* Using a virtual environment for dependency management

## API Documentation

-----------------

The API documentation is generated using OpenAPI specifications. The documentation can be accessed at `http://localhost:8080/docs` after starting the application.

## Security

-----------------

This project follows best practices for security, including:

* Using secure protocols for communication (e.g. HTTPS)
* Validating user input
* Using secure password storage
* Implementing rate limiting and IP blocking to prevent abuse
