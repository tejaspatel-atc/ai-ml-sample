import json
import logging
import os
from http import HTTPStatus
from io import BytesIO
from typing import Any, Dict, List, Literal, Optional

from config import get_prompt, make_vapi_tools
from postgrest.base_request_builder import SingleAPIResponse
from requests import Response, request
from supabase import Client, create_client

logging_level = logging.DEBUG
logging.basicConfig(level=logging_level)
logger = logging.getLogger()
logger.setLevel(logging_level)

OPEN_AI_MODEL: str = os.environ.get("OPEN_AI_MODEL", "gpt-3.5-turbo")
OPEN_AI_MODEL_TEMPERATURE: float = float(os.environ.get("OPEN_AI_MODEL_TEMPERATURE", "0.5"))
VAPI_URL: Optional[str] = os.environ.get("VAPI_URL")
VAPI_TOKEN: Optional[str] = os.environ.get("VAPI_TOKEN")
VAPI_SERVER_URL: Optional[str] = os.environ.get("VAPI_SERVER_URL")
VAPI_CUSTOM_LLM_URL: Optional[str] = os.environ.get("VAPI_CUSTOM_LLM_URL")
SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")
CORS_ALLOWED_ORIGINS: list = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
CUSTOM_TOOL_ESCALATION_ID: Optional[str] = os.environ.get("CUSTOM_TOOL_ESCALATION_ID")
CUSTOM_TOOL_APPOINTMENT_ID: Optional[str] = os.environ.get("CUSTOM_TOOL_APPOINTMENT_ID")

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def check_or_upload_files(file_data: List[Dict[str, str]]) -> List[str]:
    """
    Checks if the files in the given data have already been uploaded to VAPI.
    If not, downloads the files from Supabase storage, saves them to a temporary folder,
    and uploads them to the VAPI service. Updates the Supabase botDocument with the VAPI file ID.

    Args:
        file_data (List[Dict[str, str]]): List of dictionaries containing file information.
            Each dictionary should have:
                - 'id': ID of the file in Supabase.
                - 'name': Name of the file (optional).
                - 'path': Path to the file in Supabase storage.
                - 'vapi_file_id': ID of the file in VAPI (if it exists).

    Returns:
        List[str]: List of VAPI file IDs.

    Notes:
        - Uses Supabase storage to fetch files.
        - Handles file uploads and updates `botDocument` with the VAPI file ID.
        - Collects all VAPI file IDs in a list.
        - Temporary files are saved in a temp folder and removed after use.
    """
    vapi_file_upload_url = f"https://api.vapi.ai/file"
    headers = {"Authorization": f"Bearer {VAPI_TOKEN}"}

    vapi_file_ids = []  # List to collect all VAPI file IDs

    for file in file_data:
        try:
            # Skip if the file has already been uploaded and append the existing VAPI file ID
            if file.get("vapi_file_id"):
                vapi_file_ids.append(file["vapi_file_id"])
                continue

            file_id = file.get("id")
            file_name = file.get("name")
            file_path = file.get("path")

            # Skip if name or path is missing
            if not file_name or not file_path:
                logger.warning(f"Skipping file due to missing name or path: {file}")
                continue

            # Download the file from Supabase storage
            file_buffer = BytesIO()
            response = supabase.storage.from_("helloservice").download(file_path)
            file_buffer.write(response)
            file_buffer.seek(0)  # Reset the buffer pointer to the beginning

            # Upload the file to VAPI using the buffer
            files = {"file": (file_name, file_buffer)}
            response = request("POST", vapi_file_upload_url, files=files, headers=headers)

            # Check for a successful upload
            if response.status_code == 201:
                vapi_file_id = response.json().get("id")
                if vapi_file_id:
                    # Append the VAPI file ID to the list
                    vapi_file_ids.append(vapi_file_id)

                    # Update Supabase botDocument with the new VAPI file ID
                    supabase.table("botDocuments").update({"vapi_file_id": vapi_file_id}).eq(
                        "id", file_id
                    ).execute()
                else:
                    logger.error(f"VAPI response did not contain a file ID for file: {file_name}")
            else:
                logger.error(
                    f"Failed to upload {file_name} to VAPI. Status code: {response.status_code}"
                )

        except Exception as e:
            # Log and continue on any error
            logger.error(f"Error processing file {file.get('name')}: {e}")
            continue

    return vapi_file_ids


