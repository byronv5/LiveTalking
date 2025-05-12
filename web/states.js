// 基类
class State {
    do_next(text) {
        throw new Error("do_next 方法需要在具体状态中实现");
    }
}

// 实现类
class TaskAwakeState extends State {
    do_next(text) {
        appendChatMessage('user', text);
        loading.display('思考中...');
        handleDigitalHumanSpeak("你好，我是你的医疗助手小白，请问有什么可以帮到您的？");     
    }
}

class TaskMoveState extends State {
    do_next(text) {
        handleDigitalHumanSpeak("小白要开始移动了，请让一下哦~");
        loading.display('正在移动...');
    }
}

class TaskDirectState extends State {
    do_next(text) {
        handleDigitalHumanSpeak("小白开始执行导航任务了，请稍等哦~");
        loading.display('正在导航...');
    }
}

class TaskCompleteState extends State {
    do_next(text) {
        handleDigitalHumanSpeak("小白已到达指定位置");
    }
}

class ChatAskState extends State {
    do_next(text) {
        appendChatMessage('user', text);
        loading.display('思考中...');
    }
}

class ChatRespState extends State {
    do_next(text) {
        handleDigitalHumanSpeak(text);
    }
}

class TaskListeningState extends State {
    do_next(text) {
        // loading.display('正在听...');
    }
}

class TaskSleepingState extends State {
    do_next(text) {
        loading.display('休眠中...');
        clearChatContainer();
    }
}

class FocusAwakeState extends State {
    do_next(text) {
        handleDigitalHumanSpeak(text);
    }
}

class FocusStandbyState extends State {
    do_next(text) {
        handleDigitalHumanSpeak(text);
        loading.display('休眠中...');
        clearChatContainer();
    }
}

// 状态上下文
class StateContext {
    constructor() {
        this.isMoving = false;
        this.isSaying = false;
        this.states = {
            TASK_AWAKE: new TaskAwakeState(),
            TASK_MOVE: new TaskMoveState(),
            TASK_DIRECT: new TaskDirectState(),
            TASK_COMPLETE: new TaskCompleteState(),
            CHAT_ASK: new ChatAskState(),
            CHAT_RESP: new ChatRespState(),
            // TASK_LISTENING: new TaskListeningState(),
            TASK_SLEEPING: new TaskSleepingState(),
            FOCUS_AWAKE: new FocusAwakeState(),
            FOCUS_STANDBY: new FocusStandbyState(),
        };
    }

    handleState(payload) {
        const state = this.states[payload.command];
        this.isMoving = payload.command === 'TASK_MOVE' || payload.command === 'TASK_DIRECT';
        this.isSaying = payload.command === 'TASK_LISTENING' || payload.command === 'TASK_AWAKE' || payload.command === 'CHAT_RESP' || payload.command === 'TASK_COMPLETE';
        state.do_next(payload.text);
    }
}