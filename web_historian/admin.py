from django.contrib import admin

from .models import UrlAction, ProvidedIdentifier

@admin.register(UrlAction)
class UrlActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier', 'url', 'days', 'publish',)
    list_filter = ('publish',)


@admin.register(ProvidedIdentifier)
class ProvidedIdentifierAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'added',)
    list_filter = ('added',)
    search_fields = ('identifier',)
