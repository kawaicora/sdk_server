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
from app.utils.ErrorCode import ErrorCode, get_response_string
from app.extensions import *



@bp.route('/api/v2/upload', methods=['POST'])
def api_chat_upload():
    # 检查请求中是否包含文件
    if 'file' not in request.files:
        return {'error': '未找到文件'}, 400
    element_name = ""
    file = request.files['file']

    # 检查文件名是否有效
    if file.filename == '':
        return {'error': '无效的文件名'}, 400

    # 获取当前日期
    now = datetime.now()
    year = str(now.year)
    month = str(now.month).zfill(2)
    day = str(now.day).zfill(2)

    # 创建存储路径
    base_dir = os.path.join(DefaultConfig.UPLOAD_FOLDER, year, month, day)
    os.makedirs(base_dir, exist_ok=True)

    # 生成随机文件名
    random_hex = secrets.token_hex(32)
    _, f_ext = os.path.splitext(file.filename)
    _type = "text"
    
    if "mp4" in f_ext.lower() or "webm" in f_ext.lower():
        _type = "video"
    elif "mp3" in f_ext.lower() or "wav" in f_ext.lower() or "ogg" in f_ext.lower():
        _type = "audio"
    elif "jpg" in f_ext.lower() or "png" in f_ext.lower() or "gif" in f_ext.lower() or "jpeg" in f_ext.lower() or "bmp" in f_ext.lower() or "svg" in f_ext.lower():
        _type = "image"

    else:
        
        return Response(get_response_string(-1),status=200,content_type="application/json")
        


    new_filename = random_hex + f_ext

    # 构建完整文件路径
    file_path = os.path.join(base_dir, new_filename)

    try:
        # 保存文件
        file.save(file_path)
        file_path_v2 ="/"+ file_path

        return Response(get_response_string(code = 0,data = {"type" : _type , 'message': file_path_v2}),status=200,content_type="application/json")
        
    except Exception as e:
        return Response(get_response_string(-1),status=200,content_type="application/json")
    






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