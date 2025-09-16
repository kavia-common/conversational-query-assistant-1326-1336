import os
from typing import Any, Dict, Optional

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

try:
    # Prefer the official OpenAI Python SDK v1 if available
    from openai import OpenAI  # type: ignore
    _HAS_OPENAI = True
except Exception:  # pragma: no cover - fallback if SDK not present at runtime
    _HAS_OPENAI = False
    OpenAI = None  # type: ignore


# PUBLIC_INTERFACE
@api_view(['GET'])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def health(request):
    """
    Health check endpoint.

    Returns:
        200 OK with a simple JSON message indicating the server is up.
    """
    return Response({"message": "Server is up!"})


question_param = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=["question"],
    properties={
        "question": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="The user's question to send to the chatbot.",
            example="What is the capital of France?"
        ),
        "model": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Optional OpenAI model to use. Defaults to 'gpt-4o-mini' if not provided.",
            example="gpt-4o-mini"
        ),
        "system_prompt": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="Optional system prompt to steer assistant behavior.",
            example="You are a concise assistant."
        ),
    },
)


def _get_openai_client() -> Optional[Any]:
    """
    Create an OpenAI client if OPENAI_API_KEY exists and SDK available.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not _HAS_OPENAI:
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def _build_messages(question: str, system_prompt: Optional[str]) -> list:
    """
    Build messages array for chat.completions API.
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    return messages


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method="post",
    operation_id="chat_create",
    tags=["chat"],
    summary="Ask chatbot a question",
    description="Accepts a user question, forwards it to OpenAI, and returns the generated answer. No data is persisted.",
    request_body=question_param,
    responses={
        200: openapi.Response(
            description="Answer retrieved successfully.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "answer": openapi.Schema(type=openapi.TYPE_STRING, description="Assistant's answer")
                },
            ),
        ),
        400: "Bad Request",
        500: "Server error contacting OpenAI",
    },
)
@api_view(['POST'])
@permission_classes([AllowAny])
@renderer_classes([JSONRenderer])
def chat(request):
    """
    Chat endpoint: POST /api/chat/

    Body:
        - question (str, required): The user's question.
        - model (str, optional): OpenAI model to use. Default 'gpt-4o-mini'.
        - system_prompt (str, optional): Optional system prompt.

    Returns:
        200 OK:
            {"answer": "<assistant response>"}
        400 Bad Request:
            {"error": "<reason>"}
        500 Internal Server Error:
            {"error": "Failed to retrieve response from OpenAI."}
    """
    data: Dict[str, Any] = request.data if isinstance(request.data, dict) else {}
    question = data.get("question")
    model = (data.get("model") or "gpt-4o-mini").strip()
    system_prompt = data.get("system_prompt")

    if not isinstance(question, str) or not question.strip():
        return Response({"error": "Field 'question' is required and must be a non-empty string."},
                        status=status.HTTP_400_BAD_REQUEST)

    client = _get_openai_client()
    if client is None:
        # Give actionable error messages for missing SDK or API key
        if not _HAS_OPENAI:
            return Response({"error": "OpenAI SDK not installed on server."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not os.getenv("OPENAI_API_KEY"):
            return Response({"error": "OPENAI_API_KEY environment variable is not set."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"error": "Failed to initialize OpenAI client."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # Using Chat Completions API from OpenAI Python SDK v1
        messages = _build_messages(question.strip(), system_prompt if isinstance(system_prompt, str) else None)
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        content = completion.choices[0].message.content if completion and completion.choices else ""
        if not content:
            return Response({"error": "Empty response from OpenAI."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"answer": content})
    except Exception as e:
        return Response({"error": f"Failed to retrieve response from OpenAI: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
