class EscalateIssue:
    """
    This class represents the process of escalating an issue.

    It is responsible for triggering the escalation process if certain escalation triggers are met.
    The escalation process includes collecting user information, confirming the escalation with the user,
    and making the function call to the escalation endpoint.

    Attributes:
        __name (str): The name of the function, used for calling it at the correct time.

    Methods:
        __escalation_role(self): Returns a string describing the role of the escalation process.
        __escalation_triggers(self): Returns a string describing the triggers for escalation.
        __escalation_process(self): Returns a string describing the steps of the escalation process.
        __input_collection_process(self): Returns a string describing the process of collecting user input.
        __escalation_instruction(self): Returns a string providing instructions for the escalation process.
        __escalation_absolute_restrictions(self): Returns a string listing the absolute restrictions for the escalation process.
        template(self): Returns a string template for the escalation process.
        tool_config(self): Returns a dictionary with information about the tool configuration.

    """

    def __init__(self) -> None:
        """
        Initializes the EscalateIssue class.

        Args:
            None

        Returns:
            None
        """
        # this name is for chat gpt so that it can call the function at correct time
        # eg. for this function we want chatgpt to call this function after completion of input collection process.
        self.__name = "escalateIssue"

    @property
    def __escalation_role(self):
        """
        Returns a string describing the role of the escalation process.

        Args:
            None

        Returns:
            str: A string describing the role of the escalation process.
        """
        return "Trigger Escalation process if below escalation triggers condition fulfill.\n"

    @property
    def __escalation_triggers(self):
        """
        Returns a string describing the triggers for escalation.

        Args:
            None

        Returns:
            str: A string describing the triggers for escalation.
        """
        return """
Initiate the "[ESCALATION PROCESS]" if any of the following occur:
1. The user explicitly requests to escalate the issue.
2. The user asks for more information about the same topic more than 3 times consistently.
3. The user expresses that they don't understand and asks to connect with a human.
4. The user expresses dissatisfaction with the provided answers multiple times(at least 2).
5. The user states that the information provided is incorrect or insufficient.
6. The user asks questions that are consistently outside the scope of the provided files.
7. The user repeatedly Ask to provide more information on the same topic consistently(more than 3 times).
"""

    @property
    def __escalation_process(self):
        return """
When an escalation trigger is met:
1. Inform the user: "I understand that you may need additional assistance. I'll need to collect some information from you. Would you like to proceed ?"
2. If the user agrees, initiate the "[INPUT COLLECTION PROCESS]".
"""

    @property
    def __input_collection_process(self):
        """
        Returns a string describing the process of collecting user input.

        Args:
            None

        Returns:
            str: A string describing the process of collecting user input.
        """
        return """
Collect and process the following required inputs:
Full Name (First Name and Last Name), Email Address, and Contact Number

[INPUT COLLECTION STEPS]
Step 1: Ask the user for all required input in a conversational manner.
Step 2: Process and validate all input using the following guidelines:

Full Name:
- Extract first and last name, accommodating middle names or initials.
- Capitalize the first letter of each name component.
- Remove extra spaces or unnecessary punctuation.
- Handle common transcription errors and variations.

Example inputs and processing:
- Input: "john michael smith" → Processed: "John Smith"
- Input: "SARAH J. PARKER" → Processed: "Sarah Parker"
- Input: "lee, wong mei" → Processed: "Wong Lee"
- Input: "john space J. doe" → Processed: "John Doe"

Email Address:
- Ensure it contains a valid structure (username@domain.com).
- Remove surrounding spaces or punctuation.
- Preserve the exact spelling and case of the username.
- Handle common transcription errors and spoken formats.

Example inputs and processing:
- Input: "john.smith@example.com" → Processed: "john.smith@example.com"
- Input: "jane dot doe at gmail dot com." → Processed: "jane.doe@gmail.com"
- Input: "mike underscore johnson at work mail dot org" → Processed: "mike_johnson@workmail.org"

Contact Number:
- Aim to extract 10 digits for standard phone numbers.
- Format as a continuous string of digits.
- Remove spaces, punctuation, or words.
- Handle various transcription and spoken formats.
- Accommodate potential country codes.

Example inputs and processing:
- Input: "555-123-4567" → Processed: "5551234567"
- Input: "five five five one two three four five six seven" → Processed: "5551234567"
- Input: "plus one triple eight nine two one fifty two oh three" → Processed: "18889215203"
- Input: "oh seven seven double zero nine double zero one two three" → Processed: "07700900123"
- Input: "5 5 5 1 2 3 4 5 6 7" → Processed: "5551234567"

Step 3: If an input is unclear or invalid, explain the issue conversationally and request clarification. Offer suggestions or examples if the user seems unsure.
Step 4: Once all valid inputs are collected, confirm all inputs with the user verbatim. (NOTE: DO NOT ASK FOR EXPLICIT CONFIRMATION)

(NOTE: DO NOT SHOW THE PROCESSED INPUT TO THE USER FOR CONFIRMATION.)
"""

    @property
    def __escalation_instruction(self):
        """
        Returns a string providing instructions for the escalation process.

        Args:
            None

        Returns:
            str: A string providing instructions for the escalation process.
        """
        return """
- Always ask for user's explicit permission before initiating the escalation process.
- Inform the user that you need to collect information before escalating.
- Only proceed with the escalation function call after completing the full input collection process.
- Confirm collected information with the user before making the function call.
"""

    @property
    def __escalation_absolute_restrictions(self):
        """
        Returns a string listing the absolute restrictions for the escalation process.

        Args:
            None

        Returns:
            str: A string listing the absolute restrictions for the escalation process.
        """
        return """
- Never call the function without completing the full input collection process and receiving user confirmation.
- Do not make assumptions about user details (name, email, phone). Always collect this information directly from the user.
- Never make the function call immediately after the user agrees to escalation - always complete the input collection first.
"""

    @property
    def template(self):
        """
        Returns the template of the chat assistant.

        Args:
            None

        Returns:
            str: The template of the chat assistant.
        """
        return f"""[ESCALATION ROLE] {self.__escalation_role}
[ESCALATION TRIGGERS] {self.__escalation_triggers}
[ESCALATION PROCESS] {self.__escalation_process}
[INPUT COLLECTION PROCESS] {self.__input_collection_process}
[ESCALATION INSTRUCTIONS] {self.__escalation_instruction}
[ESCALATION ABSOLUTE RESTRICTIONS] {self.__escalation_absolute_restrictions}
"""

    @property
    def tool_config(self):
        """
        Returns a dictionary with information about the tool configuration.

        Args:
            None

        Returns:
            dict: A dictionary with information about the tool configuration.
        """
        return {
            "name": self.__name,
            "description": "Escalate Any Issue or pass request to the human.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The full name of the user.",
                    },
                    "email": {
                        "type": "string",
                        "format": "email",
                        "description": "The email address of the user.",
                    },
                    "phone": {
                        "type": "string",
                        "description": "The 10-digit contact number of the user.",
                    },
                },
                "required": ["name", "email", "phone"],
            },
        }


