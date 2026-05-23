from django.contrib import admin

from .models import Project, ProjectMembership


class ProjectMembershipInline(admin.TabularInline):
    model = ProjectMembership
    extra = 1
    autocomplete_fields = ('user',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description', 'owner__username')
    autocomplete_fields = ('owner',)
    inlines = [ProjectMembershipInline]
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('project__name', 'user__username')
    autocomplete_fields = ('project', 'user')
