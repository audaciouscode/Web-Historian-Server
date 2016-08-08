from django.contrib import admin

from .models import UrlAction, ProvidedIdentifier, UrlCategory

@admin.register(UrlAction)
class UrlActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'url', 'days', 'publish',)
    list_filter = ('publish',)


@admin.register(ProvidedIdentifier)
class ProvidedIdentifierAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'added',)
    list_filter = ('added',)
    search_fields = ('identifier',)


@admin.register(UrlCategory)
class UrlCategoryAdmin(admin.ModelAdmin):
    list_display = ('match_value', 'match_type', 'category', 'priority')
    list_filter = ('match_type', 'category')
    search_fields = ('match_value', 'category')
