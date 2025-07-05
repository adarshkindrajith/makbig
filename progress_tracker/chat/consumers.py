import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.contrib.auth.models import User
from chat.models import Message
from app1.models import dbstudent1, AdminProfile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'main_chat'
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        messages_data = [await self._serialize_message(msg) for msg in await self.get_chat_history()]
        await self.send(text_data=json.dumps({
            'type': 'chat_history',
            'messages': messages_data
        }))

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        except Exception as e:
            print(f"Disconnect error: {e}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if not self.scope["user"].is_authenticated:
            await self.send(text_data=json.dumps({'error': 'User not authenticated'}))
            return

        user = self.scope["user"]

        if message_type == 'message':
            message_content = data['message']
            replied_to_id = data.get('replied_to')
            new_message_data = await self.save_message(user, message_content, replied_to_id)

            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'chat_message', 'message_data': new_message_data}
            )

        elif message_type == 'report':
            message_id = data['id']
            updated_message_data = await self.toggle_report_status(message_id)
            if updated_message_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'chat_message', 'message_data': updated_message_data}
                )

        elif message_type == 'pin':
            if not user.is_superuser:
                await self.send(text_data=json.dumps({'error': 'You are not authorized to pin messages.'}))
                return

            message_id = data['id']
            pin_value = data['value']
            updated_message_data = await self.toggle_pin_status(message_id, pin_value)
            if updated_message_data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'chat_message', 'message_data': updated_message_data}
                )

        elif message_type == 'delete':
            if not user.is_superuser:
                await self.send(text_data=json.dumps({'error': 'You are not authorized to delete messages.'}))
                return

            message_id = data['id']
            deleted_id = await self.delete_message_from_db(message_id)
            if deleted_id:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'delete_message', 'id': deleted_id}
                )

        elif message_type == 'edit':
            msg_id = data['id']
            new_content = data['message']
            message = await self.get_message_by_id(msg_id)

            if message:
                sender_user = message.student.user if message.student else message.superuser

                if sender_user.id != self.scope["user"].id:
                    await self.send(text_data=json.dumps({'error': 'You are not authorized to edit this message.'}))
                    return

                message.content = new_content
                await sync_to_async(message.save)()

                updated_message_data = await self._serialize_message(message)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'chat_message', 'message_data': updated_message_data}
                )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({'type': 'new_message', 'message_data': event['message_data']}))

    async def delete_message(self, event):
        await self.send(text_data=json.dumps({'type': 'delete', 'id': event['id']}))

    @sync_to_async
    def get_chat_history(self):
        return list(Message.objects.select_related(
            'student__user', 'superuser', 'replied_to__student__user', 'replied_to__superuser'
        ).order_by('timestamp'))

    @sync_to_async
    def save_message(self, user, content, replied_to_id):
        replied_to_message = Message.objects.filter(id=replied_to_id).first() if replied_to_id else None

        try:
            student_profile = dbstudent1.objects.get(user=user)
            message = Message.objects.create(student=student_profile, content=content, replied_to=replied_to_message)
        except dbstudent1.DoesNotExist:
            message = Message.objects.create(superuser=user, content=content, replied_to=replied_to_message)

        return self._serialize_message_sync(message)

    @sync_to_async
    def toggle_report_status(self, message_id):
        message = Message.objects.filter(id=message_id).select_related('student__user', 'superuser').first()
        if message:
            message.reported = not message.reported
            message.save()
            return self._serialize_message_sync(message)
        return None

    @sync_to_async
    def toggle_pin_status(self, message_id, pin_value):
        message = Message.objects.filter(id=message_id).select_related('student__user', 'superuser').first()
        if message:
            message.pinned = pin_value
            message.save()
            return self._serialize_message_sync(message)
        return None

    @sync_to_async
    def delete_message_from_db(self, message_id):
        message = Message.objects.filter(id=message_id).first()
        if message:
            message.delete()
            return message_id
        return None

    @sync_to_async
    def get_message_by_id(self, msg_id):
        return Message.objects.filter(id=msg_id).select_related('student__user', 'superuser').first()

    async def _serialize_message(self, message):
        return await sync_to_async(self._serialize_message_sync)(message)

    def _serialize_message_sync(self, message):
        sender = message.student or message.superuser

        if isinstance(sender, dbstudent1):
            sender_data = {
                'id': sender.user.id if sender.user else None,
                'first_name': sender.s_firstname,
                'last_name': sender.s_lastname,
                'profile_pic': sender.s_profilepicture.url if sender.s_profilepicture else '',
                'is_superuser': False,
                'badge': sender.badge.url if sender.badge else '',
            }

        elif isinstance(sender, User):
            admin_profile = AdminProfile.objects.filter(user=sender).first()
            profile_pic = admin_profile.s_profilepicture.url if admin_profile and admin_profile.s_profilepicture else ''
            sender_data = {
                'id': sender.id,
                'first_name': sender.first_name,
                'last_name': sender.last_name,
                'profile_pic': profile_pic,
                'is_superuser': sender.is_superuser,
                'badge': '',
            }
        else:
            sender_data = {
                'id': None,
                'first_name': "Unknown",
                'last_name': "",
                'profile_pic': '',
                'is_superuser': False,
                'badge': '',
            }

        replied_to_data = None
        if message.replied_to:
            replied_sender = message.replied_to.student or message.replied_to.superuser

            if isinstance(replied_sender, dbstudent1):
                replied_sender_data = {
                    'id': replied_sender.user.id if replied_sender.user else None,
                    'first_name': replied_sender.s_firstname,
                    'last_name': replied_sender.s_lastname,
                    'profile_pic': replied_sender.s_profilepicture.url if replied_sender.s_profilepicture else '',
                    'is_superuser': False,
                    'badge': replied_sender.badge.url if replied_sender.badge else '',
                }
            elif isinstance(replied_sender, User):
                replied_sender_data = {
                    'id': replied_sender.id,
                    'first_name': replied_sender.first_name,
                    'last_name': replied_sender.last_name,
                    'profile_pic': '',
                    'is_superuser': replied_sender.is_superuser,
                    'badge': '',
                }
            else:
                replied_sender_data = {
                    'id': None,
                    'first_name': "Unknown",
                    'last_name': "",
                    'profile_pic': '',
                    'is_superuser': False,
                    'badge': '',
                }

            replied_to_data = {
                'id': message.replied_to.id,
                'content': message.replied_to.content,
                'sender': replied_sender_data
            }

        return {
            'id': message.id,
            'content': message.content,
            'timestamp': timezone.localtime(message.timestamp).isoformat(),
            'reported': message.reported,
            'pinned': message.pinned,
            'sender': sender_data,
            'replied_to': replied_to_data
        }
