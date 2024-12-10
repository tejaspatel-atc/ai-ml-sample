import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config();

const {
    OPENAI_API_KEY,
    SUPABASE_URL,
    SUPABASE_KEY,
    SOURCE_REMOVAL_REGEX,
    CUSTOM_FUNCTION_ESCALATION,
    CUSTOM_FUNCTION_APPOINTMENT,
} = process.env;

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);
export const openai = new OpenAI(OPENAI_API_KEY);
export const regex = SOURCE_REMOVAL_REGEX ? new RegExp(SOURCE_REMOVAL_REGEX, "g") : null;
export const escalationEndpoint = CUSTOM_FUNCTION_ESCALATION;
export const appointmentEndpoint = CUSTOM_FUNCTION_APPOINTMENT;
