
// 全局变量优化：明确变量含义，避免歧义
let socket;
const chatLogger = new LoggerManager("HomeLightSwitch", LoggerManager.LEVELS.DEBUG);
let currentRoomId = null;
let devicePollingTimer = null; // 设备信息轮询定时器
const $devicesContainer = $('.devices'); // 缓存设备容器DOM
const room = 'main';
const title = "主聊天室";
const room_type ="chat"
var currentDevices = []
// 初始化Socket连接（独立函数，便于重连调用）
function initSocket() {
    // 销毁旧连接（如果存在）
    if (socket) {
        socket.disconnect();
    }

    // 建立新连接
    socket = io(`${window.location.origin}`, {
        transports: ['websocket', 'polling'],
        reconnection: true, // 自动重连
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
    });

    // 连接状态监听
    socket.on('connect', () => {
        chatLogger.log('Socket连接成功，SID:', socket.id);
        socket.emit('user-register'); // 重新注册用户
        
    });
    socket.on('user-registered', (data) => {
        chatLogger.log('Register user:', data);
        socket.emit('create-room',{room_id:room,title: title,room_type:room_type})
        
        socket.emit('join-room', { 
            room_id: room,  // 统一为room_id与后端匹配
     
        });

        chatLogger.log(`send join-room to=${room}`);
        
    });

    socket.on('disconnect', (reason) => {
        chatLogger.warn('Socket断开连接:', reason);
        stopDevicePolling(); // 停止轮询
        if (reason === 'io server disconnect') {
            // 服务器主动断开，需要手动重连
            socket.connect();
        }
    });

    socket.on('reconnect', (attemptNumber) => {
        chatLogger.log(`重连成功，第${attemptNumber}次尝试`);
    });
    // 处理用户离开房间事件：根据sid移除对应的设备
    socket.on("user-left-room", (data) => {
        const leftSid = data.sid; // 获取离开用户的sid
        if (!leftSid) {
            chatLogger.warn("用户离开事件：缺少sid");
            return;
        }

        //根据sid查找对应的设备key
        let targetDeviceKey = null;
        for (const [deviceKey, deviceInfo] of Object.entries(currentDevices)) {
            if (deviceInfo.sid === leftSid) { // 设备信息中的sid与离开的sid匹配
                targetDeviceKey = deviceKey;
                break;
            }
        }

        //找到设备后移除对应的UI元素
        if (targetDeviceKey) {
            const $deviceEl = $(`.device-${targetDeviceKey}`, $devicesContainer);
            if ($deviceEl.length) {
                $deviceEl.remove();
                chatLogger.log(`用户离开，移除设备 - sid: ${leftSid}, deviceKey: ${targetDeviceKey}`);
            }
        } else {
            chatLogger.debug(`用户离开，未找到对应设备 - sid: ${leftSid}`);
        }
    });
    // 新用户加入房间
    socket.on('user-joined-room', (data) => {
        chatLogger.debug(`新用户加入房间: ${JSON.stringify(data, null, 2)}`);
        CommonUtils.MsgBox(`${data.username}加入了房间 ${data.room_info.title}`);
        
    });

    // 成功加入房间
    socket.on('joined-room', (data) => {
        chatLogger.debug(`成功加入房间: ${JSON.stringify(data.room_info, null, 2)}`);
        currentRoomId = data.room_id;
        CommonUtils.MsgBox(`您已加入房间 ${data.room_info.title}`);
        socket.emit("get-devices-info"); // 主动获取一次设备信息 只此一次 后面由设备触发设备更新

    });

    // 设备信息更新处理
    socket.on("devices-info", (devicesData) => {
        updateDevicesUI(devicesData);
    });
}

// 切换设备GPIO状态（使用设备唯一key而非sid）
function switchDeviceGpio(deviceKey, gpio) {
    if (!deviceKey || !gpio) {
        chatLogger.error('切换GPIO失败：参数不完整');
        return;
    }
    socket.emit("switch-device-gpio", { target: deviceKey, gpio: gpio });
}

// 更新设备UI
function updateDevicesUI(devicesData) {
    if (!devicesData) return;

    const currentDeviceKeys = Object.keys(devicesData);
    const docFragment = document.createDocumentFragment(); // 文档片段减少DOM重绘

    // 处理现有设备和新设备
    currentDeviceKeys.forEach(deviceKey => {
        const deviceData = devicesData[deviceKey];
        const deviceClass = `device-${deviceKey}`;
        let $deviceEl = $(`.${deviceClass}`, $devicesContainer);

        // 生成GPIO按钮
        const buttonsHtml = deviceData.gpio_status.map(statusStr => {
            const [gpio, status] = statusStr.split(":");
            const color = status === "1" ? "#cccccc" : "#ff0000";
            return `
                <button class="layui-btn" 
                        data-gpio="${gpio}" 
                        style="background: ${color};"
                        onclick="switchDeviceGpio('${deviceKey}', ${gpio})">
                    GPIO${gpio}
                </button>
            `;
        }).join('');

        // 设备已存在：更新内容
        if ($deviceEl.length) {
            $deviceEl.html(buttonsHtml);
        } 
        // 新设备：创建元素
        else {
            const deviceHtml = `
                <div class="layui-card ${deviceClass}">
                    ${buttonsHtml}
                </div>
            `;
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = deviceHtml;
            docFragment.appendChild(tempDiv.firstElementChild);
        }
    });

    // 添加新设备到容器
    $devicesContainer.append(docFragment);

    // 移除已离线的设备
    $('.layui-card', $devicesContainer).each(function() {
        const $el = $(this);
        const deviceKey = $el.attr('class').match(/device-(\S+)/)?.[1];
        if (deviceKey && !currentDeviceKeys.includes(deviceKey)) {
            $el.remove();
        }
    });
}


// 页面加载初始化
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
});