class BookAppointment:
    """
    This class represents the process of booking an appointment.

    It is responsible for triggering the appointment booking process when certain conditions are met,
    collecting necessary information from the user, confirming the details, and making the function
    call to book the appointment.

    Attributes:
        __name (str): The name of the function, used for calling it at the correct time.

    Methods:
        __booking_role(self): Returns a string describing the role of the appointment booking process.
        __booking_triggers(self): Returns a string describing the triggers for initiating appointment booking.
        __booking_process(self): Returns a string describing the steps of the booking process.
        __input_collection_process(self): Returns a string describing the process of collecting user input.
        __booking_instruction(self): Returns a string providing instructions for the booking process.
        __booking_absolute_restrictions(self): Returns a string listing the absolute restrictions for the booking process.
        template(self): Returns a string template for the appointment booking process.
        tool_config(self): Returns a dictionary with information about the tool configuration.
    """

    def __init__(self) -> None:
        """
        Initializes the BookAppointment class.

        Args:
            None

        Returns:
            None
        """
        self.__name = "bookAppointment"

    @property
    def __booking_role(self):
        """
        Returns a string describing the role of the appointment booking process.

        Args:
            None

        Returns:
            str: A string describing the role of the appointment booking process.
        """
        return "Initiate the appointment booking process when the user expresses intent to schedule an appointment or when specific booking triggers are met.\n"

    @property
    def __booking_triggers(self):
        """
        Returns a string describing the triggers for initiating appointment booking.

        Args:
            None

        Returns:
            str: A string describing the triggers for initiating appointment booking.
        """
        return """
Initiate the "[BOOKING PROCESS]" if any of the following occur:
1. The user explicitly requests to book an appointment.
2. The user asks about availability for a specific service or time slot.
3. The user inquires about scheduling a consultation or meeting.
4. The user mentions needing to set up a time for a service.
5. The user asks how to make an appointment or reservation.
"""

    @property
    def __booking_process(self):
        """
        Returns a string describing the steps of the booking process.

        Args:
            None

        Returns:
            str: A string describing the steps of the booking process.
        """
        return """
When a booking trigger is met:
1. initiate the "[INPUT COLLECTION PROCESS]".
2. After collecting all required information, summarize the details and ask for confirmation.
3. If confirmed, proceed with the function call to book the appointment.
"""

    @property
    def __input_collection_process(self):
        """
        Returns a string describing the process of collecting user input for appointment booking.

        Args:
            None

        Returns:
            str: A string describing the process of collecting user input for appointment booking.
        """
        return f"""
1. Collect and process the following required inputs in a conversational manner. Say something like "I'll need some information to request an appointment": Full Name (First Name and Last Name), Email, Contact Number, Preferred Date and Time

2. Once info is collected, let user know they will get a link to confirm the details. If this is a voice based chat (available in the system info for this thread), you will let the user know: "I'll text you a link to book your preferred time. is that ok?"


[INPUT COLLECTION STEPS]
Step 1: Ask the user for all required input in a conversational manner.

Step 2: Process and validate all input using the following guidelines:

Full Name:
- Extract first and last name, accommodating middle names or initials.
- Capitalize the first letter of each name component.
- Remove extra spaces or unnecessary punctuation.
- Handle common transcription errors and variations.

Example inputs and processing:
- Input: "john michael smith" → Processed: "John Smith"
- Input: "SARAH J. PARKER" → Processed: "Sarah Parker"
- Input: "lee, wong mei" → Processed: "Wong Lee"
- Input: "john space J. doe" → Processed: "John Doe"

Email Address:
- Ensure it contains a valid structure (username@domain.com).
- Remove surrounding spaces or punctuation.
- Preserve the exact spelling and case of the username.
- Handle common transcription errors and spoken formats.

Example inputs and processing:
- Input: "john.smith@example.com" → Processed: "john.smith@example.com"
- Input: "jane dot doe at gmail dot com." → Processed: "jane.doe@gmail.com"
- Input: "mike underscore johnson at work mail dot org" → Processed: "mike_johnson@workmail.org"

Contact Number:
- Aim to extract 10 digits for standard phone numbers.
- Format as a continuous string of digits.
- Remove spaces, punctuation, or words.
- Handle various transcription and spoken formats.
- Accommodate potential country codes.

Example inputs and processing:
- Input: "555-123-4567" → Processed: "5551234567"
- Input: "five five five one two three four five six seven" → Processed: "5551234567"
- Input: "plus one triple eight nine two one fifty two oh three" → Processed: "18889215203"
- Input: "oh seven seven double zero nine double zero one two three" → Processed: "07700900123"
- Input: "5 5 5 1 2 3 4 5 6 7" → Processed: "5551234567"

Preferred Date:
- Accept various date formats and expressions.
- Convert to a standard format (YYYY-MM-DD).
- Ensure the date is in the future.
- Verify if the date falls on a business day, if relevant.
- Handle relative date terms and contextual information.
- If user asks what dates are available, let them know you will request the date and time, and someone from the business will call back if anything changes. 

Example inputs and processing:
- Input: "next Tuesday" → Processed: "2024-10-22" (assuming today is 2024-10-14)
- Input: "March 15th" → Processed: "2025-03-15" (if 2024-03-15 has passed)
- Input: "two weeks from now" → Processed: "2024-10-28"

Preferred Time:
- Accept various time formats and expressions.
- Convert to 24-hour format (HH:MM).
- Ensure the time falls within business hours, if applicable.
- Handle relative and approximate time expressions.

Example inputs and processing:
- Input: "3 pm" → Processed: "15:00"
- Input: "quarter past ten in the morning" → Processed: "10:15"
- Input: "half past fourteen hundred hours" → Processed: "14:30"

Step 3: If an input is unclear or invalid, explain the issue conversationally and request clarification. Offer suggestions or examples if the user seems unsure.
Step 4: Once all valid inputs are collected, confirm all inputs with the user verbatim. (NOTE: DO NOT ASK FOR EXPLICIT CONFIRMATION)

(NOTE: DO NOT SHOW THE PROCESSED INPUT TO USER FOR CONFIRMATION.)
"""

    @property
    def __booking_instruction(self):
        """
        Returns a string providing instructions for the booking process.

        Args:
            None

        Returns:
            str: A string providing instructions for the booking process.
        """
        return """
- Only proceed with the booking function call after completing the full input collection process and receiving user confirmation
- You do not have access to calendar info, ask user for other preferred time and say someone will reach out if they need to change it
- If system info says that is a voice call, then  let user know you'll send them a link where they'll need to book themselves. 
- Provide a brief explanation of the service if the user seems unsure about their selection.
- Remind the user of any preparation needed for their appointment type.
"""

    @property
    def __booking_absolute_restrictions(self):
        """
        Returns a string listing the absolute restrictions for the booking process.

        Args:
            None

        Returns:
            str: A string listing the absolute restrictions for the booking process.
        """
        return """
- Never call the function without completing the full input collection process and receiving user confirmation.
- Do not make assumptions about user details (name, email, date, time, contact info). Always collect this information directly from the user.
- Never book appointments outside of business hours or on non-business days.
- Do not proceed with booking if the requested service is not available.
- Never share personal information of other clients or available time slots of specific staff members.
"""

    @property
    def template(self):
        """
        Returns the template of the appointment booking assistant.

        Args:
            None

        Returns:
            str: The template of the appointment booking assistant.
        """
        return f"""[BOOKING ROLE] {self.__booking_role}
[BOOKING TRIGGERS] {self.__booking_triggers}
[BOOKING PROCESS] {self.__booking_process}
[INPUT COLLECTION PROCESS] {self.__input_collection_process}
[BOOKING INSTRUCTIONS] {self.__booking_instruction}
[BOOKING ABSOLUTE RESTRICTIONS] {self.__booking_absolute_restrictions}
"""

    @property
    def tool_config(self):
        """
        Returns a dictionary with information about the tool configuration.

        Args:
            None

        Returns:
            dict: A dictionary with information about the tool configuration.
        """
        return {
            "name": self.__name,
            "description": "Send an appointment booking link back to the requested user to book an appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The full name (first and last) of the user.",
                    },
                    "email": {
                        "type": "string",
                        "description": "The email address of the user. Ask only when user is connected via chat. If user fails to provide a valid email after 2 attempts, use an empty string. For call interactions, use an empty string without attempting to collect.",
                    },
                    "phone": {
                        "type": "string",
                        "description": "The 10-digit contact number of the user. ",
                    },
                    "preferred_date": {
                        "type": "string",
                        "format": "date",
                        "description": "The preferred date for the appointment (YYYY-MM-DD).",
                    },
                    "preferred_time": {
                        "type": "string",
                        "format": "time",
                        "pattern": "^(?:[01]?\d|2[0-3]):(?:[0-5]\d)$",
                        "description": "The preferred time for the appointment (HH:MM in 24-hour format).",
                    },
                },
                "required": [
                    "name",
                    "email",
                    "phone",
                    "preferred_date",
                    "preferred_time",
                ],
            },
        }


function_tools_map = {
    "escalate_issue": EscalateIssue,
    "book_appointment": BookAppointment,
}
