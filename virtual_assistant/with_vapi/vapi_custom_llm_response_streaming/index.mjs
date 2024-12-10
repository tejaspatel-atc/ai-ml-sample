import { v4 as uuidv4 } from "uuid";
import { openai, supabase } from "./config.mjs";
import {
    createOrRetrieveThread,
    createThreadRun,
    handleStreamError,
    handleStreamEvents,
    insertMessage,
} from "./helper.mjs";

const handleChatStreaming = async (queryStringParameters, responseStream) => {
    const {
        bot_id: botId,
        question,
        thread_id: threadId = null,
        session_id: sessionId,
        user_id: userId,
        user_type: userType,
        channel,
        user_phone_number: userPhoneNumber,
    } = queryStringParameters || {};
    console.info("Chat function called.");
    if (!botId || !question) {
        console.error("The bot_id and question parameters are required.");
        handleStreamError(responseStream, "The bot_id and question parameters are required.");
        return;
    }
    try {
        const { data: botData, error: botError } = await supabase
            .from("bots")
            .select("active, gpt_vector_store_id, gpt_assistant_id")
            .eq("bot_id", botId)
            .maybeSingle();

        if (botError || !botData || !botData.active || !botData.gpt_assistant_id) {
            console.error("The bot does not exist or is not active.");
            handleStreamError(responseStream, "The bot does not exist or is not active.");
            return;
        }

        const { gpt_vector_store_id: gptVectorStoreId, gpt_assistant_id: gptAssistantId } = botData;

        const thread = await createOrRetrieveThread(gptVectorStoreId, threadId);
        const currentSessionId =
            sessionId && sessionId !== "00000000-0000-0000-0000-000000000000"
                ? sessionId
                : uuidv4();

        await openai.beta.threads.messages.create(thread.id, {
            role: "user",
            content: question,
        });

        const additionalInstructions = `
            - Provide all responses in MARKDOWN FORMAT ONLY. Use appropriate markdown syntax for:
            """
            - ### Titles and #### headings
            - **Bold** and *italic* text
            - Unordered lists (please do not use periods (.), instead use asterisks (*) or hyphens (-))
            - Ordered lists (using numbers and letters)
            - > Blockquote(s)
            - Code blocks (if applicable)
            - etc.
            """
        `;

        const stream = await createThreadRun(thread.id, gptAssistantId, additionalInstructions);

        await insertMessage({
            message: question,
            message_type: "user_query",
            user_id: userId || "anonymous",
            user_type: userType || "anonymous",
            bot_id: botId,
            channel: channel || "text",
            user_phone_number: userPhoneNumber || "",
            session_id: currentSessionId,
            thread_id: thread.id,
        });

        await handleStreamEvents({
            client: openai,
            stream: stream,
            responseStream: responseStream,
            isForChat: true,
            queryStringParameters: queryStringParameters,
            sessionId: currentSessionId,
            botId: botId,
        });
    } catch (error) {
        console.error("Error Occurred in Chat Streaming: ", error);
        handleStreamError(responseStream, "Unexpected Error Occurred. Please try again later.");
    }
};

const handleVoiceStreaming = async (eventBody, responseStream) => {
    const {
        model: gptModel = process.env.OPENAI_MODEL,
        temperature: gptTemperature = process.env.OPENAI_TEMPERATURE,
        metadata: { bot_id: botId, gpt_assistant_id: gptAssistantId } = {},
        messages: rawMessages = [],
    } = eventBody;
    let systemMessage = "";
    const callConversation = rawMessages.filter((obj) =>
        obj.role === "system" ? !(systemMessage = obj.content) : true
    );
    const last30Conversations = callConversation.slice(-30);
    try {
        const stream = await openai.beta.threads.createAndRun({
            assistant_id: gptAssistantId,
            instructions: systemMessage,
            metadata: { chatType: "Voice" },
            model: gptModel,
            temperature: gptTemperature,
            thread: { messages: last30Conversations },
            stream: true,
            // tools: gptVectorStoreId ? [{ type: "file_search" }] : [],
            // tool_resources: gptVectorStoreId
            //     ? { file_search: { vector_store_ids: [gptVectorStoreId] } }
            //     : null,
        });

        await handleStreamEvents({
            client: openai,
            stream: stream,
            botId: botId,
            responseStream: responseStream,
            isForChat: false,
            callConversation: callConversation,
        });
    } catch (error) {
        console.error("Error Occurred in Voice Streaming: ", error);
        handleStreamError(
            responseStream,
            "Unexpected Error Occurred. Please try again later.",
            false
        );
    }
};

export const handler = awslambda.streamifyResponse(async (event, responseStream) => {
    const { method: httpMethod } = event.requestContext.http;
    responseStream.setContentType("text/event-stream");
    try {
        if (httpMethod === "GET") {
            const { queryStringParameters } = event;
            await handleChatStreaming(queryStringParameters, responseStream);
        } else if (httpMethod === "POST") {
            const eventBody = JSON.parse(event.body);
            await handleVoiceStreaming(eventBody, responseStream);
        } else {
            console.error("Invalid HTTP method.");
            handleStreamError(responseStream, "Invalid HTTP method.");
        }
    } catch (error) {
        console.error(error);
        handleStreamError(
            responseStream,
            "Unexpected Error Occurred. Please try again later.",
            httpMethod == "GET"
        );
    }
});
