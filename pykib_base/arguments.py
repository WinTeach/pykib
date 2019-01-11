
import textwrap
from argparse import ArgumentParser, RawDescriptionHelpFormatter

__version_info__ = ('beta', '0.9')
__version__ = '-'.join(__version_info__)

def getArgumentParser():
    parser = ArgumentParser(
          prog='pykib',
          formatter_class= RawDescriptionHelpFormatter,
          epilog=textwrap.dedent('''\
    example Usage:
            Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
                python3 pykib.py -df "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
            Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
                python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
            Open the site www.winteach.de maximized and show Addressbar and navigation Buttons.
                python3 pykib.py -u https://www.winteach.de -m -sn -sa
             '''))
    parser.add_argument("-u", "--url", dest="url", help="Start and Home URL", default="https://github.com/WinTeach/pykib")
    parser.add_argument("-d", "--download", dest="download", nargs='?', const=True, default=False, help="Enables download function")
    parser.add_argument("-dh", "--downloadHandle", dest="downloadHandle", nargs='+', help="With this option, default behaviour for special file extensions can be defined, this will also work when -d is not defined. Format: #extension#|#app_to_start#|#tmpdownloadpath#")
    parser.add_argument("-dp", "--downloadPath", dest="downloadPath", help="Defines the start path for any download and upload dialog")

    parser.add_argument("-t", "--title", dest="title", help="Defines the Window Title", default="pykib")
    parser.add_argument("-dt", "--dynamicTitle", dest="dynamicTitle", nargs='?', const=True, default=False, help="When enabled the window title will display the current websites title")
    parser.add_argument("-rt", "--removeTitleBar", dest="removeTitleBar", nargs='?', const=True, default=False, help="Removes the window title bar")
    parser.add_argument("-f", "--fullscreen", dest="fullscreen", nargs='?', const=True, default=False, help="Start browser in fullscreen mode")
    parser.add_argument("-ic", "--ingoreCertificates", dest="ingoreCertificates", nargs='?', const=True, default=False, help="with this option HTTPS Warninigs will be ignored")
    parser.add_argument("-m", "--maximized", dest="maximized", nargs='?', const=True, default=False, help="Start browser in a maximized window")
    parser.add_argument("-v", "--version", action="version", version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument("--no-sandbox", dest="no-sandbox", nargs='?', const=True, default=False, help="Allows to run as root")
    parser.add_argument("-sa", "--showAddressBar", dest="showAddressBar", nargs='?', const=True, default=False, help="Shows a Address Bar when set")
    parser.add_argument("-sn", "--showNavigationButtons", dest="showNavigationButtons", nargs='?', const=True, default=False, help="Shows Navigation Buttons when set")
    parser.add_argument("-g", "--geometry", dest="geometry", default=[100,100,1024,600], nargs="+", type=int, help="Set window geomety #left# #top# #width# #height#, when using a multimonitor envireoment you can define the monitor for fullscreen or maximized mode with #left# #top#")

    parser.add_argument("-a", "--enableAdminKey",  dest="adminKey", help="Enables the admin key SHIFT+STRG+ALT+A and defines a Application which will be started when pushed")
    parser.add_argument("-wl", "--whiteList",  dest="whiteList", nargs="+", help="Enables the white List function. Only Urls which start with elemtens from this list could be opend")
    parser.add_argument("-l", "--logFile", dest="logFile", help="Dummy Argument for LogFile Path")
    
    return parser

 
        