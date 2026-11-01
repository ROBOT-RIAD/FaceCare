
import json
import logging

from django.http import StreamingHttpResponse
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Chat, Message

from .serializers import (
    ChatListSerializer,
    ChatDetailSerializer,
    MessageSerializer,
    SendMessageSerializer,
)

from .services.ai_service import stream_ai_response
from account.permissions import IsUserRole
from .renderers import EventStreamRenderer


logger = logging.getLogger(__name__)


# ----------------------------------
# Common Swagger Response Schemas
# ----------------------------------

success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "success": openapi.Schema(
            type=openapi.TYPE_BOOLEAN
        ),
        "message": openapi.Schema(
            type=openapi.TYPE_STRING
        ),
    }
)


# ----------------------------------
# SSE Event Helper
# ----------------------------------

def send_sse(event, data):

    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


# ----------------------------------
# 1. Chat Create & List
# ----------------------------------

class ChatListCreateAPIView(APIView):

    permission_classes = [IsAuthenticated, IsUserRole]

    @swagger_auto_schema(
        operation_summary="Get All Chats",
        operation_description=(
            "Retrieve all chat conversations "
            "belonging to the authenticated user."
        ),
        responses={
            200: openapi.Response(
                description="Chats retrieved successfully",
                schema=ChatListSerializer(many=True)
            ),
            401: "Authentication credentials were not provided.",
            403: "Permission denied."
        },
        tags=["AI Chat"]
    )
    def get(self, request):

        chats = (
            Chat.objects
            .filter(user=request.user)
            .prefetch_related("messages")
        )

        serializer = ChatListSerializer(
            chats,
            many=True
        )

        return Response({
            "success": True,
            "data": serializer.data
        })

    @swagger_auto_schema(
        operation_summary="Create New Chat",
        operation_description=(
            "Create a new skincare AI chat conversation "
            "for the authenticated user."
        ),
        request_body=None,
        responses={
            201: openapi.Response(
                description="Chat created successfully",
                schema=ChatDetailSerializer()
            ),
            401: "Authentication required.",
            403: "Permission denied."
        },
        tags=["AI Chat"]
    )
    def post(self, request):

        chat = Chat.objects.create(
            user=request.user,
            title="New Chat"
        )

        serializer = ChatDetailSerializer(chat)

        return Response({
            "success": True,
            "message": "Chat created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


# ----------------------------------
# 2. Chat Details & Delete
# ----------------------------------

class ChatDetailAPIView(APIView):

    permission_classes = [IsAuthenticated, IsUserRole]

    def get_object(self, request, pk):

        return Chat.objects.filter(
            id=pk,
            user=request.user
        ).first()

    @swagger_auto_schema(
        operation_summary="Retrieve Chat Details",
        operation_description=(
            "Retrieve a specific chat conversation "
            "with its associated messages."
        ),
        responses={
            200: openapi.Response(
                description="Chat details retrieved successfully",
                schema=ChatDetailSerializer()
            ),
            404: "Chat not found.",
            401: "Authentication required.",
            403: "Permission denied."
        },
        tags=["AI Chat"]
    )
    def get(self, request, pk):

        chat = self.get_object(request, pk)

        if not chat:
            return Response({
                "success": False,
                "message": "Chat not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ChatDetailSerializer(chat)

        return Response({
            "success": True,
            "data": serializer.data
        })

    @swagger_auto_schema(
        operation_summary="Delete Chat",
        operation_description=(
            "Delete a specific chat conversation "
            "and all associated messages."
        ),
        responses={
            200: openapi.Response(
                description="Chat deleted successfully",
                schema=success_response_schema
            ),
            404: "Chat not found.",
            401: "Authentication required.",
            403: "Permission denied."
        },
        tags=["AI Chat"]
    )
    def delete(self, request, pk):

        chat = self.get_object(request, pk)

        if not chat:
            return Response({
                "success": False,
                "message": "Chat not found"
            }, status=status.HTTP_404_NOT_FOUND)

        chat.delete()

        return Response({
            "success": True,
            "message": "Chat deleted successfully"
        })


# ----------------------------------
# 3. Chat Message Streaming
# ----------------------------------

class ChatMessageStreamAPIView(APIView):

    permission_classes = [IsAuthenticated, IsUserRole]
    renderer_classes = [EventStreamRenderer]

    @swagger_auto_schema(
        operation_summary="Send Message to AI Skincare Assistant",
        operation_description=(
            "Send a skincare-related message to the AI assistant. "
            "The AI uses the user's skin profile, latest skincare "
            "routine, available database products, and previous "
            "conversation history to generate a personalized response. "
            "The response is streamed using Server-Sent Events (SSE). "
            "\n\n"
            "SSE events:\n"
            "- token: Contains each generated response chunk.\n"
            "- done: Indicates that the response is completed.\n"
            "- error: Indicates a streaming error."
        ),
        request_body=SendMessageSerializer,
        consumes=["application/json"],
        produces=["text/event-stream"],
        responses={
            200: openapi.Response(
                description=(
                    "AI response streamed successfully "
                    "using text/event-stream."
                ),
                schema=openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description=(
                        "SSE events containing token, done, or error."
                    )
                )
            ),
            400: "Invalid message.",
            404: "Chat not found.",
            401: "Authentication required.",
            403: "Permission denied."
        },
        tags=["AI Chat"]
    )
    def post(self, request, pk):

        chat = Chat.objects.filter(
            id=pk,
            user=request.user
        ).first()

        if not chat:
            return Response({
                "success": False,
                "message": "Chat not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = SendMessageSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        user_message = serializer.validated_data["message"]

        # Save user message
        message = Message.objects.create(
            chat=chat,
            role="user",
            content=user_message
        )

        # Generate title
        if chat.title == "New Chat":

            chat.title = user_message[:60]

        chat.updated_at = timezone.now()

        chat.save(update_fields=[
            "title",
            "updated_at"
        ])

        def stream_response():

            full_response = []
            assistant_saved = False

            try:

                for content in stream_ai_response(
                    user=request.user,
                    chat=chat,
                    current_message_id=message.id,
                ):

                    full_response.append(content)

                    yield send_sse(
                        "token",
                        {
                            "content": content
                        }
                    )

                ai_response = "".join(full_response)

                if ai_response:

                    assistant_message = Message.objects.create(
                        chat=chat,
                        role="assistant",
                        content=ai_response
                    )

                    assistant_saved = True

                    chat.updated_at = timezone.now()

                    chat.save(update_fields=[
                        "updated_at"
                    ])

                    yield send_sse(
                        "done",
                        {
                            "message_id": assistant_message.id,
                            "content": ai_response
                        }
                    )

                else:

                    yield send_sse(
                        "error",
                        {
                            "message": "AI returned an empty response."
                        }
                    )

            except Exception:

                logger.exception(
                    "AI chat streaming failed"
                )

                yield send_sse(
                    "error",
                    {
                        "message": (
                            "Something went wrong. Please try again."
                        )
                    }
                )

            finally:

                if full_response and not assistant_saved:

                    try:

                        Message.objects.create(
                            chat=chat,
                            role="assistant",
                            content="".join(full_response)
                        )

                        chat.updated_at = timezone.now()

                        chat.save(update_fields=[
                            "updated_at"
                        ])

                    except Exception:

                        logger.exception(
                            "Failed to save partial AI response"
                        )

        response = StreamingHttpResponse(
            stream_response(),
            content_type="text/event-stream"
        )

        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        response["Connection"] = "keep-alive"

        return response


# ----------------------------------
# 4. Chat Message History
# ----------------------------------

class ChatHistoryAPIView(APIView):

    permission_classes = [IsAuthenticated, IsUserRole]

    @swagger_auto_schema(
        operation_summary="Get Chat Message History",
        operation_description=(
            "Retrieve all messages from a specific chat conversation "
            "belonging to the authenticated user."
        ),
        responses={
            200: openapi.Response(
                description="Chat history retrieved successfully",
                schema=MessageSerializer(many=True)
            ),
            404: "Chat not found.",
            401: "Authentication required.",
            403: "Permission denied."
        },
        tags=["AI Chat"]
    )
    def get(self, request, pk):

        chat = Chat.objects.filter(
            id=pk,
            user=request.user
        ).first()

        if not chat:

            return Response({
                "success": False,
                "message": "Chat not found"
            }, status=status.HTTP_404_NOT_FOUND)

        messages = chat.messages.all()

        serializer = MessageSerializer(
            messages,
            many=True
        )

        return Response({
            "success": True,
            "data": serializer.data
        })
