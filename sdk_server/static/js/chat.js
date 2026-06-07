let socket = undefined;
let chat_logger = new LoggerManager("Chat",LoggerManager.LEVELS.ALL)
let currentRoomId = null
let notificationManager= NotificationManager.getInstance()
let localUid;
notificationManager.requestPermission()
let msgTmp = ""
// 加载历史消息

async function loadHistoryMessages(room) {
    try {
        socket.emit('get-room-message-history', { room: room });

    } catch (e) {
        chat_logger.error('加载历史消息失败:', e);
        CommonUtils.MsgBox('加载历史消息失败: ' + e.message);
    }
}



var msgTemplateCache =null ;

function initMsgTemplate(msgId) {
  // 从 message_list 中读取模板
  msgTemplateCache = $(".message_list #msg_id").clone();
  // 清空message_list的模板只留缓存
  $(".message_list #msg_id").remove();
  msgTemplateCache.removeClass("hidden");
  console.log("模板读取成功：", msgTemplateCache.length ? "是" : "否");
  
}



// 添加消息到聊天框
function appendMessage(msg) {

    if (msgTemplateCache == null)
        initMsgTemplate()
    var obj = msgTemplateCache.clone() //复制一个避免全局变化
    
    if ( msg.sender_uid== localUid ) {
        obj.find(".other-msg").remove() //自己的消息移除other-msg
        
    }else{
        obj.find(".self-msg").remove() //别人的消息移除self-msg
    }
    obj.find(".items-start .msg-div .username").text(msg.sender_username || "未知用户");

    obj.find(".items-start .msg-avatar").attr("src",msg.sender_avatar != "" ? msg.sender_avatar : "/static/img/default_avatar.gif");


    switch (msg.type) {
        case "image":
            const img = document.createElement('img');
            img.src = msg.message;
            img.style.maxWidth = '100%';
            obj.find(".items-start .msg-div .msg-bubble .content").append(img)
            
            // if (msg.sender_uid + '' != CommonUtils.GetCookie("uid")) notificationManager.sendNotification(`新消息来自:${ msg.sender_username}`,"[图片]")
            break;
        case "video":
            const video = document.createElement('video');
            video.src = msg.message;
            video.controls = true;
            obj.find(".items-start .msg-div .msg-bubble .content").append(video);
            // if (msg.sender_uid + '' != CommonUtils.GetCookie("uid")) notificationManager.sendNotification(`新消息来自:${ msg.sender_username}`,"[视频]")
            break;
        case "audio":
            const audio = document.createElement('audio');
            audio.src = msg.message;
            audio.controls = true;
            obj.find(".items-start .msg-div .msg-bubble .content").append(audio);
            // if (msg.sender_uid + '' != CommonUtils.GetCookie("uid")) notificationManager.sendNotification(`新消息来自:${ msg.sender_username}`,"[音频]")
            break;
        case "text":
            obj.find(".items-start .msg-div .msg-bubble .content").text(msg.message);
            
            // if (msg.sender_uid + '' != CommonUtils.GetCookie("uid")) notificationManager.sendNotification(`新消息来自:${ msg.sender_username}`,msg.message)
            break;
        case "html":
            obj.find(".items-start .msg-div .msg-bubble .content").html(msg.message);
            // if (msg.sender_uid + '' != CommonUtils.GetCookie("uid")) notificationManager.sendNotification(`新消息来自:${ msg.sender_username}`,"[超文本]")
            break;
    }



    const timestamp = msg.timestamp ? new Date(msg.timestamp) : new Date();
    // 定义日期和时间的格式化选项
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: 'numeric',
        minute: 'numeric',
        second: 'numeric'
    };
    // 创建一个 Intl.DateTimeFormat 对象
    const formatter = new Intl.DateTimeFormat('zh-CN', options);
    // 获取格式化后的时间字符串
    const formattedTime = formatter.format(timestamp);

    obj.find(".items-start .msg-div .msg-bubble .time").text(formattedTime);
    $(".message_list").append(obj)
    $("#chat_message").scrollTop = $("#chat_message").scrollHeight;
    window.scrollTo(0, document.body.scrollHeight);
    
    

}


// 发送聊天消息
function sendChatMessage() {
    const input = document.getElementById('chat_input');
    const message = input.value.trim();
    if (message) {
        socket.emit('chat-message', { message: message, type: "html" ,room_id:currentRoomId});
        input.value = '';
    }
}
function sendMediaMessage() {
    // 创建一个 input 元素用于选择文件
    const input = document.createElement('input');
    input.type = 'file';
    // 设置允许选择的文件类型
    // input.accept = 'image/gif, image/jpeg, image/jpg, image/png, image/bmp';

    // 当用户选择文件后触发
    input.addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            $.ajax({
                url: '/api/chat/upload',
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                xhr: function () {
                    const xhr = new window.XMLHttpRequest();
                    // 监听上传进度事件
                    xhr.upload.addEventListener('progress', function (event) {
                        if (event.lengthComputable) {
                            const percentComplete = (event.loaded / event.total) * 100;
                            chat_logger.log(`上传进度: ${percentComplete}%`);
                            // 你可以在这里更新页面上的进度条显示
                        }
                    });
                    return xhr;
                },
                success: function (response) {

                    if (response.retcode === 0) {

                        socket.emit('chat-message', { type: response.data.type, message: response.data.message });
                    } else {
                        CommonUtils.MsgBox('消息发送失败: ' + response.msg);
                    }
                },
                error: function (error) {
                    chat_logger.error('消息发送失败', error);
                    CommonUtils.MsgBox('消息发送失败: ' + error);

                }
            });
        }
    });

    // 模拟点击 input 元素，触发文件选择对话框
    input.click();
}

