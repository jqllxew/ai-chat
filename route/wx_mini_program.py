import requests
from flask import request, Blueprint
from mongo import db
from config import wx_mini_program as wx_mapp_conf

mini_program_api = Blueprint(name="wx_mini_program_api", import_name=__name__, url_prefix='/wx-app')


@mini_program_api.route('/<str:code>/login', methods=['GET'])
def login(code):
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {
        'appid': wx_mapp_conf['appid'],
        'secret': wx_mapp_conf['secret'],
        'js_code': code,
        'grant_type': 'authorization_code'
    }
    res = requests.get(url, params=params)
    if res.status_code == 200 and 'openid' in res.json():
        openid = res.json()['openid']
        u = {"openid": openid}
        _u = db.u_wx.find_one(u)
        if _u is None:
            return db.u_wx.insert_one(u).inserted_id
        return _u["_id"]["$oid"]
