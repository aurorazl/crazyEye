from django.conf.urls import url
from web.views import base

urlpatterns = [

    url(r'home_summary/$', base.home_summary, name='home_summary'),
    url(r'audit/user_counts/$', base.user_login_counts, name='user_login_counts'),
    url(r'multitask/res/$', base.multitask_res),
    url(r'multitask/action/$', base.multitask_task_action, name='multitask_action'),
    url(r'dashboard_detail/$', base.dashboard_detail, name='dashboard_detail'),
    url(r'token/gen/$', base.token_gen, name='token_gen'),
    url(r'audit/cmd_logs/$', base.audit_cmd_logs)
]