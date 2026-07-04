class Message {
       
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