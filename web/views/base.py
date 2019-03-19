from django.shortcuts import render,redirect,HttpResponse,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate,login,logout
import json,datetime,os,time
from web import models
from  backend.multitask import MultiTaskManger
from web import utils
from crazyEye import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from backend.utils import json_date_to_stamp,json_date_handler
from web.forms import userform
from django.core.urlresolvers import resolve
from web import host_mgr_utils
import django.utils.timezone
from django.core.exceptions import ObjectDoesNotExist
@login_required
def home(request):
    # print(resolve(request.path),request.path_info,request.path)
    recent_tasks= models.Task.objects.all().order_by('-id')[:10]
    return render(request, 'index.html', {
        'login_user':request.user,
        'recent_tasks':recent_tasks
    })

@login_required
def home_summary(request):

    if request.method == 'GET':
        summary_data = utils.home_summary(request)
        return HttpResponse(json.dumps(summary_data,default=json_date_to_stamp))

@login_required
def user_login_counts(request):
    filter_time_stamp = request.GET.get('time_stamp')
    assert  filter_time_stamp.isdigit()
    filter_time_stamp = int(filter_time_stamp) / 1000
    filter_date_begin = datetime.datetime.fromtimestamp(filter_time_stamp)
    filter_date_end = filter_date_begin + datetime.timedelta(days=1)

    user_login_records = models.AuditLog.objects.filter(date__range=[filter_date_begin,filter_date_end]).\
        values('host_to_remote_user',
               'host_to_remote_user__host_user__username',
               'user',
               'user__name',
               'host_to_remote_user__host__hostname',
               'date')

    return  HttpResponse(json.dumps(list(user_login_records),default=json_date_handler))


def acc_login(request):
    error_msg = ''
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username,password=password)
        if user is not None:
            try:
                if user.valid_begin_time and user.valid_end_time:
                    if django.utils.timezone.now() > user.valid_begin_time and django.utils.timezone.now()  < user.valid_end_time:
                        login(request,user)
                        request.session.set_expiry(60*30)
                        return HttpResponseRedirect(request.GET.get("next") if request.GET.get("next") else "/")
                    else:
                        return render(request,'login.html',{'error_msg': 'User account is expired,please contact your IT guy for this!'})
                else:
                    login(request, user)
                    request.session.set_expiry(60 * 30)
                    return HttpResponseRedirect(request.GET.get("next") if request.GET.get("next") else "/")
            except ObjectDoesNotExist:
                    return render(request,'login.html',{'error_msg': u'CrazyEye账户还未设定,请先登录后台管理界面创建CrazyEye账户!'})
        else:
            return render(request,'login.html',{'error_msg': 'Wrong username or password!'})
    return render(request, 'login.html', {'error_msg':error_msg})

def acc_logout(request):
    logout(request)
    return redirect('/login/')

@login_required
def hosts(request):
    selected_g_id = request.GET.get('selected_group')
    if selected_g_id:
        if selected_g_id.isdigit():
            selected_g_id = int(selected_g_id)
    recent_logins = utils.recent_accssed_hosts(request)
    return render(request, 'host.html', {'login_user':request.user,
                                         'selected_g_id': selected_g_id,
                                        'active_node':"/hosts/?selected_group=-1",
                                        'recent_logins':recent_logins,
                                        'webssh':settings.SHELLINABOX})
@login_required
def auditlog(request):
    host_id = request.GET.get('host_id')
    access_records = []

    all_hosts = models.Host.objects.all()
    if host_id:
        host_id = int(host_id)

        access_records = models.AuditLog.objects.filter(host_to_remote_user__host_id=host_id).order_by('-date')

        paginator = Paginator(access_records,10)
        page = request.GET.get('page')
        try:
            access_records = paginator.page(page)
        except PageNotAnInteger:
            access_records = paginator.page(1)
        except EmptyPage:
            access_records = paginator.page(paginator.num_pages)

    return  render(request, 'auditlog.html', {'all_hosts':all_hosts,
                                                 'current_host_id': host_id,
                                                 'access_records': access_records,
                                                 'active_node':'/auditlog/?host_id=1'})

@login_required
def host_mgr(request):
    return render(request, 'host_mgr.html')

@login_required
def file_transfer(request):

    return render(request, 'file_transfer.html')

