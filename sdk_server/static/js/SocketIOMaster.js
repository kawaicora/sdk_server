class SocketIOMaster {

    constructor() {

        this.socket = null;

        // eventName -> Set<Function>
        this.handlers = new Map();
    }

    connect(url = window.location.origin) {

        if (this.socket) {
            return;
        }

        this.socket = io(url, {
            transports: ["polling"]
        });
    }

    on(name, func) {

        if (!this.socket) {
            throw new Error(
                "请先 connect()"
            );
        }

        let handlers =
            this.handlers.get(name);

        if (!handlers) {

            handlers = new Set();

            this.handlers.set(
                name,
                handlers
            );

            // Socket.IO 只注册一次
            this.socket.on(
                name,
                (...args) => {

                    const current =
                        this.handlers.get(name);

                    if (!current)
                        return;

                    for (const fn of current) {

                        try {
                            fn(...args);
                        }
                        catch (e) {
                            console.error(e);
                        }
                    }
                }
            );
        }

        handlers.add(func);
    }

    off(name, func) {

        const handlers =
            this.handlers.get(name);

        if (!handlers)
            return;

        handlers.delete(func);

        if (handlers.size === 0) {

            this.handlers.delete(name);

            // 可选
            this.socket.off(name);
        }
    }

    emit(name, ...args) {

        if (!this.socket) {
            throw new Error(
                "请先 connect()"
            );
        }

        this.socket.emit(
            name,
            ...args
        );
    }
}

export default new SocketIOMaster();