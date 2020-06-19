usage: pykib [-h] [-c CONFIGFILE] [-u URL] [-p PROXY] [-ppo PROXYPORT] [-pu PROXYUSERNAME] [-pp PROXYPASSWORD]
             [-amc ADDMEMORYCAP] [-d] [-dh DOWNLOADHANDLE [DOWNLOADHANDLE ...]] [-dp DOWNLOADPATH] [-eal]
             [-alu AUTOLOGONUSER] [-alp AUTOLOGONPASSWORD] [-ald AUTOLOGONDOMAIN] [-aluid AUTOLOGONUSERID]
             [-alpid AUTOLOGONPASSWORDID] [-aldid AUTOLOGONDOMAINID] [-es] [-sl SPELLCHECKINGLANGUAGE] [-eps]
             [-sbl SETBROWSERLANGUAGE] [-scua] [-t TITLE] [-dt] [-rt] [-f] [-ic] [-m] [-v] [--no-sandbox]
             [--js-flags JS-FLAGS] [--single-process] [--remote-debugging-port REMOTE-DEBUGGING-PORT] [-md] [-sa]
             [-sn] [-g GEOMETRY [GEOMETRY ...]] [-a ADMINKEY] [-wl WHITELIST [WHITELIST ...]]
             [URL]

positional arguments:
  URL                   alternative to -u, --url

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIGFILE, --configFile CONFIGFILE
                        Use this as configuration file - configured setting will override command line arguments. The
                        ini file settings parameters are the same like the long form command line arguments
  -u URL, --url URL     Start and Home URL
  -p PROXY, --proxy PROXY
                        Use this as HTTP Proxy
  -ppo PROXYPORT, --proxyPort PROXYPORT
                        Proxy Port
  -pu PROXYUSERNAME, --proxyUsername PROXYUSERNAME
                        Enter Proxy username if needed
  -pp PROXYPASSWORD, --proxyPassword PROXYPASSWORD
                        Enter Proxy password if needed
  -amc ADDMEMORYCAP, --addMemoryCap ADDMEMORYCAP
                        Can be set to a value in MB. If the browser needs more than this amount of memory he will kill
                        itself
  -d, --download        Enables download function
  -dh DOWNLOADHANDLE [DOWNLOADHANDLE ...], --downloadHandle DOWNLOADHANDLE [DOWNLOADHANDLE ...]
                        With this option, default behaviour for special file extensions can be defined, this will also
                        work when -d is not defined. Format: #extension#|#app_to_start#|#tmpdownloadpath#
  -dp DOWNLOADPATH, --downloadPath DOWNLOADPATH
                        Defines the start path for any download and upload dialog
  -eal, --enableAutoLogon
                        Enables the autologon functionality, this function requires at least autoLogonUser and
                        autoLogonPassword to be set. The Browser is preconfigured to work with Citrix Webinterface,
                        Citrix Storefront and RDWeb Servers
  -alu AUTOLOGONUSER, --autoLogonUser AUTOLOGONUSER
                        Defines the username used for autologon
  -alp AUTOLOGONPASSWORD, --autoLogonPassword AUTOLOGONPASSWORD
                        Defines the password used for autologon
  -ald AUTOLOGONDOMAIN, --autoLogonDomain AUTOLOGONDOMAIN
                        Defines the domain name used for autologon. If a domain name is set, but no value for
                        autoLogonDomainID, the domain will bei merged with the username to domain\username
  -aluid AUTOLOGONUSERID, --autoLogonUserID AUTOLOGONUSERID
                        Defines the ID of the HTML Element in which the username should be put in
  -alpid AUTOLOGONPASSWORDID, --autoLogonPasswordID AUTOLOGONPASSWORDID
                        Defines the ID of the HTML Element in which the password should be put in
  -aldid AUTOLOGONDOMAINID, --autoLogonDomainID AUTOLOGONDOMAINID
                        Defines the ID of the HTML Element in which the domain should be put in
  -es, --enablespellcheck
                        Enables spellchecking when set
  -sl SPELLCHECKINGLANGUAGE, --spellcheckinglanguage SPELLCHECKINGLANGUAGE
                        Defines the language for the spellcheck dictionary. Default de_DE
  -eps, --enablepdfsupport
                        Enables the Option of viewing PDFs in the BrowserWindow
  -sbl SETBROWSERLANGUAGE, --setbrowserlanguage SETBROWSERLANGUAGE
                        Overrides the default Browser Language in format de (for German), en (for English)....
  -scua, --setCitrixUserAgent
                        Overrides the default UserAgent for skipping citrix receivers client detection
  -t TITLE, --title TITLE
                        Defines the Window Title
  -dt, --dynamicTitle   When enabled the window title will display the current websites title
  -rt, --removeTitleBar
                        Removes the window title bar
  -f, --fullscreen      Start browser in fullscreen mode
  -ic, --ignoreCertificates
                        with this option HTTPS Warninigs will be ignored
  -m, --maximized       Start browser in a maximized window
  -v, --version         show program's version number and exit
  --no-sandbox          Allows to run as root
  --js-flags JS-FLAGS   Allows setting js-flags
  --single-process      Allows to run the browser in one thread
  --remote-debugging-port REMOTE-DEBUGGING-PORT
                        Allows to run as root
  -md, --memoryDebug    Show informations about the browser current memory usage
  -sa, --showAddressBar
                        Shows a Address Bar when set
  -sn, --showNavigationButtons
                        Shows Navigation Buttons when set
  -g GEOMETRY [GEOMETRY ...], --geometry GEOMETRY [GEOMETRY ...]
                        Set window geomety #left# #top# #width# #height#, when using a multimonitor envireoment you
                        can define the monitor for fullscreen or maximized mode with #left# #top#
  -a ADMINKEY, --enableAdminKey ADMINKEY
                        Enables the admin key SHIFT+STRG+ALT+A and defines a Application which will be started when
                        pushed
  -wl WHITELIST [WHITELIST ...], --whiteList WHITELIST [WHITELIST ...]
                        Enables the white List function. Only Urls which start with elemtens from this list could be
                        opend

example Usage:
        Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
            python3 pykib.py -dh "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
        Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
            python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
        Open the site www.winteach.de maximized and show Adressbar and Navigation Buttons.
            python3 pykib.py -u https://www.winteach.de -m -sn -sa