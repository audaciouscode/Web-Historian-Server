# pylint: disable=no-member,line-too-long

import calendar
import datetime
import codecs
import csv
import json
import tempfile

from django.template.loader import render_to_string

from passive_data_kit.models import DataPoint, DataSourceReference, DataGeneratorDefinition, install_supports_jsonfield

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

                index = 0
                count = points.count()

                while index < count:
                    for point in points[index:(index + 5000)]:
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

                    index += 5000

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

        return filename

    return None
