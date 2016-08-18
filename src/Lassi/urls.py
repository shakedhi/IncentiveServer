from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets, routers
from django.conf.urls import url
from incentive import views
from incentive.views import IncetiveViewSet
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


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


incentive_list = IncetiveViewSet.as_view({
    'get': 'list',
    'post': 'create'
})
incentive_detail = IncetiveViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})
incentive = IncetiveViewSet.as_view({
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
router.register(r'incentive', IncetiveViewSet)
router.register(r'users', UserViewSet)

# The API URLs are now determined automatically by the router.
# Additionally, we include the login URLs for the browsable API.
urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^about/$', views.about),
    url(r'^test/$', views.incentiveTest),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^$', 'incentive.views.home', name='home'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^add/', 'incentive.views.addIncentive', name='add'),
    url(r'^incentives/$', views.incetive_list, name='incetive_filter'),
    url(r'^login/$', views.login, name='login'),
    url(r'^wiki/$', views.wiki, name='wiki'),
    url(r'^aboutus/', views.aboutus, name='aboutus'),
    url(r'^list/$', 'incentive.views.list', name='data_set'),
    url(r'^profile/', 'incentive.views.userProfile', name='profile_page'),
    url(r'^startAlg/', 'incentive.runner.startAlg', name='startAlg'),
    url(r'^predicting/', 'incentive.runner.getTheBestForTheUser', name='predicting'),
    url(r'^timeout/$', 'incentive.views.changeTimeout', name='changeTimeout'),

    url(r'^getIncUser/$', 'incentive.views.getUserID', name='getIncUser'),
    url(r'^dash/pages/dash.html', views.dash, name='dash'),
    url(r'^dashStream/$', views.dashStream, name='dashStream'),

    url(r'^dash/pages/streamResponse/', views.stream_response, name='streamResponse'),
    url(r'^ask_by_date/$', views.ask_by_date, name='ask_by_date'),
    url(r'^ask_gt_id/$', views.ask_gt_id, name='ask_gt_id'),
    url(r'^disratio/$', views.GiveRatio, name='disratio'),
    url(r'^add_event/$', views.receive_event, name='receive_event'),

]
# url(r'^docs/', include('rest_framework_swagger.urls')),

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
