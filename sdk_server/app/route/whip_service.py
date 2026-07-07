# -*- coding: utf-8 -*-
import asyncio
import threading
from typing import Dict
import socketio
import json
import uuid
from app.utils.CommonUtils import *
from flask import Response, jsonify,current_app, abort, jsonify, request
from aiortc import RTCConfiguration, RTCIceServer, RTCPeerConnection, RTCSessionDescription, MediaStreamTrack,RTCIceCandidate
from flask_socketio import emit, join_room
from app.extensions import socketio
from app.route import bp
from app.settings import DefaultConfig
from app.route.webrtc_service import user_sessions,get_ice_servers
from aiortc.contrib.media import MediaRecorder
from aiortc.contrib.media import MediaRelay
# 存储WHIP会话信息：resource_id -> {peer_connection, sdp}
whip_sessions = {}
ice_servers_cache = None
webrtc_loop = asyncio.new_event_loop()
relay:MediaRelay = MediaRelay()
threading.Thread(
    target=webrtc_loop.run_forever,
    daemon=True
).start()


def webrtc_exec(coro):
    future = asyncio.run_coroutine_threadsafe(
        coro,
        webrtc_loop
    )
    return future.result()

def parse_ice_services_config(iceservers: Dict) -> RTCConfiguration:
    """
    将如下结构的 dict 转换为 RTCConfiguration：

    {
      "iceServers": [
        {
          "urls": ["stun:...", "turn:..."],
          "username": "...",          # optional
          "credential": "...",        # optional
          "credentialType": "..."     # ignored
        }
      ],
      "bundlePolicy": "max-bundle"    # optional
    }
    """

    if not isinstance(iceservers, dict):
        raise TypeError("iceservers must be a dict")

    raw_servers = iceservers.get("iceServers")
    if not isinstance(raw_servers, list):
        raise ValueError("iceservers['iceServers'] must be a list")

    ice_servers: List[RTCIceServer] = []

    for s in raw_servers:
        if not isinstance(s, dict):
            raise TypeError(f"Invalid iceServer entry: {s}")

        urls = s.get("urls")
        if urls is None:
            raise ValueError("iceServer missing 'urls'")

        # urls 可以是 str 或 list[str]
        if isinstance(urls, str):
            urls = [urls]
        elif not isinstance(urls, list):
            raise TypeError("iceServer['urls'] must be str or list[str]")

        ice_servers.append(
            RTCIceServer(
                urls=urls,
                username=s.get("username"),
                credential=s.get("credential"),
                credentialType=s.get("credentialType", "password"),
            )
        )

    bundle_policy = iceservers.get("bundlePolicy", "balanced")

    return RTCConfiguration(
        iceServers=ice_servers,
        bundlePolicy=bundle_policy
    )


def parse_candidate(candidate_line, sdp_mid=None, sdp_mline_index=None):

    # 去掉 a=candidate:
    if candidate_line.startswith("a="):
        candidate_line = candidate_line[2:]

    if candidate_line.startswith("candidate:"):
        candidate_line = candidate_line[10:]


    parts = candidate_line.split()

    foundation = parts[0]
    component = int(parts[1])
    protocol = parts[2].lower()
    priority = int(parts[3])
    ip = parts[4]
    port = int(parts[5])

    typ_index = parts.index("typ")
    typ = parts[typ_index + 1]


    return RTCIceCandidate(
        foundation=foundation,
        component=component,
        protocol=protocol,
        priority=priority,
        ip=ip,
        port=port,
        type=typ,
        sdpMid=sdp_mid,
        sdpMLineIndex=sdp_mline_index,
    )


async def create_peer_connection(resource_id, room_id,iceservers):
    try:
        current_app.logger.info(f"Creating peer connection for {resource_id} in room {room_id}")
        
        # 创建RTCPeerConnection配置
        configuration = parse_ice_services_config(iceservers)
    
    # 创建PeerConnection（核心对象，本身是异步兼容的）
        pc = RTCPeerConnection(configuration)
        whip_sessions[resource_id]['pc'] = pc
        recorder = MediaRecorder(f"{secrets.token_hex(16)}.mp4")
        @pc.on('connectionstatechange')
        async def on_connectionstatechange():  # 改为async函数
            current_app.logger.info(f"Connection state changed to {pc.connectionState} for {resource_id}")
            if pc.connectionState == 'connected' :
                # await recorder.start()
                pass
            if pc.connectionState == 'failed':
                current_app.logger.error(f"Connection failed for {resource_id}")
                # 异步清理资源（即使简单操作，也保持异步思维）
                if resource_id in whip_sessions:
                    del whip_sessions[resource_id]
            if pc.connectionState == "closed":
                # await recorder.stop()
                pass
        
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
              
        
        @pc.on('signalingstatechange')
        async def on_signalingstatechange():  # 改为async函数
            current_app.logger.info(f"signaling state change {pc.signalingState}")

        @pc.on('track')
        async def on_track(track: MediaStreamTrack):  #收到远程视频
            try:
                res = 0
                current_app.logger.info(f"Received {track.kind} track from {resource_id}")
                relay_track:MediaStreamTrack = relay.subscribe(track)
                if track.kind == 'video':
                    whip_sessions[resource_id]['video'] = relay_track
                elif track.kind == 'audio':
                    whip_sessions[resource_id]['audio'] = relay_track
                
                async def _loop_track(relay_track:MediaStreamTrack):
                    while True:
                        frame = await relay_track.recv()
                        current_app.logger.info(
                            f"{relay_track.kind} frame {frame}"
                        )
                asyncio.create_task(
                    _loop_track(relay_track)    
                )
                
                # recorder.addTrack(track)

                    
            except Exception as e:
                current_app.logger.error(f"Error forwarding track: {str(e)}")
   
        
        return pc
    
    except Exception as e:
        current_app.logger.error(f"Error creating peer connection: {str(e)}")
        raise



