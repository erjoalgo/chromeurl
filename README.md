

# Installation

    $ pip3 install chromeurl
    $ chromeurl --install-manifest all


# Development

1.  Obtain the chrome native component (python package). Options:
    -   from the source tree
        
            $ pip install --user ./native
2.  Install the extension. Options:
    -   automatically from the web store
        
            $ chromeurl --install-manifest extension
    -   manually from the [chrome web store](https://chrome.google.com/webstore/detail/chrome-current-url/eibefbdcoojolecpoehkpmgfaeapngjk)
    -   manually from local source tree (for development)
        -   navigate to `chrome://extensions/`
        -   `Load Unpacked` the extension directory rooted at `./chrome`
        -   note the extension \`ID\` as UNPACKED\_EXTENSION\_ID
3.  Install native host manifest (make chrome aware of the native host). Options:
    -   if extension came from the webstore
        
            $ chromeurl --install-manifest native
    -   if unpacked locally and loaded from source (for development):
        
            $ chromeurl --install-manifest native --extension-id <UNPACKED_EXTENSION_ID>


## Get current url

-   While chrome is running, make an HTTP request to get the current url
    
        $ curl http://127.0.0.1:19615/tabs/current/url
        https://developer.chrome.com/extensions/activeTab


## Debugging

-   start chromium from a terminal to see native host debug messages
-   navigate to the extension background from page (chrome://extensions)
    to see background page log messages


## Security

-   Any local process may read the user's current url
-   By default the browsing history is logged to ~/.browsing\_history.tsv


## Config file

-   Native host behavior can be configured via a config file at any of these locations:
    -   /etc/chromeurl.conf
    -   ~/.config/chromeurl.conf
-   Example config file:
    
        port = 1239
        verbose = True
        logfile = /dev/null
-   See $chromeurl --help$ for a list of options

