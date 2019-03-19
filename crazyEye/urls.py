"""crazyEye URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
from web.views import base
from web import api_urls
from web.views import asset
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'session_security/', include('session_security.urls')),
    url(r'^$', base.home, name='dashboard'),
    url(r'^login/$', base.acc_login),
    url(r'^logout/$', base.acc_logout),
    url(r'^hosts/$', base.hosts, name='host_list'),
    url(r'^auditlog/$', base.auditlog, name='auditlog'),
    url(r'^host_mgr/cmd/$', base.host_mgr, name='batch_cmd'),
    url(r'^host_mgr/file_transfer/$', base.file_transfer, name='file_transfer'),
    url(r'^batch_task_mgr/$', base.batch_task_mgr, name='batch_task_mgr'),
    url(r'^task_result/$', base.task_result, name='get_task_result'),
    url(r'^user_audit/(\d+)/$',base.user_audit, name='user_audit'),
    url(r'^multi_task/log/deatail/(\d+)/$', base.multi_task_log_detail, name='multi_task_log_detail'),

    url(r'^asset.html$', asset.AssetListView.as_view()),
    url(r'^assets.html$', asset.AssetJsonView.as_view()),
    url(r'^asset-(?P<asset_nid>\d+).html$', asset.AssetDetailView.as_view()),
    url(r'^add-asset.html$', asset.AddAssetView.as_view()),

    url(r'^api/', include(api_urls)),

    url(r'^password_reset/',base.password_reset, name='password_reset'),
    url(r'^personal/', base.personal, name='personal'),
    url(r'^kingadmin/',include('kingadmin.urls')),


]
