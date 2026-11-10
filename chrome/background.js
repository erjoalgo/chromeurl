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

var port = null;

function connect () {
    port = chrome.runtime.connectNative(NATIVE_MESSAGING_HOST);
    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        var error = chrome.runtime.lastError;
        var reason = error ? error.message : "native host exited";
        console.error("Disconnected: " + reason);
        var msg = [
            "chrome-url disconnected: " + reason,

            "Hint: consider installing or upgrading the native host app: \n",
            "$ pip install -U chromeurl",
            "$ chromeurl --install-manifest native"].join("\n");
        console.error(msg);
        notify("ChromeURL Disconnected", msg);
        port.disconnected = true;
    });
}

function postMessage ( path, data )  {
    if (port == null) {
        connect();
    }
    if (port.disconnected) {
        console.error(`refusing to post message. port has been disconnected.`);
        return;
    }
    port.postMessage({path: path, data: data});
}

function postTab ( tab ) {
    postMessage("/tabs/current/url", {url: tab.url,
                                      title: tab.title});
}

function postCurrentTabUrl () {
    // chrome.tabs.getCurrent(function(current){ this is the background page tab
    chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
        if (tabs.length == 0) {
            return;
        }
        postTab(tabs[0]);
    });
}

// Register listeners at the top level, so Chrome can wake the service
// worker for these events after stopping it.
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
            if (tabs.length > 0) {
                postTab(tabs[0]);
            }
        });

    }
});

// Connect and send the current tab whenever the service worker starts,
// including on browser startup and extension install.
postCurrentTabUrl();
// TODO lint
