let changeColor = document.getElementById('changeColor');

var WHITE = "#ffffff";
var GREEN = '#3aa757';

var bkg = chrome.extension.getBackgroundPage();
function log ( msg ) {
    // alert(msg);
    console.log(msg);
    bkg.console.log(msg);
}

function toggleColor ( button ) {
    log("on toggle");
    chrome.storage.sync.get('color', function(data) {
        chrome.storage.sync.get('colorOn', function(colorOn) {
            log("colorOn.data is "+(colorOn.data || GREEN));
            // log("colorOn.data is "+colorOn);
            var ON = colorOn.data || GREEN;
            log("current is "+data.color);
            var color = data.color == WHITE? GREEN: WHITE;
            chrome.storage.sync.set({color: color}, function() {
                console.log('color is ' + color);
            })
            changeColor.style.backgroundColor = color;
            changeColor.setAttribute('value', color);
            log("now it is "+color);

            chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
                log("inside query");
                chrome.tabs.executeScript(
                    tabs[0].id,
                    {code:
                     // "alert('inside page script');"+
                     'document.body.style.backgroundColor = "' + color + '";'});
            });
            
        });
    });
};

changeColor.onclick = toggleColor;

toggleColor();
