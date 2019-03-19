#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse

from web.service import asset


class AssetListView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'asset_list.html')


class AssetJsonView(View):
    def get(self, request):
        obj = asset.Asset()
        response = obj.fetch_assets(request)
        return JsonResponse(response.__dict__)

    def delete(self, request):
        response = asset.Asset.delete_assets(request)
        return JsonResponse(response.__dict__)

    def put(self, request):
        response = asset.Asset.put_assets(request)
        return JsonResponse(response.__dict__)

class AssetDetailView(View):
    def get(self, request,asset_nid):
        response = asset.Asset.assets_detail(asset_nid)
        print(response)
        return render(request, 'asset_detail.html', {'response': response})

class AddAssetView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'add_asset.html')
