# -*- coding: utf-8 -*-
from flask_socketio import emit
from app.route import bp
from flask import *
from uuid import UUID
from app.extensions import db,socketio
from app.settings import DefaultConfig
import requests
@socketio.on('cabbagedog-sync-connect')
def handle_sync_connect(data):
    current_app.logger.info(data)
    uuid = UUID('urn:uuid:12345678-1234-5678-1234-567812345678')
    emit('cabbagedog-sync-connected', {'uuid': str(uuid)})

model = {
    "amap_tencent_to_bd09ll": 1 ,
    "gps_to_bd09ll":2,
    "bd09ll_to_bd09mc":3,
    "bd09mc_to_bd09ll":4,
    "bd09ll_to_amap_tencent":5,
    "bd09mc_to_amap_tencent":6,
}

@socketio.on('user-location')
def handle_user_location(data):
    if DefaultConfig.BAIDU_MAP_AK != "" :
        rsp = requests.get(f"https://api.map.baidu.com/geoconv/v2/?coords={data['loc_info']['latitude']},{data['loc_info']['longitude']}&model={model.get("gps_to_bd09ll")}&ak={DefaultConfig.BAIDU_MAP_AK}")
        if rsp.status_code == 200:
            if rsp.json()['status'] == 0:
                data['loc_info']['bd09ll'] = {
                    "x":rsp.json()['result'][0]["x"],
                    "y":rsp.json()['result'][0]["y"]
                }
        
    emit('user-location', data, broadcast=True, include_self=True)

