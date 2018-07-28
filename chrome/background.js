var port;

function initTabNotifier (  ) {
    console.log( "starting tab notifier" );

    var nativeMessagingHost = "com.erjoalgo.chrome_current_url";
    port = chrome.runtime.connectNative(nativeMessagingHost);

    console.log( "port created");
    // var port = chrome.runtime.connectNative('com.my_company.my_application');

    port.onMessage.addListener(function(msg) {
        console.log("Received" + msg);
    });

    port.onDisconnect.addListener(function() {
        console.log("Disconnected");
        console.log("Disconnected: "+chrome.runtime.lastError.message);
    });

    console.log( "posting message");
    port.postMessage({ text: "hHello, my_application" });
    console.log( "after post");
}

chrome.runtime.onInstalled.addListener(function() {
    console.log("installed...");
    initTabNotifier();

    chrome.tabs.onActivated.addListener(function(data){
        console.log( "tab changed: "+data );
        chrome.tabs.get(data.tabId, function(tab){
            var url = tab.url;
            console.log( "tab url: "+url );
            console.log( "sending message");
            port.postMessage({ text: url });
            console.log( "sent message");
        });
    });
});

