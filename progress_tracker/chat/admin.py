from django.contrib import admin
from django.contrib.auth.models import User
from .models import Message
from app1.models import dbstudent1

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('get_sender_name', 'content', 'timestamp', 'reported', 'pinned', 'replied_to_display')
    list_filter = ('reported', 'pinned', 'timestamp')
    search_fields = ('content',)
    date_hierarchy = 'timestamp'
    raw_id_fields = ('replied_to',)
    actions = ['mark_as_reported', 'mark_as_not_reported', 'mark_as_pinned', 'mark_as_not_pinned']
    
    fieldsets = (
        (None, {
            'fields': ('student', 'superuser', 'content', 'replied_to', 'reported', 'pinned')
        }),
    )

    readonly_fields = ('timestamp',)

    def get_sender_name(self, obj):
        """Display proper sender name"""
        if obj.student:
            return f"{obj.student.s_firstname} {obj.student.s_lastname} (Student)"
        elif obj.superuser:
            return f"{obj.superuser.first_name} {obj.superuser.last_name} (Admin)"
        return "Unknown"
    get_sender_name.short_description = 'Sender'

    def replied_to_display(self, obj):
        if obj.replied_to:
            reply_sender = obj.replied_to.student.s_email if obj.replied_to.student else obj.replied_to.superuser.email
            return f'"{obj.replied_to.content[:30]}..." by {reply_sender}'
        return "-"
    replied_to_display.short_description = 'In Reply To'

    def mark_as_reported(self, request, queryset):
        updated = queryset.update(reported=True)
        self.message_user(request, f'{updated} messages marked as reported.', level='success')
    mark_as_reported.short_description = "Mark selected messages as reported"

    def mark_as_not_reported(self, request, queryset):
        updated = queryset.update(reported=False)
        self.message_user(request, f'{updated} messages marked as not reported.', level='success')
    mark_as_not_reported.short_description = "Mark selected messages as not reported"

    def mark_as_pinned(self, request, queryset):
        updated = queryset.update(pinned=True)
        self.message_user(request, f'{updated} messages marked as pinned.', level='success')
    mark_as_pinned.short_description = "Mark selected messages as pinned"

    def mark_as_not_pinned(self, request, queryset):
        updated = queryset.update(pinned=False)
        self.message_user(request, f'{updated} messages marked as not pinned.', level='success')
    mark_as_not_pinned.short_description = "Mark selected messages as not pinned"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('-timestamp')
