let localStream = null;
let screenStream = null;
let peerConnections = {};
let remoteUsers = {};

let heartbeat_timer = null;
let isFirst = false;
let iceServersConfig = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
    ]
};
let socket = undefined;
let localAudioContext;
let localAnalyser;
let localSource;
let webrtc_logger = new LoggerManager("WebRTC", LoggerManager.LEVELS.ALL);
// 可视化参数
let fftSize = 2048;
let verticalScale = 2;
let smoothingFactor = 0;

// 设备选择按钮事件
let select_device_ui_status = false;
// 工具函数：通过值获取对象键
function getKeyByValue(obj, targetValue) {
    for (let key in obj) {
        if (obj.hasOwnProperty(key) && obj[key] === targetValue) {
            return key;
        }
    }
    return null;
}

// 编码：先转URI编码，再用btoa
function b64Encode(str) {
    return btoa(encodeURIComponent(str));
}

// 解码：先用atob，再转URI解码
function b64Decode(str) {
    return decodeURIComponent(atob(str));
}

// 移除远程视频元素
function removeRemoteVideo(targetSid) {
    webrtc_logger.debug(`移除远程视频,sid: ${targetSid}`);
    try {
        $(`#remote_video_${targetSid}`).remove();
    } catch (e) {
        webrtc_logger.warn(`清理远程视频失败  targetSid: ${targetSid}`);
    }
}

// 添加远程视频元素
function addRemoteVideo(targetSid, streams) {
    if ($(`#remote_video_${targetSid}`).length === 0) {
        const root_div = document.createElement('div');
        // 替换layui-card为Tailwind卡片样式，保留原有ID和margin-bottom
        root_div.className = `bg-card border border-border rounded-lg shadow-md mb-2.5`;
        root_div.id = `remote_video_${targetSid}`;

        const header_div = document.createElement('div');
        // 替换layui-card-header为Tailwind样式，保留自定义类名用于标识
        header_div.className = `remote-video-lable px-4 py-3 border-t border-border text-text font-medium remote-video-lable-${targetSid}`;
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
        newVideo.muted = true;
        newVideo.controls = true;
        // 替换内联样式为Tailwind工具类（通过style设置保证优先级）
        newVideo.style.width = '100%';
        newVideo.style.height = '100%';
        newVideo.style.backgroundColor = '#000';
        newVideo.style.margin = '0';
        newVideo.style.objectFit = 'cover';
        newVideo.style.borderTopLeftRadius = '0.5rem';
        newVideo.style.borderTopRightRadius = '0.5rem';

        // 保持原有DOM嵌套顺序（视频在前，标题在后）
        root_div.appendChild(newVideo);
        root_div.appendChild(header_div);
        document.getElementById('remoteVideos').appendChild(root_div);
        webrtc_logger.debug(`创建远程视频元素 id=remote_${targetSid}`);
    }
    document.getElementById(`remote_video_${targetSid}_v`).srcObject = streams[0];
    webrtc_logger.debug(`指定视频流`);
}

// 替换音视频轨道
async function replaceTrack() {
    document.getElementById('localVideo').srcObject = localStream;
    Object.values(peerConnections).forEach(pc => {
        // 替换视频轨道
        const videoSender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
        if (videoSender && localStream) {
            const videoTrack = localStream.getVideoTracks()[0];
            // 遍历媒体流中的所有视频轨道
            if (videoTrack) {
                videoSender.replaceTrack(videoTrack);
            }
        }

        // 替换音频轨道
        const audioSender = pc.getSenders().find(s => s.track && s.track.kind === 'audio');
        if (audioSender && localStream) {
            const audioTrack = localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioSender.replaceTrack(audioTrack);
            }
        }

        // 发送offer更新
        pc.createOffer().then(offer => {
            pc.setLocalDescription(offer);
            const targetSid = getKeyByValue(peerConnections, pc);
            if (targetSid) {
                webrtc_logger.debug(`发送offer给${targetSid}`);
                socket.emit('offer', {
                    target: targetSid,
                    offer: offer,
                    room_id: sessionStorage.getItem("room")  // 新增：携带房间ID
                });
            }
        });
    });
}

