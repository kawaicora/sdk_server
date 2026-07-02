class CommonUtils {

    constructor(){

    }
    static inst (){

        if (!CommonUtils.instance){
            CommonUtils.instance = new CommonUtils();
        }
        return CommonUtils.instance;
    }
    // 静态方法，用于设置带有过期时间的cookie
    static SetCookieWithExpire(k, v, t) {
        // 创建一个新的Date对象，用于设置cookie的过期时间
        const date = new Date();
        // 将当前时间加上传入的过期时间（单位：毫秒）
        date.setTime(date.getTime() + t * 1000);
        // 将过期时间转换为UTC字符串格式
        const expires = "expires=" + date.toUTCString();
        // 设置cookie，格式为 键=值;过期时间
        document.cookie = k + "=" + v + ";" + expires + ";path=/";
    }

    // 静态方法，用于移除指定的cookie
    static RemoveCookie(k) {
        // 设置过期时间为过去的时刻
        const date = new Date();
        date.setTime(date.getTime() - 1);
        const expires = "expires=" + date.toUTCString();
        // 设置cookie的过期时间为过去，让浏览器自动删除它
        document.cookie = k + "=; " + expires + ";path=/";
    }

     // 静态方法，用于根据键获取对应的cookie值
    static GetCookie(k) {
        // 获取所有的cookie信息
        const name = k + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            // 去除cookie前面的空格
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            // 判断当前cookie的键是否与传入的键匹配
            if (c.indexOf(name) === 0) {
                // 如果匹配，返回对应的cookie值
                return c.substring(name.length, c.length);
            }
        }
        // 如果没有找到匹配的cookie，返回空字符串
        return "";
    }

    
    static MsgBox(msg,showTime = 2000,aniTime = 500){

        var p_id = "msgbox"
        var s_id = "msgbox_"+parseInt(Math.random()*1000000 )
        var prent_box_code = `<div id="${p_id}" style="pointer-events: none;position:fixed;z-index:1000;display:flex;max-width:1000px;word-break:break-all;min-width: 100%;min-height: 100%;justify-items: center;justify-content: center;top:0px;left:0px;align-content: center;flex-direction: column;padding: 10px 10px;align-items: center;"></div>` 
        var msg_box_code = `<div id="${s_id}" style="z-index:1000; display:flex; opacity: 0;max-width:1000px; word-break:break-all; min-width: 400px;justify-items: center;justify-content: center;background:#00000071;border-radius: 10px;padding: 10px 10px;color: #FFFFFF;font-size: 24px;font-weight: 500; margin: 5px 0px;">
            </div>` 
        if($("#msgbox").length == 0){
            $("body").append(prent_box_code)
        }
        
        $("#msgbox").append(msg_box_code)
        $("#"+s_id+"").text(msg)
        var msg_box_height = $("."+s_id+"").height()
        var msg_box_width = $("."+s_id+"").width()
        $("#"+s_id+"").css({
            
            "margin-top":"-"+msg_box_height/2+"px",
            "margin-left":"-"+msg_box_width/2+"px",
            "top":"50%",
            "left":"50%"
        })
        $("#"+s_id+"").animate({opacity:1},aniTime)
        setTimeout(()=>{
            $("#"+s_id+"").animate({opacity:0},aniTime)
        },showTime)
        setTimeout(()=>{
            $("#"+s_id+"").remove()
        },showTime+aniTime*2+100)
    }
    
}



class NotificationManager {
    constructor() {
        if (NotificationManager.instance) {
            return NotificationManager.instance;
        }
        
        this.permission = null;
        this.checkPermission();
        NotificationManager.instance = this;
    }
    
    static getInstance() {
        if (!NotificationManager.instance) {
            NotificationManager.instance = new NotificationManager();
        }
        return NotificationManager.instance;
    }
    async isMobile(){
        return await navigator.userAgentData.mobile
    }
    getPlatform(){
        return navigator.userAgentData.platform
    }
    checkPermission() {
        if (!('Notification' in window)) {
            this.permission = 'unsupported';
            return;
        }
        
        this.permission = Notification.permission;
    }
    
    async requestPermission() {
        if (!('Notification' in window)) {
            throw new Error('此浏览器不支持通知功能');
        }
        
        if (this.permission === 'granted') {
            return true;
        }
        
        try {
            const permission = await Notification.requestPermission();
            this.permission = permission;
            return permission === 'granted';
        } catch (error) {
            console.error('请求通知权限时出错:', error);
            return false;
        }
    }
    
