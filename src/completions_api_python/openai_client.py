import grpc
import asyncio
from completions_pb2 import ChatCompletionRequest
from completions_pb2_grpc import CompletionsServiceStub

class OpenAIClient:
    def __init__(self, grpc_server_address="localhost:50051"):
        self.grpc_server_address = grpc_server_address

    async def send_prompt(self, prompt, messages):
        async with grpc.aio.insecure_channel(self.grpc_server_address) as channel:
            stub = CompletionsServiceStub(channel)
            request = ChatCompletionRequest(prompt=prompt, messages=messages)
            response = await stub.ChatCompletion(request)
            return response.reply

# Example usage
if __name__ == "__main__":
    client = OpenAIClient()
    asyncio.run(client.send_prompt("Hello", ["What is the weather like?"]))
