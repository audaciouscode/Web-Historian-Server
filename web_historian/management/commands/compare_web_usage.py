# pylint: disable=line-too-long

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from passive_data_kit.decorators import handle_lock
from passive_data_kit.models import DataPoint

class Command(BaseCommand):
    def add_arguments(self, parser):
        pass
#        parser.add_argument('--delete',
#            action='store_true',
#            dest='delete',
#            default=False,
#            help='Delete data bundles after processing')
#
#        parser.add_argument('--count',
#            type=int,
#            dest='bundle_count',
#            default=100,
#            help='Number of bundles to process in a single run')

    @handle_lock
    def handle(self, *args, **options):
        now = timezone.now()
        start = now - datetime.timedelta(days=7)

        metadata = {}

        sources = DataPoint.objects.order_by('source').values_list('source', flat=True).distinct()

        for source in sources:
            points = DataPoint.objects.filter(source=source, created__gte=start)

            search_count = 0

            domains = set()

            for point in points:
                if 'searchTerms' in point.properties:
                    if point.properties['searchTerms'] != '':
                        search_count += 1

                if 'domain' in point.properties:
                    domains.add(point.properties['domain'])

            source_metadata = {}
            source_metadata['visits'] = points.count()
            source_metadata['searches'] = search_count
            source_metadata['domains'] = len(domains)

            metadata[source] = source_metadata

        metadata_point = DataPoint(source='web-historian-server', generator='Web Historian: Behavior Metadata', generator_identifier='web-historian-behavior-metadata')
        metadata_point.created = now
        metadata_point.recorded = now

        metadata['passive-data-metadata'] = {}
        metadata['passive-data-metadata']['source'] = 'web-historian-server'
        metadata['passive-data-metadata']['generator-id'] = 'web-historian-behavior-metadata'
        metadata['passive-data-metadata']['generator'] = 'Web Historian: Behavior Metadata'
        metadata['passive-data-metadata']['timestamp'] = int(now.strftime("%s"))

        metadata_point.properties = metadata

        metadata_point.save()
