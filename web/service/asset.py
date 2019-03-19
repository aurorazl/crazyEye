#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json
from django.db.models import Q
from web import models
from com_utils.pager import PageInfo
from com_utils.response import BaseResponse
from django.http.request import QueryDict

from .base import BaseServiceList


class Asset(BaseServiceList):
    def __init__(self):
        # 查询条件的配置
        condition_config = [
            {'name': 'idc', 'text': 'IDC位置', 'condition_type': 'input'},
            {'name': 'system_type', 'text': '资产类型', 'condition_type': 'select', 'global_name': 'system_type_list'},
            {'name': 'name', 'text': '主机name', 'condition_type': 'input'}
        ]
        # 表格的配置
        table_config = [
            {
                'q': 'id',  # 用于数据库查询的字段，即Model.Tb.objects.filter(*[])
                'title': "ID",  # 前段表格中显示的标题
                'display': 1,  # 是否在前段显示，0表示在前端不显示, 1表示在前端隐藏, 2表示在前段显示
                'text': {'content': "{id}", 'kwargs': {'id': '@id'}},
                'attr': {}  # 自定义属性
            },
            {
                'q': 'name',
                'title': "主机名",
                'display': 1,
                'text': {'content': "{n}", 'kwargs': {'n': '@name'}},
                'attr': {'name': 'name', 'id': '@name', 'origin': '@name', 'edit-enable': 'true',
                         'edit-type': 'name'}
            },
            {
                'q': 'system_type',
                'title': "系统类型",
                'display': 1,
                'text': {'content': "{n}", 'kwargs': {'n': '@@system_type_list'}},
                'attr': {'name': 'system_type', 'id': '@system_type', 'origin': '@system_type', 'edit-enable': 'true',
                         'edit-type': 'select',
                         'global-name': 'system_type_list'}
            },
            {
                'q': 'ip_addr',
                'title': "IP",
                'display': 1,
                'text': {'content': "{n}", 'kwargs': {'n': '@ip_addr'}},
                'attr': {'name': 'ip_addr', 'id': '@ip_addr', 'origin': '@ip_addr', 'edit-enable': 'true',
                         'edit-type': 'input'}
            },
            {
                'q': 'port',
                'title': "端口",
                'display': 1,
                'text': {'content': "{n}", 'kwargs': {'n': '@port'}},
                'attr': {'name': 'port', 'id': '@port', 'origin': '@port', 'edit-enable': 'true',
                         'edit-type': 'input'}
            },
            {
                'q': 'idc_id',
                'title': "IDC",
                'display': 1,
                'text': {'content': "{n}", 'kwargs': {'n': '@@idc_list'}},
                'attr': {'name': 'idc_id', 'id': '@idc_id', 'origin': '@idc_id', 'edit-enable': 'true',
                         'edit-type': 'select',
                         'global-name': 'idc_list'}
            },
            {
                'q': 'created_at',
                'title': "创建时间",
                'display': 1,
                'text': {'content': "{n}", 'kwargs': {'n': '@created_at'}},
                'attr': {}
            },
            {
                'q': None,
                'title': "选项",
                'display': 1,
                'text': {
                    'content': "<a href='/asset-{nid}.html'>查看详细</a> | <a href='/edit-asset-{nid}.html'>编辑</a>",
                    'kwargs': {'nid': '@id'}},
                'attr': {}
            },
        ]
        # 额外搜索条件
        extra_select = {
        }
        super(Asset, self).__init__(condition_config, table_config, extra_select)

    #
    @property
    def system_type_list(self):
        result = map(lambda x: {'id': x[0], 'name': x[1]}, models.Host.system_type_choices)
        return list(result)
    #
    @property
    def idc_list(self):
        values = models.IDC.objects.only('id', 'name')
        result = map(lambda x: {'id': x.id, 'name': "%s" % (x.name)}, values)
        return list(result)
    #
    # @property
    # def business_unit_list(self):
    #     values = models.Department.objects.values('id', 'name')
    #     return list(values)

    @staticmethod
    def assets_condition(request):
        # 将 "name":["",""]转变为sql语句
        con_str = request.GET.get('condition', None)
        if not con_str:
            con_dict = {}
        else:
            con_dict = json.loads(con_str)

        con_q = Q()
        for k, v in con_dict.items():
            temp = Q()
            temp.connector = 'OR'
            for item in v:
                temp.children.append((k, item))
            con_q.add(temp, 'AND')

        return con_q

    def fetch_assets(self, request):
        response = BaseResponse()
        try:
            ret = {}
            conditions = self.assets_condition(request)
            asset_count = models.Host.objects.filter(conditions).count()
            page_info = PageInfo(request.GET.get('pager', None), asset_count)
            Host_list = models.Host.objects.filter(conditions).values(
                *self.values_list)[page_info.start:page_info.end]

            ret['table_config'] = self.table_config
            ret['condition_config'] = self.condition_config
            ret['data_list'] = list(Host_list)
            ret['page_info'] = {
                "page_str": page_info.pager(),
                "page_start": page_info.start,
            }
            ret['global_dict'] = {
                'system_type_list': self.system_type_list,
                'idc_list': self.idc_list,
            #     'business_unit_list': self.business_unit_list
            }
            response.data = ret
            response.message = '获取成功'
        except Exception as e:
            response.status = False
            response.message = str(e)

        return response

    @staticmethod
    def delete_assets(request):
        response = BaseResponse()
        try:
            delete_dict = QueryDict(request.body, encoding='utf-8')
            id_list = delete_dict.getlist('id_list')
            models.Host.objects.filter(id__in=id_list).delete()
            response.message = '删除成功'
        except Exception as e:
            response.status = False
            response.message = str(e)
        return response

    @staticmethod
    def put_assets(request):
        response = BaseResponse()
        try:
            response.error = []
            put_dict = QueryDict(request.body, encoding='utf-8')
            update_list = json.loads(put_dict.get('update_list'))
            error_count = 0
            for row_dict in update_list:
                nid = row_dict.pop('nid')
                num = row_dict.pop('num')
                try:
                    models.Host.objects.filter(id=nid).update(**row_dict)
                except Exception as e:
                    response.error.append({'num': num, 'message': str(e)})
                    response.status = False
                    error_count += 1
            if error_count:
                response.message = '共%s条,失败%s条' % (len(update_list), error_count,)
            else:
                response.message = '更新成功'
        except Exception as e:
            response.status = False
            response.message = str(e)
        return response

    @staticmethod
    def assets_detail(asset_id):
        response = BaseResponse()
        try:
            response.data = models.Host.objects.filter(id=asset_id).first()

        except Exception as e:
            response.status = False
            response.message = str(e)
        return response