class BackgroundVideoDisplay {
    constructor(option) {
        this.media_com = document.createElement("video");
        this.media_com.id = "media_com";
        this.media_com.style.display = "none";

        if (typeof option.current_media_url === "undefined") {
            this.isloop = false;
        } else {
            this.isloop = option.isloop || false;
        }

        this.media_com.loop = this.isloop;
        this.media_com.muted = true;
        // this.media_com.autoplay = true;
        $('.content-container')[0].appendChild(this.media_com);

        this.current_media_info = {
            type: this.get_format_name(option.current_media_url),
            isLive: option.isLive,
            withCredentials: false,
            hasAudio: true,
            hasVideo: true,
            url: option.current_media_url
        };

        this.player = flvjs.createPlayer(this.current_media_info, {
            enableWorker: true,
            lazyLoadMaxDuration: 3 * 60,
            seekType: 'range',
        });

        this.player.attachMediaElement(this.media_com);
        this.player.load();
        this.app_to_background_play(this.media_com);

        try {
            this.media_com.play();
        } catch (error) {
            console.log(error);
        }

        document.getElementsByClassName("center-container")[0].onclick = () => {
            try {
                this.media_com.muted = !this.media_com.muted;
            } catch (error) {
                console.log(error);
            }
        };
    }

    init() {
        // 这里可以添加初始化逻辑
    }

    get_format_name(filename) {
        var index = filename.lastIndexOf(".");
        var suffix = filename.substr(index + 1);
        return suffix;
    }

    getHeightByWidth(width, w_h = "16:9") {
        var a_w_h = w_h.split(":");
        return a_w_h[1] * (width / a_w_h[0]);
    }

    getWidthByHeight(height, w_h = "16:9") {
        var a_w_h = w_h.split(":");
        return a_w_h[0] * (height / a_w_h[1]);
    }

    app_to_background_play(media_com = undefined) {
        if (media_com) {
            this.media_com = media_com;
        }
        var background_videoWidth = 1920;
        var background_videoHeight = 1080;
        var canvas = document.createElement("canvas");
        var canvas_style = "";

        canvas.setAttribute("style", canvas_style);
        $('.content-container')[0].appendChild(canvas);
        var ctx = canvas.getContext("2d");


        canvas.id = "backgroundFx";
        canvas_style = `position: fixed; width:auto;height:100%; z-index:-1;top:0;`;
        canvas.width = background_videoWidth;
        canvas.height = background_videoHeight;
        canvas.setAttribute("style", canvas_style);
        const drawSpectrum = () => {

            
            
            
            try {
                ctx.drawImage(this.media_com, 0, 0, background_videoWidth, background_videoHeight);
            } catch (e) {
                //ctx.drawImage(window.video_obj, 0, 0, background_videoWidth, background_videoHeight)
            }

            requestAnimationFrame(drawSpectrum);
        };

        drawSpectrum();
    }
}