// 添加音视频轨道到连接
async function addTrack(pc, targetSid) {
    document.getElementById('localVideo').srcObject = localStream;
    localStream.getVideoTracks().forEach(track => {
        pc.addTrack(track, localStream);
    });
    localStream.getAudioTracks().forEach(track => {
        pc.addTrack(track, localStream);
    });
}

// 创建本地音频分析器
function createLocalAnalyser(stream) {
    if (!localAudioContext || localAudioContext.state === 'closed') {
        localAudioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    localAnalyser = localAudioContext.createAnalyser();
    localAnalyser.fftSize = fftSize;
    localAnalyser.smoothingTimeConstant = smoothingFactor;
    localSource = localAudioContext.createMediaStreamSource(stream);
    localSource.connect(localAnalyser);
}


// 创建默认视频流（仅音频时使用）
async function createDefaultVideoStream(constraints = null,isScreenStream = false,isUseMicropone = true) {
    
        
    if (constraints == null) {
        constraints = {}
        constraints.audio = null 
        constraints.video = null

    }
    const stream = new MediaStream();
    let videoStream = new MediaStream();
    if (isScreenStream){  //屏幕共享
    
        videoStream = await getScreenStream();
        
    }else{ //默认流或者 摄像头流
        if(constraints.video == null){
             const canvas = document.createElement('canvas');
            canvas.width = 1920;
            canvas.height = 1080;
            const ctx = canvas.getContext('2d');
            const img = new Image();
            img.src = '/static/img/only_audio.png';
            await new Promise((resolve, reject) => {
                img.onload = resolve;
                img.onerror = reject;
            });

            function drawImageToCanvas() {
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            }
            drawImageToCanvas();
            // 定期重绘
            setInterval(drawImageToCanvas, 1000 / 5);
            videoStream = canvas.captureStream(30);
        
        }else {
            videoStream = await navigator.mediaDevices.getUserMedia(constraints)
        }
    }


    // 获取音频流
    let audioStream = null;
    try {
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: constraints.audio || {
                sampleRate: 44100,
                sampleSize: 16,
                channelCount: 2,
                echoCancellation: false,
                noiseSuppression: false
            }
        });
    } catch (error) {
        console.info(`创建音频流失败!${error.message},正在创建空白音频流`)
        CommonUtils.MsgBox(`创建音频流失败!,正在创建空白音频流`);
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioContext = new AudioContext();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 0;
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        const mediaStreamDest = audioContext.createMediaStreamDestination();
        gainNode.connect(mediaStreamDest);
        oscillator.start();
        audioStream = mediaStreamDest.stream;
    }
    if(!isUseMicropone){
        videoStream.getVideoTracks().forEach(track => stream.addTrack(track));
        videoStream.getAudioTracks().forEach(track => stream.addTrack(track));
    }else{
        videoStream.getVideoTracks().forEach(track => stream.addTrack(track));
        audioStream.getAudioTracks().forEach(track => stream.addTrack(track));
    }
    localStream = stream;
    return
}



// 获取本地媒体流
async function getLocalStream(isScreenStream=false,isUseMicropone=true) {
    try {
        const videoSelect = document.getElementById('videoSelect');
        const audioSelect = document.getElementById('audioSelect');

        const constraints = {};
        
    
        if (videoSelect.value || videoSelect.options.length > 1) {
            constraints.video = videoSelect.value ? { deviceId: { exact: videoSelect.value } } : true;
        }

        

        if (audioSelect.value || audioSelect.options.length > 1) {
            constraints.audio = audioSelect.value ? {
                deviceId: { exact: audioSelect.value },
                sampleRate: 44100,
                sampleSize: 16,
                channelCount: 2,
                echoCancellation: false,
                noiseSuppression: false
            } : true;
        }
        if(!isScreenStream){
             if (Object.keys(constraints).length === 0) {
                CommonUtils.MsgBox('没有找到任何媒体设备');
                return false;
            }

        }
       
        
        if (videoSelect.value === "default")
        {   constraints.video = null
        }
        await createDefaultVideoStream(constraints,isScreenStream,isUseMicropone);
        createLocalAnalyser(localStream);
        await replaceTrack();
        return true;
    } catch (e) {
        webrtc_logger.error('获取媒体设备失败:', e);
        CommonUtils.MsgBox('获取媒体设备失败: ' + e.message);
        return false;
    }
}

