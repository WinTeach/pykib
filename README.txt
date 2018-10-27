# pykib
QtWebEngine based minimal kiosk browser

This is only the output of --help
-----

Starting the Browser with python3 pykib.py [-h] [-u URL] [-d ]
             [-dh DOWNLOADHANDLE [DOWNLOADHANDLE ...]] [-t TITLE]
             [-dt [DYNAMICTITLE]] [-rt] [-f ]
             [-ic ] [-m ] [-v]
             [--no-sandbox ] [-sa ]
             [-sn ] [-g GEOMETRY [GEOMETRY ...]]
             [-a ADMINKEY] [-wl WHITELIST [WHITELIST ...]] [-l LOGFILE]

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
  -t TITLE, --title TITLE
                        Defines the Window Title
  -dt [DYNAMICTITLE], --dynamicTitle [DYNAMICTITLE]
                        When enabled the window title will display the current
                        websites title
  -rt [REMOVETITLEBAR], --removeTitleBar [REMOVETITLEBAR]
                        Removes the window title bar
  -f [FULLSCREEN], --fullscreen [FULLSCREEN]
                        Start browser in fullscreen mode
  -ic [INGORECERTIFICATES], --ingoreCertificates [INGORECERTIFICATES]
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
                        Set window geomety #left# #top# #width# #height#
  -a ADMINKEY, --enableAdminKey ADMINKEY
                        Enables the admin key SHIFT+STRG+ALT+A and defines a
                        Application which will be started when pushed
  -wl WHITELIST [WHITELIST ...], --whiteList WHITELIST [WHITELIST ...]
                        Enables the white List function. Only Urls which start
                        with elemtens from this list could be opend
  -l LOGFILE, --logFile LOGFILE
                        Dummy Argument for LogFile Path


example Usage:
        Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
            	python3 pykib.py -df "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
	Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
		python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
	Open the site www.winteach.de maximized and show Addressbar and navigation Buttons.
		python3 pykib.py -u https://www.winteach.de -m -sn -sa
