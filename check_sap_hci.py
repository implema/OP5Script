#!/usr/bin/env python

__author__ = 'Anton Delitsch <anton.delitsch@implema.se>'
__version__= 0.5

from optparse import OptionParser, OptionGroup
import logging as log
import requests
requests.packages.urllib3.disable_warnings()
from xml.dom import minidom
from time import strftime
import datetime
import sys
startHourDateTime = datetime.datetime.now() - datetime.timedelta(hours=1)
endHourDateTime = datetime.datetime.now()

## These will override any args passed to the script normally. Comment out after testing.
#testargs = '--help'
#testargs = '--version'
#testargs = '-vvv'

def main():
    """ Main plugin logic goes here """

    ## Parse command-line arguments
    args, args2 = parse_args()


    if args.function == 'Message_Status':
        error_value = 0
        successful_value = 0
        error_string = ""
        iflow_status =  http_call("POST", "https://" + args.server + "/Operations/com.sap.it.op.srv.commands.dashboard.IFlowStatisticCommand", "<com.sap.it.op.srv.commands.dashboard.IFlowStatisticCommand><from>" + startHourDateTime.strftime("%Y-%m-%dT%H:%M:%S.0") + "+02:00</from><to>" + endHourDateTime.strftime("%Y-%m-%dT%H:%M:%S.0") + "+02:00</to><participantId>" + args.participant +"</participantId></com.sap.it.op.srv.commands.dashboard.IFlowStatisticCommand>", args.username, args.password)
        for node in iflow_status.getElementsByTagName('IFlowStatistics'):
            IFlow = node.getElementsByTagName("camelId")[0].firstChild.nodeValue
            try:
                Error = int(node.getElementsByTagName("exchangesFailed")[0].firstChild.nodeValue)
            except:
                Error = 0
            try:
                Total = int(node.getElementsByTagName("exchangesTotal")[0].firstChild.nodeValue)
            except:
                Total = 0
            Successful = Total - Error
            try:
                ProcessingTime = int(node.getElementsByTagName("meanProcessingTime")[0].firstChild.nodeValue)
            except:
                ProcessingTime = 0
            try:
                Invocations = int(node.getElementsByTagName("numInvocations")[0].firstChild.nodeValue)
            except:
                Invocations = 0


            if (Error != 0) and (IFlow not in args.ignore.split(",")):
                error_value += int(Error)
                error_string = error_string + IFlow + ": %s , " % str(Error)
            if (Invocations != Total) and (IFlow not in args.ignore.split(",")):
                error_value += int(Invocations)
                error_string = error_string + IFlow + ": have more invocations (%s) then messages (%s), " % (str(Invocations), str(Total))
            if IFlow not in args.ignore.split(","):
                try:
                   successful_value += int(Successful)
                except: pass

        if int(error_value) >= args.crit:
            gtfo(2, 'CRIT %s messages in error state: %s|e[errors]=%s;%s;%s;; [successful]=%s;;;; ' % (str(error_value),error_string,error_value,int(args.warn),int(args.crit),str(successful_value)))
        
        if int(error_value) >= args.warn:
            gtfo(1, 'WARN: %s messages in error state: %s|e[errors]=%s;%s;%s;; [successful]=%s;;;; ' % (str(error_value),error_string,error_value,int(args.warn),int(args.crit),str(successful_value)))


        gtfo(0, 'OK: %s messages with errors|e[errors]=%s;%s;%s;; [successful]=%s;;;; ' % (error_value,error_value,int(args.warn),int(args.crit),successful_value))

    if args.function == 'Component_Status':
        nodes_status =  http_call("GET", "https://" + args.server + "/Operations/com.sap.it.nm.commands.node.GetNodesCommand", "", args.username, args.password)
        error_value = 0
        ok_value = 0
        error_string = ""
        for node in nodes_status.getElementsByTagName('components'):
            #print node
            if (node.attributes["state"].value != "STARTED") and (node.attributes["name"].value not in args.ignore.split(",")):
                error_value += 1
                error_string = error_string + node.attributes["name"].value + " : " + node.attributes["state"].value + ", "
            else:
                ok_value += 1

        if int(error_value) >= args.crit:
            gtfo(2, 'CRIT %s Components with errors %s|e[errors]=%s;%s;%s [ok]=%s;;;;' % (error_value,error_string,error_value,args.warn,args.crit,ok_value))
        
        if int(error_value) >= args.warn:
            gtfo(1, 'WARN: %s Components with errors %s||e[errors]=%s;%s;%s [ok]=%s;;;;' % (error_value,error_string,error_value,args.warn,args.crit,ok_value))


        gtfo(0, 'OK: %s Components with errors %s||e[errors]=%s;%s;%s [ok]=%s;;;;' % (error_value,error_string,error_value,args.warn,args.crit,ok_value))


    ## Uncomment to test logging levels against verbosity settings
    # log.debug('debug message')
    # log.info('info message')
    # log.warning('warning message')
    # log.error('error message')
    # log.critical('critical message')
    # log.fatal('fatal message')

    gtfo(3, 'Unknown function "%s"' % args.function)


