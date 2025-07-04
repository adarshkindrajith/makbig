
# Register your models here.
from django.contrib import admin
from .models import Module, Task
from .models import Badge, StudentBadge,Course


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class ModuleAdmin(admin.ModelAdmin):
    inlines = [TaskInline]
    list_display = ('name', 'week')

admin.site.register(Module, ModuleAdmin)


admin.site.register(Badge)
admin.site.register(StudentBadge)
admin.site.register(Course)
