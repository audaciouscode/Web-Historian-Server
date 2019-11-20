# pylint: disable=no-member,line-too-long

import bz2
import calendar
import codecs
import csv
import datetime
import gc
import json
import os
import tempfile

import StringIO

from django.conf import settings
from django.core import management
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify

from passive_data_kit.models import DataPoint, DataBundle, DataSourceReference, DataGeneratorDefinition, install_supports_jsonfield

PAGE_SIZE = 10000

def name_for_generator(identifier):
    if identifier == 'web-historian':
        return 'Web Historian Web Visits'

    return None


def compile_visualization(identifier, points_query, folder):
    if identifier == 'web-historian':
        points_query = points_query.order_by('-created')

        count = points_query.count()

        page = 0
        index = 0

        while index < count:
            visits = []

            for point in points_query[index:(index + PAGE_SIZE)]:
                visit = {}

                visit['url'] = point.properties['url']
                visit['date'] = point.properties['date']
                visit['title'] = point.properties['title']
                visit['visit_id'] = point.properties['id']
                visit['parent_id'] = point.properties['refVisitId']
                visit['search_terms'] = point.properties['searchTerms']
                visit['transition'] = point.properties['transType']

                visits.append(visit)

            output = {}

            if (index + PAGE_SIZE) < count:
                output['next'] = 'visualization-' + str(page + 1) + '.json'

            pages = int(count / PAGE_SIZE)

            if count % PAGE_SIZE != 0:
                pages += 1

            output['pages'] = pages
            output['page'] = page
            output['visits'] = visits

            filename = 'visualization-' + str(page) + '.json'

            if page == 0:
                filename = 'visualization.json'

            path = folder + '/' + filename

            with codecs.open(path, 'w', 'utf-8') as outfile:
                outfile.write(unicode(json.dumps(output, indent=2, ensure_ascii=False)))

            index += PAGE_SIZE
            page += 1

def viz_template(source, identifier):
    if identifier == 'web-historian':
        context = {
            'source': source,
            'identifier': identifier,
        }

        return render_to_string('table_web_historian.html', context)

    return None

