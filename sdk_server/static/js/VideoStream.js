class VideoStream {

    constructor() {


        this.stream = new MediaStream();

        this.emptyVideoTimer = null;

        this.audioContext = null;
        this.emptyAudioOscillator = null;
    }
    SetVideoElement(videoElement) {

        this.videoElement = videoElement;

        if (this.videoElement) {
            this.videoElement.srcObject = this.stream;
            this.videoElement.autoplay = true;
            this.videoElement.playsInline = true;
        }
    }
    async GetEmptyVideoAndAudioStream() {

        await Promise.all([
            this.GetEmptyVideoStream(),
            this.GetEmptyAudioStream()
        ]);

        return this;
    }

    GetCurrentVideoTrack() {
        return this.stream.getVideoTracks()[0] || null;
    }

    GetCurrentAudioTrack() {
        return this.stream.getAudioTracks()[0] || null;
    }

    UpdateVideoStream(stream) {
        this.stream.getVideoTracks().forEach(track => {
            this.stream.removeTrack(track);
        });

        stream.getVideoTracks().forEach(track => {
            this.stream.addTrack(track);
        });
        if (this.videoElement) {
            this.videoElement.srcObject = this.stream;
        }
    }

    UpdateAudioStream(stream) {

        this.stream.getAudioTracks().forEach(track => {
            this.stream.removeTrack(track);
        });

        stream.getAudioTracks().forEach(track => {
            this.stream.addTrack(track);
        });
        if (this.videoElement) {
            this.videoElement.srcObject = this.stream;
        }
       
    }

    async GetScreenStream() {

        if (!navigator.mediaDevices?.getDisplayMedia) {
            throw new Error("当前浏览器不支持屏幕共享");
        }

        const stream =
            await navigator.mediaDevices.getDisplayMedia({
                video: true,
                audio: {
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false,
                    channelCount: 2
                }
            });

        this.UpdateVideoStream(stream);
        if (stream.getAudioTracks().length > 0) {
            this.UpdateAudioStream(stream);
        }
       
        return stream;
    }

    async GetCameraStream(deviceId = null) {

        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("当前浏览器不支持摄像头访问");
        }
        if (deviceId == "default") {
            return await this.GetEmptyVideoStream();

        }
        const stream =
            await navigator.mediaDevices.getUserMedia({

                video: deviceId
                    ? {
                        deviceId: {
                            exact: deviceId
                        }
                    }
                    : true,

                audio: false
            });

        this.UpdateVideoStream(stream);

        return stream;
    }

    async GetAudioStream(deviceId = null) {

        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error("当前浏览器不支持麦克风访问");
        }
        if (deviceId == "empty") {
            return await this.GetEmptyAudioStream();
        }
        const stream =
            await navigator.mediaDevices.getUserMedia({

                video: false,

                audio: deviceId
                    ? {
                        deviceId: {
                            exact: deviceId
                        },
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: false,
                        channelCount: 2
                    }
                    : {
                        echoCancellation: false,
                        noiseSuppression: false,
                        autoGainControl: false,
                        channelCount: 2
                    }
            });

        this.UpdateAudioStream(stream);

        return stream;
    }

    async GetEmptyVideoStream() {

        if (this.emptyVideoTimer) {
            clearInterval(this.emptyVideoTimer);
            this.emptyVideoTimer = null;
        }

        const canvas =
            document.createElement("canvas");

        canvas.width = 1920;
        canvas.height = 1080;

        const ctx =
            canvas.getContext("2d");

        const img =
            new Image();

        img.src =
            "/static/img/only_audio.png";

        await new Promise((resolve, reject) => {
            img.onload = resolve;
            img.onerror = reject;
        });

        const draw = () => {

            ctx.clearRect(
                0,
                0,
                canvas.width,
                canvas.height
            );

            ctx.drawImage(
                img,
                0,
                0,
                canvas.width,
                canvas.height
            );
        };

        draw();

        this.emptyVideoTimer =
            setInterval(draw, 1000 / 15);

        const stream =
            canvas.captureStream(15);

        this.UpdateVideoStream(stream);
        return stream;
    }

    async GetEmptyAudioStream() {

        if (!this.audioContext) {
            this.audioContext =
                new (window.AudioContext ||
                    window.webkitAudioContext)();
        }

        if (this.emptyAudioOscillator) {
            try {
                this.emptyAudioOscillator.stop();
            } catch {
            }
        }

        const oscillator =
            this.audioContext.createOscillator();

        const gainNode =
            this.audioContext.createGain();

        gainNode.gain.value = 0;

        const destination =
            this.audioContext
                .createMediaStreamDestination();

        oscillator.connect(gainNode);
        gainNode.connect(destination);

        oscillator.start();

        this.emptyAudioOscillator =
            oscillator;

        const stream =
            destination.stream;

        this.UpdateAudioStream(stream);

        return stream;
    }

    async GetAudioDevices() {
            
        if (!navigator.mediaDevices?.enumerateDevices) {
            throw new Error("当前浏览器不支持获取媒体设备");
        }

        const devices =
            await navigator.mediaDevices.enumerateDevices();

        return devices.filter(
            d => d.kind === "audioinput"
        );
    }

    async GetVideoDevices() {

        if (!navigator.mediaDevices?.enumerateDevices) {
            throw new Error("当前浏览器不支持获取媒体设备");
        }
        const devices =
            await navigator.mediaDevices.enumerateDevices();

        return devices.filter(
            d => d.kind === "videoinput"
        );
    }

    Destroy() {

        if (this.emptyVideoTimer) {

            clearInterval(this.emptyVideoTimer);

            this.emptyVideoTimer = null;
        }

        if (this.emptyAudioOscillator) {

            try {
                this.emptyAudioOscillator.stop();
            } catch {
            }

            this.emptyAudioOscillator = null;
        }

        this.stream
            .getTracks()
            .forEach(track => {

                try {
                    track.stop();
                } catch {
                }
            });

        if (this.audioContext) {

            try {
                this.audioContext.close();
            } catch {
            }

            this.audioContext = null;
        }
    }
}


export default new VideoStream();