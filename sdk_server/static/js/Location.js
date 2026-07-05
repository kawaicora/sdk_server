import SocketIOMaster from "/static/js/SocketIOMaster.js";
import LoggerManager from "/static/js/LoggerManager.js";
class Location {
    constructor() {
        this.location = null;
        this.logger = new LoggerManager("Location", LoggerManager.LEVELS.ALL);
        this.markers = {};
        this.points = {};
        this.group = null;
        SocketIOMaster.on('connected', (data) => {
            this.logger.debug(`用户注册成功 ${JSON.stringify(data, null, 2)}`);
            this.Init()
            setInterval(() => this.reportLocation(), 10000);
        });

        SocketIOMaster.on('user-location', this.UserLocationHandler.bind(this));

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
            this.logger.debug(`\n********************************* \nsend_loc_info: ${JSON.stringify(data,null,2)}`);
            SocketIOMaster.emit('user-location',data);
            
        } catch (e) {
            this.logger.error(`loc_info access fail: ${e.message}`);
        }
    }
    Init() {

        this.map = L.map("map").setView([30, 120], 5);

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution: "OpenStreetMap"
            }
            
        ).addTo(this.map);

        this.group = L.featureGroup().addTo(this.map);

       
        
    }

    async UserLocationHandler(data) {
        
        const id = data.user_id;
        const latlng = [
            data.loc_info.latitude,
            data.loc_info.longitude
        ];
        
        // 第一次出现
        if (!this.markers[id]) {

            const marker = L.marker(latlng, {
                title: data.username
            });

            // 名字一直显示在下面
            marker.bindTooltip(data.username, {
                permanent: true,
                direction: "bottom",
                offset: [-15, 20]
            });

            marker.addTo(this.group);

            this.markers[id] = marker;
            
      

        } else {

            this.markers[id].setLatLng(latlng);

        }
        // // 自动缩放到所有人
        // const bounds = this.group.getBounds();

        // if (bounds.isValid()) {
        //     this.map.fitBounds(bounds, {
        //         padding: [40, 40],
        //         maxZoom: 16
        //     });
        // }

        this.logger.debug(`\n********************************* \nrecv_loc_info: ${JSON.stringify(data,null,2)}`);
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