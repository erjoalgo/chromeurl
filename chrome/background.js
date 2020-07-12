var CHROME_INFO_SERVICE = "http://localhost:19615";
var NATIVE_MESSAGING_HOST = "com.erjoalgo.chrome_current_url";

function start ( mode ) {
    var port = chrome.runtime.connectNative(NATIVE_MESSAGING_HOST);
    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        console.log("Disconnected: "+chrome.runtime.lastError.message);
        var msg = [
            "chrome-url disconnected: " + chrome.runtime.lastError.message,
            "Hint: consider installing or upgrading the native host app: \n",
            "$ pip install -U chromeurl",
            "$ chromeurl --install native"].join("\n");
        alert(msg);
    });

    function postMessage ( path, data, mode )  {
        if (mode == "stdin") {
            port.postMessage({path: path, data: data});
        } else if (mode == "http") {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', CHROME_INFO_SERVICE + path, true);
            xhr.setRequestHeader('Content-type', 'application/json');
            xhr.onreadystatechange = function() {
                if(xhr.readyState == 4) {
                    if (xhr.status != 200) {
                        var msg = (
                            "failed to update current tab url: "
                                + xhr.status+ " " + xhr.responseText)
                        console.log(msg);
                        alert(msg);
                    } else   {
                        console.log("posted url");
                    }
                }
            }
            if (data)  {
                xhr.send(JSON.stringify(data));
            }
        } else  {
            console.error("unknown mode: "+mode);
        }
    }

    function postCurrentTabUrl () {
        // chrome.tabs.getCurrent(function(current){ this is the background page tab
        chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
            if (tabs.length == 0) {
                return;
            }
            var tab = tabs[0];
            postMessage("/tabs/current/url", {url: tab.url}, mode);
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

// var MODE = "http";
var MODE = "stdin";

chrome.runtime.onInstalled.addListener(function() {
    start(MODE);
});

chrome.runtime.onStartup.addListener(function() {
    // console.log( "on startup..." );
    start(MODE);
});
// TODO lint
