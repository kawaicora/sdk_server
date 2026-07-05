# -*- coding: utf-8 -*-
import json
from flask import Response,Blueprint, current_app,request
import requests


def get_real_ip():
    """
    获取客户端真实IP
    支持:
        Cloudflare CDN
        Cloudflare Tunnel
        FRP
        Nginx Reverse Proxy
        Direct Connection
    """

    # Cloudflare
    ip = request.headers.get("CF-Connecting-IP")
    if ip:
        return ip

    # 标准反向代理
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()

    # Nginx
    ip = request.headers.get("X-Real-IP")
    if ip:
        return ip

    # 直连
    return request.remote_addr

bp = Blueprint('root', __name__)


@bp.route('/<path:url_path>',methods=['GET','POST'])
def last_roue(url_path):
    return Response(json.dumps({"code":-1}), status=404, content_type='application/json')


@bp.before_request
def before_request():
    ip = get_real_ip()

    # r = requests.get(
    #     f"https://ipwho.is/{ip}",
    #     timeout=5
    # )

    current_app.logger.info(f"****请求开始: {ip}  {request.path} \n******")
# 注册服务
import app.route.dispatch_service
import app.route.account_service
import app.route.view_service
import app.route.socketio_common_services
import app.route.webrtc_service
import app.route.chat_service
import app.route.sync_service
import app.route.whip_service
import app.route.shop_service
import app.route.device_controller_service