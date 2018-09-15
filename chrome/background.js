var POST_CURRENT_TAB_URL_SERVICE = "http://localhost:19615/tabs/current/url";
var NATIVE_MESSAGING_HOST = "com.erjoalgo.chrome_current_url";

function start ( mode ) {
    var port = chrome.runtime.connectNative(NATIVE_MESSAGING_HOST);
    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        console.log("Disconnected");
        console.log("Disconnected: "+chrome.runtime.lastError.message);
    });

    function postCurrentTabUrl () {
        // chrome.tabs.getCurrent(function(current){ this is the background page tab
        chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
            if (tabs.length>0) {
                var tab = tabs[0];
                // assert(tab);
                var url = tab.url;
                if (mode == "native") {
                    port.postMessage({ text: url });
                } else if (mode == "http") {
                    var xhr = new XMLHttpRequest();
                    xhr.open('POST', POST_CURRENT_TAB_URL_SERVICE, true);
                    xhr.setRequestHeader('Content-type', 'application/json');
                    xhr.onreadystatechange = function() {
                        if(xhr.readyState == 4 && xhr.status != 200) {
                            console.log("failed to update current tab url: "+xhr.status);
                            // alert(xhr.responseText);
                        }
                    }
                    xhr.send(JSON.stringify({url: url}));
                } else  {
                    console.log("unknown mode: "+mode);
                }
            }
        });
    }

    chrome.tabs.onActivated.addListener(function(activeInfo){
        console.log("via activated");
        postCurrentTabUrl();
    });

    chrome.tabs.onUpdated.addListener(function(tabId, changeInfo){
        console.log("via on updated");
        console.log("changes: ");
        console.log(changeInfo);
        postCurrentTabUrl();
    });

    chrome.windows.onFocusChanged.addListener(function(windowId){
        if (windowId != chrome.windows.WINDOW_ID_NONE) {
            chrome.tabs.query({windowId: windowId, active: true}, function(tabs){
                // assume there is always a tab if there is a current window
                console.log("via on-focus changed");
                postCurrentTabUrl();
            });
        }
    });

    // set the current tab initially
    chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
        // assume there is always a tab if there is a current window
        console.log("via startup");
        postCurrentTabUrl();
    });

    // TODO shutdown native host process on exit
    // chrome.runtime.onExit.addListener(function() {
    //     port.postMessage({ exit: true });
    // });
}

var MODE = "http";
chrome.runtime.onInstalled.addListener(function() {
    alert("chrome url installed!");
    start(MODE);
});

chrome.runtime.onStartup.addListener(function() {
    // console.log( "on startup..." );
    start(MODE);
});
