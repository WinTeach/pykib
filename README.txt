# pykib
QtWebEngine based minimal kiosk browser

This is only the output of --help
-----
usage: pykib [-h] [-u URL] [-d [DOWNLOAD]]
             [-dh DOWNLOADHANDLE [DOWNLOADHANDLE ...]] [-dp DOWNLOADPATH]
             [-eal [ENABLEAUTOLOGON]] [-alu AUTOLOGONUSER]
             [-alp AUTOLOGONPASSWORD] [-ald AUTOLOGONDOMAIN]
             [-aluid AUTOLOGONUSERID] [-alpid AUTOLOGONPASSWORDID]
             [-aldid AUTOLOGONDOMAINID] [-es [ENABLESPELLCHECK]]
             [-sl SPELLCHECKINGLANGUAGE] [-t TITLE] [-dt [DYNAMICTITLE]]
             [-rt [REMOVETITLEBAR]] [-f [FULLSCREEN]]
             [-ic [IGNORECERTIFICATES]] [-m [MAXIMIZED]] [-v]
             [--no-sandbox [NO-SANDBOX]] [-sa [SHOWADDRESSBAR]]
             [-sn [SHOWNAVIGATIONBUTTONS]] [-g GEOMETRY [GEOMETRY ...]]
             [-a ADMINKEY] [-wl WHITELIST [WHITELIST ...]]

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     Start and Home URL
  -d [DOWNLOAD], --download [DOWNLOAD]
                        Enables download function
  -dh DOWNLOADHANDLE [DOWNLOADHANDLE ...], --downloadHandle DOWNLOADHANDLE [DOWNLOADHANDLE ...]
                        With this option, default behaviour for special file
                        extensions can be defined, this will also work when -d
                        is not defined. Format:
                        #extension#|#app_to_start#|#tmpdownloadpath#
  -dp DOWNLOADPATH, --downloadPath DOWNLOADPATH
                        Defines the start path for any download and upload
                        dialog
  -eal [ENABLEAUTOLOGON], --enableAutoLogon [ENABLEAUTOLOGON]
                        Enables the autologon functionality, this function
                        requires at leats autoLogonUser and autoLogonUser to
                        be set. The Browser is preconfigured to work with
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
  -es [ENABLESPELLCHECK], --enablespellcheck [ENABLESPELLCHECK]
                        Enables spellchecking when set
  -sl SPELLCHECKINGLANGUAGE, --spellcheckinglanguage SPELLCHECKINGLANGUAGE
                        Defines the language for the spellcheck dictionary.
                        Default de_DE
  -t TITLE, --title TITLE
                        Defines the Window Title
  -dt [DYNAMICTITLE], --dynamicTitle [DYNAMICTITLE]
                        When enabled the window title will display the current
                        websites title
  -rt [REMOVETITLEBAR], --removeTitleBar [REMOVETITLEBAR]
                        Removes the window title bar
  -f [FULLSCREEN], --fullscreen [FULLSCREEN]
                        Start browser in fullscreen mode
  -ic [IGNORECERTIFICATES], --ignoreCertificates [IGNORECERTIFICATES]
                        with this option HTTPS Warninigs will be ignored
  -m [MAXIMIZED], --maximized [MAXIMIZED]
                        Start browser in a maximized window
  -v, --version         show program's version number and exit
  --no-sandbox [NO-SANDBOX]
                        Allows to run as root
  -sa [SHOWADDRESSBAR], --showAddressBar [SHOWADDRESSBAR]
                        Shows a Address Bar when set
  -sn [SHOWNAVIGATIONBUTTONS], --showNavigationButtons [SHOWNAVIGATIONBUTTONS]
                        Shows Navigation Buttons when set
  -g GEOMETRY [GEOMETRY ...], --geometry GEOMETRY [GEOMETRY ...]
                        Set window geomety #left# #top# #width# #height#, when
                        using a multimonitor envireoment you can define the
                        monitor for fullscreen or maximized mode with #left#
                        #top#
  -a ADMINKEY, --enableAdminKey ADMINKEY
                        Enables the admin key SHIFT+STRG+ALT+A and defines a
                        Application which will be started when pushed
  -wl WHITELIST [WHITELIST ...], --whiteList WHITELIST [WHITELIST ...]
                        Enables the white List function. Only Urls which start
                        with elemtens from this list could be opend

example Usage:
        Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
            python3 pykib.py -dh "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
        Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
            python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
        Open the site www.winteach.de maximized and show Addressbar and navigation Buttons.
            python3 pykib.py -u https://www.winteach.de -m -sn -sa