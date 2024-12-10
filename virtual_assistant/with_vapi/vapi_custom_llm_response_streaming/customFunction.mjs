import fetch from "node-fetch";
import { appointmentEndpoint, escalationEndpoint } from "./config.mjs";

export const escalateIssue = async ({
    sessionId,
    name,
    email,
    phone,
    botId,
    isForChat,
    callConversation,
}) => {
    try {
        const response = await fetch(escalationEndpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                session_id: sessionId,
                name: name,
                email: email,
                phone: phone,
                bot_id: botId,
                is_voice: !isForChat,
                chat_history: callConversation,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return JSON.stringify(result);
    } catch (error) {
        console.error("Error escalating issue: ", error);
        return "Unexpected Error Occurred. Please try again later.";
    }
};

export const bookAppointment = async ({
    sessionId,
    name,
    email,
    phone,
    preferred_date,
    preferred_time,
    botId,
    isForChat,
    callConversation,
}) => {
    try {
        const response = await fetch(appointmentEndpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                session_id: sessionId,
                name: name,
                email: email,
                phone: phone,
                preferred_date: preferred_date,
                preferred_time: preferred_time,
                bot_id: botId,
                is_voice: !isForChat,
                chat_history: callConversation,
            }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return JSON.stringify(result);
    } catch (error) {
        console.error("Error booking appointment: ", error);
        return "Unexpected Error Occurred. Please try again later.";
    }
};
