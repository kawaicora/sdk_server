import LoggerManager from "/static/js/LoggerManager.js";
import VideoStream from "/static/js/VideoStream.js";
import SocketIOMaster from "/static/js/SocketIOMaster.js";
import Chat from "/static/js/Chat.js";
import PageManager from "/static/js/PageManager.js";
class WebRTC {
    constructor() {
        this.peerConnections = {};
        this.iceServers =  null; 
        this.logger = new LoggerManager("WebRTC", LoggerManager.LEVELS.ALL);
        this.selectDeviceUiStatus = false;
        
        PageManager.SwitchPage("room_list");
        
        SocketIOMaster.on('joined-room',this.HandleJoinRoom.bind(this));
        SocketIOMaster.on('user-joined-room', this.HandleJoinRoom.bind(this));
        SocketIOMaster.on('offer', this.HandleOffer.bind(this));
        SocketIOMaster.on('answer', this.HandleAnswer.bind(this));
        SocketIOMaster.on('ice-candidate', this.HandleIceCandidate.bind(this));
        SocketIOMaster.on('user-left-room', this.HandleLeftRoom.bind(this));
        SocketIOMaster.on('room-list-updated', this.HandleRoomListUpdated.bind(this));
        SocketIOMaster.on('room-users-updated', this.HandleRoomUserUpdate.bind(this));
        // 错误提示
        SocketIOMaster.on('error', (data) => {
            this.logger.log(`错误 :  ${data.msg} , event:${data.event} `);
            CommonUtils.MsgBox(`错误 :  ${data.msg}  `);
        });
        
        SocketIOMaster.on('connected', (data) => {
            this.logger.debug(`用户注册成功 ${JSON.stringify(data, null, 2)}`);
            
            this.EnumerateDevices();
            //初始化流
            VideoStream.GetAudioStream("default");
            VideoStream.GetEmptyVideoStream(); 
            

            $('#createRoomBtn').on('click', () => {
                const title = $('#roomTitle').val();
                if (title.length < 2 || !title) {
                    CommonUtils.MsgBox("检查标题字数是否2个以上，或者标题是否未填写");
                    return;
                }
                const room_id = "room_s_" + Date.now();
                SocketIOMaster.emit('create-room',{room_id:room_id,title:title,room_type:"webrtc"})
            });
            $('#videoSelect').on('change',this.HandleVideoSelect.bind(this));
            $('#audioSelect').on('change',this.HandleAudioSelect.bind(this));
            $('#capture_screen_button').on('click', () => {
                CommonUtils.MsgBox("屏幕共享功能如果使用系统音频就采集系统声音否则使用上一次的音频输入设备声音,如果上一次没有选择音频输入设备就不采集声音",10);
                this.HandleScreenSelect();
                

            });
            $('#switchBtn').on('click', () => {
                this.ShowSelectDevice();
            });
            
   
            
            
            setInterval(() => {
                for (var i = 0 ; i< $(`.remote-video-lable`).length ; i++){
                    var sid = $(`.remote-video-lable`).eq(i).attr("class").split("remote-video-lable-")[1]
                    if ($(`.remote-video-lable`)[i].innerText.indexOf(sid) != -1 ){
                    SocketIOMaster.emit('room_users_update',{room_id:sessionStorage.getItem("room")});   //  获取用户信息更新用户名
                    } 
                }
            
            }, 3000); // 
        });

       
    }

    async HandleScreenSelect (){
        await VideoStream.GetScreenStream();
        await this.ReplaceTrack();
    }
    async HandleAudioSelect (){
        const audioSelect = document.getElementById('audioSelect');
        await VideoStream.GetAudioStream(audioSelect.value);
        await this.ReplaceTrack();
    }

    async HandleVideoSelect (){
        const videoSelect = document.getElementById('videoSelect');
        await VideoStream.GetCameraStream(videoSelect.value);
        await this.ReplaceTrack();
    }

