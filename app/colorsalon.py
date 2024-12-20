from openai import AsyncOpenAI
import os
from typing import List
from datetime import datetime, timedelta
from .custom_types import (
    ResponseRequiredRequest,
    ResponseResponse,
    Utterance,
)

begin_sentence = "Hello, welcome to The Color Bar Salon. How can I assist you today?"
agent_prompt = """
Task: As a phone agent for The Color Bar Salon, your responsibilities include answering questions about the business, such as services offered, location/address, and hours of operation. You will also guide users through booking an appointment by collecting and confirming their personal details.

Conversational Style: Communicate concisely and conversationally. Aim for responses in short, clear prose, ideally under 10 words. This succinct approach helps in maintaining clarity and focus during interactions.

Personality: Your approach should be friendly and professional, balancing warmth with efficiency. It's important to listen actively and provide accurate information, ensuring that the user's needs are met promptly.
"""

class ColorSalonClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            organization=os.environ["OPENAI_ORGANIZATION_ID"],
            api_key=os.environ["OPENAI_API_KEY"],
        )

    def draft_begin_message(self):
        response = ResponseResponse(
            response_id=0,
            content=begin_sentence,
            content_complete=True,
            end_call=False,
        )
        return response

    def convert_transcript_to_openai_messages(self, transcript: List[Utterance]):
        messages = []
        for utterance in transcript:
            if utterance.role == "agent":
                messages.append({"role": "assistant", "content": utterance.content})
            else:
                messages.append({"role": "user", "content": utterance.content})
        return messages

    def prepare_prompt(self, request: ResponseRequiredRequest):
        # Calculate tomorrow's date
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        prompt = [
            {
                "role": "system",
                "content": f'##Objective\nYou are a phone agent for The Color Bar Salon, engaging in a human-like voice conversation with the user. You will respond based on your given instruction and the provided transcript and be as human-like as possible\n\n## Style Guardrails\n- [Be concise] Keep your response succinct, short, and get to the point quickly. Address one question or action item at a time. Don\'t pack everything you want to say into one utterance.\n- [Do not repeat] Don\'t repeat what\'s in the transcript. Rephrase if you have to reiterate a point. Use varied sentence structures and vocabulary to ensure each response is unique and personalized.\n- [Be conversational] Speak like a human as though you\'re speaking to a close friend -- use everyday language and keep it human-like. Occasionally add filler words, while keeping the prose short. Avoid using big words or sounding too formal.\n- [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate humor or wit; get emotional or empathetic; apply elements of surprise or suspense to keep the user engaged. Don\'t be a pushover.\n- [Be proactive] Lead the conversation and do not be passive. Most times, engage users by ending with a question or suggested next step.\n\n## Response Guideline\n- [Overcome ASR errors] This is a real-time transcript, expect there to be errors. If you can guess what the user is trying to say, then guess and respond. When you must ask for clarification, pretend that you heard the voice and be colloquial (use phrases like "didn\'t catch that", "some noise", "pardon", "you\'re coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever mention "transcription error", and don\'t repeat yourself.\n- [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and to your role. Don\'t repeat yourself in doing this. You should still be creative, human-like, and lively.\n- [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.\n\n## Role\n'
                + agent_prompt,
            },
            {
                "role": "system",
                "content": f'Today\'s date is {datetime.now().strftime("%Y-%m-%d")}. Tomorrow\'s date is {tomorrow_date}.',
            },
            {
                "role": "system",
                "content": 'The Color Bar Salon offers the following services: Haircut, Full Color, Highlights, Balayage, Keratin Treatment, and more. The salon is located at multiple locations in the Philippines. The hours of operation are Monday to Friday from 9 AM to 7 PM, and Saturday to Sunday from 10 AM to 6 PM.',
            },
            {
                "role": "system",
                "content": 'Pricing: Haircut - PHP 500, Full Color - PHP 1500, Highlights - PHP 2000, Balayage - PHP 2500, Keratin Treatment - PHP 3000.',
            },
            {
                "role": "system",
                "content": 'Locations: \n1. Makati - 123 Ayala Ave, Makati, Metro Manila\n2. Quezon City - 456 Timog Ave, Quezon City, Metro Manila\n3. Taguig - 789 BGC, Taguig, Metro Manila',
            },
            {
                "role": "system",
                "content": 'Hours of Operation: \nMonday: 9 AM to 7 PM\nTuesday: 9 AM to 7 PM\nWednesday: 9 AM to 7 PM\nThursday: 9 AM to 7 PM\nFriday: 9 AM to 7 PM\nSaturday: 10 AM to 6 PM\nSunday: 10 AM to 6 PM',
            }
        ]
        transcript_messages = self.convert_transcript_to_openai_messages(
            request.transcript
        )
        for message in transcript_messages:
            prompt.append(message)

        if request.interaction_type == "reminder_required":
            prompt.append(
                {
                    "role": "user",
                    "content": "(Now the user has not responded in a while, you would say:)",
                }
            )
        return prompt

    async def draft_response(self, request: ResponseRequiredRequest):
        prompt = self.prepare_prompt(request)
        stream = await self.client.chat.completions.create(
            model=os.environ["OPENAI_LLM_MODEL"],  # Use the model specified in the environment variable
            messages=prompt,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                response = ResponseResponse(
                    response_id=request.response_id,
                    content=chunk.choices[0].delta.content,
                    content_complete=False,
                    end_call=False,
                )
                yield response

        # Send final response with "content_complete" set to True to signal completion
        response = ResponseResponse(
            response_id=request.response_id,
            content="",
            content_complete=True,
            end_call=False,
        )
        yield response
