import datetime
import hashlib

import idsentence

from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpResponseNotAllowed, JsonResponse, HttpResponseNotFound, FileResponse

from django.shortcuts import render, render_to_response
from django.template import RequestContext

from passive_data_kit.models import DataPoint

from .models import UrlAction, ProvidedIdentifier

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
        return HttpResponseForbidden()
    
    c = RequestContext(request)
    c['source_id'] = source_id
    
    return render_to_response('historian_user_data.html', c)

