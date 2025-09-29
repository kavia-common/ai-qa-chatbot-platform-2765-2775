from typing import Optional

from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Conversation, Message
from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    AskSerializer,
    ConversationSerializer,
)
from .services import WeatherQnAEngine


@api_view(['GET'])
def health(request):
    """
    PUBLIC_INTERFACE
    Returns health status of the backend.

    Returns:
        200 OK with {"message": "Server is up!"}
    """
    return Response({"message": "Server is up!"})


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """
    Register a new user with username/password.

    Body:
        - username: string
        - password: string
        - email: string (optional)

    Returns:
        201 Created with {"message": "Registered", "user": {"id":..., "username":...}}
        400 Bad Request on validation errors.
    """
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data["username"]
    password = serializer.validated_data["password"]
    email = serializer.validated_data.get("email", "")

    if User.objects.filter(username=username).exists():
        return Response({"detail": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    return Response({"message": "Registered", "user": {"id": user.id, "username": user.username}}, status=status.HTTP_201_CREATED)


# PUBLIC_INTERFACE
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """
    Login with username/password. Uses session authentication for simplicity.

    Body:
        - username: string
        - password: string

    Returns:
        200 OK with {"message": "Logged in", "user": {"id":..., "username":...}}
        401 Unauthorized on invalid credentials.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = authenticate(username=serializer.validated_data["username"], password=serializer.validated_data["password"])
    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    django_login(request, user)
    return Response({"message": "Logged in", "user": {"id": user.id, "username": user.username}})


# PUBLIC_INTERFACE
@api_view(['POST'])
def logout(request):
    """
    Logout current authenticated user (session-based).

    Returns:
        200 OK with {"message": "Logged out"}
    """
    django_logout(request)
    return Response({"message": "Logged out"})


# PUBLIC_INTERFACE
@api_view(['POST'])
def ask(request):
    """
    Submit a question to the weather Q&A engine and receive an answer.

    Body:
        - question: string
        - conversation_id: integer (optional) - if omitted, a new conversation is created.

    Returns:
        200 OK with {"conversation_id": <id>, "question": "...", "answer": "..."}
        201 Created when a new conversation is created with the first messages.
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    serializer = AskSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    question = serializer.validated_data["question"]
    conv_id: Optional[int] = serializer.validated_data.get("conversation_id")

    created = False
    conversation: Conversation
    if conv_id:
        try:
            conversation = Conversation.objects.get(id=conv_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"detail": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    else:
        title = question[:50]
        conversation = Conversation.objects.create(user=request.user, title=title)
        created = True

    # Store user message
    Message.objects.create(conversation=conversation, role="user", content=question)

    # Get answer from engine
    engine = WeatherQnAEngine()
    answer_text = engine.answer(question)

    # Store assistant message
    Message.objects.create(conversation=conversation, role="assistant", content=answer_text)

    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return Response(
        {"conversation_id": conversation.id, "question": question, "answer": answer_text},
        status=status_code,
    )


# PUBLIC_INTERFACE
@api_view(['GET'])
def conversations(request):
    """
    List conversations for the authenticated user with last few messages.

    Query Params:
        - include_messages: bool (default true)

    Returns:
        200 OK with list of conversations and optional messages.
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)

    qs = Conversation.objects.filter(user=request.user).order_by("-updated_at")
    data = ConversationSerializer(qs, many=True).data
    return Response(data)


# PUBLIC_INTERFACE
@api_view(['GET'])
def conversation_detail(request, conversation_id: int):
    """
    Retrieve a single conversation and all messages.

    Path Params:
        - conversation_id: integer

    Returns:
        200 OK with conversation object and messages.
        404 Not Found if missing or not owned by user.
    """
    if not request.user.is_authenticated:
        return Response({"detail": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        conv = Conversation.objects.get(id=conversation_id, user=request.user)
    except Conversation.DoesNotExist:
        return Response({"detail": "Conversation not found"}, status=status.HTTP_404_NOT_FOUND)
    data = ConversationSerializer(conv).data
    return Response(data)
