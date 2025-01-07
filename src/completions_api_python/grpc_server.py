import asyncio
import grpc
from concurrent import futures
from completions_pb2 import ChatCompletionResponse
from completions_pb2_grpc import CompletionsServiceServicer, add_CompletionsServiceServicer_to_server
from src.completions_api_python.main import CompletionsAPI

class CompletionsServicer(CompletionsServiceServicer):
    def __init__(self):
        self.api_instance = CompletionsAPI()

    async def ChatCompletion(self, request, context):
        # Convert gRPC request to the format expected by the CompletionsAPI
        messages = [{"role": "user", "content": msg} for msg in request.messages]
        assistant_reply = await self.api_instance.stream_completion(messages)
        
        # Return the response
        return ChatCompletionResponse(reply=assistant_reply)

async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    add_CompletionsServiceServicer_to_server(CompletionsServicer(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    print("gRPC server started on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
