from django.db import models
import django
from web import auth

# Create your models here.

class Host(models.Model):
    """存储主机列表"""
    name = models.CharField(max_length=64,unique=True)
    ip_addr = models.GenericIPAddressField(unique=True)
    port = models.SmallIntegerField(default=22)
    idc = models.ForeignKey("IDC")
    system_type_choices = (
        ('0','Windows'),
        ('1', 'Linux/Unix')
    )
    system_type = models.CharField(choices=system_type_choices,max_length=32,default='1')
    enabled = models.BooleanField(default=True, help_text='主机若不想被用户访问可以去掉此选项')
    memo = models.CharField(max_length=128, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    #remote_users = models.ManyToManyField("RemoteUser")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = '主机'
        verbose_name_plural = '主机'

class HostGroup(models.Model):
    """存储主机组"""
    name = models.CharField(max_length=64,unique=True)
    memo = models.CharField(max_length=128, blank=True, null=True)
    host_to_remote_users = models.ManyToManyField("HostToRemoteUser")

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = '主机组'
        verbose_name_plural = '主机组'

class HostToRemoteUser(models.Model):
    """绑定主机和远程用户的对应关系"""
    host = models.ForeignKey("Host")
    remote_user = models.ForeignKey("RemoteUser")

    enabled = models.BooleanField(default=True)
    class Meta:
        unique_together = ("host", "remote_user")
        verbose_name = '主机与远程用户绑定'
        verbose_name_plural = '主机远程与用户绑定'

    def __str__(self):
        return "%s %s"%(self.host,self.remote_user)

class RemoteUser(models.Model):
    """存储远程要管理的主机的账号信息"""
    auth_type_choices = ((0,'ssh-password'),(1,'ssh-key'))
    auth_type = models.SmallIntegerField(choices=auth_type_choices,default=0,help_text='如果选择SSH/KEY，请确保你的私钥文件已在settings.py中指定')
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=64,blank=True,null=True,help_text='如果auth_method选择的是SSH/KEY,那此处不需要填写..')
    memo = models.CharField(max_length=128,blank=True,null=True)
    def __str__(self):
        return '%s(%s)' %(self.username,self.password)
    class Meta:
        verbose_name = '远程用户'
        verbose_name_plural = '远程用户'
        unique_together = ('auth_type','password','username')


class UserProfile(auth.AbstractBaseUser,auth.PermissionsMixin):
    """堡垒机账号"""
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=64, verbose_name="姓名")
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)

    department = models.ForeignKey('Department', verbose_name='部门', blank=True, null=True)

    host_to_remote_users = models.ManyToManyField("HostToRemoteUser",blank=True)
    host_groups = models.ManyToManyField("HostGroup",blank=True)

    memo = models.TextField('备注', blank=True, null=True, default=None)
    date_joined = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    valid_begin_time = models.DateTimeField(default=django.utils.timezone.now, help_text="yyyy-mm-dd HH:MM:SS")
    valid_end_time = models.DateTimeField(blank=True, null=True, help_text="yyyy-mm-dd HH:MM:SS")

    USERNAME_FIELD = 'email'    # 哪个字段当作用户名
    REQUIRED_FIELDS = ['name']  # 必须字段

    objects = auth.UserManager()    # 创建用户的方法

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    class Meta:
        verbose_name = 'CrazyEye账户'
        verbose_name_plural = 'CrazyEye账户'

        permissions = (
            ('web_access_dashboard', '可以访问 审计主页'),
            ('web_batch_cmd_exec', '可以访问 批量命令执行页面'),
            ('web_batch_batch_file_transfer', '可以访问 批量文件分发页面'),
            ('web_config_center', '可以访问 堡垒机配置中心'),
            ('web_config_items', '可以访问 堡垒机各配置列表'),
            ('web_invoke_admin_action', '可以进行admin action执行动作'),
            ('web_table_change_page', '可以访问 堡垒机各配置项修改页'),
            ('web_table_change', '可以修改 堡垒机各配置项'),
        )
class IDC(models.Model):
    """机房信息"""
    name = models.CharField(max_length=64,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'IDC'
        verbose_name_plural = 'IDC'

class SessionTrack(models.Model): #没用了的表

    date = models.DateTimeField(auto_now_add=True)
    closed = models.BooleanField(default=False)
    def __str__(self):
        return '%s' %self.id


class Session(models.Model):
    '''生成用户操作session id '''
    user = models.ForeignKey('UserProfile')
    bind_host = models.ForeignKey('HostToRemoteUser')
    tag = models.CharField(max_length=128,default='n/a')
    closed = models.BooleanField(default=False)
    cmd_count = models.IntegerField(default=0) #命令执行数量
    stay_time = models.IntegerField(default=0, help_text="每次刷新自动计算停留时间",verbose_name="停留时长(seconds)")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '<id:%s user:%s bind_host:%s>' % (self.id,self.user.email,self.bind_host.host)
    class Meta:
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'


class AuditLog(models.Model):
    """存储审计日志"""
    session = models.ForeignKey(SessionTrack,null=True,blank=True)
    user = models.ForeignKey("UserProfile",verbose_name="堡垒机账号",null=True,blank=True)
    host_to_remote_user = models.ForeignKey("HostToRemoteUser" ,null=True,blank=True)
    action_choices = (
        (0,'CMD'),
        (1,'Login'),
        (2,'Logout'),
        (3,'GetFile'),
        (4,'SendFile'),
        (5,'exception'),
    )
    log_type = models.SmallIntegerField(choices=action_choices,default=0)
    content = models.CharField(max_length=255,null=True,blank=True)
    date = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    memo = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return "%s %s" %(self.host_to_remote_user, self.content)
    class Meta:
        verbose_name = '审计日志old'
        verbose_name_plural = '审计日志old'

class Department(models.Model):
    name = models.CharField(max_length=64,unique=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = '部门'
        verbose_name_plural = '部门'

class Task(models.Model):
    """批量任务"""
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    task_type_choices = (('cmd','批量命令'),('file-transfer','文件传输'))

    task_type = models.CharField(choices=task_type_choices,max_length=64)
    content = models.CharField(max_length=255, verbose_name="任务内容")
    user = models.ForeignKey("UserProfile")
    hosts = models.ManyToManyField('HostToRemoteUser')
    expire_time = models.IntegerField(default=30)
    task_pid = models.IntegerField(default=0)
    note = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return "taskid:%s type:%s cmd: %s"%(self.id,self.task_type,self.content)
    class Meta:
        verbose_name = '批量任务'
        verbose_name_plural = '批量任务'

class TaskLogDetail(models.Model):
    """存储大任务子结果"""
    task = models.ForeignKey("Task")
    host_to_remote_user = models.ForeignKey("HostToRemoteUser")
    result = models.TextField(verbose_name="任务执行结果")

    status_choices = ((0,'initialized'),(1,'sucess'),(2,'failed'),(3,'timeout'))
    status = models.SmallIntegerField(choices=status_choices,default=0)
    note = models.CharField(max_length=100, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s %s"%(self.task,self.host_to_remote_user)
    class Meta:
        verbose_name = '批量任务日志'
        verbose_name_plural = '批量任务日志'

class Token(models.Model):
    user = models.ForeignKey(UserProfile)
    host = models.ForeignKey(HostToRemoteUser)
    token = models.CharField(max_length=64)
    date = models.DateTimeField(default=django.utils.timezone.now)
    expire = models.IntegerField(default=300)

    def __str__(self):
        return '%s : %s' % (self.host.host.ip_addr, self.token)