def compile_report(generator, sources, data_start=None, data_end=None, date_type='created'): # pylint: disable=too-many-branches, too-many-statements, too-many-locals
    if generator == 'web-historian':
        filename = tempfile.gettempdir() + '/pdk_' + generator + '.txt'

        # for ignore_source in settings.WH_IGNORE_SOURCES:
        #    sources.remove(ignore_source)

        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter='\t')

            writer.writerow(['Source', 'Generator', 'Generator Identifier', 'Created Timestamp', 'Created Date', 'Recorded Timestamp', 'Recorded Date', 'Visit ID', 'URL ID', 'Referrer ID', 'Domain', 'Protocol', 'URL', 'Title', 'Top Domain', 'Search Terms', 'Transition Type', 'Timestamp', 'Date'])

            for source in sources:
                source_reference = DataSourceReference.reference_for_source(source)

                generator_definition = DataGeneratorDefinition.defintion_for_identifier(generator)

                points = DataPoint.objects.filter(source_reference=source_reference, generator_definition=generator_definition)

                if data_start is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__gte=data_start)
                    else:
                        points = points.filter(created__gte=data_start)

                if data_end is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__lte=data_end)
                    else:
                        points = points.filter(created__lte=data_end)

                points = points.order_by('source', 'created')

                count = points.count()

                for point in points.iterator():
                    row = []

                    row.append(point.source)
                    row.append(point.generator)
                    row.append(point.generator_identifier)
                    row.append(str(calendar.timegm(point.created.utctimetuple())))
                    row.append(point.created.isoformat())
                    row.append(str(calendar.timegm(point.recorded.utctimetuple())))
                    row.append(point.recorded.isoformat())

                    if 'id' in point.properties:
                        row.append(str(point.properties['id']))
                    else:
                        row.append('')

                    if 'urlId' in point.properties:
                        row.append(str(point.properties['urlId']))
                    else:
                        row.append('')

                    if 'refVisitId' in point.properties:
                        row.append(str(point.properties['refVisitId']))
                    else:
                        row.append('')

                    if 'domain' in point.properties:
                        row.append(point.properties['domain'])
                    else:
                        row.append('')

                    if 'protocol' in point.properties:
                        row.append(point.properties['protocol'])
                    else:
                        row.append('')

                    if 'url' in point.properties:
                        row.append(point.properties['url'])
                    else:
                        row.append('')

                    if 'title' in point.properties:
                        row.append(point.properties['title'])
                    else:
                        row.append('')

                    if 'topDomain' in point.properties:
                        row.append(point.properties['topDomain'])
                    else:
                        row.append('')

                    if 'searchTerms' in point.properties:
                        row.append(point.properties['searchTerms'])
                    else:
                        row.append('')

                    if 'transType' in point.properties:
                        row.append(point.properties['transType'])
                    else:
                        row.append('')

                    if 'date' in point.properties:
                        timestamp = float(point.properties['date']) / 1000

                        row.append(str(timestamp))

                        date_obj = datetime.datetime.utcfromtimestamp(timestamp)

                        row.append(date_obj.isoformat())
                    else:
                        row.append('')
                        row.append('')

                    row = [s.encode('utf-8') for s in row]

                    writer.writerow(row)

                    outfile.flush()

        return filename
    elif generator == 'pdk-app-event':
        filename = tempfile.gettempdir() + '/pdk_' + generator + '.txt'

        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter='\t')

            writer.writerow([
                'Source',
                'Created Timestamp',
                'Created Date',
                'Recorded Timestamp',
                'Recorded Date',
                'Event Name',
                'Session ID',
                'Step',
                'Event Properties'
            ])

            for source in sources:
                source_reference = DataSourceReference.reference_for_source(source)
                generator_definition = DataGeneratorDefinition.defintion_for_identifier(generator)

                points = DataPoint.objects.filter(source_reference=source_reference, generator_definition=generator_definition)

                if data_start is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__gte=data_start)
                    else:
                        points = points.filter(created__gte=data_start)

                if data_end is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__lte=data_end)
                    else:
                        points = points.filter(created__lte=data_end)

                points = points.order_by('source', 'created')

                index = 0
                count = points.count()

                while index < count:
                    for point in points[index:(index + 5000)]:
                        row = []

                        row.append(point.source)

                        row.append(calendar.timegm(point.created.utctimetuple()))
                        row.append(point.created.isoformat())

                        row.append(calendar.timegm(point.recorded.utctimetuple()))
                        row.append(point.recorded.isoformat())

                        properties = {}

                        if install_supports_jsonfield():
                            properties = point.properties
                        else:
                            properties = json.loads(point.properties)

                        row.append(properties['event_name'])

                        if 'event_details' in properties:
                            if 'session_id' in properties['event_details']:
                                row.append(properties['event_details']['session_id'])
                            else:
                                row.append(None)

                            if 'step' in properties['event_details']:
                                row.append(properties['event_details']['step'])
                            else:
                                row.append(None)

                            row.append(json.dumps(properties['event_details']))

                        writer.writerow(row)

                    index += 5000

                    writer.writerow(row)

                    outfile.flush()

        return filename
    elif generator == 'web-historian-behavior-metadata':
        filename = tempfile.gettempdir() + '/pdk_' + generator + '.txt'

        with open(filename, 'w') as outfile:
            writer = csv.writer(outfile, delimiter='\t')

            writer.writerow([
                'Source',
                'Created Timestamp',
                'Created Date',
                'Recorded Timestamp',
                'Recorded Date',
                'Participant ID',
                'Domains',
                'Searches',
                'Visits'
            ])

            rows = 0

            for source in sources:
                source_reference = DataSourceReference.reference_for_source(source)
                generator_definition = DataGeneratorDefinition.defintion_for_identifier(generator)

                points = DataPoint.objects.filter(source_reference=source_reference, generator_definition=generator_definition)

                if data_start is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__gte=data_start)
                    else:
                        points = points.filter(created__gte=data_start)

                if data_end is not None:
                    if date_type == 'recorded':
                        points = points.filter(recorded__lte=data_end)
                    else:
                        points = points.filter(created__lte=data_end)

                points = points.order_by('source', 'created')

                seen = {}

                count = points.count()

                for point in points.iterator():
                    properties = {}

                    if install_supports_jsonfield():
                        properties = point.properties
                    else:
                        properties = json.loads(point.properties)

                    for key in properties:
                        if key != 'passive-data-metadata' and key != 'web-historian-server':
                            participant = properties[key]

                            if (key in seen) is False:
                                seen[key] = {}

                            if seen[key] != participant:
                                row = []

                                row.append(point.source)

                                row.append(calendar.timegm(point.created.utctimetuple()))
                                row.append(point.created.isoformat())

                                row.append(calendar.timegm(point.recorded.utctimetuple()))
                                row.append(point.recorded.isoformat())

                                row.append(key)
                                row.append(participant['domains'])
                                row.append(participant['searches'])
                                row.append(participant['visits'])

                                writer.writerow(row)

                                rows += 1

                                seen[key] = participant

                            outfile.flush()

                    properties = None

        return filename

    return None



