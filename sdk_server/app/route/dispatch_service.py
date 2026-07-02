# -*- coding:utf-8 -*-
import base64
import requests
from app.route import bp
from flask import request, current_app
from app.settings import *
import datetime
import eyed3
from app.utils.CommonUtils import *
import secrets
from app.utils.ErrorCode import ErrorCode
from app.extensions import *

#https://afdian.com/api/my/profile   如果你登陆了 可以直接访问这个获得用户信息json

#https://afdian.com/api/user/get-profile?user_id=5386c44a0b1811edb2d252540025c377  获取特定用户的 信息

@bp.route("/api/afdian_pay",methods=['POST'])
def afdian_pay():
    if request.is_json :
        if request.json["ec"] != 200:
            current_app.logger.info("订单数据错误")
            return CommonUtils.json_response(request.get_json())
        current_app.logger.info("订单数据")
        CommonUtils.format_json_log(current_app.logger.info,request.get_json())
        rsp = requests.get(f"https://afdian.com/api/user/get-profile?user_id={request.get_json()['data']['order']['user_id']}")
        if rsp.status_code != 200:
            current_app.logger.info("获取用户信息失败")
            return CommonUtils.json_response({"ec":-1,"em":"get userinfo fail"})
        current_app.logger.info("订单用户信息")
        CommonUtils.format_json_log(current_app.logger.info,rsp.json())
    return CommonUtils.json_response({"ec":200,"em":"ok"})