def prepare_payload(
    event_body: Dict[str, Any], bot_detail: Dict[str, Any], bot_id: str
) -> Dict[str, Any]:
    """This function prepares the payload for the API call

    Args:
        event_body (Dict[str, Any]): event body
        bot_detail (Dict[str, Any]): bot detail
        bot_id (str): bot id

    Returns:
        Dict[str, Any]: payload
    """
    logger.info("retrieving data from the event body...")
    # retrieve data from event body
    is_semantic_caching_enabled: bool = event_body.get("semantic_caching") or False
    is_emotion_recognition_enabled: bool = event_body.get("emotion_recognition") or True
    is_filler_injection_enabled: bool = event_body.get("filler_injection") or False
    is_call_recording_enabled: bool = event_body.get("call_recording") or True
    is_back_channeling_enabled: bool = event_body.get("back_channeling") or False
    can_assistant_end_the_call: bool = event_body.get("assistant_end_call") or True
    can_assistant_detect_voice_mail: bool = event_body.get("voice_mail_detection") or False
    end_call_message: str = event_body.get("end_call_message") or "Thank you! Have a nice day"
    background_sound: Literal["off", "office"] = event_body.get("background_sound") or "off"
    translate_language: str = event_body.get("translated_language") or "en-US"
    voice_provider_name: str = event_body.get("voice_provider_name") or "rime-ai"
    voice_id: str = event_body.get("voice_id") or "lagoon"
    num_words_to_interrupt_assistant: int = int(event_body.get("interruption_threshold") or "3")
    is_background_denoising_enabled: bool = event_body.get("background_denoising") or True
    is_custom_llm_enabled: bool = event_body.get("custom_llm") or False
    max_duration_seconds: int = int(event_body.get("max_duration_seconds") or "1200")
    end_call_phrases: list = list(
        map(str.strip, (event_body.get("end_call_phrases") or "goodbye,bye bye").split(","))
    )
    forwarding_phone_number: str = event_body.get("forwarding_phone_number")
    function_tools = ["escalate_issue"]
    function_tools.extend(event_body.get("custom_functions", []))
    # retrieve data from supabase generate_response
    bot_name: str = bot_detail.get("bot_name") or "Ava"
    bot_prompt: str = get_prompt(
        bot_name=bot_name,
        role_use_case=bot_detail.get("role_use_case"),
        custom_functions_list=function_tools,
        custom_template=bot_detail.get("prompt"),
    )
    bot_first_message: str = (
        bot_detail.get("greeting") or f"Hello there! What can I help you with today?"
    )

    vapi_metadata: dict = {
        "bot_id": bot_id,
        "gpt_assistant_id": bot_detail.get("gpt_assistant_id"),
        "gpt_vector_store_id": bot_detail.get("gpt_vector_store_id"),
    }

    # prepare payload for the vapi assistant
    vapi_model = {
        "messages": [{"content": bot_prompt, "role": "system"}],
        "model": OPEN_AI_MODEL,
        "temperature": OPEN_AI_MODEL_TEMPERATURE,
        "emotionRecognitionEnabled": is_emotion_recognition_enabled,
    }

    if VAPI_CUSTOM_LLM_URL and is_custom_llm_enabled:
        vapi_model["provider"] = "custom-llm"
        vapi_model["url"] = VAPI_CUSTOM_LLM_URL
    else:
        vapi_model["provider"] = "openai"
        vapi_model["semanticCachingEnabled"] = is_semantic_caching_enabled

    file_urls = check_or_upload_files(bot_detail.get("botDocuments") or [])
    if file_urls:
        vapi_model["knowledgeBase"] = {"provider": "canonical", "fileIds": file_urls, "topK": 0.5}

    if forwarding_phone_number:
        # Use E164 Format for the forwarding_phone_number: https://www.twilio.com/docs/glossary/what-e164
        vapi_model["tools"] = make_vapi_tools(call_forwarding_number=forwarding_phone_number)

    if function_tools:
        vapi_model["toolIds"] = []
        if "escalate_issue" in function_tools:
            vapi_model["toolIds"].append(CUSTOM_TOOL_ESCALATION_ID)
        if "book_appointment" in function_tools:
            vapi_model["toolIds"].append(CUSTOM_TOOL_APPOINTMENT_ID)

    logger.info("creating payload for the vapi assistant...")
    payload = {
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": translate_language,
            "smartFormat": True,
            "keywords": [],
            "endpointing": 500,
        },
        "model": vapi_model,
        "voice": {
            "fillerInjectionEnabled": is_filler_injection_enabled,
            "provider": voice_provider_name,
            "voiceId": voice_id,
        },
        "startSpeakingPlan": {"waitSeconds": 0.9},
        "firstMessageMode": "assistant-speaks-first",
        "recordingEnabled": is_call_recording_enabled,
        "endCallFunctionEnabled": can_assistant_end_the_call,
        "llmRequestDelaySeconds": 0.5,
        "numWordsToInterruptAssistant": num_words_to_interrupt_assistant,
        "maxDurationSeconds": max_duration_seconds,
        "backgroundSound": background_sound,
        "backchannelingEnabled": is_back_channeling_enabled,
        "backgroundDenoisingEnabled": is_background_denoising_enabled,
        "name": f"{bot_name}_{bot_id}",
        "firstMessage": bot_first_message,
        "voicemailDetectionEnabled": can_assistant_detect_voice_mail,
        "endCallMessage": end_call_message,
        "endCallPhrases": end_call_phrases,
        "metadata": vapi_metadata,
        "serverMessages": ["end-of-call-report"],
        "serverUrl": VAPI_SERVER_URL,
    }
    return payload


