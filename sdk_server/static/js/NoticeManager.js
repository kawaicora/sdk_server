

class NotificationManager {
    constructor() {
     
        this.permission = null;
        this.checkPermission();
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


}


export default new NotificationManager();