// 枚举媒体设备
async function enumerateDevices() {
    try {
        let videoDevices = [];
        let audioDevices = [];

        // 获取音频设备
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    sampleRate: 44100,
                    sampleSize: 16,
                    channelCount: 2,
                    echoCancellation: false,
                    noiseSuppression: false
                }
            });
            stream.getTracks().forEach(track => track.stop());
            const devices = await navigator.mediaDevices.enumerateDevices();
            audioDevices = devices.filter(device => device.kind === 'audioinput');
        } catch (e) {
            webrtc_logger.warn('无法获取音频设备:', e);
            CommonUtils.MsgBox('无法获取音频设备');
        }

        // 获取视频设备
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            stream.getTracks().forEach(track => track.stop());
            const devices = await navigator.mediaDevices.enumerateDevices();
            videoDevices = devices.filter(device => device.kind === 'videoinput');
        } catch (e) {
            webrtc_logger.warn('无法获取视频设备:', e);
            CommonUtils.MsgBox('无法获取视频设备');
        }

        const videoSelect = document.getElementById('videoSelect');
        const audioSelect = document.getElementById('audioSelect');
        const selectedVideo = videoSelect.value;
        const selectedAudio = audioSelect.value;

        videoSelect.innerHTML = '';
        audioSelect.innerHTML = '';

        // 添加默认选项
        const defaultVideo = document.createElement('option');
        defaultVideo.value = 'default';
        defaultVideo.text = '不开启摄像头';
        videoSelect.appendChild(defaultVideo);

        const defaultAudio = document.createElement('option');
        defaultAudio.value = 'default';
        defaultAudio.text = '默认音频输入';
        audioSelect.appendChild(defaultAudio);



        // 添加视频设备
        videoDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `摄像头 ${videoSelect.length}`;
            videoSelect.appendChild(option);
            if (device.deviceId === selectedVideo) option.selected = true;
        });


        // 添加音频设备
        audioDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `麦克风 ${audioSelect.length}`;
            audioSelect.appendChild(option);
            if (device.deviceId === selectedAudio) option.selected = true;
        });

        videoSelect.disabled = videoDevices.length === 0;
        audioSelect.disabled = audioDevices.length === 0;

        // 设备变更监听
        navigator.mediaDevices.ondevicechange = enumerateDevices;
    } catch (e) {
        webrtc_logger.error('枚举设备失败:', e);
        CommonUtils.MsgBox('枚举设备失败: ' + e.message);
    }
}



// 开始屏幕共享
async function getScreenStream() {
    try {
        
        stream = await navigator.mediaDevices.getDisplayMedia({
            video: true,
            audio: {
                sampleRate: 44100,
                sampleSize: 16,
                channelCount: 2,
                echoCancellation: false,
                noiseSuppression: false
            }
        });
        
    } catch (e) {
        webrtc_logger.error('屏幕共享失败:', e);
        CommonUtils.MsgBox('屏幕共享失败: ' + e.message);
        return null;
    }
    return stream
}


