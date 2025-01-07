import asyncio
import grpc.aio
from . import realtime_api_pb2, realtime_api_pb2_grpc
from .main import RealtimeAPI
from src.modules.logging import logger

class RealtimeAPIServicer(realtime_api_pb2_grpc.RealtimeAPIServicer):
    def __init__(self, use_realtime_api=True):
        self.realtime_api = RealtimeAPI(prompts=None, use_realtime_api=use_realtime_api)

    async def StreamAudio(self, request_iterator, context):
        try:
            async for audio_request in request_iterator:
                audio_data = audio_request.audio_data
                # Process audio data using realtime_api
                self.realtime_api.mic.queue.put(audio_data)
                
                # Create response
                response = realtime_api_pb2.APIResponse()
                if hasattr(self.realtime_api, 'assistant_reply') and self.realtime_api.assistant_reply:
                    response.text.text = self.realtime_api.assistant_reply
                yield response
        except Exception as e:
            logger.error(f"Error in StreamAudio: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return

    async def SendTextPrompt(self, request, context):
        try:
            prompt = request.prompt
            logger.info(f"Received text prompt: {prompt}")
            
            # Initialize websocket connection if needed
            if not hasattr(self.realtime_api, 'websocket'):
                await self.realtime_api.run()
            
            # Send prompt to assistant
            await self.realtime_api.send_initial_prompts([prompt])
            
            # Create and yield response
            response = realtime_api_pb2.APIResponse()
            response.text.text = self.realtime_api.assistant_reply
            yield response
            
        except Exception as e:
            logger.error(f"Error in SendTextPrompt: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return

async def serve(use_realtime_api=True):
    server = grpc.aio.server()
    realtime_api_pb2_grpc.add_RealtimeAPIServicer_to_server(
        RealtimeAPIServicer(use_realtime_api=use_realtime_api),
        server
    )
    server.add_insecure_port('[::]:50051')
    logger.info("Starting gRPC server on [::]:50051")
    await server.start()
    await server.wait_for_termination()
