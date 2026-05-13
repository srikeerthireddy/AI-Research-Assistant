"""
Streaming Responses Module
Enables real-time streaming of LLM responses with FastAPI
"""
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Optional
import json
import asyncio
from openai import AsyncOpenAI

# Initialize async OpenAI client
client = AsyncOpenAI()

async def stream_response_generator(
    prompt: str,
    context: str,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 2000,
    temperature: float = 0.7
) -> AsyncGenerator[str, None]:
    """
    Stream response from OpenAI API
    Yields JSON-formatted chunks for frontend consumption
    """
    try:
        async with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI research assistant. Provide detailed, accurate answers based on the context provided."
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {prompt}"
                }
            ]
        ) as stream:
            async for text in stream.text_stream:
                # Stream chunk as JSON for frontend parsing
                chunk = json.dumps({"type": "chunk", "data": text})
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming
        
        # Send completion signal
        completion = json.dumps({"type": "complete", "data": "done"})
        yield f"data: {completion}\n\n"
    except Exception as e:
        error_msg = json.dumps({"type": "error", "data": str(e)})
        yield f"data: {error_msg}\n\n"

async def stream_summary_generator(
    text: str,
    length: str = "moderate",
    model: str = "gpt-3.5-turbo"
) -> AsyncGenerator[str, None]:
    """Stream summary generation"""
    length_prompts = {
        "concise": "Provide a very brief summary (2-3 sentences)",
        "moderate": "Provide a moderate summary (5-7 sentences)",
        "detailed": "Provide a detailed summary (10-15 sentences)"
    }
    
    try:
        async with client.messages.stream(
            model=model,
            max_tokens=1500,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a skilled summarizer. {length_prompts.get(length, 'Provide a summary')}"
                },
                {
                    "role": "user",
                    "content": f"Summarize this text:\n\n{text}"
                }
            ]
        ) as stream:
            async for text_chunk in stream.text_stream:
                chunk = json.dumps({"type": "chunk", "data": text_chunk})
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.01)
        
        completion = json.dumps({"type": "complete", "data": "done"})
        yield f"data: {completion}\n\n"
    except Exception as e:
        error_msg = json.dumps({"type": "error", "data": str(e)})
        yield f"data: {error_msg}\n\n"

def create_streaming_response(generator: AsyncGenerator) -> StreamingResponse:
    """
    Create a FastAPI StreamingResponse
    """
    return StreamingResponse(generator, media_type="text/event-stream")
