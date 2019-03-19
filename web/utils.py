from crazyEye import settings
import os, tempfile, zipfile
from django.http import HttpResponse
#from django.core.servers.basehttp import FileWrapper
from wsgiref.util import FileWrapper #from django.core.servers.basehttp import FileWrapper
from web import models
import django
from django.db.models import Count,Sum
from backend import utils
import random,json,datetime,time
# from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone


def recent_accssed_hosts(request):
    days_before_14 = django.utils.timezone.now() +django.utils.timezone.timedelta(days=-14)
    recent_logins = models.AuditLog.objects.filter(date__gt = days_before_14,user_id=request.user.id,log_type=1).order_by('date')
    unique_bindhost_ids = set([i[0] for i in recent_logins.values_list('host_to_remote_user_id')])
    recent_login_hosts = []
    for h_id in unique_bindhost_ids:
        recent_login_hosts.append(recent_logins.filter(host_to_remote_user_id=h_id).latest('date'))

    return  set(recent_login_hosts)

def home_summary(request):
    data_dic = {
        'user_login_statistics' :[],
        'recent_active_users':[],
        'recent_active_users_cmd_count':[],
        'summary':{}
    }
    days_before_30 = django.utils.timezone.now() + django.utils.timezone.timedelta(days=-30)
    #data_dic['user_login_statistics'] = list(models.AuditLog.objects.filter(action_type=1).extra({"login_date":"date(date)"}).values_list('login_date').annotate(count=Count('pk')))
    data_dic['user_login_statistics'] = list(models.AuditLog.objects.filter(date__gt=days_before_30).extra({'login_date':'date(date)'}).values_list('login_date').annotate(count=Count('pk')))
    days_before_7 = django.utils.timezone.now() +django.utils.timezone.timedelta(days=-7)
    #recent_active_users= models.Session.objects.all()[0:10].values('user','user__name','cmd_count').annotate(Count('user'))
    recent_active_users= models.AuditLog.objects.all()[0:10].values("user",'user__name').annotate(Sum('content'),Count('id'))
    recent_active_users_cmd_count= models.AuditLog.objects.filter(date__gt = days_before_7,log_type=0).values('user','user__name').annotate(Count('content'))
    data_dic['recent_active_users'] = list(recent_active_users)
    data_dic['recent_active_users_cmd_count'] = list(recent_active_users_cmd_count)
    data_dic['summary']['total_servers'] = models.Host.objects.count()
    data_dic['summary']['total_users'] = models.UserProfile.objects.count()
    data_dic['summary']['current_logging_users'] = get_all_logged_in_users().count()

    #current_connection servers
    current_connected_hosts = models.Session.objects.filter(closed=0).count()

    #current_connected_hosts = login_times - logout_times
    data_dic['summary']['current_connected_hosts'] = current_connected_hosts
    return  data_dic

def get_all_logged_in_users():
    # Query all non-expired sessions
    # use timezone.now() instead of datetime.now() in latest versions of Django
    sessions = Session.objects.filter(expire_date__gte=django.utils.timezone.now())
    uid_list = []

    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))

    # Query all logged in users based on id list
    return models.UserProfile.objects.filter(id__in=uid_list)

class Dashboard(object):
    def __init__(self,request):
        self.request = request

    def get(self):
        data_type = self.request.GET.get("data_type")
        assert  data_type is not None
        func = getattr(self,data_type)
        return func()
    def get_online_users(self):
        return  get_all_logged_in_users().values('name','department__name','last_login','id')

    def get_online_hosts(self):
        return   models.Session.objects.filter(closed=0).values('bind_host__host__name',
                                                                 'user__name',
                                                                 'bind_host__host__ip_addr',
                                                                 'bind_host__host__id',
                                                                 'bind_host__remote_user__username',
                                                                 'tag',
                                                                 'cmd_count',
                                                                'stay_time',
                                                                 'id','date')

class Token(object):
    def __init__(self,request):
        self.request = request
        self.token_type = request.POST.get('token_type')
        self.token = {'token':None}
    def generate(self):
        func = getattr(self,self.token_type)
        return func()
    def host_token(self):
        bind_host_id = self.request.POST.get('bind_host_id')
        host_obj = models.HostToRemoteUser.objects.get(id=int(bind_host_id))
        latest_token_obj = models.Token.objects.filter(host_id = int(bind_host_id),user_id=self.request.user.id).last()
        token_gen_flag = False

        if latest_token_obj:

            token_gen_time_stamp = time.mktime(latest_token_obj.date.timetuple())
            current_time = time.mktime(django.utils.timezone.now().timetuple() )
            if current_time - token_gen_time_stamp >latest_token_obj.expire:#token expired
                token_gen_flag = True
        else:
            token_gen_flag = True

        if token_gen_flag:
            token = ''.join(random.sample('zyxwvutsrqponmlkjihgfedcba1234567890',6))
            models.Token.objects.create(
                user = self.request.user,
                host = host_obj,
                token = token
            )
        else:
            token = latest_token_obj.token
        self.token['token'] = token
        return  json.dumps(self.token)