def parse_args():
    """ Parse command-line arguments """

    parser = OptionParser(usage='usage: %prog [-v|vv|vvv] [options]',
                          version='{0}: v.{1} by {2}'.format('%prog', __version__, __author__))

    ## Verbosity (want this first, so it's right after --help and --version)
    parser.add_option('-v', help='Set verbosity level',
                      action='count', default=0, dest='v')

    ## CLI arguments specific to this script
    group = OptionGroup(parser,'Plugin Options')
    group.add_option('-s', '--server', help='Server',
                     default=None)
    group.add_option('-u', '--username', help='Username',
                     default=None)
    group.add_option('-p', '--password', help='Password',
                     default=None)
    group.add_option('-3', '--participant', help='Participantid',
                     default=None)   
    group.add_option('-f', '--function', help='Check function, one of: Messages_Status, Component_Status',
                     default=None)
    group.add_option('-i', '--ignore', help='IFlows/components to ignore',
                     default="")
    group.add_option('-n', '--profile', help='Node Profile: iflmap, tmn',
                     default="iflmap")

    ## Common CLI arguments
    parser.add_option('-c', '--critical', help='Set the critical threshold. Default: %(default)s',
                      default=97, type=float, dest='crit', metavar='##')
    parser.add_option('-w', '--warning', help='Set the warning threshold. Default: %(default)s',
                      default=95, type=float, dest='warn', metavar='##')
    
    parser.add_option_group(group)

    ## Try to parse based on the testargs variable. If it doesn't exist, use args
    try:
        args, args2 = parser.parse_args(testargs.split())
    except NameError:
        args, args2 = parser.parse_args()

    ## Set the logging level based on the -v arg
    log.getLogger().setLevel([log.ERROR, log.WARN, log.INFO, log.DEBUG][args.v])

    log.debug('Parsed arguments: {0}'.format(args))
    log.debug('Other  arguments: {0}'.format(args2))

    return args, args2

def gtfo(exitcode, message=''):
    """ Exit gracefully with exitcode and (optional) message """

    log.debug('Exiting with status {0}. Message: {1}'.format(exitcode, message))
    
    if message:
        print(message)
    exit(exitcode)

def http_call(method, url, data, username, password):
    """ Make HTTP call to server and return value """
    response = None
    response = None
    #print data

    try:
        if method == "POST":
            response = requests.post(url, data=data, auth=(username, password), verify=False)
        if method == "GET":
            response = requests.get(url, auth=(username, password), verify=False)
        #print response.content
    except:
        gtfo(1, 'WARN: Failed to connect to server')

    if response.status_code != "200":
       gtfo(1, 'WARN: Failed to connect to server. Code ' + str(response.status_code))


    try:
        response = minidom.parseString(response.content)

    except:
        gtfo(1, 'WARN: Failed to parse response from server')

    return response


if __name__ == '__main__':
    ## Initialize logging before hitting main, in case we need extra debuggability
    log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    main()