    async SwitchDevice(){
        await this.ReplaceTrack();
    }
    async GetIceConfig() {
        try {
            const response = await fetch('/api/ice_servers_config');
            this.iceServersConfig = await response.json();
            this.logger.debug(`ICE配置加载成功 ${JSON.stringify(this.iceServersConfig, null, 2)}`);
        } catch (error) {
            this.logger.error('加载ICE配置失败:', error);
        }
    }
    // 创建RTCPeerConnection
    async CreatePeerConnection(targetSid) {
        if (this.peerConnections[targetSid]) {
            this.logger.debug(`复用已存在的连接 targetSid=${targetSid}`);
            return this.peerConnections[targetSid];
        }
        this.logger.debug(`创建新连接 targetSid=${targetSid}, config=`, JSON.stringify(this.iceServersConfig, null, 2));
        
        const pc = new (window.RTCPeerConnection || 
                        window.webkitRTCPeerConnection || 
                        window.mozRTCPeerConnection || 
                        window.msRTCPeerConnection)(this.iceServersConfig);

        if (!pc) {
            alert('您的浏览器不支持 WebRTC，无法进行视频通话');
            console.error('浏览器不支持 RTCPeerConnection');
        }

        
        // 处理远程流
        pc.ontrack = (event) => {
            this.logger.debug(`收到远程流 targetSid=${targetSid}`);
            if (targetSid === sessionStorage.getItem("sid")) {
                this.logger.debug(`收到本地流 ${targetSid}，不处理`);
                return;
            }
            if (event.streams.length === 0) {
                this.logger.warn(`收到远程流 targetSid=${targetSid} 不包含流`);
                return;
            }
            event.streams[0].getAudioTracks().forEach(track => {
                this.logger.debug(`远程流包含音频轨道 targetSid=${targetSid}, trackId=${track.id}`);
                this.logger.debug(`信息 ${JSON.stringify(track.getSettings(), null, 2)}`);
            });
            event.streams[0].getVideoTracks().forEach(track => {
                this.logger.debug(`远程流包含视频轨道 targetSid=${targetSid}, trackId=${track.id}`);
                this.logger.debug(`信息 ${JSON.stringify(track.getSettings(), null, 2)}`);
            });
            this.AddRemoteVideo(targetSid, event.streams);
        };

        // 处理ICE候选
        pc.onicecandidate = (event) => {
            if (event.candidate) {
                this.logger.debug(`发送ICE候选 targetSid=${targetSid}`);
                SocketIOMaster.emit('ice-candidate', {
                    target: targetSid,
                    room_id: sessionStorage.getItem("room"),  // 新增：携带房间ID
                    candidate: {
                        address: event.candidate.address,
                        candidate: event.candidate.candidate,
                        component: event.candidate.component,
                        foundation: event.candidate.foundation,
                        port: event.candidate.port,
                        priority: event.candidate.priority,
                        protocol: event.candidate.protocol,
                        relatedAddress: event.candidate.relatedAddress,
                        relatedPort: event.candidate.relatedPort,
                        relayProtocol: event.candidate.relayProtocol,
                        sdpMLineIndex: event.candidate.sdpMLineIndex,
                        sdpMid: event.candidate.sdpMid,
                        tcpType: event.candidate.tcpType,
                        type: event.candidate.type,
                        url: event.candidate.url,
                        usernameFragment: event.candidate.usernameFragment
                    }
                });
            }
        };

        // 连接状态变化
        pc.onconnectionstatechange = () => {
            
            this.logger.debug(`连接状态变化 targetSid=${targetSid}, state=${pc.connectionState}`);

            switch (pc.connectionState) {
                case 'disconnected':
                case 'failed':
                case 'closed':
                    this.RemoveConnection(targetSid);

                    this.CreatePeerConnection(targetSid);
                    this.logger.debug(`尝试重新创建连接 targetSid=${targetSid}`);
                    break;
                default:
                    break;
            }
            SocketIOMaster.emit("on-connection-state-change",{
                target: targetSid,
                state: pc.connectionState
            })
        };

        // ICE连接状态变化
        pc.oniceconnectionstatechange = () => {
            
            this.logger.debug(`ICE连接状态变化 targetSid=${targetSid}, state=${pc.iceConnectionState}`);

        };

        // 信令状态变化
        pc.onsignalingstatechange = () => {
            this.logger.debug(`信令状态变化 targetSid=${targetSid}, state=${pc.signalingState}`);
        };

        this.peerConnections[targetSid] = pc;

        // 添加本地视频
        // await VideoStream.GetAudioStream("default");
        
        await this.AddTrack(pc);
        VideoStream.stream.getVideoTracks().forEach(track => {
            this.logger.debug(`获取视频流 info ${JSON.stringify(track.getSettings(), null, 2)}`);
        });
        VideoStream.stream.getAudioTracks().forEach(track => {
            this.logger.debug(`获取音频流 info ${JSON.stringify(track.getSettings(), null, 2)}`);
        });

        document.getElementById("localVideo").srcObject = VideoStream.stream
        return pc;
    }
    RemoveConnection(sid) {
        this.logger.warn(`连接失败，清理资源 targetSid=${sid}`);
        this.RemoveRemoteVideo(sid);
        const pc = this.peerConnections[sid];
        pc.close();
        delete this.peerConnections[sid];
    };
    EnforceStereo(sdp) {
        const lines = sdp.split('\r\n');
        let hasFmtp111 = false;

        for (let i = 0; i < lines.length; i++) {
            if (lines[i].startsWith('a=fmtp:111')) {
                hasFmtp111 = true;
                if (!lines[i].includes('stereo=1')) {
                    lines[i] += ';stereo=1;sprop-stereo=1';
                }
                break;
            }
        }

        // 极端情况：连 a=fmtp:111 都没有（基本不会发生）
        if (!hasFmtp111) {
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].startsWith('a=rtpmap:111 opus')) {
                    lines.splice(i + 1, 0, 'a=fmtp:111 minptime=10;useinbandfec=1;stereo=1;sprop-stereo=1');
                    break;
                }
            }
        }

        return lines.join('\r\n');
    }

    
    // 处理offer
    async HandleOffer(data) {
        if (data.from_sid === sessionStorage.getItem("sid")) {
            this.logger.debug(`忽略自己的offer from=${data.from_sid}`);
            return;
        }
        this.logger.debug(`收到offer from=${data.from_sid}`);

        try {
            let pc = this.peerConnections[data.from_sid];
            if (pc && pc.signalingState !== 'stable') {
                this.logger.debug(`重置现有连接 from=${data.from_sid}, state=${pc.signalingState}`);
                pc.close();
                delete this.peerConnections[data.from_sid];
                pc = null;
            }
            if (!pc) {
                pc = await this.CreatePeerConnection(data.from_sid);
            }
            if (pc.signalingState === 'have-remote-offer') {
                this.logger.debug(`回滚远程offer from=${data.from_sid}`);
                await pc.setRemoteDescription({ type: 'rollback' });
            }
            await pc.setRemoteDescription(data.offer);
            const answer = await pc.createAnswer();
            // answer.sdp = this.EnforceStereo(answer.sdp);
            await pc.setLocalDescription(answer);
            this.logger.debug(`处理offer完成 from=${data.from_sid}`);
            this.logger.debug(`offer内容: ${JSON.stringify(data.offer, null, 2)}`);
            this.logger.debug(`发送answer to=${data.from_sid}`);
            this.logger.debug(`answer内容: ${JSON.stringify(answer, null, 2)}`);
            SocketIOMaster.emit('answer', {
                target: data.from_sid,
                room_id: sessionStorage.getItem("room"),  // 新增：携带房间ID
                answer: answer
            });
        } catch (e) {
            this.logger.error(`处理offer失败 from=${data.from_sid}`, e);
           
        }
    }

    // 处理answer
    async HandleAnswer(data) {
        if (data.from_sid === sessionStorage.getItem("sid")) {
            this.logger.debug(`忽略自己的answer from=${data.from_sid}`);
            return;
        }
        this.logger.debug(`收到answer from=${data.from_sid}`);
        try {
            const pc = this.peerConnections[data.from_sid];
            if (pc && pc.signalingState === 'have-local-offer') {
                await pc.setRemoteDescription(data.answer);
                this.logger.debug(`Answer处理完成 from=${data.from_sid}`);
                this.logger.debug(`answer内容: ${JSON.stringify(data.answer, null, 2)}`);
            } else {
                this.logger.warn(`忽略answer，信令状态不正确 from=${data.from_sid}, state=${pc?.signalingState}`);
            }
        } catch (e) {
            this.logger.error(`处理answer失败 from=${data.from_sid}`, e);
        }
    }

    // 处理ICE候选
    async HandleIceCandidate(data) {
        if (data.from_sid === sessionStorage.getItem("sid")) {
            this.logger.debug(`忽略自己的candidate from=${data.from_sid}`);
            return;
        }
        this.logger.debug(`收到ICE候选 from=${data.from_sid}`);
        try {
            const pc = this.peerConnections[data.from_sid];
            if (pc && data.candidate ) {
                await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                this.logger.debug(`ICE候选添加完成 from=${data.from_sid}`);
                this.logger.debug(`candidate内容: ${JSON.stringify(data.candidate, null, 2)}`);
            }
        } catch (e) {
            this.logger.error(`处理ICE候选失败 from=${data.from_sid}`, e);
        }
    }

    GetKeyByValue(obj, targetValue) {
        for (let key in obj) {
            if (obj.hasOwnProperty(key) && obj[key] === targetValue) {
                return key;
            }
        }
        return null;
    }
    async AddTrack(pc){
        VideoStream.stream.getVideoTracks().forEach(track => {
            pc.addTrack(track, VideoStream.stream);
        });
        VideoStream.stream.getAudioTracks().forEach(track => {
            pc.addTrack(track, VideoStream.stream);
        });

        // 发送offer更新
        pc.createOffer().then(async offer => {
            // offer.sdp = this.EnforceStereo(offer.sdp);
            await pc.setLocalDescription(offer);
            const targetSid = this.GetKeyByValue(this.peerConnections, pc);
            if (targetSid) {
                this.logger.debug(`发送offer给${targetSid}`);
                SocketIOMaster.emit('offer', {
                    target: targetSid,
                    offer: offer,
                    room_id: sessionStorage.getItem("room")  // 新增：携带房间ID
                });
                this.logger.debug(`offer内容: ${JSON.stringify(offer, null, 2)}`);
            }
        });
    }
    // 替换音视频轨道
    async ReplaceTrack() {
        
        Object.values(this.peerConnections).forEach(pc => {

            


            // 替换视频轨道
            const videoSender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
            if (videoSender && VideoStream.stream) {
                const videoTrack = VideoStream.stream.getVideoTracks()[0];
                // 遍历媒体流中的所有视频轨道
                if (videoTrack) {
                    videoSender.replaceTrack(videoTrack);
                }
            }

            // 替换音频轨道
            const audioSender = pc.getSenders().find(s => s.track && s.track.kind === 'audio');
            if (audioSender && VideoStream.stream) {
                const audioTrack = VideoStream.stream.getAudioTracks()[0];
                if (audioTrack) {
                    audioSender.replaceTrack(audioTrack);
                }
            }

            // 发送offer更新
            pc.createOffer().then(async offer => {
                // offer.sdp = this.EnforceStereo(offer.sdp);
                await pc.setLocalDescription(offer);
                const targetSid = this.GetKeyByValue(this.peerConnections, pc);
                if (targetSid) {
                    this.logger.debug(`发送offer给${targetSid}`);
                    SocketIOMaster.emit('offer', {
                        target: targetSid,
                        offer: offer,
                        room_id: sessionStorage.getItem("room")  // 新增：携带房间ID
                    });
                    this.logger.debug(`offer内容: ${JSON.stringify(offer, null, 2)}`);
                }
            });
        });

        
    }


    async HandleJoinRoom(data){

        if (this.iceServers == null){
            await this.GetIceConfig()
        }
        if (data.sid === sessionStorage.getItem("sid")) {  //自己
            sessionStorage.setItem("room",data.room_id);
            PageManager.SwitchPage("video_chat");
            $('#remoteVideos').html(`
                <div class="bg-card border border-border rounded-lg shadow-md mb-2.5 w-full">
                    <div class="select-device-2 relative">
                        <video id="localVideo" autoplay playsinline muted style =" width:100%; height:auto"
                            class="w-full h-full bg-black m-0 object-cover rounded-t-lg">
                        </video>
                    </div>
                    <div class="local-video-lable px-2 py-2 border-t border-border text-text font-medium">
                        <i class="fa-solid fa-user mr-1.5"></i>本地视频 ${sessionStorage.getItem("sid")}
                    </div>
                </div>
            `);

            // 离开房间按钮事件（jQuery绑定）
            $('.exit-room-btn').off('click')
            $('.exit-room-btn').on('click', () => {
                $('#remoteVideos').html('');
                SocketIOMaster.emit('leave-room', { room_id: sessionStorage.getItem("room") });  // 与后端匹配
                this.logger.info("发送离开房间请求")
                sessionStorage.removeItem("room")
                // 如果是自己离开，更新UI
                if (data.sid === sessionStorage.getItem("sid")) {
                    sessionStorage.removeItem("room")
                    PageManager.SwitchPage("room_list")
                }
            });
             $('#localVideo').off('click')
             $('#localVideo').on('click', () => {
                this.ShowSelectDevice();
             });
            
        }
       
        await this.CreatePeerConnection(data.sid);
    }
    HandleLeftRoom(data){
        this.logger.debug(`用户离开房间 ${JSON.stringify(data, null, 2)}`);
        if (this.peerConnections[data.sid]) {
            this.peerConnections[data.sid].close();
            delete this.peerConnections[data.sid];
        }
        this.RemoveRemoteVideo(data.sid);
        // 如果是自己离开，更新UI
        if (data.sid === sessionStorage.getItem("sid")) {
            sessionStorage.removeItem("room")
            $('.room-select-container').removeClass('hidden');
            $('.video-chat-container').addClass('hidden');
        }
    }

    HandleRoomListUpdated(data){
        this.logger.debug(`房间列表更新: ${JSON.stringify(data, null, 2)}`);
        let appendHtml = '';
        data.forEach(e => {
            if(e.room_type == "webrtc"){
                appendHtml += `
                <div class="bg-card border border-border rounded-lg shadow-md overflow-hidden room-card" style = "width: 150px; height: 150px;"
                                    data-room-id="${e.room_id}"
                                    data-room-title="${e.title}" ">


                    <div class="video-container h-36 relative">
                        <img src="${e.cover || 'https://picsum.photos/130/150?random=1'}" alt="房间封面" class="w-full h-full object-cover">
                        <div id="${e.room_id}_room_hum_count" class="absolute bottom-1.5 right-1.5 bg-black/50 px-2 py-0.5 rounded-full text-xs text-white">
                            <i class="fa-solid fa-user mr-1"></i> ${e.user_count}
                        </div>
                        <h4 class="whitespace-nowrap overflow-hidden text-ellipsis font-medium text-text">${e.title}</h4>
                    </div>
                    
                </div>
                `;
            }
            
        });
    $('#roomGrid').html(appendHtml);
       $(".room-card")
        .on("mouseenter", function () {
            $(".room_info_layer").removeClass("hidden");
        })
        .on("mouseleave", function () {
            $(".room_info_layer").addClass("hidden");
        });
        document.querySelectorAll(".room-card")
        .forEach(btn => {

            btn.addEventListener("click", () => {

                this.JoinRoom(
                    btn.dataset.roomId,
                    btn.dataset.roomTitle
                );
            });

        });
    }
    

    HandleRoomUserUpdate(data){
        this.logger.debug(`房间用户更新: ${JSON.stringify(data, null, 2)}`);
        Object.keys(data.users).forEach(key => {
            try {
                $(`.remote-video-lable-${data.users[key]['sid']}`).html(`<i class="layui-icon" style="margin-right:5px;">&#xe60e;</i>远程用户: ${data.users[key]["username"]}`);
            } catch (e) {
                this.logger.warn("更新用户标签失败! uid=" + key);
            }
            if (data.users[key]['sid'] === sessionStorage.getItem("sid")) {
                $(`.local-video-lable`).html(`<i class="layui-icon" style="margin-right:5px;">&#xe60e;</i>本地视频: ${data.users[key]["username"]}`);
            }
        });
    }
    JoinRoom(room_id, title){
        SocketIOMaster.emit('join-room',{room_id:room_id,title:title})
    }
    LeaveRoom(room_id){
        SocketIOMaster.emit('leave-room',{room_id:room_id})
    }

    //UI
    ShowSelectDevice(){
           
        if (!this.selectDeviceUiStatus) {
            $('.device-select-container-mask').removeClass('hidden');
            this.selectDeviceUiStatus = true;
        } else {
            $('.device-select-container-mask').addClass('hidden');
            this.selectDeviceUiStatus = false;
        }
    }
    async EnumerateDevices() {

        const videoSelect = document.getElementById('videoSelect');
        const audioSelect = document.getElementById('audioSelect');
        const selectedVideo = videoSelect.value;
        const selectedAudio = audioSelect.value;

        videoSelect.innerHTML = '';
        audioSelect.innerHTML = '';



        const defaultVideo = document.createElement('option');
        defaultVideo.value = 'default';
        defaultVideo.text = '不开启摄像头';
        videoSelect.appendChild(defaultVideo);

        const emptyAudio = document.createElement('option');
        emptyAudio.value = 'empty';
        emptyAudio.text = '关闭音频输入';
        audioSelect.appendChild(emptyAudio);

        try {
                
            (await VideoStream.GetVideoDevices()).forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `${videoSelect.length}`;
                videoSelect.appendChild(option);
                if (device.deviceId === selectedVideo) option.selected = true;
            });

            (await VideoStream.GetAudioDevices()).forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `${audioSelect.length}`;
                audioSelect.appendChild(option);
                if (device.deviceId === selectedAudio) option.selected = true;
            });

            navigator.mediaDevices.ondevicechange = this.EnumerateDevices.bind(this);
        }catch (error) {
            this.logger.error('获取设备列表失败:', error);
        }
    }


    // 添加远程视频元素A
    AddRemoteVideo(targetSid, streams) {
        if ($(`#remote_video_${targetSid}`).length === 0) {
            const root_div = document.createElement('div');
            // 替换layui-card为Tailwind卡片样式，保留原有ID和margin-bottom
            root_div.className = `bg-card border border-border rounded-lg shadow-md mb-2.5 w-full`;
            root_div.id = `remote_video_${targetSid}`;
            // root_div.style.width = "500px";
            const header_div = document.createElement('div');
            // 替换layui-card-header为Tailwind样式，保留自定义类名用于标识
            header_div.className = `remote-video-lable px-2 py-2 border-t border-border text-text font-medium remote-video-lable-${targetSid}`;
            try {
                // 替换layui图标为Font Awesome，调整间距
                header_div.innerHTML = `<i class="fa-solid fa-user mr-1.5"></i>远程用户: ${remoteUsers[targetSid]['username']}`;
            } catch (e) {
                header_div.innerHTML = `<i class="fa-solid fa-user mr-1.5"></i>远程用户: ${targetSid}`;
            }

            const newVideo = document.createElement('video');
            newVideo.id = `remote_video_${targetSid}_v`;
            // 移除layui-card，保留业务类名，添加Tailwind视频样式
            newVideo.className = 'remote-video';
            newVideo.autoplay = true;
            newVideo.playsinline = true;
            newVideo.controls = true;
            // 替换内联样式为Tailwind工具类（通过style设置保证优先级）
            newVideo.style.width = '100%';
            newVideo.style.height = 'auto';
            newVideo.style.backgroundColor = '#000';
            newVideo.style.margin = '0';
            newVideo.style.objectFit = 'cover';
            newVideo.style.borderTopLeftRadius = '0.5rem';
            newVideo.style.borderTopRightRadius = '0.5rem';

            // 保持原有DOM嵌套顺序（视频在前，标题在后）
            root_div.appendChild(newVideo);
            root_div.appendChild(header_div);
            document.getElementById('remoteVideos').appendChild(root_div);
            this.logger.debug(`创建远程视频元素 id=remote_${targetSid}`);
        }
        document.getElementById(`remote_video_${targetSid}_v`).srcObject = streams[0];
        
    }

    // 移除远程视频元素
    RemoveRemoteVideo(targetSid) {
        this.logger.debug(`移除远程视频,sid: ${targetSid}`);
        try {
            $(`#remote_video_${targetSid}`).remove();
        } catch (e) {
            this.logger.warn(`清理远程视频失败  targetSid: ${targetSid}`);
        }
    }


   
}



export default new WebRTC();