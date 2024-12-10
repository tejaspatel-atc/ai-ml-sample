## Overview

This project provides an AWS Lambda function that handles GET requests to interact with an AI bot. It uses Supabase as a backend database and the OpenAI API for generating AI responses. The function is designed to work within an event-driven architecture, handling HTTP requests, querying databases, managing sessions, and interacting with OpenAI's language model.

## Features

- **AWS Lambda Integration**: The function is designed to work seamlessly with AWS Lambda and AWS API Gateway.
- **Supabase Integration**: It uses Supabase for database operations, storing bot configurations, and user interactions.
- **OpenAI Integration**: The function leverages OpenAI's API to generate responses from a language model.
- **Session Management**: Manages user sessions and threads for ongoing interactions.
- **Input Validation**: Ensures required parameters are present and valid.
- **Error Handling**: Provides comprehensive error responses for various failure scenarios.

## Environment Variables

The function relies on the following environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key.
- `SUPABASE_URL`: The URL of your Supabase project.
- `SUPABASE_KEY`: Your Supabase API key.
- `SOURCE_REMOVAL_REGEX` (optional): A regex pattern to filter out unwanted content from AI responses.

## Dependencies

The project uses the following dependencies:

- `@supabase/supabase-js`: Supabase client for database operations.
- `dotenv`: For loading environment variables from a `.env` file.
- `openai`: OpenAI client for interacting with their API.
- `uuid`: For generating unique session IDs.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Set up environment variables:

   Create a `.env` file in the root directory and add the following:

   ```plaintext
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SOURCE_REMOVAL_REGEX=your_regex_pattern
   ```

## Usage

Deploy the function to AWS Lambda using your preferred deployment method. Configure the Lambda function to handle HTTP GET requests via Function URL.

## Function Logic

1. **Request Validation**: The function checks the HTTP method and query parameters. Only GET requests are allowed, and required parameters (`bot_id` and `question`) must be present.
2. **Bot Configuration Retrieval**: Queries the Supabase database to retrieve the bot's configuration using the provided `bot_id`.
3. **Thread Management**: Creates a new thread or retrieves an existing thread based on the `thread_id`.
4. **Session Management**: Generates a new session ID if necessary.
5. **Message Handling**: Sends the user's question to the OpenAI API and stores the interaction in the Supabase database.
6. **Response Streaming**: Streams the AI-generated response back to the client, applying any specified regex transformations to the response content.
7. **Error Handling**: Catches and logs errors, returning appropriate error responses to the client.

## Error Responses

The function returns JSON responses for various error scenarios:

- `method_not_allowed`: Returned if the HTTP method is not GET.
- `missing_query_parameters`: Returned if required query parameters are missing.
- `bot_not_found`: Returned if the bot configuration is not found in the database.
- `bot_not_active`: Returned if the bot is not active.
- `bot_not_configured`: Returned if the bot is not properly configured.
- `internal_error`: Returned for unexpected internal errors.

## Example Request

```http
GET /?bot_id=your_bot_id&question=your_question
```

## Example Response

```json
{
  "status": "starts",
  "thread_id": "generated_thread_id",
  "session_id": "generated_session_id"
}
```

As the response is streamed, it will include the AI-generated content and a completion status:

```json
{
  "status": "completed",
  "thread_id": "generated_thread_id",
  "session_id": "generated_session_id"
}
```
