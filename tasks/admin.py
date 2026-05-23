from django.contrib import admin

from .models import Attachment, Comment, Label, Task


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    autocomplete_fields = ('author',)
    readonly_fields = ('created_at',)


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    autocomplete_fields = ('uploaded_by',)
    readonly_fields = ('uploaded_at',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'assignee', 'deadline', 'updated_at')
    list_filter = ('status', 'priority', 'project', 'deadline')
    search_fields = ('title', 'description', 'project__name', 'assignee__username')
    autocomplete_fields = ('project', 'assignee', 'created_by', 'labels')
    inlines = [CommentInline, AttachmentInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'task__title', 'author__username')
    autocomplete_fields = ('task', 'author')


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'file', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('task__title', 'uploaded_by__username')
    autocomplete_fields = ('task', 'uploaded_by')


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)
