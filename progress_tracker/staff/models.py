from django.db import models
from django.contrib.auth.models import User
from learning.models import Task,Course

class StudentTaskProgress(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)  
    is_completed = models.BooleanField(default=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


    def __str__(self):
        return f"{self.student.username} - {self.task.title}"
    
    class Meta:
        unique_together = ('student', 'task')