##################################################################

@bp.route('/api/whip/<room_id>', methods=['POST'])
async def whip_v1_endpoint(room_id):
    try:
        scheme = request.scheme    
        resource_id = str(uuid.uuid4())
        offer_sdp = request.get_data(as_text=True)
        # 存储会话信息
        whip_sessions[resource_id] = {
            'room_id': room_id,
           
        }
        current_app.logger.info(f"New WHIP request for room {room_id}, resource {resource_id}")
        iceservers = get_ice_servers()
        # 创建对等连接
        # pc = await create_peer_connection(resource_id, room_id,iceservers)
        pc = webrtc_exec(create_peer_connection(resource_id, room_id,iceservers))
        try:
            # current_app.logger.info(f"offer sdp \n \n {offer_sdp}")
            #接收端逻辑
            offer = RTCSessionDescription(sdp=offer_sdp, type='offer')
            whip_sessions[resource_id]['offer'] = offer_sdp
            # emit('offer', {
            #     'resource_id': resource_id,
            #     'offer': {'sdp': offer_sdp, 'type': 'offer'}
            # })
            
            # await pc.setRemoteDescription(offer)
            webrtc_exec(pc.setRemoteDescription(offer))

            # answer = await pc.createAnswer()
            answer = webrtc_exec(pc.createAnswer())
            # current_app.logger.info(f"answer sdp \n \n {answer.sdp}")
            whip_sessions[resource_id]['answer'] = answer.sdp
            # await pc.setLocalDescription(answer)
            webrtc_exec(pc.setLocalDescription(answer))
            # offer发到接收端     
            # emit('answer', {
            #     'resource_id': resource_id,
            #     'answer': {'sdp': offer_sdp, 'type': 'offer'}
            # })
           
            # 关键修改：不等待ICE收集完成，直接返回初步SDP
            # （利用Trickle ICE后续补充候选，避免OBS超时）
            links = CommonUtils.ice_servers_to_link_header(iceservers)
            headers = {
                'Link':links[4],
                'Location': f'https://www.kawaimoe.org/api/whip/{room_id}/{resource_id}',
                'Content-Type': 'application/sdp',
                "Accept-Patch": "application/trickle-ice-sdpfrag"
            }
            rsp:Response = Response(pc.localDescription.sdp, 201, headers=headers) 
            current_app.logger.info(f"pc.localDescription sdp \n \n {pc.localDescription.sdp}")
            current_app.logger.info(f"Returning SDP answer (ICE may still be gathering) for {resource_id}")
            return rsp
            
        except Exception as e:
            current_app.logger.error(f"Error in WebRTC handshake: {str(e)}")
            if resource_id in whip_sessions:
                del whip_sessions[resource_id]
            return Response("", 502)
            
    except Exception as e:
        current_app.logger.error(f"Error in WHIP endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route(
    '/api/whip/<room_id>/<resource_id>',
    methods=['PATCH']
)
async def whip_patch(room_id, resource_id):

    session = whip_sessions.get(resource_id)

    if not session:
        return Response(status=404)


    pc = session["pc"]

    sdpfrag = request.get_data(as_text=True)

    current_app.logger.info(
        f"PATCH ICE\n{sdpfrag}"
    )


    current_mid = None
    mline_index = 0


    for line in sdpfrag.splitlines():

        if line.startswith("a=mid:"):
            current_mid = line[6:]


        elif line.startswith("a=candidate:"):

            candidate = parse_candidate(
                line,
                current_mid,
                mline_index
            )

            # await pc.addIceCandidate(candidate)
            webrtc_exec(pc.addIceCandidate(candidate))


        elif line.startswith("m="):
            mline_index += 1


    return Response(status=204)

##################################################################


@bp.route('/api/whip/<room_id>/<resource_id>', methods=['DELETE'])
async def whip_delete_session(room_id, resource_id):
    current_app.logger.info(f"WHIP DELETE for room {room_id}, resource {resource_id}")

    session = whip_sessions.get(resource_id)
    if not session:
        current_app.logger.warning(f"DELETE called for non-existent resource {resource_id}")
        return Response(status=404)

    # 房间一致性校验（WHIP 推荐）
    if session.get("room_id") != room_id:
        current_app.logger.warning(
            f"Room mismatch: session={session.get('room_id')}, path={room_id}"
        )
        return Response(status=404)

    pc = session.get("pc")
    if pc:
        try:
            
            # await pc.close()
            webrtc_exec(pc.close())
        except Exception as e:
            current_app.logger.warning(f"Error closing PeerConnection: {e}")

    # 清理会话
    del whip_sessions[resource_id]

    current_app.logger.info(f"WHIP session {resource_id} deleted successfully")
    return Response(status=204)

