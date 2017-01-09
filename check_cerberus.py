#!/usr/bin/env python

__author__ = 'Anton Delitsch <anton.delitsch@implema.se>'
__version__= 0.1

from optparse import OptionParser, OptionGroup
import logging as log
import requests
requests.packages.urllib3.disable_warnings()
import xml.dom.minidom

## These will override any args passed to the script normally. Comment out after testing.
#testargs = '--help'
#testargs = '--version'
#testargs = '-vvv'

def main():
    """ Main plugin logic goes here """

    ## Parse command-line arguments
    args, args2 = parse_args()


    #print args
    if args.function == 'CurrentConnections':
        function = 'GetAllCurrentConnectionCountRequest'
        response = http_call(args.server, args.username, args.password, function, args.function_argument)
        value = response['SOAP-ENV:Body'][0]['ns1:GetAllCurrentConnectionCountResponse'][0]['ns1:result'][0]
        if int(value) >= args.crit:
            gtfo(2, 'CRIT %s connection|c[connections]=%s;%s;%s' % (value,value,args.warn,args.crit))
        
        if int(value) >= args.warn:
            gtfo(1, 'WARN: %s conenctions|c[connections]=%s;%s;%s' % (value,value,args.warn,args.crit))


        gtfo(0, 'OK: %s connections|c[connections]=%s;%s;%s' % (value,value,args.warn,args.crit))

    if args.function == 'ServerState':
        function = 'ServerSummaryStatusRequest'
        response = http_call(args.server, args.username, args.password, function, args.function_argument)
        vulnerabilityStatus = response['SOAP-ENV:Body'][0]['ns1:ServerSummaryStatusResponse'][0]['ns1:result'][0]['ns2:vulnerabilityStatus'][0]

        if vulnerabilityStatus != 'None':
            gtfo(2, 'CRIT: Found %s vulnerability' % vulnerabilityStatus)


        if response['SOAP-ENV:Body'][0]['ns1:ServerSummaryStatusResponse'][0]['ns1:result'][0]['ns2:ftpStatus'][0] != "Secure":
            gtfo(1, 'WARN: FTP is not secure')

        if response['SOAP-ENV:Body'][0]['ns1:ServerSummaryStatusResponse'][0]['ns1:result'][0]['ns2:sftpStatus'][0] != "Secure":
            gtfo(1, 'WARN: SFTP is not secure')

        gtfo(0, 'OK: Everything OK')



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
    group.add_option('-s', '--server', help='SOAP service url',
                     default=None)
    group.add_option('-u', '--username', help='SOAP username',
                     default=None)
    group.add_option('-p', '--password', help='SOAP password',
                     default=None)    
    group.add_option('-f', '--function', help='Check function, one of: CurrentConnections, ServerState',
                     default=None)
    group.add_option('-a', '--function_argument', help='Functioun arguments',
                     default=None)

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

def http_call(server, username, password, function, function_argument):
    """ Make SOAP call to server and return value """
    response = None
    url = server + '/service/cerberusftpservice'
    body = '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:cer="http://cerberusllc.com/service/cerberusftpservice" xmlns:com="http://cerberusllc.com/common">'
    body = body + '<soap:Header/>'
    body = body + '<soap:Body><cer:' + function +'><com:credentials><com:user>' + username +'</com:user><com:password>' + password +'</com:password></com:credentials></cer:' + function +'></soap:Body>'
    body = body + '</soap:Envelope>'
    headers = {'Content-Type': 'application/soap+xml;charset=UTF-8', 'Content-length': '%d' % len(body)}
    response = requests.post(server, data=body,headers=headers, verify=False)

    return xmltodict(response.content)

def xmltodict(xmlstring):
    doc = xml.dom.minidom.parseString(xmlstring)
    return elementtodict(doc.documentElement)

def elementtodict(parent):
    child = parent.firstChild
    if (not child):
        return None
    elif (child.nodeType == xml.dom.minidom.Node.TEXT_NODE):
        return child.nodeValue
    
    d={}
    while child is not None:
        if (child.nodeType == xml.dom.minidom.Node.ELEMENT_NODE):
            try:
                d[child.tagName]
            except KeyError:
                d[child.tagName]=[]
            d[child.tagName].append(elementtodict(child))
        child = child.nextSibling
    return d


if __name__ == '__main__':
    ## Initialize logging before hitting main, in case we need extra debuggability
    log.basicConfig(level=log.DEBUG, format='%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
    main()
