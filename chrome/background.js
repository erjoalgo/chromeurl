var NATIVE_MESSAGING_HOST = "com.erjoalgo.chrome_current_url";

function start ( ) {
    var port = chrome.runtime.connectNative(NATIVE_MESSAGING_HOST);
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

    // TODO shutdown native host process on exit
    // chrome.runtime.onExit.addListener(function() {
    //     port.postMessage({ exit: true });
    // });
}

chrome.runtime.onInstalled.addListener(function() {
    alert("chrome url installed!");
    start();
});

chrome.runtime.onStartup.addListener(function() {
    // console.log( "on startup..." );
    start();
});
