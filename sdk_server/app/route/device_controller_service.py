import asyncio
import secrets
import time
import aiohttp
from flask import Response, request, current_app
import os
from datetime import datetime
from threading import Thread
from flask_socketio import emit
from app.extensions import socketio, db
from datetime import datetime
from app.settings import DefaultConfig
from app.sql_class.Tables import Message
from app.utils.ErrorCode import *
from app.route import bp
from app.route.socketio_common_services import get_user_by_sid, user_sessions, rooms, get_room_by_sid, get_room_by_uid
from app.utils.LoggerManager import logger
# 设备信息存储（key: 设备MAC拼接字符串，value: 设备详细信息）
devices_info = {}




def remove_offline_devices():
    to_remove = []

    for mac, info in devices_info.items():
        sid = info.get("sid")
        # 没有 sid → 不处理
        if not sid:
            logger.info(f"→ 设备 {mac} 没有 sid 或 sid 为空")
            continue

        # 判断 sid 是否存在于在线用户
        is_online = any(sid == user.get("sid") for user in user_sessions)

        if not is_online:
            logger.info(f"→ 找不到在线用户，准备移除 SID: {sid}")
            to_remove.append(sid)

    # 第二轮：真正删除
    for sid in to_remove:
        remove_device_by_sid(sid)
        logger.info(f"设备已移除 SID: {sid}")

# 辅助函数：根据SID查找设备key
def get_device_key_by_sid(sid):
    for key, info in devices_info.items():
        if info.get('sid') == sid:
            return key
    return None

@socketio.on('switch-device-gpio')
def handle_switch_device_gpio(data):
    sid = request.sid
    c_user = get_user_by_sid(sid)
    if not c_user:
        current_app.logger.warning(f"切换GPIO失败：用户不存在 - SID: {sid}")
        return

    c_room = get_room_by_uid(c_user.get('uid'))
    if not c_room:
        current_app.logger.warning(f"切换GPIO失败：用户无房间 - SID: {sid}")
        return

    # 从数据中获取设备key和GPIO（前端已改为传递key）
    device_key = data.get("target")
    gpio = data.get("gpio")
    
    # 参数验证
    if not device_key or gpio is None:
        current_app.logger.warning(f"切换GPIO失败：参数不全 - key: {device_key}, GPIO: {gpio}")
        return
    
    # 查找设备当前SID
    device_info = devices_info.get(device_key)
    if not device_info:
        current_app.logger.warning(f"切换GPIO失败：设备不存在 - key: {device_key}")
        return
    
    target_sid = device_info.get('sid')
    if not target_sid:
        current_app.logger.warning(f"切换GPIO失败：设备无SID - key: {device_key}")
        return

    # 转发控制命令
    emit("switch-device-gpio", {"gpio": gpio}, room=target_sid)
    current_app.logger.info(f"转发GPIO切换命令 - 设备key: {device_key}, GPIO: {gpio}, 目标SID: {target_sid}")

@socketio.on('set-device-gpio-value')
def handle_set_device_gpio_value(data):
    sid = request.sid
    c_user = get_user_by_sid(sid)
    if not c_user:
        current_app.logger.warning(f"设置GPIO值失败：用户不存在 - SID: {sid}")
        return

    c_room = get_room_by_uid(c_user.get('uid'))
    if not c_room:
        current_app.logger.warning(f"设置GPIO值失败：用户无房间 - SID: {sid}")
        return

    # 参数解析与验证
    device_key = data.get("target")
    gpio = data.get("gpio")
    value = data.get("value")
    
    if not all([device_key, gpio is not None, value is not None]):
        current_app.logger.warning(f"设置GPIO值失败：参数不全 - {data}")
        return
    
    if not isinstance(gpio, int) or not isinstance(value, int) or value not in (0, 1):
        current_app.logger.warning(f"设置GPIO值失败：参数无效 - GPIO: {gpio}, value: {value}")
        return

    # 查找设备SID
    device_info = devices_info.get(device_key)
    if not device_info or not device_info.get('sid'):
        current_app.logger.warning(f"设置GPIO值失败：设备无效 - key: {device_key}")
        return

    # 转发命令
    emit("set-device-gpio-value", {'gpio': gpio, 'value': value}, room=device_info['sid'])
    current_app.logger.info(f"转发GPIO设置命令 - 设备key: {device_key}, GPIO: {gpio}, 值: {value}")


