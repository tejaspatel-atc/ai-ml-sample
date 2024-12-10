# Prompt Engine

## Overview

The `prompts_engine` package is designed to facilitate the creation of customized prompts for chat assistant bots. This package includes classes for defining the escalation process of issues (`EscalateIssue`) and for creating chat assistant prompts (`Prompt`). These classes help streamline the configuration and management of chat assistant behaviors.

## Setup

### Prerequisites

- Python 3.7 or higher
- A development environment with access to Python package management tools like `pip`

### Installation

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install dependencies:**
    Install the necessary dependencies using `pip`:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

No additional configuration is required beyond the installation steps. Ensure your environment has the necessary dependencies installed.

## Usage

### EscalateIssue Class

The `EscalateIssue` class handles the escalation process when certain triggers are met. It provides methods to describe the escalation role, triggers, process, input collection, instructions, and restrictions.

#### Example Usage

```python
from prompts.custom_functions import EscalateIssue

escalate_issue = EscalateIssue()

print(escalate_issue.template)
print(escalate_issue.tool_config)
```

### Prompt Class

The `Prompt` class represents a chat assistant prompt, including the bot's identity, role, and behavior. It provides properties to define various aspects of the chat assistant's operation, such as information delivery, conversation control, and restrictions.

#### Example Usage

```python
from prompts.prompt import Prompt

bot_name = "ChatBot"
role_use_case = "customer support"
prompt = Prompt(bot_name, role_use_case)

print(prompt.default_template)
```

### Lambda Zip creation

```bash
cd <repository-directory>
pip install . -t <layer-directory>/python
cd <layer-directory>/python
zip -r <layer-name>.zip .
```

## Class Documentation

### EscalateIssue Class

- **Attributes:**
  - `__name`: The name of the function for calling it at the correct time.

- **Methods:**
  - `__escalation_role(self)`: Describes the role of the escalation process.
  - `__escalation_triggers(self)`: Lists the triggers for escalation.
  - `__escalation_process(self)`: Describes the steps of the escalation process.
  - `__input_collection_process(self)`: Describes the process of collecting user input.
  - `__escalation_instruction(self)`: Provides instructions for the escalation process.
  - `__escalation_absolute_restrictions(self)`: Lists the absolute restrictions for the escalation process.
  - `template(self)`: Returns a string template for the escalation process.
  - `tool_config(self)`: Returns a dictionary with information about the tool configuration.

### Prompt Class

- **Attributes:**
  - `bot_name`: The name of the chat assistant bot.
  - `role_use_case`: The role and use case of the chat assistant.

- **Properties:**
  - `__identity(self)`: Returns the identity of the chat assistant.
  - `__primary_role(self)`: Returns the primary role of the chat assistant.
  - `__assistance_process(self)`: Describes the assistance process.
  - `__information_delivery(self)`: Describes the information delivery process.
  - `__handling_repeated_questions(self)`: Describes how the chat assistant handles repeated questions.
  - `__information_boundaries(self)`: Describes the information boundaries.
  - `__conversation_control(self)`: Describes the conversation control.
  - `__clarification(self)`: Describes the clarification process.
  - `__demeanor(self)`: Describes the demeanor.
  - `__absolute_restrictions(self)`: Describes the absolute restrictions.
  - `__general_instruction(self)`: Provides the general instruction.
  - `__general_function_restriction(self)`: Describes the general function restriction.
  - `default_template(self)`: Returns the default template for the chat assistant prompt.

## Troubleshooting

### Common Issues

1. **Missing Dependencies:**
    - Ensure all required dependencies are installed as specified in the `requirements.txt` file.

2. **Incorrect Class Usage:**
    - Verify that you are correctly instantiating and using the classes as shown in the example usage sections.

### Logging

- The package does not include internal logging. You can add logging as needed based on your specific use case and environment.
