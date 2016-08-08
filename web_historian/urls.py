from django.conf.urls import url

from .views import actions_json, historian_user_home, fetch_id_json, historian_visualization_data, categories_json

urlpatterns = [
    url(r'^categories.json$', categories_json, name='categories_json'),
    url(r'^actions.json$', actions_json, name='actions_json'),
    url(r'^fetch-id.json$', fetch_id_json, name='fetch_id_json'),
    url(r'^user/(?P<source_id>.+)$', historian_user_home, name='historian_user_home'),
    url(r'^visualization/(?P<source_id>.+)/(?P<page>\d+).json$', historian_visualization_data, name='historian_visualization_data'),
]
