class LoggerManager {
    static LEVELS = {
        ALL:-1,
        
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
    static GetLogger(TAG, LEVEL = LoggerManager.LEVELS.ALL){
        this.TAG = TAG;
        this.LEVEL = LEVEL;
    }
    log_ex(type,method, file, line, args) {
        const now = new Date();
        const timeStr = `[${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}.${now.getMilliseconds().toString().padStart(3, '0')}]`;
        
        
        // 构建日志头部（固定格式部分）
        const logHeader = `${timeStr} [${this.getLogTypeDesc(type)}] [${this.TAG}] [${file}:${line} in ${method}]`;
        // 构建 console 样式字符串
        const logStyle = this.getLogStyle(type);

        // 根据类型选择对应的 console 方法，复用多参数特性输出
        switch (type) {
            case 1:
                // console.debug 支持多参数，依次传入样式、头部、剩余参数（自动展开）
                console.log(`%c${logHeader}`, logStyle, ...args);
                break;
            case 2:
                console.info(`%c${logHeader}`, logStyle, ...args);
                break;
            case 3:
                console.warn(`%c${logHeader}`, logStyle, ...args);
                break;
            case 4:
                console.error(`%c${logHeader}`, logStyle, ...args);
                break;
            default:
                console.log(`%c${logHeader}`, logStyle, ...args);
        }
    }

    // 辅助方法：获取日志类型描述（可选，优化可读性）
    getLogTypeDesc(type) {
        switch (type) {
            case 1: return "调试";
            case 2: return "信息";
            case 3: return "警告";
            case 4: return "错误";
            default: return "系统";
        }
    }

    // 辅助方法：获取日志样式（可选，抽离样式便于维护）
    getLogStyle(type) {
        switch (type) {
            case 1: return 'color: #795548;';
            case 2: return 'color: #00ffcc;';
            case 3: return 'color: #ffff55;';
            case 4: return 'color: #F44336; font-weight: bold;';
            default: return 'color: #607D8B;';
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
            this.log_ex(0,method, file, line,args)
        }
    }

    // 实现 console.info 方法
    info(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.INFO)) {
            const { method, file, line } = this.getCallerInfo(); 
            this.log_ex(LoggerManager.LEVELS.INFO,method, file, line,args)
        }
    }

    // 实现 console.warn 方法
    warn(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.WARN)) {
            const { method, file, line } = this.getCallerInfo(); 
            this.log_ex(LoggerManager.LEVELS.WARN,method, file, line,args)
        }
    }

    // 实现 console.error 方法
    error(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.ERROR)) {
            const { method, file, line } = this.getCallerInfo(); 
            this.log_ex(LoggerManager.LEVELS.ERROR,method, file, line,args)
        }
    }

    // 实现 console.debug 方法
    debug(...args) {
        if (this.shouldLog(LoggerManager.LEVELS.DEBUG)) {
            const { method, file, line } = this.getCallerInfo(); 
            this.log_ex(LoggerManager.LEVELS.DEBUG,method, file, line,args)
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


export default LoggerManager;