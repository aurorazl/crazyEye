import os,sys
from backend import ssh_interactive
from  backend import db_conn
from crazyEye import settings
from web import models
from django.contrib import auth
import datetime
import django
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from backend import paramiko_ssh
class ArgvHandler(object):
    """接收用户参数,并调用相应的功能"""
    def __init__(self,sys_args):
        self.sys_args = sys_args

    def help_msg(self,error_msg=''):
        """打印帮助"""
        msgs = """
        %s
        run     run audit interactive interface
        help    show helps
        """ % error_msg
        exit(msgs)

    def print_msg(msg, msg_type, exit=False):
        if msg_type == 'err':
            print("\033[31;1m%s\033[0m" % msg)
        elif msg_type == 'normal':
            print("\033[32;1m%s\033[0m" % msg)
        elif msg_type == 'warning':
            print("\033[33;1m%s\033[0m" % msg)

        if exit:
            sys.exit()

    def call(self):
        """根据用户参数,调用对应的方法"""
        if len(self.sys_args) == 1:
            self.help_msg()

        if hasattr(self,self.sys_args[1]):
            func = getattr(self,self.sys_args[1])
            func()
        else:
            print("\033[31;1mInvalid argument!\033[0m")
            self.help_msg("没有方法:%s"% self.sys_args[1])

    def run(self):
        """启动用户交互程序"""
        self.token_auth()
        from  backend.ssh_interactive import SshHandler
        obj = SshHandler(self)
        # self.token_auth()
        obj.interactive(self.print_msg)

    def token_auth(self):
        count = 0
        while count <3:
            token = input("press ENTER if you don't have token, [input your token]:").strip()
            if len(token) == 0:return None
            filter_date = datetime.timedelta(seconds=-300)
            token_list = models.Token.objects.filter(token=token,date__gt=django.utils.timezone.now() +filter_date)
            if len(token_list) >0:
                if len(token_list) >1:
                    print("Found more than 1 matched tokens,I cannot let you login,please contact your IT guy!")
                else: #auth correct
                    bind_host_obj = token_list[0].host
                    self.login_user = token_list[0].user
                    self.user_id = token_list[0].user.id

                    self.print_msg("--- logging host[%s@%s(%s)], be patient,it may takes a minute --- " %(bind_host_obj.host_user.username,bind_host_obj.host.hostname,bind_host_obj.host.ip_addr),'normal')
                    try:
                        #ssh_interactive.login(self,bind_host_obj)
                        paramiko_ssh.ssh_connect(self,bind_host_obj)
                        self.print_msg('Bye!','warning',exit=True)
                    except Exception as e:
                        print(e)
                    finally:
                        self.flush_audit_log(bind_host_obj)
            else:
                count +=1
                print("Invalid token,got %s times to try!" % (3-count))
        else:
            sys.exit("Invalid token, too many attempts,exit.")

    def flush_audit_log(self,h):
        for log in self.cmd_logs:
            row = models.AuditLog(
                    user = self.login_user,
                    host = h,
                    log_type = log[2],
                    content = log[1],
                    date =  log[0]
                )
            row.save()
        self.cmd_logs =[]
        return True