# 前端加载时调用调用一次 后面不使用
@socketio.on('get-devices-info')
def handle_get_devices_info():
    sid = request.sid
    c_user = get_user_by_sid(sid)
    if not c_user:
        current_app.logger.warning(f"获取设备信息失败：用户不存在 - SID: {sid}")
        return

    c_room = get_room_by_uid(c_user.get('uid'))
    if not c_room:
        current_app.logger.warning(f"获取设备信息失败：用户无房间 - SID: {sid}")
        return
    
    # 发送设备信息给请求用户
    emit("devices-info", devices_info, room=sid)
    current_app.logger.debug(f"发送设备信息给用户 - SID: {sid}, 设备数量: {len(devices_info)}")

@socketio.on("device-heap")
def handle_device_heap(data):
    sid = request.sid
    c_user = get_user_by_sid(sid)
    if not c_user:
        current_app.logger.warning(f"设备HEAP上报失败：用户不存在 - SID: {sid}")
        return
    
    c_room = get_room_by_uid(c_user.get('uid'))
    if not c_room:
        current_app.logger.warning(f"设备HEAP上报失败：用户无房间 - SID: {sid}")
        return
    current_app.logger.warning(f"""
设备总计   HEAP：{data.get("total_heap")}KB
设备已使用 HEAP：{data.get("use_heap")}KB
设备剩余   HEAP：{data.get("free_heap")}KB
设备HEAP百分比 ：{str(data.get("heap_usage") ) }%
""")
        
# 设备连接成功时调用一次 以及GPIO状态切换时调用 
@socketio.on("device-status")
def handle_device_status(data):
    sid = request.sid
    c_user = get_user_by_sid(sid)
    if not c_user:
        current_app.logger.warning(f"设备状态上报失败：用户不存在 - SID: {sid}")
        return

    c_room = get_room_by_uid(c_user.get('uid'))
    if not c_room:
        current_app.logger.warning(f"设置GPIO值失败：用户无房间 - SID: {sid}")
        return
    # 解析设备MAC并生成唯一key
    device_mac = data.get("device_mac")
    if not device_mac:
        current_app.logger.warning(f"设备状态上报失败：无MAC地址 - SID: {sid}")
        return
    
    mac_char_arr = device_mac.split(":")
    device_key = "".join(mac_char_arr)

    # 更新设备信息（包含最新SID）
    data['sid'] = sid
    old_sid = devices_info.get(device_key, {}).get("sid")
    devices_info[device_key] = data

    # 记录SID变更日志
    if old_sid and old_sid != sid:
        current_app.logger.info(f"设备SID变更 - key: {device_key}, 旧SID: {old_sid}, 新SID: {sid}")

    # 发送设备信息给请求用户
    emit("devices-info", devices_info, room=c_room.get("room_id"))
    current_app.logger.debug(f"发送设备信息给用户 - SID: {sid}, 设备数量: {len(devices_info)}")
    current_app.logger.debug(f"设备状态更新 - key: {device_key}, IP: {data.get('device_ip')}, MAC: {device_mac}")


def remove_device_by_sid(sid):

    # 移除断开连接的设备
    device_key = get_device_key_by_sid(sid)
    if device_key:
        del devices_info[device_key]
        logger.info(f"设备断开连接，已移除 - key: {device_key}, SID: {sid}")
    else:
        current_app.logger.debug(f"用户断开连接 - SID: {sid}")
