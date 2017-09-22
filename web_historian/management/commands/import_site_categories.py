import requests

from django.core.management.base import BaseCommand

from passive_data_kit.decorators import handle_lock
from web_historian.models import UrlCategory

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('json_url', type=str)

    @handle_lock
    def handle(self, *args, **options):
        request = requests.get(options['json_url'])

        current_index = len(request.json()['children'])

        for child in request.json()['children']:
            category = UrlCategory(priority=current_index)
            category.category = child['category']
            category.match_type = child['search']
            category.match_value = child['value']

            category.save()

            current_index -= 1
