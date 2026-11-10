var NATIVE_MESSAGING_HOST = "com.erjoalgo.chrome_current_url";
const ICON_PATH = '/link-128.png';

function notify (title, message) {
    chrome.notifications.create({
        type: 'basic',
        iconUrl: ICON_PATH,
        title: title,
        message: message,
        priority: 1
    });
}

function start () {
    var port = chrome.runtime.connectNative(NATIVE_MESSAGING_HOST);
    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        console.error("Disconnected: "+chrome.runtime.lastError.message);
        var msg = [
            "chrome-url disconnected: " + chrome.runtime.lastError.message,
            "Hint: consider installing or upgrading the native host app: \n",
            "$ pip install -U chromeurl",
            "$ chromeurl --install-manifest native"].join("\n");
        console.error(msg);
        notify("ChromeURL Disconnected", msg);
        port.disconnected = true;
    });

    function postMessage ( path, data )  {
        if (port.disconnected) {
            console.error(`refusing to post message. port has been disconnected.`);
            return;
        }
        port.postMessage({path: path, data: data});
    }

    function postCurrentTabUrl () {
        // chrome.tabs.getCurrent(function(current){ this is the background page tab
        chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
            if (tabs.length == 0) {
                return;
            }
            var tab = tabs[0];
            postMessage("/tabs/current/url", {url: tab.url,
                                              title: tab.title});
        });
    }

    chrome.tabs.onActivated.addListener(function(activeInfo){
        postCurrentTabUrl();
    });

    chrome.tabs.onUpdated.addListener(function(tabId, changeInfo){
        if (changeInfo.url != null) {
            postCurrentTabUrl();
        }
    });

    chrome.windows.onFocusChanged.addListener(function(windowId){
        if (windowId != chrome.windows.WINDOW_ID_NONE) {
            chrome.tabs.query({windowId: windowId, active: true}, function(tabs){
                // assume there is always a tab if there is a current window
                postCurrentTabUrl();
            });
        }
    });
    // set the current tab on startup
    postCurrentTabUrl();
}

chrome.runtime.onInstalled.addListener(function() {
    start();
});

chrome.runtime.onStartup.addListener(function() {
    // console.log( "on startup..." );
    start();
});

// TODO lint
