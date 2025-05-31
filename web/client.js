var pc = null;

function negotiate() {
    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });
    // 创建 DataChannel
    const dataChannel = pc.createDataChannel('statusChannel');
    // 监听 DataChannel 事件
    dataChannel.onopen = function() {
        console.log('DataChannel 已打开');
    };
    // 监听数字人状态
    dataChannel.onmessage = function(event) {
        const data = JSON.parse(event.data);
        // data结构：{status: 'start', text: '你好', msgenvent: null}
        // start：开始播放；end：结束播报
        if (data.status === 'start') {
            // 只有在非移动状态下才隐藏 loading
            if (!stateContext.isMoving) {
                loading.hide();
            }
            statusDisplay.hideAll();
            // 播报开始
            appendChatMessage('bot', data.text);
             // 激活打断按钮
            document.getElementById('interruptBtn').disabled = false;
        }
        if (data.status === 'end') {
            sendStatusMessage(!stateContext.isMoving);           
            if (stateContext.canSpeak) {
                statusDisplay.showListening();
            }
            // 禁用打断按钮
            document.getElementById('interruptBtn').disabled = true;
        }
    };

    return pc.createOffer().then((offer) => {
        return pc.setLocalDescription(offer);
    }).then(() => {
        // wait for ICE gathering to complete
        return new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(() => {
        var offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then((response) => {
        return response.json();
    }).then((answer) => {
        document.getElementById('sessionid').value = answer.sessionid;
        return pc.setRemoteDescription(answer);
    }).catch((e) => {
        alert(e);
    });
}

function start() {
    // 使用之前定义的rtcConfiguration
    pc = new RTCPeerConnection(rtcConfiguration);

    // connect audio / video
    pc.addEventListener('track', (evt) => {
        if (evt.track.kind == 'video') {
            document.getElementById('video').srcObject = evt.streams[0];
        } else {
            document.getElementById('audio').srcObject = evt.streams[0];
        }
    });

    negotiate();
}

function stop() {
    // close peer connection
    setTimeout(() => {
        pc.close();
    }, 500);
}

window.onunload = function(event) {
    // 在这里执行你想要的操作
    setTimeout(() => {
        pc.close();
    }, 500);
};

window.onbeforeunload = function (e) {
    setTimeout(() => {
            pc.close();
        }, 500);
    e = e || window.event
    // 兼容IE8和Firefox 4之前的版本
    if (e) {
        e.returnValue = '关闭提示'
    }
    // Chrome, Safari, Firefox 4+, Opera 12+ , IE 9+
    return '关闭提示'
}