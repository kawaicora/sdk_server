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
            var data  = {
                user_id: sessionStorage.getItem("uid"),
                platform:navigator.platform,
                user_agent:navigator.userAgent,
                
                loc_info:loc
            }
            this.logger.debug(`loc_info: ${JSON.stringify(data)}`);
            SocketIOMaster.emit('user-location',data);
        } catch (e) {
            this.logger.error(`loc_info access fail: ${e.message}`);
        }
    }

    async UserLocationHandler(data) {
        this.logger.debug(`收到用户地理位置: ${JSON.stringify(data)}`);
        if(document.getElementById('map_' + data.user_id)){
            return;
        }
        var tmp = document.createElement('div');
        tmp.style.width = '300px';
        tmp.style.height = '150px';
        tmp.id = 'map_' + data.user_id;
        map_list.appendChild(tmp);
        try {
            var map=L.map(tmp.id).setView([data.loc_info.latitude,data.loc_info.longitude],10);
            L.tileLayer(
                'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                {
                    attribution:`user: ${data.user_id}` 
                }
            ).addTo(map);
            L.marker([data.loc_info.latitude,data.loc_info.longitude]).addTo(map);
        }catch(e){


        }
        
        
        
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