# -*- coding: utf-8 -*-
import asyncio
import socketio
import json
import uuid
from flask import Response, jsonify,current_app, abort, jsonify, request
from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription, MediaStreamTrack,RTCIceCandidate
from flask_socketio import emit, join_room
from app.extensions import socketio
from app.route import bp
from app.settings import DefaultConfig
from app.route.webrtc_service import user_sessions
# 存储WHIP会话信息：resource_id -> {peer_connection, sdp}
whip_sessions = {}
obs_answer_response = {}
obs_answer_gather_complate = asyncio.Event()
active_connections = {}

# 向客户端发送响应消息
async def create_peer_connection(resource_id, room_id):
    try:
        current_app.logger.info(f"Creating peer connection for {resource_id} in room {room_id}")
        
        # 创建RTCPeerConnection配置
        configuration = RTCConfiguration()
        configuration.iceServers = []
        # 异步添加ICE服务器（避免同步循环堵塞，虽然这里逻辑简单，但保持异步思维）
        for ice_server in DefaultConfig.ICE_SERVERS['iceServers']:
            try:
                urls = ice_server['urls']
                username = ice_server.get('username')
                credential = ice_server.get('credential')
                # 构造ICE服务器对象（轻量操作，无需异步）
                ice_server_obj = RTCIceServer(
                    urls=urls,
                    username=username,
                    credential=credential
                )
                configuration.iceServers.append(ice_server_obj)
            except Exception as e:
                current_app.logger.error(f"Error adding ICE server: {str(e)}")
    
    # 创建PeerConnection（核心对象，本身是异步兼容的）
        pc = RTCPeerConnection(configuration)

        # ICE候选收集完成事件（仅用于标记状态，不强制等待）
        gather_complete = asyncio.Event()

        # --------------------------
        # 关键优化1：所有回调函数异步化
        # 避免同步函数堵塞事件循环
        # --------------------------
        
        @pc.on('connectionstatechange')
        async def on_connectionstatechange():  # 改为async函数
            current_app.logger.info(f"Connection state changed to {pc.connectionState} for {resource_id}")
            if pc.connectionState == 'failed':
                current_app.logger.error(f"Connection failed for {resource_id}")
                # 异步清理资源（即使简单操作，也保持异步思维）
                if resource_id in whip_sessions:
                    del whip_sessions[resource_id]
        
        @pc.on('iceconnectionstatechange')
        async def on_iceconnectionstatechange():  # 改为async函数
            current_app.logger.info(f"ICE connection state changed to {pc.iceConnectionState} for {resource_id}")
            if pc.iceConnectionState == 'failed':
                current_app.logger.error(f"ICE connection failed for {resource_id}")

        @pc.on('icegatheringstatechange')
        async def on_icegatheringstatechange():  # 改为async函数
            current_app.logger.info(f"ICE gathering state changed to {pc.iceGatheringState} for {resource_id}")
            if pc.iceGatheringState == "complete":
                current_app.logger.info(f"ICE gathering completed for {resource_id}")
                gather_complete.set()  # 仅标记事件，不强制等待
        
        @pc.on('signalingstatechange')
        async def on_signalingstatechange():  # 改为async函数
            current_app.logger.info(f"signaling state change {pc.signalingState}")

        @pc.on('track')
        async def on_track(track):  # 改为async函数（关键！处理轨道可能有耗时操作）
            try:
                current_app.logger.info(f"Received {track.kind} track from {resource_id}")
                current_app.logger.info(f"Received {track.kind} track from {resource_id}")
                # 获取当前会话的房间ID
                room_id = whip_sessions[resource_id]['room_id']
        
                # 遍历房间内所有其他客户端
                for client_id, client_pc in active_connections.get(room_id, {}).items():
                    if client_id != resource_id:  # 不要转发给自己
                        # 创建新的发送轨道并复制原轨道内容
                        if track.kind == 'video':
                            # 查找或创建视频发送轨道
                            video_sender = next(
                                (sender for sender in client_pc.getSenders() if sender.track and sender.track.kind == 'video'),
                                None
                            )
                            if not video_sender:
                                video_sender = client_pc.addTrack(track)
                            else:
                                await video_sender.replaceTrack(track)
                                
                        elif track.kind == 'audio':
                            # 查找或创建音频发送轨道
                            audio_sender = next(
                                (sender for sender in client_pc.getSenders() if sender.track and sender.track.kind == 'audio'),
                                None
                            )
                            if not audio_sender:
                                audio_sender = client_pc.addTrack(track)
                            else:
                                await audio_sender.replaceTrack(track)
                                
            except Exception as e:
                current_app.logger.error(f"Error forwarding track: {str(e)}")
   
        
        return pc, gather_complete
    
    except Exception as e:
        current_app.logger.error(f"Error creating peer connection: {str(e)}")
        raise