    sendNotification(title, body, icon = '', image = '') {
        if (this.permission !== 'granted') {
            console.warn('通知权限未授予，无法发送通知');
            return null;
        }
        
        const options = {
            body: body,
            icon: icon || undefined,
            requireInteraction: false
        };
        
        // 如果提供了图片，添加到选项
        if (image) {
            options.image = image;
        }
        
        const notification = new Notification(title, options);
        
        // 设置自动关闭
        setTimeout(() => {
            notification.close();
        }, 5000);
        
        // 点击通知时关闭
        notification.onclick = () => {
            window.focus();
            notification.close();
        };
        
        return notification;
    }

   
    static ShowGlobalTopScrollText(options = {}) {

        return NotificationManager.getInstance()._showGlobalTopScrollText({
            msg: "",
            duration: 8000,
            fontSize: 100,
            fontWeight: "0",

            textGradient: [
                "#FFFFFF",
                "#FFFFFF"
            ],

            strokeWidth: 3,

            strokeGradient: [
                "#000000",
                "#000000"
            ],

            shadowBlur: 15,

            shadowColor: "#FFFFFF",

            top: 30,

            zIndex: 999999,

            ...options
        });
    }

    static ShowGlobalTopScrollVIPText(msg) {

        return NotificationManager.ShowGlobalTopScrollText({

            msg,

            textGradient: [
                "#FFF8C6",
                "#FFD700",
                "#FF9F00"
            ],

            strokeGradient: [
                "#ffffff",
                "#f7ff83"
            ],

            shadowColor: "#FFD700",
            shadowBlur: 25
        });
    }

    static ShowGlobalTopScrollPayText(msg) {

        return NotificationManager.ShowGlobalTopScrollText({

            msg,

            textGradient: [
                "#ffb341",
                "#ff6753"
            ],

            strokeGradient: [
                "#ff5d72",
                "#e4fff2"
            ],

            shadowColor: "#00FF88",
            shadowBlur: 20
        });
    }

    static ShowGlobalTopScrollGiftText(msg) {

        return NotificationManager.ShowGlobalTopScrollText({

            msg,

            textGradient: [
                "#FFC9F9",
                "#FF59D6"
            ],

            strokeGradient: [
                "#ffe5cf",
                "#ffd6a0"
            ],

            shadowColor: "#FF59D6",
            shadowBlur: 25
        });
    }

    _showGlobalTopScrollText(opt) {

        if (!this._scrollContainer) {

            this._scrollContainer = document.createElement("div");

            this._scrollContainer.style.position = "fixed";
            this._scrollContainer.style.left = "0";
            this._scrollContainer.style.top = "0";
            this._scrollContainer.style.width = "100%";
            this._scrollContainer.style.pointerEvents = "none";
            this._scrollContainer.style.zIndex = opt.zIndex;

            document.body.appendChild(
                this._scrollContainer
            );
        }

        const item = document.createElement("div");

        const textGradient =
            `linear-gradient(90deg, ${opt.textGradient.join(",")})`;

        item.innerHTML = `
            <span>${opt.msg}</span>
        `;

        item.style.position = "absolute";
        item.style.whiteSpace = "nowrap";
        item.style.fontWeight = opt.fontWeight;
        item.style.fontSize = `${opt.fontSize}px`;
        item.style.top = `${opt.top}px`;

        item.style.background = textGradient;

        item.style.webkitBackgroundClip = "text";
        item.style.backgroundClip = "text";

        item.style.color = "transparent";

        item.style.filter =
            `drop-shadow(0 0 ${opt.shadowBlur}px ${opt.shadowColor})`;

        const strokeColor =
            opt.strokeGradient[0];

        item.style.webkitTextStroke =
            `${opt.strokeWidth}px ${strokeColor}`;

        item.style.left = "100%";

        this._scrollContainer.appendChild(
            item
        );

        const totalWidth =
            item.offsetWidth;

        const start =
            window.innerWidth;

        const end =
            -totalWidth - 50;

        const beginTime =
            performance.now();

        const animate = (now) => {

            const p =
                (now - beginTime) / opt.duration;

            if (p >= 1) {

                item.remove();
                return;
            }

            const x =
                start +
                (end - start) * p;

            item.style.transform =
                `translateX(${x - start}px)`;

            requestAnimationFrame(
                animate
            );
        };

        requestAnimationFrame(
            animate
        );
    }
}


