import openai
import logging
from src.modules.logging import logger

class OpenAIClient:
    def __init__(self, use_realtime_api=True):
        self.use_realtime_api = use_realtime_api
        self.api_key = openai.api_key

    async def send_prompt(self, prompt):
        if self.use_realtime_api:
            # Implement method to send prompt via Realtime API
            pass
        else:
            return await self.send_prompt_normal_api(prompt)

    async def send_prompt_normal_api(self, prompt):
        try:
            completion = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            response_text = ""
            async for chunk in completion:
                chunk_message = chunk['choices'][0]['delta']
                if 'content' in chunk_message:
                    delta = chunk_message['content']
                    response_text += delta
                    print(delta, end='', flush=True)
            print()
            return response_text
        except Exception as e:
            logger.error(f"Error with OpenAI API: {str(e)}")
            return ""