def upsert_url(url: str, assistant_id: Optional[str] = None) -> str:
    """
    Returns the URL with the assistant ID appended if it is present.

    Args:
        url (str): The base URL.
        assistant_id (Optional[str]): The ID of the assistant.

    Returns:
        str: The URL with the assistant ID appended if it is present.
    """
    return f"{url}/{assistant_id}" if assistant_id else url


def upsert_vapi_assistant(
    payload: Dict[str, Any], vapi_assistant_id: Optional[str]
) -> tuple[Literal["PATCH", "POST"], Response]:
    """
    Makes a PATCH or POST request to the Vapi assistant API based on whether a `vapi_assistant_id` is present in the bot details.

    Args:
        payload (Dict[str, Any]): The payload to be sent in the request.
        vapi_assistant_id (Optional[str]): The ID of the Vapi assistant.

    Returns:
        tuple[Literal["PATCH", "POST"], Response]: A tuple containing the HTTP method and response from the API call.
    """
    if vapi_assistant_id:
        request_method = "PATCH"
        logger.info("Updating vapi assistant...")
    else:
        request_method = "POST"
        logger.info("Creating vapi assistant...")
    vapi_local_url = upsert_url(VAPI_URL, vapi_assistant_id)
    headers = {"Authorization": f"Bearer {VAPI_TOKEN}", "Content-Type": "application/json"}
    vgenerate_response: Response = request(
        request_method, vapi_local_url, json=payload, headers=headers
    )
    return request_method, vgenerate_response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda function handler for creating or updating a Vapi assistant.

    This function receives an HTTP request event and processes it to create or update a Vapi assistant.
    It follows a step-by-step process to validate the request, retrieve the necessary parameters, and make API calls to Vapi.

    Parameters:
    - event (Dict[str, Any]): The event containing the HTTP request details.
    - context (Any): The context object, not used in this function.

    Returns:
    - Dict[str, Any]: The response containing the status code, headers, and body.

    Steps:
    1. Extract the HTTP method and request body from the event.
    2. Check if the HTTP method is "POST". If not, return a response with a 400 status code and an error message.
    3. Extract the required parameters from the request body.
    4. Check if the required parameters are present. If not, return a response with a 400 status code and an error message.
    5. Retrieve the bot details from the supabase database using the `supabase` client.
    6. Check if the bot exists and has a `gpt_assistant_id`. If not, return a response with a 400 status code and an error message.
    7. Prepare the payload for the Vapi assistant API call.
    8. Make a PATCH or POST request to the Vapi assistant API based on whether a `vapi_assistant_id` is present in the bot details.
    9. If the Vapi assistant API call succeeds, update the `vapi_assistant_id` field in the supabase database.
    10. Log the action in the `appLogs` table in the supabase database.

    Note:
    - The function uses the `generate_response` helper function to generate the response dictionary.
    - The function uses the `prepare_payload` helper function to prepare the payload for the Vapi assistant API call.
    - The function uses the `upsert_vapi_assistant` helper function to make the API call.
    - The function relies on external dependencies such as the supabase database and the Vapi API.
    - The function follows a modular design, with the main logic separated into smaller functions.
    """

    def generate_response(status_code: int, body: str):
        """
        Generates a response dictionary with the given status code and data.

        Args:
            status_code (int): The HTTP status code for the response.
            body (str): The data to be included in the response body.

        Returns:
            Dict[str, Any]: The response dictionary with the following structure:
                {
                    "statusCode": int,
                    "headers": {"Content-Type": "application/json"},
                    "body": str,
                }
        """
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json",
                **(
                    {"Access-Control-Allow-Origin": event.get("headers", {}).get("origin")}
                    if event["headers"].get("origin") in CORS_ALLOWED_ORIGINS
                    else {}
                ),
            },
            "body": json.dumps(body),
        }

    try:
        logger.debug("requested event %s", event)
        # check for the correct http method.
        if event["httpMethod"] != "POST":
            logger.error("wrong http method")
            return generate_response(
                status_code=HTTPStatus.BAD_REQUEST,
                body={
                    "code": "wrong_http_method",
                    "message": "This API is accept only POST request.",
                },
            )

        # retrieve event body.
        event_body = json.loads(event["body"])

        # retrieve bot_id from event_body
        bot_id: Optional[str[int]] = event_body.get("bot_id")

        # check for the required payload
        if not bot_id or bot_id == "null":
            logger.error("bot_id not found in the request body")
            return generate_response(
                status_code=HTTPStatus.BAD_REQUEST,
                body={
                    "code": "required_bot_id",
                    "message": "bot_id not found in the request body.",
                },
            )

        logger.info("getting data from the supabase for the bot %s...", bot_id)
        bot_detail_object: Optional[SingleAPIResponse] = (
            supabase.table("bots")
            .select(
                "bot_name, agent_role, industry, prompt, greeting, gpt_assistant_id, vapi_assistant_id",
                "gpt_vector_store_id",
                "botDocuments(id, name, path, vapi_file_id)",
            )
            .eq("bot_id", bot_id)
            .eq("active", True)
            .maybe_single()
            .execute()
        )

        if bot_detail_object is None:
            logger.error("Given bot_id have no details in database or is not active")
            return generate_response(
                status_code=HTTPStatus.BAD_REQUEST,
                body={
                    "code": "wrong_bot_id",
                    "message": "Given bot_id have no details in database or is not active.",
                },
            )
        bot_detail = bot_detail_object.data
        logger.debug("Bot Details %s", bot_detail)

        if not bot_detail.get("gpt_assistant_id"):
            logger.error("bot have no gpt_assistant_id")
            return generate_response(
                status_code=HTTPStatus.BAD_REQUEST,
                body={"code": "bot_not_configured", "message": "bot have no gpt assistant id."},
            )

        payload = prepare_payload(event_body=event_body, bot_detail=bot_detail, bot_id=bot_id)
        logger.debug("vapi assistant payload: %s", payload)

        request_method, vgenerate_response = upsert_vapi_assistant(
            payload=payload, vapi_assistant_id=bot_detail.get("vapi_assistant_id")
        )

        if vgenerate_response.status_code in [200, 201]:
            logger.info("vapi assistant api succeed")

            response_data = vgenerate_response.json()
            logger.debug("Vapi Response: %s", response_data)

            supabase.table("bots").update({"vapi_assistant_id": response_data["id"]}).eq(
                "bot_id", bot_id
            ).execute()

            return generate_response(
                status_code=HTTPStatus.OK,
                body={
                    "message": f'vapi assistant {"created" if request_method == "POST" else "updated"} successfully'
                },
            )
        else:
            logger.info("vapi assistant api failed due to %s", vgenerate_response.text)
            return generate_response(
                status_code=(vgenerate_response.status_code),
                body={"message": vgenerate_response.text},
            )
    except Exception as e:
        logger.error("%s error occurred, at line no %s", str(e), e.__traceback__.tb_lineno)
        return generate_response(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            body={"code": "unexpected_error_occurred", "body": str(e)},
        )


if __name__ == "__main__":
    lambda_handler(
        {
            "httpMethod": "POST",
            "body": json.dumps({"bot_id": 48, "custom_functions": ["book_appointment"]}),
        },
        {},
    )
