from django.contrib import admin

from .models import AISuggestion


@admin.register(AISuggestion)
class AISuggestionAdmin(admin.ModelAdmin):
    list_display = ('kind', 'user', 'task', 'created_at')
    list_filter = ('kind', 'created_at')
    search_fields = ('prompt', 'response', 'user__username', 'task__title')
    autocomplete_fields = ('user', 'task')
    readonly_fields = ('created_at',)
