import asyncio
import grpc
import argparse
import os
from . import realtime_api_pb2, realtime_api_pb2_grpc
from src.modules.logging import logger
from .main import RealtimeAPI

async def run_text_prompt(prompt: str):
    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = realtime_api_pb2_grpc.RealtimeAPIStub(channel)
        
        try:
            response_iterator = stub.SendTextPrompt(
                realtime_api_pb2.TextRequest(prompt=prompt)
            )
            async for response in response_iterator:
                if response.HasField('text'):
                    print("Assistant:", response.text.text)
                elif response.HasField('audio'):
                    print("Received audio response")
                elif response.HasField('function_call'):
                    print("Function call:", response.function_call.function_name)
                elif response.HasField('error'):
                    print("Error:", response.error.error_message)
        except Exception as e:
            logger.error(f"Error during gRPC call: {str(e)}")

def main():
    print(f"Starting realtime API...")
    logger.info(f"Starting realtime API...")
    parser = argparse.ArgumentParser(
        description="Run the realtime API with optional prompts."
    )
    parser.add_argument("--prompts", type=str, help="Prompts separated by |")
    parser.add_argument('--server', action='store_true', help='Run in gRPC server mode')
    parser.add_argument(
        '--use_realtime_api',
        action='store_true',
        help='Use the OpenAI Realtime API'
    )
    args = parser.parse_args()

    use_realtime_api = args.use_realtime_api or os.getenv("USE_REALTIME_API", "false").lower() == "true"

    if args.server:
        from .grpc_server import serve
        try:
            asyncio.run(serve(use_realtime_api=use_realtime_api))
        except KeyboardInterrupt:
            logger.info("gRPC server terminated by user")
        except Exception as e:
            logger.exception(f"An unexpected error occurred in gRPC server: {e}")
    else:
        prompts = args.prompts.split("|") if args.prompts else None
        realtime_api_instance = RealtimeAPI(prompts)
        try:
            asyncio.run(realtime_api_instance.run())
        except KeyboardInterrupt:
            logger.info("Program terminated by user")
        except Exception as e:
            logger.exception(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Press Ctrl+C to exit the program.")
    main()
