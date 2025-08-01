#!/usr/bin/env python3
# pykib - A PyQt6 based kiosk browser with a minimum set of functionality
# Copyright (C) 2022 Tobias Wintrich
#
# This file is part of pykib.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import configparser
import os
import sys

__version_info__ = ('devel', '3.0.51')
__version__ = '-'.join(__version_info__)

__remote_daemon_protocol_version__ = '1.2.0.0'

def getArguments(dirname):
    parser = ArgumentParser(
        prog='pykib',
        formatter_class=RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
    example Usage:
            Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
                python3 pykib.py -dh "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
            Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
                python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
            Open the site www.winteach.de maximized and show Adressbar and Navigation Buttons.
                python3 pykib.py -u https://www.winteach.de -m -sn -sa
             '''))


    parser.add_argument("-c", "--configFile", dest="configFile", help="Use this as configuration file - configured setting will override command line arguments. The ini file settings parameters are the same like the long form command line arguments")

    parser.add_argument("-u", "--url", dest="url", help="Start and Home URL")

    parser.add_argument('defaultURL', metavar='URL', nargs='?', type=str, help="alternative to -u, --url")

    parser.add_argument("-p", "--proxy", dest="proxy", help="Use this as HTTP Proxy")
    parser.add_argument("-ppo", "--proxyPort", dest="proxyPort", help="Proxy Port", default=8080, type=int)
    parser.add_argument("-pu", "--proxyUsername", dest="proxyUsername", help="Enter Proxy username if needed")
    parser.add_argument("-pp", "--proxyPassword", dest="proxyPassword", help="Enter Proxy password if needed")
    parser.add_argument("-pdlip", "--proxyDisabledForLocalIp", dest="proxyDisabledForLocalIp", help="Disable Proxy for local IPs", action='store_true')

    parser.add_argument("-ppp", "--persistentProfilePath", dest="persistentProfilePath",
                        help="Defines a folder where the webprofile should be stored. Browser will be allways in private mode if not defined")

    parser.add_argument("-amc", "--addMemoryCap", dest="addMemoryCap", default=0,
                        help="Can be set to a value in MB. If the browser needs more than this amount of memory he will kill itself")

    parser.add_argument("-d", "--download", dest="download", action='store_true',
                        help="Enables download function")
    parser.add_argument("-dh", "--downloadHandle", dest="downloadHandle", nargs='+',
                        help="With this option, default behaviour for special file extensions can be defined, this will also work when -d is not defined. "
                             "Format: #extension#|#app_to_start#|#tmpdownloadpath#")
    parser.add_argument("-dp", "--downloadPath", dest="downloadPath",
                        help="Defines the start path for any download and upload dialog")

    parser.add_argument("-ijs", "--injectJavascript", dest="injectJavascript", nargs='+',
                        help="With this option, a js script file can be defined which should be injected on every page when loadFinished is triggered."
                             "Format: #pathToScript#|#once#|#argX#::argXvalue....."
                             "#pathToScript# = path to Script. Full path or relative to folder 'scripts' from installation dir"
                             "#once# = 0 or 1. If 1 it will be injected only when the first site load completes. With 0 or default it will be injected each time a site is loaded."
                             "#argX#::#value# = define Arguments which should be replaced in Script File at Runtime. in Script use {argX} in script file")

    parser.add_argument("-aush", "--addUrlSchemeHandler", dest="addUrlSchemeHandler", nargs='+',
                        help="With this option, additional URL Schemes can be defined which should be handled by the browser. If a URL starts with one of the defined schemes, the browser will send them to xdg-open (linux) or start (windows) command. "
                             "Example: teams workspaces customscheme ")

    parser.add_argument("-eal", "--enableAutoLogon", dest="enableAutoLogon", action='store_true',
                        help="Enables the autologon functionality, this function requires at least autoLogonUser and autoLogonPassword to be set. The Browser is preconfigured to work with Citrix Webinterface, Citrix Storefront and RDWeb Servers")
    parser.add_argument("-alu", "--autoLogonUser", dest="autoLogonUser", help="Defines the username used for autologon")
    parser.add_argument("-alp", "--autoLogonPassword", dest="autoLogonPassword", default=False,
                        help="Defines the password used for autologon")
    parser.add_argument("-ald", "--autoLogonDomain", dest="autoLogonDomain", default=False,
                        help="Defines the domain name used for autologon. If a domain name is set, but no value for autoLogonDomainID, the domain will bei merged with the username to domain\\username")
    parser.add_argument("-aluid", "--autoLogonUserID", dest="autoLogonUserID", default=False,
                        help="Defines the ID of the HTML Element in which the username should be put in")
    parser.add_argument("-alpid", "--autoLogonPasswordID", dest="autoLogonPasswordID", default=False,
                        help="Defines the ID of the HTML Element in which the password should be put in")
    parser.add_argument("-aldid", "--autoLogonDomainID", dest="autoLogonDomainID", default=False,
                        help="Defines the ID of the HTML Element in which the domain should be put in")

    parser.add_argument("-cou", "--closeOnUrl", dest="closeOnUrl", default=False,
                        help="if set, the browser will be closed when a url contains this string")


    #these 2 are usefull for handling command line oauth urls which should be opened in the browser
    parser.add_argument("-oaif", "--oAuthInputFile", dest="oAuthInputFile", nargs='?', type=str, help="Defines a file which is monitor. If the file contains a url the browser will be redirected to this url. The file contents will be cleared after the redirect.")
    parser.add_argument("-oaof", "--oAuthOutputFile", dest="oAuthOutputFile", nargs='?', type=str, help="Defines a file which is written when the browser is redirected to a url (by oAuthInputFile). The file will contain the url to which the browser was redirected.")
    parser.add_argument("-oaoui", "--oAuthOutputUrlIdentifier", dest="oAuthOutputUrlIdentifier", nargs='?', type=str, help="Defines string which should be part of the url to accept this for oAuthOutputFile")
    parser.add_argument("-oaocs", "--oAuthOutputCloseSuccess", dest="oAuthOutputCloseSuccess", default=False, help="if set, the browser will be closed after a successful oAuth redirect instead of turning back")


    parser.add_argument("-es", "--enablespellcheck", dest="enableSpellcheck", action='store_true',
                        help="Enables spellchecking when set")
    parser.add_argument("-sl", "--spellcheckinglanguage", dest="spellCheckingLanguage", default="en_US",
                        help="Defines the language for the spellcheck dictionary. Default en_US")
    parser.add_argument("-eps", "--enablepdfsupport", dest="enablepdfsupport", action='store_true',
                        help="Enables the Option of viewing PDFs in the BrowserWindow")
    parser.add_argument("-prm", "--pdfreadermode", dest="pdfreadermode", action='store_true',
                        help="if set the close button will close pykib complete instead of only the pdf and the Download Button will be labeld with 'save'")

    parser.add_argument("-sbl", "--setbrowserlanguage", dest="setBrowserLanguage", default="en",
                        help="Overrides the default Browser Language in format de (for German), en (for English)....")
    parser.add_argument("-scua", "--setCitrixUserAgent", dest="setCitrixUserAgent", action='store_true',
                        help="Overrides the default UserAgent for skipping citrix receivers client detection")

    parser.add_argument("-t", "--title", dest="title", help="Defines the Window Title", default="Pykib - Python based Kiosk Browser")
    parser.add_argument("-dt", "--dynamicTitle", dest="dynamicTitle", action='store_true',
                        help="When enabled the window title will display the current websites title")
    parser.add_argument("-san", "--systemApplicationName", dest="systemApplicationName", default="Pykib",
                        help="With this option the system application Name which will shown on pulse audio and some other apps can be overritten")
    parser.add_argument("-rt", "--removeTitleBar", dest="removeTitleBar", action='store_true',
                        help="Removes the window title bar")
    parser.add_argument("-f", "--fullscreen", dest="fullscreen", action='store_true',
                        help="Start browser in fullscreen mode")
    parser.add_argument("-aot", "--alwaysOnTop", dest="alwaysOnTop", action='store_true',
                        help="Makes the Browser Windows to Stay always on top of all other Windows")
    parser.add_argument("-rwc", "--removeWindowControls", dest="removeWindowControls", action='store_true',
                        help="This Option will remove the top Window Frame (with the Buttons Minimize/Maximize/Close)")
    parser.add_argument("-ic", "--ignoreCertificates", dest="ignoreCertificates", action='store_true',
                        help="with this option HTTPS Warnings will be ignored")
    parser.add_argument("-m", "--maximized", dest="maximized", action='store_true',
                        help="Start browser in a maximized window")

    parser.add_argument("-v", "--version", action="version", version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument("-rdpv", "--remoteDaemonProtocolVersion", action="version", version=__remote_daemon_protocol_version__)

    parser.add_argument("-isds", "--ignoreSystemDpiSettings", dest="ignoreSystemDpiSettings", action='store_true', help="When set, the Browser won't try to use the systems DPI Settings")
    parser.add_argument("-szf", "--setZoomFactor", dest="setZoomFactor", help="Set Zoom Factor for Webpages in percent. Allowed Values between 25 and 500. Allowed only in combination with ignoreSystemDpiSettings", default=100, type=int)

    parser.add_argument("--no-sandbox", dest="noSandbox", action='store_true',
                        help="Allows to run as root")
    parser.add_argument("--name", dest="name", help="Used to set the WM_CLASS", default="Pykib")
    parser.add_argument("--disable-gpu", dest="disableGpu", action='store_true',
                        help="Disables QTs GPU Support")
    parser.add_argument("--js-flags", dest="jsFlags", help="Allows setting js-flags")
    parser.add_argument("--single-process", dest="singleProcess", action='store_true', help="Allows to run the browser in one thread")
    parser.add_argument("--remote-debugging-port", dest="remoteDebuggingPort",
                        help="Allows to debug with chromes webbrowser console")
    parser.add_argument("-md", "--memoryDebug", dest="memoryDebug", action='store_true',
                        help="Show informations about the browser current memory usage")

    parser.add_argument("-sa", "--showAddressBar", dest="showAddressBar", action='store_true',
                        help="Shows a Address Bar when set")
    parser.add_argument("-sn", "--showNavigationButtons", dest="showNavigationButtons", action='store_true', help="Shows Navigation Buttons when set")
    parser.add_argument("-slpb", "--showLoadingProgressBar", dest="showLoadingProgressBar", action='store_true',
                        help="Shows a Progress Bar on site loading.")
    parser.add_argument("-spb", "--showPrintButton", dest="showPrintButton", action='store_true',
                        help="Shows a Print Button when set. enablePrintSupport will be set to True")
    parser.add_argument("-epsu", "--enablePrintSupport", dest="enablePrintSupport", action='store_true',
                        help="Allows Priting with CTRL+P and showing Navigation Buttons when set")
    parser.add_argument("-ecm", "--enableContextMenu", dest="enableContextMenu", action='store_true', help="Enables a minimal context Menu")
    parser.add_argument("-etm", "--enableTrayMode", dest="enableTrayMode", action='store_true',
                        help="when this option is set the browser will be minimized to tray instead of closed")
    parser.add_argument("-sih", "--startInTray", dest="startInTray", action='store_true',
                        help="when this option is set the browser will start to Tray.")
    parser.add_argument("-ecbpo", "--enableCleanupBrowserProfileOption", dest="enableCleanupBrowserProfileOption", action='store_true',
                        help="when this option is set the user has the option to Cleanup the Browser Profile (in tray and "
                             "context menu). When 'Cleanup Browser Profile' is performed it will:"
                             "- remove all Browser Cookies"
                             "- perform localStorage.clean() and sessionStorage.clean() via JS"
                             "- reload the current Site")


    parser.add_argument("-g", "--geometry", dest="geometry", nargs="+", type=int,
                        help="Set window geomety #left# #top# #width# #height#, when using a multimonitor envireoment you can define the monitor for fullscreen or maximized mode with #left# #top#")
    parser.add_argument("-ng", "--normalizeGeometry", dest="normalizeGeometry", action='store_true',
                        help="This Option makes the #left# geometry Parameter be calculated started from the primary screen (windows default behavior). "
                             "Specially help full in multi monitor enviroments when using the remote damon function")
    parser.add_argument("-bw", "--browserWidth", dest="browserWidth",
                        help="Set window width in pixel. Will be Overwritten if geometry is set", default=1000, type=int)
    parser.add_argument("-bh", "--browserHeight", dest="browserHeight",
                        help="Set window height in pixel. Will be Overwritten if geometry is set", default=800, type=int)

    parser.add_argument("-a", "--enableAdminKey", dest="adminKey",
                        help="Enables the admin key SHIFT+STRG+ALT+A and defines a Application which will be started when pushed")
    parser.add_argument("-epkh", "--enablePrintKeyHandle", dest="enablePrintKeyHandle", action='store_true',
                        help="When enabled, a press on the 'Print'-Button will insert a Image of the current page to the clipboard")
    parser.add_argument("-wl", "--whiteList", dest="whiteList", nargs="+",
                        help="Enables the white List function. Only Urls which start with elemtens from this list could be opend")
    parser.add_argument("-wlmfo", "--whiteListMainFrameOnly", dest="whiteListMainFrameOnly", action='store_true',
                        help="When set, whitelist will only be checked in mainframe navigation requests")

    parser.add_argument("-ll", "--logLevel", dest="logLevel", default="ERROR",
                        help="Setting the Level of Loggin. Allowed Values are ERROR, INFO, WARNING and DEBUG, Default is ERROR")
    parser.add_argument("-lf", "--logFile", dest="logFile", default="",
                        help="Specify a file where the log should be written to. If not set the log will be written to stdout")

    parser.add_argument("-sjsc", "--showJsConsole", dest="showJsConsole", action='store_true',
                        help="Showing all js console entry on in DEBUG log")

    parser.add_argument("-art", "--autoReloadTimer", dest="autoReloadTimer", help="Here you can configure a Timeout (in seconds) after which the actives site gets reloaded", default=0, type=int)

    parser.add_argument("-brt", "--browserResetTimeout", dest="browserResetTimeout", help="Here you can configure a Timeout of inactivity (in seconds) after which the browser will be resettet", default=0, type=int)

    parser.add_argument("-ama", "--allowMicAccess", dest="allowMicAccess", action='store_true', help="Allows all Websites to use your Microfon")

    parser.add_argument("-awa", "--allowWebcamAccess", dest="allowWebcamAccess", action='store_true', help="Allows all Websites to use your Webcam")

    parser.add_argument("-ads", "--allowDesktopSharing", dest="allowDesktopSharing", action='store_true', help="Allows all Websites to share your screen and local computers audio")
    parser.add_argument("-abn", "--allowBrowserNotifications", dest="allowBrowserNotifications", action='store_true', help="Allows all Websites to send Push Notifications")
    parser.add_argument("-pns", "--playNotificationSound", dest="playNotificationSound", action='store_true',
                        help="if set a sound jingle is played when a notification is received")

    parser.add_argument("-emd", "--enableMouseDrag", dest="enableMouseDrag", action='store_true', help="Enable Single Click (Touch) website movement (js injection)")
    parser.add_argument("-sp", "--storePid", dest="storePid", action='store_true',
                        help="With this Option each start of the Rangee Browser the current Process ID will be written to the file .pykibLatestProcId in the users tmp path")
    parser.add_argument("-spp", "--storePidPath", dest="storePidPath",
                        help="Path where the temporary current process id should be stored on the system. Only works in combination with --storePid")

    # Settings for Running in Remote Browser Daemon
    parser.add_argument("-rbd", "--remoteBrowserDaemon", dest="remoteBrowserDaemon", action='store_true',
                        help="start a remote browser daemon")
    parser.add_argument("-rbmi", "--remoteBrowserMoveInterval", dest="remoteBrowserMoveInterval", type=int, default=50,
                        help="Define Interval in ms in which movement requests are send when moving the remote browser window - Default 50ms")
    parser.add_argument("-rbmpmi", "--remoteBrowserPixmapMonitorInterval", dest="remoteBrowserPixmapMonitorInterval", type=int, default=500,
                        help="This option allows you to define the interval at which the optionally installed "
                             "server-side connector app monitors the viewport of the server-side browser for "
                             "overlapping applications. If an overlapping application is detected, the server sends"
                             " a pixmap to the remote browser, which cuts out the area of the overlapping application."
                             "Lower values lead to a higher CPU load on the server side.   "
                             "disabled = 0, min = 50, max = 2000, Default 300ms")
    parser.add_argument("-rl", "--remotingList", dest="remotingList", nargs="+", default='',
                        help="Defined a List of Urls which should be remoted - use * as wildcard")
    parser.add_argument("-aubr", "--allowUserBasedRemoting", dest="allowUserBasedRemoting", action='store_true',
                        help="When this option is set, the user on the remote side is allowed to define an own additional remoting list")
    parser.add_argument("-rbix11", "--remoteBrowserIgnoreX11", dest="remoteBrowserIgnoreX11", action='store_true',
                        help="With this Option X11BypassWindowManagerHint will be used to force the browser to top. Usually not needed")

    # Settings only for Running Remote Browser Daemon in Unix Socket Mode
    parser.add_argument("-rbsp", "--remoteBrowserSocketPath", dest="remoteBrowserSocketPath", help="When this option is set, the remote browser Deamon will only listen "
                                                                                                   "to commands send to this socket. Any other communication options will be disabled")
    parser.add_argument("-rbkai", "--remoteBrowserKeepAliveInterval", dest="remoteBrowserKeepAliveInterval", type=int, default=1000,
                        help="Define interval in ms in which keep alive aignals should be send. At least 200, 0 will disable keep alive function - Default 1000ms")
    parser.add_argument("-rbkael", "--remoteBrowserKeepAliveErrorLimit", dest="remoteBrowserKeepAliveErrorLimit", type=int, default=5,
                        help="Define interval how many keepAlive Signal losts in a row will be tolerated. Default 5")

    # Settings only for Running Remote Browser Daemon in Websocket Mode
    parser.add_argument("-rbp", "--remoteBrowserPort", dest="remoteBrowserPort", type=int, default=8765,
                        help="Define the Port on which the remoteBrowserDaemon waits for incoming websocket connections")
    parser.add_argument("-rbst", "--remoteBrowserSessionToken", dest="remoteBrowserSessionToken",
                        help="Only Request which includes the configured Token will be accepted. This Option will be overritten if 'useTemporarySessionToken' is set")
    parser.add_argument("-utst", "--useTemporarySessionToken", dest="useTemporarySessionToken", action='store_true',
                        help="With this Option each start of the daemon a temporary session Token will be created")
    parser.add_argument("-tstp", "--temporarySessionTokenPath", dest="temporarySessionTokenPath",
                        help="Path where the temporary session token should be stored on the system. If not set the file .pykibTemporarySessionToken will be stored in the users tmp path")


    args, unknown = parser.parse_known_args()
    if unknown:
        logging.warning("ignoring undefined arguments:")
        logging.warning(unknown)

    if (args.configFile):
        if (os.path.isfile(dirname + "/" + args.configFile)):
            args.configFile = dirname + "/" + args.configFile
        elif (not os.path.isfile(args.configFile)):
            print("Configuration File " + args.configFile + " can't be found!")
            sys.exit()
        args = parseConfigFile(args, parser)

    args.remoteDaemonProtocolVersion = __remote_daemon_protocol_version__
    return args

def parseConfigFile(args, parser):
    print("config File '"+args.configFile+"' used")

    config_arguments = {}

    #first save all command line arguments into new arguments array
    for val in vars(args):
        config_arguments[val] = getattr(args, val)

    #Load Values from Configuration File
    config = configparser.ConfigParser()
    config.optionxform = str
    config.sections()
    config.read(args.configFile)

    #Override command line arguments
    for key, val in config['PYKIB'].items():
        print(key, val)
        if(val.lower() == 'false'):
            config_arguments[key] = False
        elif(val.lower() == 'true'):
            config_arguments[key] = True
        elif(key == 'geometry'):
            config_arguments[key] = list(map(int, val.split()))
        elif(key == 'whiteList' or key == 'addUrlSchemeHandler'):
            config_arguments[key] = val.split(" ")
        elif(key == 'downloadHandle' or key == 'injectJavascript'):
            config_arguments[key] = val.split("\"")
            config_arguments[key] = filter(None, config_arguments[key])
            config_arguments[key] = filter(bool, config_arguments[key])
            config_arguments[key] = filter(len, config_arguments[key])
            config_arguments[key] = filter(lambda item: item, config_arguments[key])
        elif(val != ''):
            config_arguments[key] = val

    #use the new configuration array as default values for argparse and parse again
    parser.set_defaults(**config_arguments)
    args = parser.parse_args({})
    return args