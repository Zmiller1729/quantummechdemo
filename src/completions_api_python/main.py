import asyncio
import os
import json
import argparse
import inspect
import logging
from openai import AsyncOpenAI
# import ChatCompletion
from openai import AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from dotenv import load_dotenv
from src.modules.assistant import AssistantAPI
from src.modules.logging import log_tool_call, log_error, log_info, setup_logging
from src.modules.tools.base.tools import function_map, tools
from src.modules.tools.pulumi.pulumi import tools as pulumi_tools, function_map as pulumi_function_map

# Load environment variables
load_dotenv()

class CompletionsAPI(AssistantAPI):
    def __init__(self, prompts=None, debug=False):
        super().__init__(prompts, debug=debug)
        self.client = AsyncOpenAI(
            # This is the default and can be omitted
            api_key=self.api_key,
        )
        self.messages = []  # To keep track of the conversation history
        # self.tools = tools
        self.tools = tools + pulumi_tools
        self.function_map = {**function_map, **pulumi_function_map}
        self.model = "gpt-4-0613"

    async def run(self):
        if self.prompts:
            await self.send_initial_prompts()
        else:
            while True:
                # Capture user input
                user_input = input("You: ")
                if user_input.lower() in {"exit", "quit"}:
                    break
                # Append user's message
                self.messages.append({"role": "user", "content": user_input})
                # Get assistant's response
                assistant_reply = await self.stream_completion(self.messages)
                # Append assistant's reply
                self.messages.append({"role": "assistant", "content": assistant_reply})
                print()
                # print(f"\nAssistant: {assistant_reply}")

    async def initialize_session(self, websocket=None):
        # No initialization needed for the completions API
        pass

    async def send_initial_prompts(self, websocket=None):
        if self.prompts:
            for prompt in self.prompts:
                self.messages.append({"role": "user", "content": prompt})
                assistant_reply = self.stream_completion(self.messages)
                self.messages.append({"role": "assistant", "content": assistant_reply})
                print(f"\nAssistant: {assistant_reply}")

    async def handle_event(self, event, websocket=None):
        # No event handling needed for the completions API
        pass

    async def execute_function(self, function_name, arguments):
        if function_name in self.function_map:
            # Parse arguments if they are provided as a JSON string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError as e:
                    error_message = f"Error parsing arguments for function '{function_name}': {str(e)}"
                    log_error(self.logger, error_message)
                    return json.dumps({"error": error_message})

            # Ensure arguments is a dictionary before unpacking
            if not isinstance(arguments, dict):
                error_message = f"Arguments for function '{function_name}' must be a dictionary after parsing."
                log_error(self.logger,error_message)
                return json.dumps({"error": error_message})

            # Execute the function and handle any execution errors
            try:
                # Check if the function is a coroutine (asynchronous function)
                function = self.function_map[function_name]
                if inspect.iscoroutinefunction(function):
                    result = await function(**arguments)
                else:
                    result = function(**arguments)
                log_tool_call(self.logger, function_name, arguments, result)
                # Print the result to the console
                print(f"\n🛠️ Function '{function_name}' executed successfully. Result: {result}")
                return json.dumps(result)
            except Exception as e:
                error_message = f"Error executing function '{function_name}': {str(e)}"
                log_error(self.logger, error_message)
                return json.dumps({"error": error_message})
        else:
            error_message = f"Function '{function_name}' not found."
            log_error(self.logger, error_message)
            return json.dumps({"error": error_message})

    async def stream_completion(self, messages):
        content_buffer = [
            f"\nAssistant: ",
        ]
        print("\nAssistant: ")

        function_name_buffer = None
        arguments_buffer = []

        try:
            stream: AsyncStream[ChatCompletionChunk] = await self.client.chat.completions.create(
                model=self.model,  # Use a compatible model
                messages=messages,
                # functions=tools,
                functions=self.tools,
                function_call="auto",
                stream=True
            )
            async for chunk in stream:
                choice=chunk.choices[0]
                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(choice)
                # Check if this chunk contains part of a function call
                if choice.delta.function_call:
                    self.logger.debug(f"Function call: {choice.delta.function_call}")
                # Accumulate the function name if it's present in the chunk
                    if choice.delta.function_call.name:
                        function_name_buffer = choice.delta.function_call.name
                    
                    # Accumulate arguments in chunks
                    if choice.delta.function_call.arguments:
                        arguments_buffer.append(choice.delta.function_call.arguments)

                if choice.delta.content:
                    print(choice.delta.content or "", end="")
                    content_buffer.append(choice.delta.content or "")

                if self.logger.isEnabledFor(logging.DEBUG):
                    self.logger.debug(f"Function name buffer: {function_name_buffer}")

                # Handle finish reasons
                if choice.finish_reason:
                    if choice.finish_reason == "function_call":
                        # Execute the function call
                        full_arguments = "".join(arguments_buffer)
                        self.logger.info(f"Complete function call: {function_name_buffer} with arguments {full_arguments}")
                        result = await self.execute_function(function_name_buffer, full_arguments)
                        content_buffer.append(result)
                        # Reset buffers for next function call
                        function_name_buffer = None
                        arguments_buffer = []

                        # Reset buffers for next function call
                        function_name_buffer = None
                        arguments_buffer = []

                    elif choice.finish_reason == "stop":
                        # Model completed its response
                        self.logger.info("Response completed by model.")
                        break  # Optional: Exit if you want to end here

                    elif choice.finish_reason == "length":
                        # Response was cut off due to token limit
                        self.logger.warning("Response length limit reached. Consider re-prompting for full answer.")
                        content_buffer.append("[Response truncated due to length limit]")

                    elif choice.finish_reason == "content_filter":
                        # Content moderation was triggered
                        self.logger.warning("Response filtered due to content moderation.")
                        content_buffer.append("[Response was filtered due to content moderation]")

            return "".join(content_buffer) + "\n"
        except Exception as e:
            log_error(self.logger, f"An error occurred during the completion stream: {e}")
            return ""

def main():
    print("Starting OpenAI API assistant...")
    parser = argparse.ArgumentParser(
        description="Run the OpenAI API assistant with optional prompts."
    )
    parser.add_argument("--prompts", type=str, help="Prompts separated by |")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logger = setup_logging("completions_api", logging.DEBUG if args.debug else logging.INFO)
    logger.info("Starting OpenAI API assistant...")
    parser = argparse.ArgumentParser(
        description="Run the OpenAI API assistant with optional prompts."
    )
    parser.add_argument("--prompts", type=str, help="Prompts separated by |")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    prompts = args.prompts.split("|") if args.prompts else None

    debug = args.debug
    openai_api_instance = CompletionsAPI(prompts, debug=debug)
    openai_api_instance.logger = logger
    try:
        asyncio.run(openai_api_instance.run())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print("Press Ctrl+C to exit the program.")
    main()
