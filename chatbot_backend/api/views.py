import os
from typing import Any, Dict, Optional

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# LangChain imports
try:
    # langchain and langchain-openai provide a high-level interface to OpenAI
    from langchain_openai import ChatOpenAI  # type: ignore
    from langchain_core.prompts import ChatPromptTemplate  # type: ignore
    _HAS_LANGCHAIN = True
except Exception:  # pragma: no cover
    _HAS_LANGCHAIN = False
    ChatOpenAI = None  # type: ignore
    ChatPromptTemplate = None  # type: ignore


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


def _build_prompt(system_prompt: Optional[str]) -> Any:
    """
    Build a LangChain ChatPromptTemplate using optional system prompt.
    """
    system_part = system_prompt if isinstance(system_prompt, str) and system_prompt.strip() else "You are a helpful assistant."
    # A simple two-part prompt: system + user input
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_part),
            ("user", "{question}"),
        ]
    )
    return prompt


def _get_llm(model_name: str) -> Optional[Any]:
    """
    Initialize a LangChain ChatOpenAI LLM if API key is set and langchain is available.
    Uses OPENAI_API_KEY from environment. No persistence is involved.
    """
    if not _HAS_LANGCHAIN:
        return None
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        # ChatOpenAI reads OPENAI_API_KEY from env; pass model name through
        return ChatOpenAI(model=model_name, temperature=0.7)
    except Exception:
        return None


# PUBLIC_INTERFACE
@swagger_auto_schema(
    method="post",
    operation_id="chat_create",
    tags=["chat"],
    summary="Ask chatbot a question",
    description="Accepts a user question, forwards it to OpenAI through LangChain, and returns the generated answer. No data is persisted.",
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

    llm = _get_llm(model)
    if llm is None:
        if not _HAS_LANGCHAIN:
            return Response({"error": "LangChain packages not installed on server."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        if not os.getenv("OPENAI_API_KEY"):
            return Response({"error": "OPENAI_API_KEY environment variable is not set."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"error": "Failed to initialize language model."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # Build a simple chain: prompt -> ChatOpenAI
        prompt = _build_prompt(system_prompt)
        chain = prompt | llm  # LCEL composition: PromptTemplate -> LLM
        # Invoke the chain with the question variable; returns an AIMessage
        ai_message = chain.invoke({"question": question.strip()})
        # ai_message could be an AIMessage or str depending on LC version; handle both
        content = getattr(ai_message, "content", None) or (str(ai_message) if ai_message is not None else "")

        if not content:
            return Response({"error": "Empty response from OpenAI via LangChain."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"answer": content})
    except Exception as e:
        return Response({"error": f"Failed to retrieve response from OpenAI via LangChain: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
