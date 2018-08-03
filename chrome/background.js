chrome.runtime.onInstalled.addListener(function() {
    alert("chrome url installed");
}

chrome.runtime.onStartup.addListener(function() {
    var nativeMessagingHost = "com.erjoalgo.chrome_current_url";
    var port = chrome.runtime.connectNative(nativeMessagingHost);

    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        console.log("Disconnected");
        console.log("Disconnected: "+chrome.runtime.lastError.message);
    });

    function postCurrentTabUrl (tabId) {
        chrome.tabs.get(tabId, function(tab){
            if (tab != null) {
                var url = tab.url;
                port.postMessage({ text: url });
            }
        });
    }

    chrome.tabs.onActivated.addListener(function(activeInfo){postCurrentTabUrl(activeInfo.tabId)});

    chrome.tabs.onUpdated.addListener(function(tabId){postCurrentTabUrl(tabId)});

    chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
        // assume there is always a tab if there is a current window
        postCurrentTabUrl(tabs[0].id);
    });
});

