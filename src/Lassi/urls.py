from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User
from rest_framework import serializers, routers
from django.conf.urls import url
from incentive import views, runner
from incentive.views import IncentiveViewSet, UserViewSet
from rest_framework import renderers
from django.conf.urls import include
from django.contrib import admin

admin.autodiscover()

admin.site.site_header = 'Incentive Server'
admin.site.site_title = 'Incentive Server'
admin.site.index_title = 'Admin'


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


incentive_list = IncentiveViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
incentive_detail = IncentiveViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})
incentive = IncentiveViewSet.as_view({
    'get': 'highlight'
}, renderer_classes=[renderers.StaticHTMLRenderer])

user_list = UserViewSet.as_view({
    'get': 'list'
})
user_detail = UserViewSet.as_view({
    'get': 'retrieve'
})

# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'incentive', IncentiveViewSet)
router.register(r'users', UserViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^about/$', views.about),
    url(r'^test/$', views.incentive_test),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^$', views.home, name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^add/', views.add_incentive, name='add'),
    url(r'^incentives/$', views.incentive_list, name='incentive_filter'),
    url(r'^login/$', views.login, name='login'),
    url(r'^changePassword/$', views.change_password, name='change_password'),
    url(r'^wiki/$', views.wiki, name='wiki'),
    url(r'^aboutus/', views.aboutus, name='aboutus'),
    url(r'^list/$', views.data_set, name='data_set'),
    url(r'^profile/', views.user_profile, name='profile_page'),
    url(r'^startAlg/', runner.start_alg, name='start_alg'),
    url(r'^timeout/$', views.change_timeout, name='change_timeout'),

    url(r'^getIncUser/$', views.get_user_id, name='getIncUser'),
    url(r'^sendIncentive/$', views.send_incentive, name='sendIncentive'),
    url(r'^dash/pages/dash.html', views.dash, name='dash'),
    url(r'^dashStream/$', views.dash_stream, name='dashStream'),

    url(r'^dash/pages/streamResponse/', views.stream_response, name='streamResponse'),
    url(r'^ask_by_date/$', views.ask_by_date, name='ask_by_date'),
    url(r'^ask_gt_id/$', views.ask_gt_id, name='ask_gt_id'),
    url(r'^disratio/$', views.give_ratio, name='disratio'),

    url(r'^collectiveReminder/$', views.send_collective_reminder, name='reminder'),
    url(r'^invalidate/(?P<cid>[1-9][0-9]*)/$', views.invalidate_from_collective, name='invalidate'),
    url(r'^invalidate/$', views.invalidate_no_collective, name='invalidate_no_collective'),
]
# url(r'^docs/', include('rest_framework_swagger.urls')),

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
