#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement

'''
A script to select a subset of GNAF-CORE addresses.
If the number of addresses in the subset is not specified then the whole of GNAF_CORE.psv is outout,
but only the columns required for the mkHealth Population - Australia related scripts.

SYNOPSIS
$ python selectGNAF.py [-D dataDir|--dataDir=dataDir] [-I GNAFinputfile|--GNAFinputfile=GNAFinputfile]
                       -O GNAFoutputfile|--GNAFoutputfile=GNAFoutputfile
                       [-n addresses|--addresses=addresses] [-s states|--states=states]
                       [-v loggingLevel|--loggingLevel=loggingLevel]
                       [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

REQUIRED
-O GNAFoutputfile|--GNAFoutputfile=GNAFoutputfile
The GNAF-CORE formatted output file of the selected subset of GNAF_CORE addresses

OPTIONS
-D dataDir|--dataDir=dataDir
The directory containing the source address data. The subset will be created in this directory.

-I GNAFinputfile|--GNAFinputfile=GNAFinputfile (default=GNAF_CORE.psv)
The GNAF-CORE formatted input file of addresses

-n addresses|--addresses=addresses
The number of GNAF_CORE addresses in the subset

-s states|-states=states
The states to be included in the subset of GNAF_CORE addresses (e.g. -s VIC,WA)

-v loggingLevel|--verbose=loggingLevel
Set the level of logging that you want.

-L logDir|--logDir=logDir
The name of the folder for the logging file

-l logfile|--logfile=logfile
The name of a logginf file where you want all messages captured.
'''

import sys
import io
import os
import csv
import zipfile
import random
import argparse
import logging

# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0        # successful termination
EX_WARN = 1        # non-fatal termination with warnings

EX_USAGE = 64        # command line usage error
EX_DATAERR = 65        # data format error
EX_NOINPUT = 66        # cannot open input
EX_NOUSER = 67        # addressee unknown
EX_NOHOST = 68        # host name unknown
EX_UNAVAILABLE = 69    # service unavailable
EX_SOFTWARE = 70    # internal software error
EX_OSERR = 71        # system error (e.g., can't fork)
EX_OSFILE = 72        # critical OS file missing
EX_CANTCREAT = 73    # can't create (user) output file
EX_IOERR = 74        # input/output error
EX_TEMPFAIL = 75    # temp failure; user is invited to retry
EX_PROTOCOL = 76    # remote error in protocol
EX_NOPERM = 77        # permission denied
EX_CONFIG = 78        # configuration error


