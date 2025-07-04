from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    videolink = models.URLField(blank=True, null=True)  

    def __str__(self):
        return self.name


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    name = models.CharField(max_length=100)
    week = models.PositiveIntegerField()
    material_pdf = models.FileField(upload_to='module_pdfs/', null=True, blank=True)  # <-- NEW FIELD



    class Meta:
        ordering = ['week']
        unique_together = ('course', 'week')

    def __str__(self):
        return f"Week {self.week}: {self.name}"


class Task(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']
        unique_together = ('module', 'order')

    def __str__(self):
        return self.title

# -------------------------
# STUDENT PROGRESS & TRACKING
# -------------------------
class StudentTask(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'task')

    def __str__(self):
        status = 'Completed' if self.is_completed else 'Incomplete'
        return f"{self.student.username} - {self.task.title} - {status}"


class StudentCurrentModule(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)  
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.module.name if self.module else 'No module'} - Course: {self.course.name if self.course else 'No course'}"

    def approve_next_week(self):
        if not self.module:
            return False
        next_module = Module.objects.filter(
            course=self.module.course,
            week=self.module.week + 1
        ).first()
        if next_module:
            self.module = next_module
            self.save()
            return True
        return False

# -------------------------
# BADGE SYSTEM
# -------------------------
# models.py
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='badge_images/', null=True, blank=True)
    week = models.PositiveIntegerField(null=True, blank=True)  # e.g., Week 1, 2, 3...

    def __str__(self):
        return f"{self.name} (Week {self.week})"



class StudentBadge(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'badge')

    def __str__(self):
        return f"{self.student.username} - {self.badge.name}"

# -------------------------
# ENROLLMENT TRACKING
# -------------------------
class CourseEnrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.name}"
