# pylint: disable=no-member,line-too-long

import datetime
import hashlib
import time

import numpy

from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound

from django.shortcuts import render
from django.utils import timezone

from passive_data_kit.models import DataPoint, DataBundle

from web_historian import idsentence

from .models import UrlAction, ProvidedIdentifier, UrlCategory

def hash_for_source_id(source_id):
    hashes = DataPoint.objects.sources()

    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    days = [today, yesterday, tomorrow]

    for source_hash in hashes:
        for day in days:
            md5_hash = hashlib.md5() # nosec

            md5_hash.update(source_hash + day)

            if md5_hash.hexdigest() == source_id:
                return hash

    return None

def fetch_id_json(request): # pylint: disable=unused-argument
    # Source: https://gist.github.com/prschmid/4447660
    generator = idsentence.IntIdSentence()
    new_id = generator.generate()

    while ProvidedIdentifier.objects.filter(identifier=new_id[1]).count() > 0:
        new_id = generator.generate()

    ProvidedIdentifier(identifier=new_id[1]).save()

    response_obj = {'new_id': new_id[1]}

    response = JsonResponse(response_obj, safe=False, json_dumps_params={'indent': 2})

    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Request-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Headers'] = 'Content-Type'

    return response


def actions_json(request): # pylint: disable=unused-argument
    actions = []

    for action in UrlAction.objects.all():
        action_obj = {}
        action_obj['name'] = action.name
        action_obj['identifier'] = action.identifier
        action_obj['url'] = action.url
        action_obj['days'] = action.days

        if action.publish is not None:
            action_obj['publish'] = action.publish.isoformat()
        else:
            action_obj['publish'] = None

        actions.append(action_obj)

    response = JsonResponse(actions, safe=False, json_dumps_params={'indent': 2})

    response['Access-Control-Allow-Origin'] = '*'
#   response['Access-Control-Allow-Methods'] = 'GET'
#   response['Access-Control-Request-Headers'] = 'Content-Type'
#   response['Access-Control-Allow-Headers'] = 'Content-Type'

    return response


def categories_json(request): # pylint: disable=unused-argument
    root_obj = {'name': 'categories'}

    categories = []

    for category in UrlCategory.objects.all().order_by('-priority'):
        cat_obj = {}
        cat_obj['search'] = category.match_type
        cat_obj['value'] = category.match_value
        cat_obj['category'] = category.category

        categories.append(cat_obj)

    root_obj['children'] = categories

    response = JsonResponse(root_obj, safe=False, json_dumps_params={'indent': 2})

    response['Access-Control-Allow-Origin'] = '*'
#    response['Access-Control-Allow-Methods'] = 'GET'
#    response['Access-Control-Request-Headers'] = 'Content-Type'
#    response['Access-Control-Allow-Headers'] = 'Content-Type'

    return response


def historian_visualization_data(request, source_id, page): # pylint: disable=unused-argument
    data_hash = hash_for_source_id(source_id)

    folder = settings.MEDIA_ROOT + '/pdk_visualizations/' + data_hash + '/web-historian'

    filename = 'visualization-' + page + '.json'

    if page == '0':
        filename = 'visualization.json'

    try:
        with open(folder + '/' + filename) as data_file:
            return HttpResponse(data_file.read(), content_type='application/json')
    except IOError:
        pass

    return HttpResponseNotFound()

def historian_user_delete(request, source_id):
    data_hash = hash_for_source_id(source_id)

    if data_hash is not None:
        points = DataPoint.objects.filter(source=data_hash)
        bundles = DataBundle.objects.filter(properties__0__contains={'passive-data-kit': {'source': data_hash}})

        payload = {}
        payload['passive-data-metadata'] = {}
        payload['passive-data-metadata']['source'] = 'web-historian-server'
        payload['passive-data-metadata']['generator-id'] = 'web-historian-server-deletion'
        payload['passive-data-metadata']['generator'] = 'Web Historian Server Deletion'
        payload['passive-data-metadata']['timestamp'] = time.mktime(datetime.datetime.timetuple(timezone.now()))
        payload['points-deleted'] = points.count()
        payload['bundles-deleted'] = bundles.count()
        payload['source_id'] = data_hash

        if 'value' in request.POST:
            payload['why_deleted'] = request.POST['value']

        if 'other_reason' in request.POST:
            payload['other_reason'] = request.POST['other_reason']

        delete_point = DataPoint(source=payload['passive-data-metadata']['source'])
        delete_point.generator = payload['passive-data-metadata']['generator']
        delete_point.generator_identifier = payload['passive-data-metadata']['generator-id']
        delete_point.created = timezone.now()
        delete_point.recorded = delete_point.created
        delete_point.properties = payload
        delete_point.save()

        points.delete()
        bundles.delete()

    return HttpResponse('{"success": true}', content_type='application/json')

