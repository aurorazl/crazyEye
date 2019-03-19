#_*_coding:utf-8_*_

import os,sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crazyEye.settings")
base_dir = '/'.join(os.path.abspath(os.path.dirname(__file__)).split("/")[:-1])
sys.path.append(base_dir)
import django
django.setup()

from web import models