// 从 peerConnections 中通过 RTCPeerConnection 实例查找对应的 sid
function getSidFromPc(targetPc) {
    // 遍历存储连接的 peerConnections 对象（格式：{ sid: pc, ... }）
    for (const [sid, pc] of Object.entries(peerConnections)) {
        // 找到与目标 pc 实例匹配的键（sid）
        if (pc === targetPc) {
            return sid;
        }
    }
    return null; // 未找到对应 sid
}
// 创建RTCPeerConnection
async function createPeerConnection(targetSid) {
    if (peerConnections[targetSid]) {
        webrtc_logger.debug(`复用已存在的连接 targetSid=${targetSid}`);
        return peerConnections[targetSid];
    }
    webrtc_logger.debug(`创建新连接 targetSid=${targetSid}, config=`, JSON.stringify(iceServersConfig, null, 2));
    
    const pc = new (window.RTCPeerConnection || 
                    window.webkitRTCPeerConnection || 
                    window.mozRTCPeerConnection || 
                    window.msRTCPeerConnection)(iceServersConfig);

    if (!pc) {
        alert('您的浏览器不支持 WebRTC，无法进行视频通话');
        console.error('浏览器不支持 RTCPeerConnection');
    }

    if (!localStream) {
        await createDefaultVideoStream();
    }

    await addTrack(pc, targetSid);

    // 处理远程流
    pc.ontrack = (event) => {
        webrtc_logger.debug(`收到远程流 targetSid=${targetSid}`);
        if (targetSid === sessionStorage.getItem("sid")) {
            webrtc_logger.debug(`收到本地流 ${targetSid}，不处理`);
            return;
        }
        if (event.streams.length === 0) {
            CommonUtils.MsgBox(`收到远程流 targetSid=${targetSid} 不包含流`);
            return;
        }
        addRemoteVideo(targetSid, event.streams);
    };

    // 处理ICE候选
    pc.onicecandidate = (event) => {
        if (event.candidate) {
            webrtc_logger.debug(`发送ICE候选 targetSid=${targetSid}`);
            socket.emit('ice-candidate', {
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
        
        webrtc_logger.debug(`连接状态变化 targetSid=${targetSid}, state=${pc.connectionState}`);
        // socket.emit('connection-state', {
        //     target: targetSid,
        //     state: pc.connectionState
        // });
        
        const removeConnection = (sid) => {
            webrtc_logger.warn(`连接失败，清理资源 targetSid=${sid}`);
            removeRemoteVideo(sid);
            const pc = peerConnections[sid];
            pc.close();
            delete peerConnections[sid];
        };

        switch (pc.connectionState) {
            case 'disconnected':
            case 'failed':
            case 'closed':
                removeConnection(targetSid);
                break;
            default:
                break;
        }
        socket.emit("on-connection-state-change",{
            target: targetSid,
            state: pc.connectionState
        })
    };

    // ICE连接状态变化
    pc.oniceconnectionstatechange = () => {
        
        webrtc_logger.debug(`ICE连接状态变化 targetSid=${targetSid}, state=${pc.iceConnectionState}`);

    };

    // 信令状态变化
    pc.onsignalingstatechange = () => {
        webrtc_logger.debug(`信令状态变化 targetSid=${targetSid}, state=${pc.signalingState}`);
    };

    peerConnections[targetSid] = pc;
    return pc;
}

// 处理offer
async function handleOffer(data) {
    if (data.from_sid === sessionStorage.getItem("sid")) {
        webrtc_logger.debug(`忽略自己的offer from=${data.from_sid}`);
        return;
    }
    webrtc_logger.debug(`收到offer from=${data.from_sid}`);

    try {
        let pc = peerConnections[data.from_sid];
        if (pc && pc.signalingState !== 'stable') {
            webrtc_logger.debug(`重置现有连接 from=${data.from_sid}, state=${pc.signalingState}`);
            pc.close();
            delete peerConnections[data.from_sid];
            pc = null;
        }
        if (!pc) {
            pc = await createPeerConnection(data.from_sid);
        }
        if (pc.signalingState === 'have-remote-offer') {
            webrtc_logger.debug(`回滚远程offer from=${data.from_sid}`);
            await pc.setRemoteDescription({ type: 'rollback' });
        }
        await pc.setRemoteDescription(data.offer);
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        webrtc_logger.debug(`发送answer to=${data.from_sid}`);
        socket.emit('answer', {
            target: data.from_sid,
            room_id: sessionStorage.getItem("room"),  // 新增：携带房间ID
            answer: answer
        });
    } catch (e) {
        webrtc_logger.error(`处理offer失败 from=${data.from_sid}`, e);
        CommonUtils.MsgBox('处理offer失败: ' + e.message);
    }
}

// 处理answer
async function handleAnswer(data) {
    if (data.from_sid === sessionStorage.getItem("sid")) {
        webrtc_logger.debug(`忽略自己的answer from=${data.from_sid}`);
        return;
    }
    webrtc_logger.debug(`收到answer from=${data.from_sid}`);
    try {
        const pc = peerConnections[data.from_sid];
        if (pc && pc.signalingState === 'have-local-offer') {
            await pc.setRemoteDescription(data.answer);
            webrtc_logger.debug(`Answer处理完成 from=${data.from_sid}`);
        } else {
            webrtc_logger.warn(`忽略answer，信令状态不正确 from=${data.from_sid}, state=${pc?.signalingState}`);
        }
    } catch (e) {
        webrtc_logger.error(`处理answer失败 from=${data.from_sid}`, e);
        CommonUtils.MsgBox('处理answer失败: ' + e.message);
    }
}

// 处理ICE候选
async function handleIceCandidate(data) {
    if (data.from_sid === sessionStorage.getItem("sid")) {
        webrtc_logger.debug(`忽略自己的candidate from=${data.from_sid}`);
        return;
    }
    webrtc_logger.debug(`收到ICE候选 from=${data.from_sid}`);
    try {
        const pc = peerConnections[data.from_sid];
        if (pc) {
            await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
            webrtc_logger.debug(`ICE候选添加完成 from=${data.from_sid}`);
        }
    } catch (e) {
        webrtc_logger.error(`处理ICE候选失败 from=${data.from_sid}`, e);
        CommonUtils.MsgBox('处理ICE候选失败: ' + e.message);
    }
}

// 加载ICE配置
async function loadIceConfig() {
    try {
        const response = await fetch('/api/ice_servers_config');
        iceServersConfig = await response.json();
        webrtc_logger.debug(`ICE配置加载成功 ${JSON.stringify(iceServersConfig, null, 2)}`);
    } catch (error) {
        webrtc_logger.error('加载ICE配置失败:', error);
        CommonUtils.MsgBox('加载ICE配置失败');
    }
}

// 加入房间
function join_room_ex(room_id, title) {
    socket.emit('join-room', { 
        room_id: room_id,  // 统一为room_id与后端匹配

    });
    webrtc_logger.debug(`发送进房请求 room_id=${room_id}`);
}
function on_show_select_device_click(){
           
    if (!select_device_ui_status) {
        $('.device-select-container-mask').removeClass('hidden');
        select_device_ui_status = true;
    } else {
        $('.device-select-container-mask').addClass('hidden');
        select_device_ui_status = false;
    }
}


function connect(){
    socket = io(`${window.location.origin}`, 
        {
            transports: ['websocket', 'polling']
        }
    );

}




// 初始化
async function WebrtcInit() {
    await enumerateDevices();
    connect();
    // 统一用jQuery绑定事件（不修改DOM id/class）
    
    $('#videoSelect').on('change', () => {
        getLocalStream()
    });
    $('#audioSelect').on('change', () => {
        getLocalStream()
    });
    $('#capture_screen_button').on('click', () => {
        getLocalStream(true,true);
        on_show_select_device_click();
    });
    $('#switchBtn').on('click', () => {
        getLocalStream();
        on_show_select_device_click();
    });
    $('#createRoomBtn').on('click', () => {
        const title = $('#roomTitle').val();
        if (title.length < 2 || !title) {
            CommonUtils.MsgBox("检查标题字数是否2个以上，或者标题是否未填写");
            return;
        }
        const room_id = "room_s_" + Date.now();
        socket.emit('create-room',{room_id:room_id,title:title,room_type:"webrtc"})
    });

    // Socket事件监听
    socket.on('offer', handleOffer);
    socket.on('answer', handleAnswer);
    socket.on('ice-candidate', handleIceCandidate);


    socket.on('user-registered', (data) => {
        webrtc_logger.debug(`用户注册成功 ${JSON.stringify(data, null, 2)}`);
        sessionStorage.setItem("sid",data.sid)
        CommonUtils.SetCookieWithExpire("uid", data.uid, 30 * 24 * 3600);
    });

    // 房间用户更新
    socket.on('room-users-updated', (data) => {  // 与后端事件名匹配
        remoteUsers = data.users;
        webrtc_logger.debug(`房间用户更新: ${JSON.stringify(data, null, 2)}`);
        Object.keys(data.users).forEach(key => {
            try {
                $(`.remote-video-lable-${data.users[key]['sid']}`).html(`<i class="layui-icon" style="margin-right:5px;">&#xe60e;</i>远程用户: ${data.users[key]["username"]}`);
            } catch (e) {
                webrtc_logger.warn("更新用户标签失败! uid=" + key);
            }
            if (data.users[key]['sid'] === sessionStorage.getItem("sid")) {
                $(`.local-video-lable`).html(`<i class="layui-icon" style="margin-right:5px;">&#xe60e;</i>本地视频: ${data.users[key]["username"]}`);
            }
        });
    });

    socket.on("current-sid",(data) => {  //##########没啥用
        if (sessionStorage.getItem("sid") != data.sid){
       
            webrtc_logger.info(`SID变更,会话失效 之前的SID:${sessionStorage.getItem("sid")} 当前SID:${data.sid}`)
         
        }
    })

    // 新用户加入房间
    socket.on('user-joined-room', async (data) => {  // 与后端事件名匹配
        webrtc_logger.debug(`新用户加入房间 ${JSON.stringify(data.room_info, null, 2)}`);
        CommonUtils.MsgBox(`${data.username}加入了房间 ${data.room_info.title}`);
        // 创建连接并发送offer
        const pc = await createPeerConnection(data.sid);
        pc.createOffer().then(offer => {
            pc.setLocalDescription(offer);
            socket.emit('offer', {
                target: data.sid,
                room_id: sessionStorage.getItem("room"),
                offer: offer
            });
            webrtc_logger.debug(`发送offer to=${data.sid}`);
        }).catch(e => {
            webrtc_logger.error(`创建offer失败 to=${data.sid}`, e);
            CommonUtils.MsgBox('创建offer失败: ' + e.message);
        });
    });

    // 自身加入房间成功
    socket.on('joined-room',async (data) => {  // 与后端事件名匹配
        webrtc_logger.debug(`自身加入房间成功 ${JSON.stringify(data.room_info, null, 2)}`);
    
        sessionStorage.setItem("room",data.room_id)
        $('.room-select-container').addClass('hidden');
        $('.video-chat-container').removeClass('hidden');
        $('#remoteVideos').html(`
            <div class="bg-card border border-border rounded-lg shadow-md mb-2.5 w-full">
                <div class="select-device-2 relative">
                    <video id="localVideo" muted autoplay playsinline
                        class="w-full h-full bg-black m-0 object-cover rounded-t-lg">
                    </video>
                </div>
                <div class="local-video-lable px-4 py-3 border-t border-border text-text font-medium">
                    <i class="fa-solid fa-user mr-1.5"></i>本地视频 ${sessionStorage.getItem("sid")}
                </div>
            </div>
        `);

        // 离开房间按钮事件（jQuery绑定）
        $('#leftRoomBtn').on('click', () => {
            $('#remoteVideos').html('');
            socket.emit('leave-room', { room_id: sessionStorage.getItem("room") });  // 与后端匹配
            webrtc_logger.info("发送离开房间请求")
            sessionStorage.removeItem("room")
            // 如果是自己离开，更新UI
            if (data.sid === sessionStorage.getItem("sid")) {
                sessionStorage.removeItem("room")
                $('.room-select-container').removeClass('hidden');
                $('.video-chat-container').addClass('hidden');
            }
        });



        

        $('.device-select-container-mask').on('click', e => {
             if (!$(e.target).hasClass("device-select-container-mask")){
                return;
            }
            on_show_select_device_click();
        });
        $( '.select-device-2').on('click',()=>{on_show_select_device_click()})
        const pc = await createPeerConnection(data.sid);
        try {
            webrtc_logger.debug(`创建offer to=${data.sid}`);
            const offer = await pc.createOffer();
            webrtc_logger.debug(`设置本地描述 to=${data.sid}`);
            await pc.setLocalDescription(offer);

            webrtc_logger.debug(`发送offer给${data.sid} `) //${offer.sdp}
            socket.emit('offer', {
                target: data.sid,
                room_id:data.room_id,
                offer: offer
            });
        } catch (e) {
            webrtc_logger.error(`创建offer失败 to=${data.sid}`, e);
            CommonUtils.MsgBox('创建offer失败: ' + e.message);
        }

    });

    // 用户离开房间
    socket.on('user-left-room', (data) => {  // 与后端事件名匹配
        webrtc_logger.debug(`用户离开房间 ${JSON.stringify(data, null, 2)}`);
        CommonUtils.MsgBox(`${data.username}离开了房间`);
        if (peerConnections[data.sid]) {
            peerConnections[data.sid].close();
            delete peerConnections[data.sid];
        }
        removeRemoteVideo(data.sid);
        // 如果是自己离开，更新UI
        if (data.sid === sessionStorage.getItem("sid")) {
            sessionStorage.removeItem("room")
            $('.room-select-container').removeClass('hidden');
            $('.video-chat-container').addClass('hidden');
        }
    });

    // 房间列表更新
    socket.on('room-list-updated', (room_list) => {  // 与后端事件名匹配
        webrtc_logger.debug(`房间列表更新: ${JSON.stringify(room_list, null, 2)}`);
        let appendHtml = '';
        room_list.forEach(e => {
            if(e.room_type == "webrtc"){
                appendHtml += `


                <div class="bg-card border border-border rounded-lg shadow-md overflow-hidden room-card" data-room-id="${e.room_id}">
                    <div class="video-container h-36 relative">
                        <img src="${e.cover || 'https://picsum.photos/300/200?random=1'}" alt="房间封面" class="w-full h-full object-cover">
                        <div id="${e.room_id}_room_hum_count" class="absolute bottom-1.5 right-1.5 bg-black/50 px-2 py-0.5 rounded-full text-xs text-white">
                            <i class="fa-solid fa-user mr-1"></i> ${e.user_count}
                        </div>
                    </div>
                    <div class="p-2.5 text-center">
                        <h4 class="whitespace-nowrap overflow-hidden text-ellipsis font-medium text-text">${e.title}</h4>
                        <button class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-1 rounded-md text-sm w-4/5 mt-2.5 transition-colors" 
                                onclick="join_room_ex('${e.room_id}','${e.title}')">
                            进入房间
                        </button>
                    </div>
                </div>
                `;
            }
            
        });
        $('#roomGrid').html(appendHtml);
    });

    // 错误提示
    socket.on('error', (data) => {
        webrtc_logger.log(`错误 :  ${data.msg} , event:${data.event} `);
        CommonUtils.MsgBox(`错误 :  ${data.msg}  `);
    });

    // 加载配置并注册用户
    await loadIceConfig();
    
    $('.room-select-container').removeClass('hidden');

    
    socket.on('open' , (data) => {
        webrtc_logger.error('连接打开:', data);

    })
    socket.on('connect', (data) => {
        webrtc_logger.log('连接成功:', data);
        socket.emit('user-register');
        webrtc_logger.log(`开始注册用户`);

    })

    socket.on('ping', (data) => {
        webrtc_logger.log('PING:', data);
    })

    socket.on('packet', (data) => {
        webrtc_logger.log('收到数据包:', data);
    });

    socket.on('connect_error', (data) => {
        webrtc_logger.log('连接错误:', data);
    })
    socket.on('disconnect', (data) => {
        webrtc_logger.log('连接断开:', data);
    });
    socket.on('close', (data) => {
        webrtc_logger.log('连接关闭:', data);
    });
    socket.on('reconnect_attempt', (data) => {
        webrtc_logger.log('重新连接尝试:', data);
    });
    socket.on('reconnect_failed', (data) => {
        webrtc_logger.log('重新连接失败:', data);
    });
    socket.on('reconnect_error', (data) => {
        webrtc_logger.log('重新连接错误:', data);
    });
    
    socket.on('error' , (data) => {
        webrtc_logger.error('连接错误,错误信息:', data);

    })

    setInterval(() => {
        if (sessionStorage.getItem("room")) {
            socket.emit('room_users_update', { room_id: sessionStorage.getItem("room") });
        }
        // socket.emit('get-current-sid');
        
    }, 10000);
}

// 唤醒锁相关
let wakeLock = null;
async function requestWakeLock() {
    try {
        if ('wakeLock' in navigator) {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('已获取屏幕唤醒锁，防止休眠');
            wakeLock.addEventListener('release', () => {
                console.log('唤醒锁已释放');
            });
        } else {
            console.log('浏览器不支持 Wake Lock API');
        }
    } catch (err) {
        console.error(`获取唤醒锁失败: ${err.name}, ${err.message}`);
    }
}
function releaseWakeLock() {
    if (wakeLock) {
        wakeLock.release();
        wakeLock = null;
        console.log('唤醒锁已手动释放');
    }
}

// 页面可见性变化
function handleVisibilityChange() {
    if (document.visibilityState === 'hidden') {
        console.log('用户离开标签页/窗口进入后台');
    } else if (document.visibilityState === 'visible') {
        console.log('用户返回标签页/窗口进入前台');
        // socket.emit('user-register');
        // webrtc_logger.log(`重新注册用户`);
    }
}

// // 页面加载完成后初始化
// $(document).ready(() => {  // 统一用jQuery ready
//     WebrtcInit();
//     requestWakeLock();
//     $(document).on('click', () => {
//         webrtc_logger.info("document click");
//     });
//     document.addEventListener('visibilitychange', handleVisibilityChange);
// });