def historian_user_home(request, source_id): # pylint: disable=too-many-branches, too-many-statements
    data_hash = hash_for_source_id(source_id)

    if data_hash is None:
        context = {}

        response = render(request, 'historian_loading_data.html', context=context)

        response.status_code = 403

        return response

    context = {}
    context['source_id'] = source_id

    last_usage_compare = DataPoint.objects.filter(generator_identifier='web-historian-behavior-metadata').order_by('-created').first()

    if last_usage_compare is not None:
        my_data = None

        domain_counts = []
        search_counts = []
        visit_counts = []

        for source, value in last_usage_compare.properties.iteritems():
            if source == data_hash:
                my_data = value
            elif 'domains' in value:
                if value['domains'] > 0:
                    domain_counts.append(value['domains'])
                    search_counts.append(value['searches'])
                    visit_counts.append(value['visits'])

        context['compare_end'] = last_usage_compare.created
        context['compare_start'] = last_usage_compare.created - datetime.timedelta(days=7)

        if domain_counts:
            context['avg_domains'] = numpy.median(domain_counts)
        else:
            context['avg_domains'] = 0

        if search_counts:
            context['avg_searches'] = numpy.median(search_counts)
        else:
            context['avg_searches'] = 0

        if visit_counts:
            context['avg_visits'] = numpy.median(visit_counts)
        else:
            context['avg_visits'] = 0

        if my_data is not None:
            context['my_domains'] = my_data['domains']

            try:
                context['my_domains_percentage'] = (my_data['domains'] / (sum(domain_counts) / float(len(domain_counts)))) * 100
            except ZeroDivisionError:
                context['my_domains_percentage'] = 0

            context['my_searches'] = my_data['searches']

            try:
                context['my_searches_percentage'] = (my_data['searches'] / (sum(search_counts) / float(len(search_counts)))) * 100
            except ZeroDivisionError:
                context['my_searches_percentage'] = 0

            context['my_visits'] = my_data['visits']

            try:
                context['my_visits_percentage'] = (my_data['visits'] / (sum(visit_counts) / float(len(visit_counts)))) * 100
            except ZeroDivisionError:
                context['my_visits_percentage'] = 0

            if context['my_domains'] > context['avg_domains']:
                context['my_domains_bar'] = 80
                context['avg_domains_bar'] = 80 * (context['avg_domains'] / context['my_domains'])
            elif context['my_domains'] == 0:
                context['my_domains_bar'] = 0
                context['avg_domains_bar'] = 80
            else:
                context['my_domains_bar'] = 80 * (context['my_domains'] / context['avg_domains'])
                context['avg_domains_bar'] = 80

            if context['my_searches'] > context['avg_searches']:
                context['my_searches_bar'] = 80
                context['avg_searches_bar'] = 80 * (context['avg_searches'] / context['my_searches'])
            elif context['my_searches'] == 0:
                context['my_searches_bar'] = 0
                context['avg_searches_bar'] = 80
            else:
                context['my_searches_bar'] = 80 * (context['my_searches'] / context['avg_searches'])
                context['avg_searches_bar'] = 80

            if context['my_visits'] > context['avg_visits']:
                context['my_visits_bar'] = 80
                context['avg_visits_bar'] = 80 * (context['avg_visits'] / context['my_visits'])
            elif context['my_visits'] == 0:
                context['my_visits_bar'] = 0
                context['avg_visits_bar'] = 80
            else:
                context['my_visits_bar'] = 80 * (context['my_visits'] / context['avg_visits'])
                context['avg_visits_bar'] = 80

    return render(request, 'historian_user_data.html', context=context)

def historian_sample_data_json(request): # pylint: disable=unused-argument
    visits = []

    for point in DataPoint.objects.filter(source=settings.SAMPLE_DATA_SOURCE, generator_identifier='web-historian'):
        visits.append(point.fetch_properties())

    response = JsonResponse(visits, safe=False, json_dumps_params={'indent': 2})

    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Request-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Headers'] = 'Content-Type'

    return response
