import grpc
import asyncio
from completions_pb2 import ChatCompletionRequest
from completions_pb2_grpc import CompletionsServiceStub

async def run():
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = CompletionsServiceStub(channel)
        
        # Example prompt and messages
        prompt = "Hello, how can I assist you today?"
        messages = ["Hello", "What is the weather like today?"]
        
        # Create the request
        request = ChatCompletionRequest(prompt=prompt, messages=messages)
        
        # Send the request and get the response
        response = await stub.ChatCompletion(request)
        print(f"Assistant reply: {response.reply}")

if __name__ == "__main__":
    asyncio.run(run())
