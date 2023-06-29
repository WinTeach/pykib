Python Based Kiosk Browser
Python3 and packages from requirements.txt are neccessary to run this browser.

Output from -h (--help):
------------------------------------------------------------------------------
usage: pykib [-h] [-c CONFIGFILE] [-u URL] [-p PROXY] [-ppo PROXYPORT]
             [-pu PROXYUSERNAME] [-pp PROXYPASSWORD]
             [-ppp PERSISTENTPROFILEPATH] [-amc ADDMEMORYCAP] [-d]
             [-dh DOWNLOADHANDLE [DOWNLOADHANDLE ...]] [-dp DOWNLOADPATH]
             [-ijs INJECTJAVASCRIPT [INJECTJAVASCRIPT ...]] [-eal]
             [-alu AUTOLOGONUSER] [-alp AUTOLOGONPASSWORD]
             [-ald AUTOLOGONDOMAIN] [-aluid AUTOLOGONUSERID]
             [-alpid AUTOLOGONPASSWORDID] [-aldid AUTOLOGONDOMAINID] [-es]
             [-sl SPELLCHECKINGLANGUAGE] [-eps] [-prm]
             [-sbl SETBROWSERLANGUAGE] [-scua] [-t TITLE] [-dt]
             [-san SYSTEMAPPLICATIONNAME] [-rt] [-f] [-aot] [-rwc] [-ic] [-m]
             [-v] [-rdpv] [-isds] [-szf SETZOOMFACTOR] [--no-sandbox]
             [--name NAME] [--disable-gpu] [--js-flags JS-FLAGS]
             [--single-process]
             [--remote-debugging-port REMOTE-DEBUGGING-PORT] [-md] [-sa] [-sn]
             [-slpb] [-ecm] [-etm] [-sih] [-ecbpo]
             [-g GEOMETRY [GEOMETRY ...]] [-ng] [-a ADMINKEY] [-epkh]
             [-wl WHITELIST [WHITELIST ...]] [-wlmfo] [-ll LOGLEVEL] [-sjsc]
             [-art AUTORELOADTIMER] [-brt BROWSERRESETTIMEOUT] [-ama] [-awa]
             [-ads] [-abn] [-pns] [-emd] [-sp] [-spp STOREPIDPATH] [-rbd]
             [-rbmi REMOTEBROWSERMOVEINTERVAL]
             [-rbmpmi REMOTEBROWSERPIXMAPMONITORINTERVAL]
             [-rl REMOTINGLIST [REMOTINGLIST ...]] [-aubr] [-rbix11]
             [-rbsp REMOTEBROWSERSOCKETPATH]
             [-rbkai REMOTEBROWSERKEEPALIVEINTERVAL]
             [-rbkael REMOTEBROWSERKEEPALIVEERRORLIMIT]
             [-rbp REMOTEBROWSERPORT] [-rbst REMOTEBROWSERSESSIONTOKEN]
             [-utst] [-tstp TEMPORARYSESSIONTOKENPATH]
             [URL]

positional arguments:
  URL                   alternative to -u, --url

options:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configFile CONFIGFILE
                        Use this as configuration file - configured setting
                        will override command line arguments. The ini file
                        settings parameters are the same like the long form
                        command line arguments
  -u URL, --url URL     Start and Home URL
  -p PROXY, --proxy PROXY
                        Use this as HTTP Proxy
  -ppo PROXYPORT, --proxyPort PROXYPORT
                        Proxy Port
  -pu PROXYUSERNAME, --proxyUsername PROXYUSERNAME
                        Enter Proxy username if needed
  -pp PROXYPASSWORD, --proxyPassword PROXYPASSWORD
                        Enter Proxy password if needed
  -ppp PERSISTENTPROFILEPATH, --persistentProfilePath PERSISTENTPROFILEPATH
                        Defines a folder where the webprofile should be
                        stored. Browser will be allways in private mode if not
                        defined
  -amc ADDMEMORYCAP, --addMemoryCap ADDMEMORYCAP
                        Can be set to a value in MB. If the browser needs more
                        than this amount of memory he will kill itself
  -d, --download        Enables download function
  -dh DOWNLOADHANDLE [DOWNLOADHANDLE ...], --downloadHandle DOWNLOADHANDLE [DOWNLOADHANDLE ...]
                        With this option, default behaviour for special file
                        extensions can be defined, this will also work when -d
                        is not defined. Format:
                        #extension#|#app_to_start#|#tmpdownloadpath#
  -dp DOWNLOADPATH, --downloadPath DOWNLOADPATH
                        Defines the start path for any download and upload
                        dialog
  -ijs INJECTJAVASCRIPT [INJECTJAVASCRIPT ...], --injectJavascript INJECTJAVASCRIPT [INJECTJAVASCRIPT ...]
                        With this option, a js script file can be defined
                        which should be injected on every page when
                        loadFinished is triggered.Format: #pathToScript#|#once
                        #|#argX#::argXvalue.....#pathToScript# = path to
                        Script. Full path or relative to folder 'scripts' from
                        installation dir#once# = 0 or 1. If 1 it will be
                        injected only when the first site load completes. With
                        0 or default it will be injected each time a site is
                        loaded.#argX#::#value# = define Arguments which should
                        be replaced in Script File at Runtime. in Script use
                        {argX} in script file
  -eal, --enableAutoLogon
                        Enables the autologon functionality, this function
                        requires at least autoLogonUser and autoLogonPassword
                        to be set. The Browser is preconfigured to work with
                        Citrix Webinterface, Citrix Storefront and RDWeb
                        Servers
  -alu AUTOLOGONUSER, --autoLogonUser AUTOLOGONUSER
                        Defines the username used for autologon
  -alp AUTOLOGONPASSWORD, --autoLogonPassword AUTOLOGONPASSWORD
                        Defines the password used for autologon
  -ald AUTOLOGONDOMAIN, --autoLogonDomain AUTOLOGONDOMAIN
                        Defines the domain name used for autologon. If a
                        domain name is set, but no value for
                        autoLogonDomainID, the domain will bei merged with the
                        username to domain\username
  -aluid AUTOLOGONUSERID, --autoLogonUserID AUTOLOGONUSERID
                        Defines the ID of the HTML Element in which the
                        username should be put in
  -alpid AUTOLOGONPASSWORDID, --autoLogonPasswordID AUTOLOGONPASSWORDID
                        Defines the ID of the HTML Element in which the
                        password should be put in
  -aldid AUTOLOGONDOMAINID, --autoLogonDomainID AUTOLOGONDOMAINID
                        Defines the ID of the HTML Element in which the domain
                        should be put in
  -es, --enablespellcheck
                        Enables spellchecking when set
  -sl SPELLCHECKINGLANGUAGE, --spellcheckinglanguage SPELLCHECKINGLANGUAGE
                        Defines the language for the spellcheck dictionary.
                        Default en_US
  -eps, --enablepdfsupport
                        Enables the Option of viewing PDFs in the
                        BrowserWindow
  -prm, --pdfreadermode
                        if set the close button will close pykib complete
                        instead of only the pdf and the Download Button will
                        be labeld with 'save'
  -sbl SETBROWSERLANGUAGE, --setbrowserlanguage SETBROWSERLANGUAGE
                        Overrides the default Browser Language in format de
                        (for German), en (for English)....
  -scua, --setCitrixUserAgent
                        Overrides the default UserAgent for skipping citrix
                        receivers client detection
  -t TITLE, --title TITLE
                        Defines the Window Title
  -dt, --dynamicTitle   When enabled the window title will display the current
                        websites title
  -san SYSTEMAPPLICATIONNAME, --systemApplicationName SYSTEMAPPLICATIONNAME
                        With this option the system application Name which
                        will shown on pulse audio and some other apps can be
                        overritten
  -rt, --removeTitleBar
                        Removes the window title bar
  -f, --fullscreen      Start browser in fullscreen mode
  -aot, --alwaysOnTop   Makes the Browser Windows to Stay always on top of all
                        other Windows
  -rwc, --removeWindowControls
                        This Option will remove the top Window Frame (with the
                        Buttons Minimize/Maximize/Close)
  -ic, --ignoreCertificates
                        with this option HTTPS Warnings will be ignored
  -m, --maximized       Start browser in a maximized window
  -v, --version         show program's version number and exit
  -rdpv, --remoteDaemonProtocolVersion
                        show program's version number and exit
  -isds, --ignoreSystemDpiSettings
                        When set, the Browser won't try to use the systems DPI
                        Settings
  -szf SETZOOMFACTOR, --setZoomFactor SETZOOMFACTOR
                        Set Zoom Factor for Webpages in percent. Allowed
                        Values between 25 and 500. Allowed only in combination
                        with ignoreSystemDpiSettings
  --no-sandbox          Allows to run as root
  --name NAME           Used to set the WM_CLASS
  --disable-gpu         Disables QTs GPU Support
  --js-flags JS-FLAGS   Allows setting js-flags
  --single-process      Allows to run the browser in one thread
  --remote-debugging-port REMOTE-DEBUGGING-PORT
                        Allows to debug with chromes webbrowser console
  -md, --memoryDebug    Show informations about the browser current memory
                        usage
  -sa, --showAddressBar
                        Shows a Address Bar when set
  -sn, --showNavigationButtons
                        Shows Navigation Buttons when set
  -slpb, --showLoadingProgressBar
                        Shows a Progress Bar on site loading.
  -ecm, --enableContextMenu
                        Enables a minimal context Menu
  -etm, --enableTrayMode
                        when this option is set the browser will be minimized
                        to tray instead of closed
  -sih, --startInTray   when this option is set the browser will start to
                        Tray.
  -ecbpo, --enableCleanupBrowserProfileOption
                        when this option is set the user has the option to
                        Cleanup the Browser Profile (in tray and context
                        menu). When 'Cleanup Browser Profile' is performed it
                        will:- remove all Browser Cookies- perform
                        localStorage.clean() and sessionStorage.clean() via
                        JS- reload the current Site
  -g GEOMETRY [GEOMETRY ...], --geometry GEOMETRY [GEOMETRY ...]
                        Set window geomety #left# #top# #width# #height#, when
                        using a multimonitor envireoment you can define the
                        monitor for fullscreen or maximized mode with #left#
                        #top#
  -ng, --normalizeGeometry
                        This Option makes the #left# geometry Parameter be
                        calculated started from the primary screen (windows
                        default behavior). Specially help full in multi
                        monitor enviroments when using the remote damon
                        function
  -a ADMINKEY, --enableAdminKey ADMINKEY
                        Enables the admin key SHIFT+STRG+ALT+A and defines a
                        Application which will be started when pushed
  -epkh, --enablePrintKeyHandle
                        When enabled, a press on the 'Print'-Button will
                        insert a Image of the current page to the clipboard
  -wl WHITELIST [WHITELIST ...], --whiteList WHITELIST [WHITELIST ...]
                        Enables the white List function. Only Urls which start
                        with elemtens from this list could be opend
  -wlmfo, --whiteListMainFrameOnly
                        When set, whitelist will only be checked in mainframe
                        navigation requests
  -ll LOGLEVEL, --logLevel LOGLEVEL
                        Setting the Level of Loggin. Allowed Values are ERROR,
                        INFO, WARNING and DEBUG, Default is ERROR
  -sjsc, --showJsConsole
                        Showing all js console entry on in DEBUG log
  -art AUTORELOADTIMER, --autoReloadTimer AUTORELOADTIMER
                        Here you can configure a Timeout (in seconds) after
                        which the actives site gets reloaded
  -brt BROWSERRESETTIMEOUT, --browserResetTimeout BROWSERRESETTIMEOUT
                        Here you can configure a Timeout of inactivity (in
                        seconds) after which the browser will be resettet
  -ama, --allowMicAccess
                        Allows all Websites to use your Microfon
  -awa, --allowWebcamAccess
                        Allows all Websites to use your Webcam
  -ads, --allowDesktopSharing
                        Allows all Websites to share your screen and local
                        computers audio
  -abn, --allowBrowserNotifications
                        Allows all Websites to send Push Notifications
  -pns, --playNotificationSound
                        if set a sound jingle is played when a notification is
                        received
  -emd, --enableMouseDrag
                        Enable Single Click (Touch) website movement (js
                        injection)
  -sp, --storePid       With this Option each start of the Rangee Browser the
                        current Process ID will be written to the file
                        .pykibLatestProcId in the users tmp path
  -spp STOREPIDPATH, --storePidPath STOREPIDPATH
                        Path where the temporary current process id should be
                        stored on the system. Only works in combination with
                        --storePid
  -rbd, --remoteBrowserDaemon
                        start a remote browser daemon
  -rbmi REMOTEBROWSERMOVEINTERVAL, --remoteBrowserMoveInterval REMOTEBROWSERMOVEINTERVAL
                        Define Interval in ms in which movement requests are
                        send when moving the remote browser window - Default
                        50ms
  -rbmpmi REMOTEBROWSERPIXMAPMONITORINTERVAL, --remoteBrowserPixmapMonitorInterval REMOTEBROWSERPIXMAPMONITORINTERVAL
                        This option allows you to define the interval at which
                        the optionally installed server-side connector app
                        monitors the viewport of the server-side browser for
                        overlapping applications. If an overlapping
                        application is detected, the server sends a pixmap to
                        the remote browser, which cuts out the area of the
                        overlapping application.Lower values lead to a higher
                        CPU load on the server side. disabled = 0, min = 50,
                        max = 2000, Default 300ms
  -rl REMOTINGLIST [REMOTINGLIST ...], --remotingList REMOTINGLIST [REMOTINGLIST ...]
                        Defined a List of Urls which should be remoted - use *
                        as wildcard
  -aubr, --allowUserBasedRemoting
                        When this option is set, the user on the remote side
                        is allowed to define an own additional remoting list
  -rbix11, --remoteBrowserIgnoreX11
                        With this Option X11BypassWindowManagerHint will be
                        used to force the browser to top. Usually not needed
  -rbsp REMOTEBROWSERSOCKETPATH, --remoteBrowserSocketPath REMOTEBROWSERSOCKETPATH
                        When this option is set, the remote browser Deamon
                        will only listen to commands send to this socket. Any
                        other communication options will be disabled
  -rbkai REMOTEBROWSERKEEPALIVEINTERVAL, --remoteBrowserKeepAliveInterval REMOTEBROWSERKEEPALIVEINTERVAL
                        Define interval in ms in which keep alive aignals
                        should be send. At least 200, 0 will disable keep
                        alive function - Default 1000ms
  -rbkael REMOTEBROWSERKEEPALIVEERRORLIMIT, --remoteBrowserKeepAliveErrorLimit REMOTEBROWSERKEEPALIVEERRORLIMIT
                        Define interval how many keepAlive Signal losts in a
                        row will be tolerated. Default 5
  -rbp REMOTEBROWSERPORT, --remoteBrowserPort REMOTEBROWSERPORT
                        Define the Port on which the remoteBrowserDaemon waits
                        for incoming websocket connections
  -rbst REMOTEBROWSERSESSIONTOKEN, --remoteBrowserSessionToken REMOTEBROWSERSESSIONTOKEN
                        Only Request which includes the configured Token will
                        be accepted. This Option will be overritten if
                        'useTemporarySessionToken' is set
  -utst, --useTemporarySessionToken
                        With this Option each start of the daemon a temporary
                        session Token will be created
  -tstp TEMPORARYSESSIONTOKENPATH, --temporarySessionTokenPath TEMPORARYSESSIONTOKENPATH
                        Path where the temporary session token should be
                        stored on the system. If not set the file
                        .pykibTemporarySessionToken will be stored in the
                        users tmp path

example Usage:
        Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
            python3 pykib.py -dh "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
        Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
            python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
        Open the site www.winteach.de maximized and show Adressbar and Navigation Buttons.
            python3 pykib.py -u https://www.winteach.de -m -sn -sa