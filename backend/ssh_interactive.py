from django.contrib.auth import authenticate
from backend import paramiko_ssh
from web import models
import django
import sys
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from crazyEye import settings

class SshHandler(object):
    """堡垒机交互脚本"""

    def __init__(self,argv_handler_instance):
        self.argv_handler_instance = argv_handler_instance
        self.models = models
        self.cmd_logs = []
        self.django_settings = settings

    def auth(self):
        """认证程序"""
        count = 0
        while count < 3:
            username = input("堡垒机账号:").strip()
            password = input("Password:").strip()
            user = authenticate(username=username,password=password)
            try:
                if user is not None:  # pass authentication
                    if user.valid_begin_time and user.valid_end_time:
                        if django.utils.timezone.now() > user.valid_begin_time and django.utils.timezone.now() < user.valid_end_time:
                            self.user = user
                            self.user_id = user.id
                            return True
                        else:
                            sys.exit("\033[31;1mYour account is expired,please contact your IT guy for this!\033[0m")
                    else:
                        sys.exit("\033[31;1mYour account is expired,please contact your IT guy for this!\033[0m")

                else:
                    print("\033[31;1mInvalid username or password!\033[0m")
                    count += 1
            except ObjectDoesNotExist:
                sys.exit(
                    "\033[31;1mhaven't set CrazyEye account yet ,please login http://localhost:8000/admin find 'CrazyEye账户' and create an account first!\033[0m")
        else:
            sys.exit("Invalid username and password, too many attempts,exit.")


    def interactive(self,log):
        """启动交互脚本"""
        if self.auth():
            print("Ready to print all the authorized hosts...to this user ...")
            while True:
                try:
                    host_group_list = self.user.host_groups.select_related().all()
                    for index,host_group_obj in enumerate(host_group_list):
                        print("%s.\t%s[%s]"%(index,host_group_obj.name, host_group_obj.host_to_remote_users.count()))
                    print("z.\t未分组主机[%s]" % (self.user.host_to_remote_users.select_related().count()))

                    choice = input("请选择主机组>>:").strip()
                    if choice.isdigit():
                        choice = int(choice)
                        if choice < len(host_group_list):
                            selected_host_group  = host_group_list[choice]
                        else:
                            log("No this option!", 'err')
                    elif choice == 'z':
                        selected_host_group = self.user

                    while True:
                        host_list = selected_host_group.host_to_remote_users.select_related().all()
                        for index,host_to_user_obj in enumerate(host_list):
                            print("%s.\t%s" % (index, host_to_user_obj))

                        choice = input("请选择主机>>:").strip()
                        if choice.isdigit():
                            choice = int(choice)
                            if choice < len(host_list):
                                selected_host_to_user_obj = host_list[choice]
                                print("going to logon  %s" % selected_host_to_user_obj )
                                try:
                                    paramiko_ssh.ssh_connect(self, selected_host_to_user_obj )
                                except Exception as e:
                                    print("\033[31;1m%s\033[0m" % e)
                                finally:
                                    self.flush_audit_log(selected_host_to_user_obj)
                            else:
                                log("No this option!", 'err')
                        if choice == "b":
                            break
                        elif choice == 'exit':
                            log('Bye!', 'warning', exit=True)
                except (KeyboardInterrupt, EOFError):
                    log("input 'exit' to logout!", 'err')
                except UnicodeEncodeError as e:
                    log("%s, make sure you terminal supports utf8 charset!" % str(e), 'err', exit=True)

    @transaction.atomic
    def flush_audit_log(self,h):
        for log in self.cmd_logs:
            row = models.AuditLog(
                    user = self.user,
                    host = h,
                    log_type = log[2],
                    content = log[1],
                    date =  log[0]
                )
            row.save()
        self.cmd_logs =[]
        return True