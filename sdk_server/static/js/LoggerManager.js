class LoggerManager {
    static LEVELS = {
        DEBUG: 1,
        INFO: 2,
        WARN: 3,
        ERROR: 4
    }
    constructor(TAG, LEVEL) {
        this.TAG = TAG;
        this.LEVEL = LEVEL;
    }
    // 日志工具函数 - 仅输出到控制台
    log_ex(message, type = 2) {
        const now = new Date();
        const timeStr = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now.getMilliseconds().toString().padStart(3, '0')}]`;
        const { method, file, line } = this.getCallerInfo();
        // 根据类型输出不同样式的日志
        switch (type) {
            
            //   case 'sender':
            //     console.log(`%c${timeStr} [发送方] ${message}`, 'color: #4CAF50; font-weight: bold');
            //     break;
            //   case 'receiver':
            //     console.log(`%c${timeStr} [接收方] ${message}`, 'color: #2196F3; font-weight: bold');
            //     break;
            case 1:
                console.debug(`%c${timeStr} [调试] [${this.TAG}] [${file}:${line} in ${method}] ${message}`, 'color: #795548;');
                break;
            case 2:
                console.debug(`%c${timeStr} [信息] [${this.TAG}] [${file}:${line} in ${method}] ${message}`, 'color: #00ffcc;');
                break;
            case 3:
                console.debug(`%c${timeStr} [警告] [${this.TAG}] [${file}:${line} in ${method}] ${message}`, 'color: #ffff55;');
                break;
            case 4:
                console.error(`%c${timeStr} [错误] [${this.TAG}] [${file}:${line} in ${method}] ${message}`, 'color: #F44336; font-weight: bold');
                break;
            default:
                console.log(`%c${timeStr} [系统] [${this.TAG}] [${file}:${line} in ${method}] ${message}`, 'color: #607D8B;');
        }
    }

    // 辅助函数，用于检查是否允许输出该级别的日志
    shouldLog(level) {
        return level >= this.LEVEL;
    }

    // 获取调用栈信息
    getCallerInfo() {
        const error = new Error();
        const stackLines = error.stack.split('\n');
        // 跳过 LoggerManager 类自身的调用栈信息
        const callerLine = stackLines[3];
        const match = callerLine.match(/at (.*) \((.*):(\d+):(\d+)\)/);
        if (match) {
            const method = match[1];
            const file = match[2];
            const line = match[3];
            return { method, file, line };
        }
        return {};
    }

    // 实现 console.log 方法
    log(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG)) {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}]`, ...args);
        }
    }

    // 实现 console.info 方法
    info(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.INFO)) {
            const { method, file, line } = this.getCallerInfo();
            console.info(`[${this.TAG}] [${file}:${line} in ${method}]`, ...args);
        }
    }

    // 实现 console.warn 方法
    warn(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.WARN)) {
            const { method, file, line } = this.getCallerInfo();
            console.warn(`[${this.TAG}] [${file}:${line} in ${method}]`, ...args);
        }
    }

    // 实现 console.error 方法
    error(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.ERROR)) {
            const { method, file, line } = this.getCallerInfo();
            console.error(`[${this.TAG}] [${file}:${line} in ${method}]`, ...args);
        }
    }

    // 实现 console.debug 方法
    debug(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG)) {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}]`, ...args);
        }
    }

    // 实现 console.table 方法
    table(data, columns) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG)) {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}]`);
            console.table(data, columns);
        }
    }

    // 实现 console.time 方法
    time(label) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG)) {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}] Starting timer: ${label}`);
            console.time(label);
        }
    }

    // 实现 console.timeEnd 方法
    timeEnd(label) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG)) {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}] Ending timer: ${label}`);
            console.timeEnd(label);
        }
    }

    // 实现 console.group 方法
    group(label) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG) && typeof console.group === 'function') {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}] Starting group: ${label}`);
            console.group(label);
        }
    }

    // 实现 console.groupEnd 方法
    groupEnd() {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG) && typeof console.groupEnd === 'function') {
            const { method, file, line } = this.getCallerInfo();
            console.log(`[${this.TAG}] [${file}:${line} in ${method}] Ending group`);
            console.groupEnd();
        }
    }

    // 实现 console.clear 方法
    clear() {
        console.clear();
    }
}
