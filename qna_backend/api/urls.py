from django.urls import path
from .views import health, register, login, logout, ask, conversations, conversation_detail

urlpatterns = [
    path('health/', health, name='Health'),
    path('auth/register/', register, name='Register'),
    path('auth/login/', login, name='Login'),
    path('auth/logout/', logout, name='Logout'),
    path('chat/ask/', ask, name='Ask'),
    path('chat/conversations/', conversations, name='Conversations'),
    path('chat/conversations/<int:conversation_id>/', conversation_detail, name='ConversationDetail'),
]