function register_record_mic() {
    let mediaRecorder;
    let recordedChunks = [];


    // 请求麦克风权限
    navigator.mediaDevices.getUserMedia({ audio: {
        sampleRate: 48000,
        sampleSize: 16,
        channelCount: 2,
        echoCancellation: false,
        noiseSuppression: false
    } })
        .then((stream) => {
            mediaRecorder = new MediaRecorder(stream);
            document.getElementById('recordButton').style.background = "#cccccc";

            let record_start = () => {

                document.getElementById('recordButton').style.background = "#00cccc";
                recordedChunks = [];
                mediaRecorder.start();
                recordButtonText.textContent = '录制中...';
                
            }
            let record_stop = () =>{
                mediaRecorder.stop();
                recordButtonText.textContent = '发送语音';
                document.getElementById('recordButton').style.background = "#cccccc";
            }

            document.getElementById('recordButton').addEventListener('mousedown',record_start)
            document.getElementById('recordButton').addEventListener('touchstart',record_start)
            // 停止录制
            document.getElementById('recordButton').addEventListener('mouseup', record_stop);
            document.getElementById('recordButton').addEventListener('touchend', record_stop);

            // 录制数据可用时保存数据块
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };

            // 录制停止后处理数据
            mediaRecorder.onstop = () => {
                const blob = new Blob(recordedChunks, { type: 'audio/wav' });
                const formData = new FormData();
                formData.append('file', blob, 'recorded_audio.wav');



                $.ajax({
                    url: '/api/chat/upload',
                    type: 'POST',
                    data: formData,
                    contentType: false,
                    processData: false,
                    xhr: function () {
                        const xhr = new window.XMLHttpRequest();
                        // 监听上传进度事件
                        xhr.upload.addEventListener('progress', function (event) {
                            if (event.lengthComputable) {
                                const percentComplete = (event.loaded / event.total) * 100;
                                chat_logger.log(`上传进度: ${percentComplete}%`);
                                // 你可以在这里更新页面上的进度条显示
                            }
                        });
                        return xhr;
                    },
                    success: function (response) {

                        if (response.retcode === 0) {

                            socket.emit('chat-message', { type: response.data.type, message: response.data.message });
                        } else {
                            CommonUtils.MsgBox('消息发送失败: ' + response.msg);
                        }
                    },
                    error: function (error) {
                        chat_logger.error('消息发送失败', error);
                    }
                });
            };
        })
        .catch((error) => {
            chat_logger.error('无法访问麦克风:', error);
        });

}


function connect(){

    socket = io(`${window.location.origin}`, 
        {
            transports: ['polling','websocket']
        }
    );
}

async function ChatInit(){
    const room = 'main';
    const title = "主聊天室";
    
    connect();
    register_record_mic()
    document.getElementById('send_pic_button').onclick = sendMediaMessage;
    document.getElementById("send_msg_button").onclick = sendChatMessage;
    document.getElementById('chat_input').onkeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    };

    socket.on('user-registered', (data) => {
        chat_logger.log('Register user:', data);
        localSid = data.sid;
        localUid = data.uid
        socket.emit('create-room',{room_id:room,title:title,room_type:"chat"})


        socket.emit('join-room', { 
            room_id: room,  // 统一为room_id与后端匹配
        });

        chat_logger.log(`send join-room to=${room}`);
        
    });

    socket.on('user-joined-room', async (data) => {
        chat_logger.debug(`新用户加入房间 ${JSON.stringify(data, null, 2)}`);
        CommonUtils.MsgBox(`${data.username}加入了房间 ${data.room_info.title}`);
        
    });

    socket.on('joined-room', async (data) => {
        chat_logger.debug(`成功加入房间 ${JSON.stringify(data.room_info, null, 2)}`);
        currentRoomId = data.room_id
        CommonUtils.MsgBox(`${data.username}加入了房间 ${data.room_info.title}`);
        loadHistoryMessages(data.room_id)
        chat_logger.debug(`加载历史消息`);
        
    });

    // Socket事件监听
    socket.on('chat-message', appendMessage);
    
    
    socket.on('open' , (data) => {
        chat_logger.error('连接打开:', data);

    })
    socket.on('connect', (data) => {
        chat_logger.log('连接成功:', data);

        
    })
    socket.emit('user-register');
    


}

// // 页面加载完成后初始化
// document.addEventListener('DOMContentLoaded', init);