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



@bp.route("/api/afdian_pay",methods=['POST'])
def afdian_pay():
    if request.is_json :
        CommonUtils.format_json_log(current_app.logger.info,request.json)
    return CommonUtils.json_response({"ec":200,"em":"ok"})