def load_backup(filename, content):
    prefix = 'historian_backup_' + settings.ALLOWED_HOSTS[0]

    if filename.startswith(prefix) is False:
        return

    if 'json-dumpdata' in filename:
        filename = filename.replace('.json-dumpdata.bz2.encrypted', '.json')

        path = os.path.join(tempfile.gettempdir(), filename)

        with open(path, 'wb') as fixture_file:
            fixture_file.write(content)

        management.call_command('loaddata', path)

        os.remove(path)
    elif 'pdk-bundle' in filename:
        bundle = DataBundle(recorded=timezone.now())

        if install_supports_jsonfield():
            bundle.properties = json.loads(content)
        else:
            bundle.properties = content

        bundle.save()
    else:
        print '[historian.pdk_api.load_backup] Unknown file type: ' + filename

def incremental_backup(parameters): # pylint: disable=too-many-locals
    to_transmit = []
    to_clear = []

    # Dump full content of these models. No incremental backup here.

    dumpdata_apps = (
        'web_historian.ProvidedIdentifier',
        'web_historian.UrlAction',
        'web_historian.UrlCategory',
    )

    prefix = 'historian_backup_' + settings.ALLOWED_HOSTS[0]

    if 'start_date' in parameters:
        prefix += '_' + parameters['start_date'].isoformat()

    if 'end_date' in parameters:
        prefix += '_' + parameters['end_date'].isoformat()

    backup_staging = tempfile.gettempdir()

    try:
        backup_staging = settings.PDK_BACKUP_STAGING_DESTINATION
    except AttributeError:
        pass

    for app in dumpdata_apps:
        print '[historian] Backing up ' + app + '...'
        buf = StringIO.StringIO()
        management.call_command('dumpdata', app, stdout=buf)
        buf.seek(0)

        database_dump = buf.read()

        buf = None

        gc.collect()

        compressed_str = bz2.compress(database_dump)

        database_dump = None

        gc.collect()

        filename = prefix + '_' + slugify(app) + '.json-dumpdata.bz2'

        path = os.path.join(backup_staging, filename)

        with open(path, 'wb') as fixture_file:
            fixture_file.write(compressed_str)

        to_transmit.append(path)

    # Using parameters, only backup matching DataPoint objects.

    bundle_size = 500

    historian_def = DataGeneratorDefinition.definition_for_identifier('web-historian')
    behavior_def = DataGeneratorDefinition.definition_for_identifier('web-historian-behavior-metadata')

    query = Q(generator_definition=historian_def) | Q(generator_definition=behavior_def)

    if 'start_date' in parameters:
        query = query & Q(recorded__gte=parameters['start_date'])

    if 'end_date' in parameters:
        query = query & Q(recorded__lt=parameters['end_date'])

    count = DataPoint.objects.filter(query).count()

    index = 0

    while index < count:
        filename = prefix + '_data_points_' + str(index) + '_' + str(count) + '.pdk-bundle.bz2'

        print '[historian] Backing up data points ' + str(index) + ' of ' + str(count) + '...'

        bundle = []

        for point in DataPoint.objects.filter(query).order_by('recorded')[index:(index + bundle_size)]:
            bundle.append(point.fetch_properties())

        index += bundle_size

        compressed_str = bz2.compress(json.dumps(bundle))

        path = os.path.join(backup_staging, filename)

        with open(path, 'wb') as compressed_file:
            compressed_file.write(compressed_str)

        to_transmit.append(path)

    return to_transmit, to_clear


def clear_points(to_clear): # pylint: disable=unused-argument
    pass # Don't delete EMA points - these are used for other calculations.
