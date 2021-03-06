from __future__ import unicode_literals

from django.db import models

SEARCH_TYPES = (
    ('domainExact', 'Exact Domain Match'),
    ('topDomainExact', 'Root Domain Match'),
)

class UrlAction(models.Model):
    name = models.CharField(max_length=1024, db_index=True, default='New URL Action')
    identifier = models.CharField(max_length=1024, db_index=True, unique=True)
    url = models.URLField(max_length=1024, db_index=True)
    days = models.IntegerField(default=-1)
    publish = models.DateTimeField(null=True, blank=True)

class ProvidedIdentifier(models.Model):
    identifier = models.CharField(max_length=1024, db_index=True)
    added = models.DateTimeField(auto_now_add=True)

class UrlCategory(models.Model):
    priority = models.IntegerField(default=0)
    category = models.CharField(max_length=1024, default='Other')
    match_type = models.CharField(max_length=1024, choices=SEARCH_TYPES)
    match_value = models.CharField(max_length=1024, default='', blank=True)