if __name__ == '__main__' :
    '''
The main code
    '''

    # Save the program name
    progName = sys.argv[0]
    progName = progName[0:-3]        # Strip off the .py ending

    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--dataDir', dest='dataDir', default='data',
                        help='The name of the directory containing source address data and where the subset will be created')
    parser.add_argument ('-I', '--GNAFinputfile', dest='GNAFinputfile', default='GNAF_CORE.psv', help='The name of the file of GNAF-CORE addresses')
    parser.add_argument ('-O', '--GNAFoutputfile', required=True, dest='GNAFoutputfile', help='The name of the file for the subset of GNAF-CORE addresses to be created')
    parser.add_argument ('-n', '--addresses', dest='noOfAddresses', type=int, help='The number of GNAF_CORE addresses to be included in the subset')
    parser.add_argument ('-s', '--states', dest='states', help='The comma separated list of states to be included in the subset (e.g. -s VIC,WA)')
    parser.add_argument ('-v', '--verbose', dest='loggingLevel', type=int, choices=range(0,5), help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument ('-L', '--logDir', dest='logDir', default='logs', help='The name of a directory for the logging file')
    parser.add_argument ('-l', '--logfile', metavar='logfile', dest='logfile', action='store', help='The name of a logging file')
    args = parser.parse_args()

    # Parse the command line options
    logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if args.loggingLevel :    # Change the logging level from "WARN" if the -v vebose option is specified
        loggingLevel = args.loggingLevel
        if args.logfile :        # and send it to a file if the -o logfile option is specified
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else :
        if args.logfile :        # send the default (WARN) logging to a file if the -o logfile option is specified
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p',
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')

    # Get the command line arguments
    dataDir = args.dataDir
    GNAFinputfile = args.GNAFinputfile
    GNAFoutputfile = args.GNAFoutputfile
    noOfAddresses = args.noOfAddresses
    states = args.states
    statesList = None
    if states is not None:
        for row in csv.reader([states], dialect=csv.excel):
            statesList = row
            break

    # Read in Mesh Block data
    # MB_CODE_2021,MB_CATEGORY_2021,CHANGE_FLAG_2021,CHANGE_LABEL_2021,SA1_CODE_2021,SA2_CODE_2021,SA2_NAME_2021,SA3_CODE_2021,SA3_NAME_2021,SA4_CODE_2021,SA4_NAME_2021,GCCSA_CODE_2021,GCCSA_NAME_2021,STATE_CODE_2021,STATE_NAME_2021,AUS_CODE_2021,AUS_NAME_2021,AREA_ALBERS_SQKM,ASGS_LOCI_URI_2021
    MB = {}                    # key=Mesh Block 2016 code, value=SA1 code
    logging.info('Reading Mesh Blocks')
    with zipfile.ZipFile(os.path.join(dataDir, 'MB_2021_AUST.zip')) as zf:
        with zf.open('MB_2021_AUST.csv', 'r') as mb:
            mbReader = csv.DictReader(io.TextIOWrapper(mb, encoding='utf-8-sig'), dialect=csv.excel)
            for row in mbReader:
                MB[row['MB_CODE_2021']] = row['SA1_CODE_2021']

    # Read in the G-NAF CORE addresses
    # ADDRESS_DETAIL_PID|DATE_CREATED|ADDRESS_LABEL|ADDRESS_SITE_NAME|BUILDING_NAME|FLAT_TYPE|FLAT_NUMBER|LEVEL_TYPE|LEVEL_NUMBER|NUMBER_FIRST|NUMBER_LAST|LOT_NUMBER|STREET_NAME|STREET_TYPE|STREET_SUFFIX|LOCALITY_NAME|STATE|POSTCODE|LEGAL_PARCEL_ID|MB_CODE|ALIAS_PRINCIPAL|PRINCIPAL_PID|PRIMARY_SECONDARY|PRIMARY_PID|GEOCODE_TYPE|LONGITUDE|LATITUDE
    logging.info('Reading addresses')
    SA1s = set()            # SA1 values
    SA1list = []            # A list of SA1s (for random selection)
    addresses = {}            # key=SA1, value=dict(GNAF_CORE data)
    # Map all the overseas territories into NSW and WA
    OTstates = {'2':'NSW', '6':'WA'}
    inCount = outCount = 0
    with open(os.path.join(dataDir, GNAFinputfile), 'rt', encoding='utf-8-sig') as gnafCore:
        gnafReader = csv.DictReader(gnafCore, delimiter='|')
        header = True
        stripColumns = False
        for row in gnafReader:
            if header:
                if 'ADDRESS_DETAIL_PID' in row:
                    stripColumns = True
            # Strip out any unnecessary columns if they are present in the input file
            if stripColumns:
                del row['ADDRESS_DETAIL_PID']
                del row['DATE_CREATED']
                del row['ADDRESS_LABEL']
                del row['ADDRESS_SITE_NAME']
                del row['BUILDING_NAME']
                del row['FLAT_TYPE']
                del row['FLAT_NUMBER']
                del row['LEVEL_TYPE']
                del row['LEVEL_NUMBER']
                del row['NUMBER_LAST']
                del row['LOT_NUMBER']
                del row['LEGAL_PARCEL_ID']
                del row['ALIAS_PRINCIPAL']
                del row['PRINCIPAL_PID']
                del row['PRIMARY_SECONDARY']
                del row['PRIMARY_PID']
                del row['GEOCODE_TYPE']
            if header:
                heading = row.keys()
                header = False
                if noOfAddresses is None:
                    gnafSelection = open(GNAFoutputfile, 'wt', encoding='utf-8-sig', newline="")
                    gnafWriter = csv.DictWriter(gnafSelection, fieldnames=heading, delimiter='|')
                    gnafWriter.writeheader()
                    logging.info('Copying all %s addresses', GNAFinputfile)

            inCount += 1
            if (inCount % 100000) == 0:
                logging.info('%d addresses read in', inCount)
            mb = row['MB_CODE']
            if mb not in MB:
                continue
            # Check if a required state
            if statesList is not None:
                # Merge 'Other Territories' back into the nearest state (based on the first digit of the postcode)
                if row['STATE'] == 'OT':
                    Postcode = row['POSTCODE']
                    State = OTstates[Postcode[0:1]]
                else:
                    State = row['STATE']
                if State not in statesList:
                    continue

            # Save the address
            if noOfAddresses is None:
                gnafWriter.writerow(row)
                outCount += 1
                if (outCount % 100000) == 0:
                    logging.info('%d GNAF_CORE addresses selected', outCount)
                continue
            sa1 = MB[mb]
            SA1s.add(sa1)
            if sa1 not in addresses:
                addresses[sa1] = []
            addresses[sa1].append(row)
    logging.info('Total of %d addresses read in', inCount)

    if noOfAddresses is None:
        gnafSelection.close()
        logging.info('Total of %d GNAF_CORE addresses selected', outCount)
        sys.exit(EX_OK)

    # Create the subset of addresses
    logging.info('Creating %d GNAF_CORE addresses', noOfAddresses)
    SA1list = list(SA1s)
    with open(os.path.join(dataDir, GNAFoutputfile), 'wt', encoding='utf-8-sig', newline="") as gnafSelection:
        gnafWriter = csv.DictWriter(gnafSelection, fieldnames=heading, delimiter='|')
        gnafWriter.writeheader()
        for i in range(noOfAddresses):
            sa1 = random.choice(SA1list)
            while len(addresses[sa1]) == 0:
                sa1 = random.choice(SA1list)
            thisAddress = random.randrange(len(addresses[sa1]))
            gnafWriter.writerow(addresses[sa1][thisAddress])
            del addresses[sa1][thisAddress]
            if ((i + 1) % 100000) == 0:
                logging.info('%d GNAF_CORE addresses selected', i + 1)
    logging.info('Total of %d GNAF_CORE addresses selected', i + 1)
    sys.exit(EX_OK)
