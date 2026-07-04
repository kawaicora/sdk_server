import SocketIOMaster from "/static/js/SocketIOMaster.js";

class Location {
    constructor() {
        this.location = null;
        this.logger = new LoggerManager("Location", LoggerManager.LEVELS.ALL);
        this.maps = {};
        this.markers = {};
        SocketIOMaster.connect();
        SocketIOMaster.emit('user-register');


        SocketIOMaster.on('user-location', this.UserLocationHandler.bind(this));

        setInterval(() => this.reportLocation(), 10000);
    }

    async reportLocation() {
        try {
            const loc = await this.GetLocation();
            var data  = {
                user_id: sessionStorage.getItem("uid"),
                username: sessionStorage.getItem("username"),
                platform:navigator.platform,
                user_agent:navigator.userAgent,
                loc_info:loc
            }
            this.logger.debug(`\n********************************* \nsend_loc_info: ${JSON.stringify(data)}`);
            SocketIOMaster.emit('user-location',data);
        } catch (e) {
            this.logger.error(`loc_info access fail: ${e.message}`);
        }
    }
    async UserLocationHandler(data) {

        this.logger.debug(`\n********************************* \nrecv_loc_info: ${JSON.stringify(data)}`);

        const id = data.user_id;
        const latlng = [
            data.loc_info.latitude,
            data.loc_info.longitude
        ];

        // 第一次创建
        if (!this.maps[id]) {

            const div = document.createElement("div");
            div.id = "map_" + id;
            div.style.width = "300px";
            div.style.height = "150px";

            map_list.appendChild(div);

            const map = L.map(div.id).setView(latlng, 12);

            L.tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {
                    attribution: `user: ${data.username}`,
                }
            ).addTo(map);

            const marker = L.marker(latlng).addTo(map);

            this.maps[id] = map;
            this.markers[id] = marker;

            return;
        }

        // 已存在，只更新位置
        this.markers[id].setLatLng(latlng);

        // 如果希望地图始终跟随用户
        this.maps[id].panTo(latlng);
    }

    async GetLocation() {
        if (this.location) {
            return this.location;
        }

        if (this.locationPromise) {
            return this.locationPromise;
        }

        this.locationPromise = new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                pos => {
                    this.location = pos.coords;
                    this.locationPromise = null;
                    resolve(this.location);
                },
                err => {
                    this.locationPromise = null;
                    reject(err);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 60000
                }
            );
        });

        return this.locationPromise;
    }
}

export default new Location();