##################################################################

@bp.route('/whip/v1/<room_id>', methods=['POST'])
async def whip_v1_endpoint(room_id):
    try:
        resource_id = str(uuid.uuid4())
        offer_sdp = request.get_data(as_text=True)
        current_app.logger.info(f"New WHIP request for room {room_id}, resource {resource_id}")

        # 创建对等连接
        pc, gather_complete = await create_peer_connection(resource_id, room_id)
        
        # 存储会话信息
        whip_sessions[resource_id] = {
            'peer_connection': pc,
            'room_id': room_id,
            'sdp': offer_sdp,
            'gather_complete': gather_complete
        }
        
        try:
            # 设置远程描述(Offer)
            offer = RTCSessionDescription(sdp=offer_sdp, type='offer')
            await pc.setRemoteDescription(offer)
            
            # 创建并设置本地Answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)

            # 转发Offer给客户端（如需）
            emit('offer', {
                'resource_id': resource_id,
                'offer': {'sdp': offer_sdp, 'type': 'offer'}
            })

            # 关键修改：不等待ICE收集完成，直接返回初步SDP
            # （利用Trickle ICE后续补充候选，避免OBS超时）
            headers = {
                'Location': f'/whip/{room_id}/{resource_id}',
                'Content-Type': 'application/sdp'
            }

            current_app.logger.info(f"Returning SDP answer (ICE may still be gathering) for {resource_id}")
            return Response(pc.localDescription.sdp, 201, headers=headers)
            
        except Exception as e:
            current_app.logger.error(f"Error in WebRTC handshake: {str(e)}")
            if resource_id in whip_sessions:
                del whip_sessions[resource_id]
            raise
            
    except Exception as e:
        current_app.logger.error(f"Error in WHIP endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


##################################################################


@bp.route('/whip/<room_id>/<resource_id>', methods=['PATCH'])
async def whip_trickle_ice(room_id, resource_id):
    if resource_id not in whip_sessions:
        abort(404, "Resource not found")
    
    pc = whip_sessions[resource_id]['peer_connection']
    candidate_data = request.get_json()
    
    # 解析并添加ICE候选
    try:
        candidate = RTCIceCandidate(
            foundation=candidate_data['foundation'],
            component=candidate_data['component'],
            priority=candidate_data['priority'],
            ip=candidate_data['ip'],
            protocol=candidate_data['protocol'],
            port=candidate_data['port'],
            type=candidate_data['type']
        )
        await pc.addIceCandidate(candidate)
        return Response(status=204)
    except Exception as e:
        current_app.logger.error(f"Error adding ICE candidate: {str(e)}")
        return jsonify({'error': str(e)}), 400






#########################################################################################

@socketio.on('obs-answer')
def obs_answer(data):
    resource_id = data.get('resource_id')
    if not resource_id or resource_id not in whip_sessions:
        current_app.logger.error(f"Invalid resource ID in obs-answer: {resource_id}")
        return
        
    answer_data = data.get('answer')
    if not answer_data or 'sdp' not in answer_data:
        current_app.logger.error(f"Invalid answer data from OBS")
        return
        
    session = whip_sessions[resource_id]
    pc = session['peer_connection']
    
    try:
        # 设置远程描述(Answer)
        answer = RTCSessionDescription(sdp=answer_data['sdp'], type='answer')
        asyncio.ensure_future(pc.setRemoteDescription(answer))
        
        current_app.logger.info(f"Successfully set remote answer for {resource_id}")
    except Exception as e:
        current_app.logger.error(f"Error setting remote answer: {str(e)}")