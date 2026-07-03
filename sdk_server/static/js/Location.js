import SocketIOMaster from "/static/js/SocketIOMaster.js";

class Location {
    constructor() {
        this.location = null;
        this.logger = new LoggerManager("Location", LoggerManager.LEVELS.ALL);

        SocketIOMaster.connect();
        SocketIOMaster.emit('user-register');

        SocketIOMaster.on('user-registered', data => {
            sessionStorage.setItem("sid", data.sid);
            sessionStorage.setItem("uid", data.uid);
        });

        SocketIOMaster.on('user-location', this.UserLocationHandler.bind(this));

        setInterval(() => this.reportLocation(), 10000);
    }

    async reportLocation() {
        try {
            const loc = await this.GetLocation();
            this.logger.debug(`当前地理位置: ${JSON.stringify(loc)}`);
            SocketIOMaster.emit('user-location', {
                user_id: sessionStorage.getItem("uid"),
                platform:navigator.platform,
                user_agent:navigator.userAgent,
                
                loc_info:loc
            });
        } catch (e) {
            this.logger.error(`获取地理位置失败: ${e.message}`);
        }
    }

    async UserLocationHandler(data) {
        this.logger.debug(`收到用户地理位置: ${JSON.stringify(data)}`);
    }

    async GetLocation() {
        if (this.location) return this.location;

        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                pos => {
                    this.location = pos.coords;
                    resolve(this.location);
                },
                reject,
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        });
    }
}

export default new Location();