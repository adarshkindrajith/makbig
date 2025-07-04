from django.db import models
from app1.models import dbstudent1
from django.contrib.auth.models import User



class Message(models.Model):
    student = models.ForeignKey(dbstudent1, on_delete=models.CASCADE, null=True, blank=True)
    superuser = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    reported = models.BooleanField(default=False)
    pinned = models.BooleanField(default=False)
    
    replied_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"{self.get_display_name()}: {self.content[:50]}"

    def get_display_name(self):
        """Return proper name based on sender type"""
        if self.student:
            return f"{self.student.s_firstname} {self.student.s_lastname}"
        elif self.superuser:
            return f"{self.superuser.first_name} {self.superuser.last_name}"
        return "Unknown User"

    def get_profile_picture(self):
        """Return profile picture URL or default"""
        if self.student and self.student.s_profilepicture:
            return self.student.s_profilepicture.url
        # You can extend this if superuser has profile pictures elsewhere
        return None
