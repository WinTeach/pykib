#!/usr/bin/env python3
# pykib - A PyQt6 based kiosk browser with a minimum set of functionality
# Copyright (C) 2021 Tobias Wintrich
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

import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import configparser
import os
import sys

__version_info__ = ('devel', '3.0.6')
__version__ = '-'.join(__version_info__)

__remote_daemon_protocol_version__ = '1.0.0.4'

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

    parser.add_argument("-ppp", "--persistentProfilePath", dest="persistentProfilePath",
                        help="Defines a folder where the webprofile should be stored. Browser will be allways in private mode if not defined")

    parser.add_argument("-amc", "--addMemoryCap", dest="addMemoryCap", default=0,
                        help="Can be set to a value in MB. If the browser needs more than this amount of memory he will kill itself")

    parser.add_argument("-d", "--download", dest="download", action='store_true',
                        help="Enables download function")
    parser.add_argument("-dh", "--downloadHandle", dest="downloadHandle", nargs='+',
                        help="With this option, default behaviour for special file extensions can be defined, this will also work when -d is not defined. Format: #extension#|#app_to_start#|#tmpdownloadpath#")
    parser.add_argument("-dp", "--downloadPath", dest="downloadPath",
                        help="Defines the start path for any download and upload dialog")

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
                        help="with this option HTTPS Warninigs will be ignored")
    parser.add_argument("-m", "--maximized", dest="maximized", action='store_true',
                        help="Start browser in a maximized window")

    parser.add_argument("-v", "--version", action="version", version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument("-rdpv", "--remoteDaemonProtocolVersion", action="version", version=__remote_daemon_protocol_version__)

    parser.add_argument("-isds", "--ignoreSystemDpiSettings", dest="ignoreSystemDpiSettings", action='store_true', help="When set, the Browser won't try to use the systems DPI Settings")
    parser.add_argument("-szf", "--setZoomFactor", dest="setZoomFactor", help="Set Zoom Factor for Webpages in percent. Allowed Values between 25 and 500. Allowed only in combination with ignoreSystemDpiSettings", default=100, type=int)

    parser.add_argument("--no-sandbox", dest="no-sandbox", action='store_true',
                        help="Allows to run as root")
    parser.add_argument("--name", dest="name", help="Used to set the WM_CLASS", default="Pykib")
    parser.add_argument("--disable-gpu", dest="disable-gpu", action='store_true',
                        help="Disables QTs GPU Support")
    parser.add_argument("--js-flags", dest="js-flags", help="Allows setting js-flags")
    parser.add_argument("--single-process", dest="singleProcess", action='store_true', help="Allows to run the browser in one thread")
    parser.add_argument("--remote-debugging-port", dest="remote-debugging-port",
                        help="Allows to debug with chromes webbrowser console")
    parser.add_argument("-md", "--memoryDebug", dest="memoryDebug", action='store_true',
                        help="Show informations about the browser current memory usage")

    parser.add_argument("-sa", "--showAddressBar", dest="showAddressBar", action='store_true',
                        help="Shows a Address Bar when set")
    parser.add_argument("-sn", "--showNavigationButtons", dest="showNavigationButtons", action='store_true', help="Shows Navigation Buttons when set")
    parser.add_argument("-slpb", "--showLoadingProgressBar", dest="showLoadingProgressBar", action='store_true',
                        help="Shows a Progress Bar on site loading.")
    parser.add_argument("-ecm", "--enableContextMenu", dest="enableContextMenu", action='store_true', help="Enables a minimal context Menu")

    parser.add_argument("-g", "--geometry", dest="geometry", default=[100, 100, 1024, 600], nargs="+", type=int,
                        help="Set window geomety #left# #top# #width# #height#, when using a multimonitor envireoment you can define the monitor for fullscreen or maximized mode with #left# #top#")
    parser.add_argument("-ng", "--normalizeGeometry", dest="normalizeGeometry", action='store_true',
                        help="This Option makes the #left# geometry Parameter be calculated started from the primary screen (windows default behavior). "
                             "Specially help full in multi monitor enviroments when using the remote damon function")

    parser.add_argument("-a", "--enableAdminKey", dest="adminKey",
                        help="Enables the admin key SHIFT+STRG+ALT+A and defines a Application which will be started when pushed")
    parser.add_argument("-wl", "--whiteList", dest="whiteList", nargs="+",
                        help="Enables the white List function. Only Urls which start with elemtens from this list could be opend")
    parser.add_argument("-wlmfo", "--whiteListMainFrameOnly", dest="whiteListMainFrameOnly", action='store_true',
                        help="When set, whitelist will only be checked in mainframe navigation requests")

    parser.add_argument("-ll", "--logLevel", dest="logLevel", default="ERROR",
                        help="Setting the Level of Loggin. Allowed Values are ERROR, INFO, WARNING and DEBUG, Default is ERROR")

    parser.add_argument("-art", "--autoReloadTimer", dest="autoReloadTimer", help="Here you can configure a Timeout (in seconds) after which the actives site gets reloaded", default=0, type=int)

    parser.add_argument("-ama", "--allowMicAccess", dest="allowMicAccess", action='store_true', help="Allows all Websites to use your Microfon")

    parser.add_argument("-awa", "--allowWebcamAccess", dest="allowWebcamAccess", action='store_true', help="Allows all Websites to use your Webcam")

    parser.add_argument("-ads", "--allowDesktopSharing", dest="allowDesktopSharing", action='store_true', help="Allows all Websites to share your screen and local computers audio")

    parser.add_argument("-emd", "--enableMouseDrag", dest="enableMouseDrag", action='store_true', help="Enable Single Click (Touch) website movement (js injection)")
    parser.add_argument("-sp", "--storePid", dest="storePid", action='store_true',
                        help="With this Option each start of the Rangee Browser the current Process ID will be written to the file .pykibLatestProcId in the users tmp path")
    parser.add_argument("-spp", "--storePidPath", dest="storePidPath",
                        help="Path where the temporary current process id should be stored on the system. Only works in combination with --storePid")

    # Settings for Running in Remote Browser Daemon
    parser.add_argument("-rbd", "--remoteBrowserDaemon", dest="remoteBrowserDaemon", action='store_true',
                        help="start a remote browser daemon")
    parser.add_argument("-rbp", "--remoteBrowserPort", dest="remoteBrowserPort", type=int, default=8765,
                        help="Define the Port on which the remoteBrowserDaemon waits for incoming websocket connections")
    parser.add_argument("-rbmi", "--remoteBrowserMoveInterval", dest="remoteBrowserMoveInterval", type=int, default=50,
                        help="Define Interval in ms in which movement requests are send when moving the remote browser window - Default 50ms")
    parser.add_argument("-rl", "--remotingList", dest="remotingList", nargs="+", default='',
                        help="Defined a List of Urls which should be remoted - use * as wildcard")
    parser.add_argument("-aubr", "--allowUserBasedRemoting", dest="allowUserBasedRemoting", action='store_true',
                        help="When this option is set, the user on the remote side is allowed to define an own additional remoting list")
    parser.add_argument("-rbst", "--remoteBrowserSessionToken", dest="remoteBrowserSessionToken",
                        help="Only Request which includes the configured Token will be accepted. This Option will be overritten if 'useTemporarySessionToken' is set")
    parser.add_argument("-utst", "--useTemporarySessionToken", dest="useTemporarySessionToken", action='store_true',
                        help="With this Option each start of the daemon a temporary session Token will be created")
    parser.add_argument("-tstp", "--temporarySessionTokenPath", dest="temporarySessionTokenPath",
                        help="Path where the temporary session token should be stored on the system. If not set the file .pykibTemporarySessionToken will be stored in the users tmp path")



    args = parser.parse_args();
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
        elif(key == 'whiteList'):
            config_arguments[key] = val.split(" ")
        elif(key == 'downloadHandle'):
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