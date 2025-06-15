from django.contrib import admin
from .models import ChatMessage



@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'message_short', 'user', 'session_id', 'timestamp')
    list_filter = ('sender', 'user')
    search_fields = ('message', 'user__username', 'session_id')
    ordering = ('-timestamp',)

    def message_short(self, obj):
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message
    message_short.short_description = 'Message'
    #This line sets the column header (label) shown in the Django admin list view for the message_short method.

    # class Media:
    #     js = ('chat/admin_search_hint.js',)