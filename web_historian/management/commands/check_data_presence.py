# pylint: disable=line-too-long

import csv
# import json

from django.core.management.base import BaseCommand

from passive_data_kit.models import DataPoint # , DataBundle

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ids-file.csv', nargs=1, type=str)

    def handle(self, *args, **options):
        with open(options['ids-file.csv'][0], 'rb') as csvfile:
            reader = csv.reader(csvfile)

            point_counts = {}
            bundle_counts = {}

            user_ids = []

            for row in reader:
                user_id = row[0]

                user_ids.append(user_id)

                point_counts[user_id] = DataPoint.objects.filter(source=user_id).count()
                bundle_counts[user_id] = 0

#            last_pk = DataBundle.objects.all().order_by('-pk').first().pk
#
#            index = 0
#
#            while index < last_pk:
#                try:
#                    bundle = DataBundle.objects.get(pk=index)
#
#                    props_string = json.dumps(bundle.properties)
#
#                    for user_id in user_ids:
#                        if (user_id in bundle_counts) is False:
#
#                        if user_id in props_string:
#                            bundle_counts[user_id] += 1
#                except DataBundle.DoesNotExist:
#                    pass
#
#                if index % 1000 == 0:
#                    print('. ' + str(index) + ' / ' + str())
#
#                index += 1
#
#            for user_id in user_ids:
#                print user_id + '\t' + str(point_counts[user_id]) + ' points\t' + str(bundle_counts[user_id]) + ' bundles'

            for user_id in user_ids:
                if point_counts[user_id] > 0:
                    print user_id + '\t' + str(point_counts[user_id]) + ' points'

                    for point in DataPoint.objects.filter(source=user_id).order_by('created'):
                        sec_id = point.fetch_secondary_identifier()

                        if sec_id == 'clicked_step':
                            sec_id = sec_id + ':' + str(point.properties['event_details']['step'])

                        print point.created.isoformat() + ': ' + point.generator_identifier + '[' + sec_id + '] - ' + point.generator

                    print '\n'