@login_required
def batch_task_mgr(request):

    print(request.POST)
    task_data= json.loads(request.POST.get('task_data'))
    print("task_data",task_data)

    task_obj = MultiTaskManger(request)

    response = {
        'task_id':task_obj.task_obj.id,
        'selected_hosts': list(task_obj.task_obj.tasklogdetail_set.all().values('id',
                                                       'host_to_remote_user__host__ip_addr',
                                                       'host_to_remote_user__host__name',
                                                       'host_to_remote_user__remote_user__username')
                                )
    }

    return HttpResponse( json.dumps(response))



def task_result(request):
    task_id = request.GET.get('task_id')

    sub_tasklog_objs = models.TaskLogDetail.objects.filter(task_id=task_id)

    #log_data = sub_tasklog_objs.values('id','status','result','date')  #data need json_encode
    log_data = list(sub_tasklog_objs.values('id','status','result'))

    return HttpResponse(json.dumps(log_data))

def password_reset(request):

    if request.method == "GET":
        change_form = userform.UserCreationForm(instance=request.user)
    else:
        change_form = userform.UserCreationForm(request.POST, instance=request.user)
        if change_form.is_valid():
            change_form.save()
            # url = "/%s/" % request.path.strip("/password_reset/")
            return redirect('/admin/')

    return render(request, 'password_reset.html', {'user_obj': request.user,
                                                              'form': change_form})

@login_required
def dashboard_detail(request):
    if request.method == 'GET':
        detail_ins = utils.Dashboard(request)
        res = list(detail_ins.get())
        return HttpResponse(json.dumps(res,default=json_date_handler))

@login_required
def audit_cmd_logs(request):
    session_id  = request.GET.get('session_id')
    if session_id:
        session_id = int(session_id)
        cmd_records = list(models.Session.objects.filter(id = session_id).values().order_by('date'))

        data = {
            'data':cmd_records,
            'action_choices':models.AuditLog.action_choices
        }

        return  HttpResponse(json.dumps(data,default=json_date_handler))

@login_required
def user_audit(request,user_id):
    page = request.GET.get('page')
    data_type = request.GET.get('type')

    all_user = models.UserProfile.objects.all()
    department_list = models.Department.objects.all()
    user_obj = None
    login_records = []
    multitask_records= []
    if int(user_id)!=0:
        user_obj = models.UserProfile.objects.get(id=int(user_id))
        user_login_records = models.AuditLog.objects.filter(user_id=user_obj.id,log_type=1).order_by('-date')
        user_multi_task_records = models.Task.objects.filter(user_id= user_obj.id).order_by('-start_time')
        paginator = Paginator(user_login_records,10)
        paginator_multi = Paginator(user_multi_task_records,10)

        try:
            login_records = paginator.page(page)
        except PageNotAnInteger:
            login_records = paginator.page(1)
        except EmptyPage:
            login_records = paginator.page(paginator.num_pages)

        try:
            multitask_records = paginator_multi.page(page)
        except PageNotAnInteger:
            multitask_records = paginator_multi.page(1)
        except EmptyPage:
            multitask_records = paginator_multi.page(paginator_multi.num_pages)

    return  render(request,'user_audit.html',{
        'department_list':department_list,
        'user_obj':user_obj,
        'user_login_records':login_records,
        'multitask_records':multitask_records,
        'active_node':'/user_audit/',
        'data_type': data_type, #for tab switch usage
        'all_user':all_user
    })

@login_required
def multi_task_log_detail(request,task_id):

    log_obj = models.Task.objects.get(id=task_id)

    return render(request,'multi_task_log_detail.html',{'log_obj':log_obj})

@login_required
def multitask_task_action(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        m = host_mgr_utils.MultiTask(action,request)
        res = m.run()

        return  HttpResponse(json.dumps(res))

@login_required
def multitask_res(request):
    multi_task = host_mgr_utils.MultiTask('get_task_result',request)
    task_result = multi_task.run()
    return HttpResponse(task_result)


@login_required
def token_gen(request):
    #token_type = request.POST.get('token_type')
    token = utils.Token(request)
    token_key = token.generate()

    return HttpResponse(token_key)

@login_required
def personal(request):
    if request.method == 'POST':
        msg = {}
        old_passwd = request.POST.get('old_passwd')

        new_password = request.POST.get('new_passwd')
        user = authenticate(username=request.user.email,password=old_passwd)
        if user is not None:
            request.user.set_password(new_password)
            request.user.save()
            msg['msg'] = 'Password has been changed!'
            msg['res'] = 'success'
        else:
            msg['msg'] = 'Old password is incorrect!'
            msg['res'] = 'failed'

        return HttpResponse(json.dumps(msg))
    else:
        return render(request,'personal.html',{'info_form':userform.UserProfileForm()})