from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit_logs.services import create_audit_log

from .serializers import (
    ChatMessageSerializer,
    ChatSendResponseSerializer,
    ChatSessionCreateSerializer,
    ChatSessionDetailSerializer,
    ChatSessionListSerializer,
    SendMessageSerializer,
)
from .services import (
    DailyMessageLimitReached,
    archive_chat_session,
    create_chat_session,
    delete_chat_session,
    get_session_messages,
    get_user_session,
    get_user_sessions,
    send_message_to_agent,
)


class ChatSessionListCreateView(APIView):
    def get(self, request):
        serializer = ChatSessionListSerializer(get_user_sessions(request.user), many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ChatSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = create_chat_session(
            user=request.user,
            agent_key=serializer.validated_data.get('agent_key'),
            title=serializer.validated_data.get('title'),
        )
        create_audit_log(
            user=request.user,
            event_type='chat_session_created',
            request=request,
            object_type='ChatSession',
            object_id=session.id,
            metadata={'agent_key': session.agent.key},
        )
        return Response(
            ChatSessionDetailSerializer(session).data,
            status=status.HTTP_201_CREATED,
        )


class ChatSessionDetailView(APIView):
    def get(self, request, session_id):
        session = get_user_session(request.user, session_id)
        return Response(ChatSessionDetailSerializer(session).data)

    def patch(self, request, session_id):
        action = request.data.get('action')
        if action == 'archive':
            session = archive_chat_session(request.user, session_id)
        elif action == 'delete':
            session = delete_chat_session(request.user, session_id)
            create_audit_log(
                user=request.user,
                event_type='chat_session_deleted',
                request=request,
                object_type='ChatSession',
                object_id=session_id,
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'detail': 'Provide action: archive or delete.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        create_audit_log(
            user=request.user,
            event_type='chat_session_archived',
            request=request,
            object_type='ChatSession',
            object_id=session_id,
        )
        return Response(ChatSessionDetailSerializer(session).data)


class ChatSessionMessagesView(APIView):
    def get(self, request, session_id):
        messages = get_session_messages(request.user, session_id)
        return Response(ChatMessageSerializer(messages, many=True).data)

    def post(self, request, session_id):
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = send_message_to_agent(
                user=request.user,
                session_id=session_id,
                content=serializer.validated_data['content'],
            )
        except DailyMessageLimitReached as exc:
            create_audit_log(
                user=request.user,
                event_type='usage_limit_reached',
                request=request,
                object_type='ChatSession',
                object_id=session_id,
                metadata={'remaining_messages': exc.usage.get('remaining_messages')},
            )
            return Response(
                {
                    'detail': str(exc.detail),
                    'usage': exc.usage,
                },
                status=exc.status_code,
            )

        create_audit_log(
            user=request.user,
            event_type='chat_message_sent',
            request=request,
            object_type='ChatSession',
            object_id=session_id,
            metadata={'agent_message_id': result['agent_message'].id},
        )
        return Response(ChatSendResponseSerializer(result).data, status=status.HTTP_201_CREATED)
