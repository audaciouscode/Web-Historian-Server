import datetime
import hashlib

import idsentence
import numpy

from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseNotFound, FileResponse

from django.shortcuts import render, render_to_response
from django.template import RequestContext

from passive_data_kit.models import DataPoint

from .models import UrlAction, ProvidedIdentifier, UrlCategory

def hash_for_source_id(source_id):
    hashes = DataPoint.objects.order_by().values_list('source').distinct()
    
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    
    days = [today, yesterday, tomorrow]
    
    for hash in hashes:
        for day in days:
            m = hashlib.md5()
            m.update(hash[0] + day)
            
            if m.hexdigest() == source_id:
                return hash[0]
    
    return None

def fetch_id_json(request):
    # Source: https://gist.github.com/prschmid/4447660
    generator = idsentence.IntIdSentence()
    new_id = generator.generate()
    
    while (ProvidedIdentifier.objects.filter(identifier=new_id[1]).count() > 0):
        new_id = generator.generate()
        
    ProvidedIdentifier(identifier=new_id[1]).save()
    
    response_obj = { 'new_id': new_id[1] }
    
    response = JsonResponse(response_obj, safe=False, json_dumps_params={ 'indent': 2 })
    
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'
    response['Access-Control-Request-Headers'] = 'Content-Type'
    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response


def actions_json(request):
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
            
    response = JsonResponse(actions, safe=False, json_dumps_params={ 'indent': 2 })
    
    response['Access-Control-Allow-Origin'] = '*'
#   response['Access-Control-Allow-Methods'] = 'GET'
#   response['Access-Control-Request-Headers'] = 'Content-Type'
#   response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response
    

def categories_json(request):
    root_obj = { 'name': 'categories' }
    
    categories = []
    
    for category in UrlCategory.objects.all().order_by('-priority'):
        cat_obj = {}
        cat_obj['search'] = category.match_type
        cat_obj['value'] = category.match_value
        cat_obj['category'] = category.category
        
        categories.append(cat_obj)
        
    root_obj['children'] = categories
            
    response = JsonResponse(root_obj, safe=False, json_dumps_params={ 'indent': 2 })
    
    response['Access-Control-Allow-Origin'] = '*'
#    response['Access-Control-Allow-Methods'] = 'GET'
#    response['Access-Control-Request-Headers'] = 'Content-Type'
#    response['Access-Control-Allow-Headers'] = 'Content-Type'
    
    return response
    

def historian_visualization_data(request, source_id, page):
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
    
def historian_user_home(request, source_id):
    data_hash = hash_for_source_id(source_id)
    
    if data_hash is None:
        c = RequestContext(request)
    
        response = render_to_response('historian_loading_data.html', context_instance=c)

        response.status_code = 403
        
        return response
    
    c = RequestContext(request)
    c['source_id'] = source_id
    
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

        c['compare_end'] = last_usage_compare.created
        c['compare_start'] = last_usage_compare.created - datetime.timedelta(days=7)
        
        c['avg_domains'] = numpy.median(domain_counts)
        c['avg_searches'] = numpy.median(search_counts)
        c['avg_visits'] = numpy.median(visit_counts)
                  
        if my_data is not None:
            c['my_domains'] = my_data['domains']
            c['my_domains_percentage'] = (my_data['domains'] / (sum(domain_counts) / float(len(domain_counts)))) * 100

            c['my_searches'] = my_data['searches']
            c['my_searches_percentage'] = (my_data['searches'] / (sum(search_counts) / float(len(search_counts)))) * 100

            c['my_visits'] = my_data['visits']
            c['my_visits_percentage'] = (my_data['visits'] / (sum(visit_counts) / float(len(visit_counts)))) * 100
            
            if c['my_domains'] > c['avg_domains']:
                c['my_domains_bar'] = 80
                c['avg_domains_bar'] = 80 * (c['avg_domains'] / c['my_domains'])
            else:
                c['my_domains_bar'] = 80 * (c['my_domains'] / c['avg_domains'])
                c['avg_domains_bar'] = 80

            if c['my_searches'] > c['avg_searches']:
                c['my_searches_bar'] = 80
                c['avg_searches_bar'] = 80 * (c['avg_searches'] / c['my_searches'])
            else:
                c['my_searches_bar'] = 80 * (c['my_searches'] / c['avg_searches'])
                c['avg_searches_bar'] = 80

            if c['my_visits'] > c['avg_visits']:
                c['my_visits_bar'] = 80
                c['avg_visits_bar'] = 80 * (c['avg_visits'] / c['my_visits'])
            else:
                c['my_visits_bar'] = 80 * (c['my_visits'] / c['avg_visits'])
                c['avg_visits_bar'] = 80
    
    return render_to_response('historian_user_data.html', c)
