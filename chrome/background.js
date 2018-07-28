var port;

function initTabNotifier (  ) {
    var nativeMessagingHost = "com.erjoalgo.chrome_current_url";
    port = chrome.runtime.connectNative(nativeMessagingHost);

    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        console.log("Disconnected");
        console.log("Disconnected: "+chrome.runtime.lastError.message);
    });
}

chrome.runtime.onInstalled.addListener(function() {
    initTabNotifier();

    chrome.tabs.onActivated.addListener(function(data){
        chrome.tabs.get(data.tabId, function(tab){
            var url = tab.url;
            port.postMessage({ text: url });
        });
    });
});

