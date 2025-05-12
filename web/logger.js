// 保存原始的 console 方法
const originalConsole = {
    log: console.log,
    error: console.error,
    warn: console.warn,
    info: console.info
};

// 格式化时间
function formatTime() {
    const now = new Date();
    return now.toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
    });
}

// 重写 console 方法
console.log = function() {
    const args = Array.from(arguments);
    originalConsole.log(`[${formatTime()}]`, ...args);
};

console.error = function() {
    const args = Array.from(arguments);
    originalConsole.error(`[${formatTime()}]`, ...args);
};

console.warn = function() {
    const args = Array.from(arguments);
    originalConsole.warn(`[${formatTime()}]`, ...args);
};

console.info = function() {
    const args = Array.from(arguments);
    originalConsole.info(`[${formatTime()}]`, ...args);
};