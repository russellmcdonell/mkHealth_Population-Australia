#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement

'''
A script to create HL7 admission, transfer and discharge messages
from an Excel spreadsheet of randomly created health networks, hospitals, clinics, specialists, GPs and patients
created by mkHealthPopulation.py

SYNOPSIS
$ python mkHL7v2.py [-I inputDir|--inputDir=inputDir] [-i inputfile|--inputfile=inputfile]
                    [-O outputDir|--outputDir=outputDir] [-o outputfile|--outputfile=outputfile]
                    [-v loggingLevel|--loggingLevel=loggingLevel]
                    [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

OPTIONS
-I inputDir|--inputDir=inputDir
The directory containing input file will be created (default='input')
[mkHL7v2.cfg will be read from this directory]

-i inputfile|--infile=inputfile
The input file to be created (default='clinicDoctors.csv')

-O outputDir|--outputDir=outputDir
The directory in which the output file will be created (default='output')

-o outputfile|--outputfile=outputfile
The output file to be created (default='clinicDoctors.csv')

-v loggingLevel|--verbose=loggingLevel
Set the level of logging that you want.

-L logDir|--logDir=logDir
The name of the folder for the logging file

-l logfile|--logfile=logfile
The name of a logging file where you want all messages captured.
'''

import sys
import os
import argparse
import logging
import configparser
import random
import csv
import datetime
from openpyxl import load_workbook
from openpyxl import utils

# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0                # successful termination
EX_WARN = 1                # non-fatal termination with warnings

EX_USAGE = 64            # command line usage error
EX_DATAERR = 65            # data format error
EX_NOINPUT = 66            # cannot open input
EX_NOUSER = 67            # addressee unknown
EX_NOHOST = 68            # host name unknown
EX_UNAVAILABLE = 69        # service unavailable
EX_SOFTWARE = 70        # internal software error
EX_OSERR = 71            # system error (e.g., can't fork)
EX_OSFILE = 72            # critical OS file missing
EX_CANTCREAT = 73        # can't create (user) output file
EX_IOERR = 74            # input/output error
EX_TEMPFAIL = 75        # temp failure; user is invited to retry
EX_PROTOCOL = 76        # remote error in protocol
EX_NOPERM = 77            # permission denied
EX_CONFIG = 78            # configuration error


if __name__ == '__main__':
    '''
The main code
    '''

    # Save the program name
    progName = sys.argv[0]
    progName = progName[0:-3]        # Strip off the .py ending

    parser = argparse.ArgumentParser()
    parser.add_argument('-I', '--inputDir', metavar='inputDir', dest='inputDir', default='input',
                        help='The name of the folder containing the health population Excel file to be read (default="input")')
    parser.add_argument('-i', '--inputfile', metavar='inputfile', dest='inputfile', default='healthPopulation.xlsx',
                        help='The name of health population Excel file to be read (default="healthPopulation.xlsx")')
    parser.add_argument('-O', '--outputDir', dest='outputDir', default='output',
                        help='The name of the output directory [mkHL7v2.cfg will be read from this directory] (default="output")')
    parser.add_argument('-o', '--outputfile', metavar='outputfile', dest='outputfile', default='ADT.hl7',
                        help='The name of file of HL7 messages to be created (default="ADT.hl7"')
    parser.add_argument('-v', '--verbose', dest='loggingLevel', type=int, choices=range(0, 5),
                        help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument('-L', '--logDir', dest='logDir', default='logs',
                        help='The name of a directory for the logging file (default="logs")')
    parser.add_argument('-l', '--logfile', metavar='logfile',
                        dest='logfile', help='The name of a logging file')
    args = parser.parse_args()

    # Set up logging
    logging_levels = {0: logging.CRITICAL, 1: logging.ERROR,
                      2: logging.WARNING, 3: logging.INFO, 4: logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if args.loggingLevel:  # Change the logging level from "WARN" if the -v vebose option is specified
        loggingLevel = args.loggingLevel
        if args.logfile:        # and send it to a file if the -o logfile option is specified
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else:
            logging.basicConfig(
                format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else:
        # send the default (WARN) logging to a file if the -o logfile option is specified
        if args.logfile:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p',
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')

    # Parse the command line options
    inputDir = args.inputDir
    inputfile = args.inputfile
    outputDir = args.outputDir
    outputfile = args.outputfile

    # Read in the spreadsheet of hospitals and patients
    try:
        wb = load_workbook(filename=os.path.join(inputDir, inputfile))
    except (utils.exceptions.InvalidFileException, IOError):
        logging.fatal('No workbook named %s!', inputfile)
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    # Start with the network of public hospitals
    try:
        ws = wb['Health Networks']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Health Networks')
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    header = True
    networkNames = []
    networkID = {}
    networkAuth = {}
    for row in ws.values:
        if header:
            header = False
            continue
        values = list(row)
        network = values[0]
        name = values[1]
        auth = values[2]
        if name in networkNames:
            continue
        networkNames.append(name)
        networkID[name] = network
        networkAuth[network] = auth

    # Next get the associated public hospitals
    try:
        ws = wb['Public Hospitals']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Public Hospitals')
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    header = True
    hospitalNames = []
    hospitalID = {}
    hospitalAuth = {}
    hospitalNetwork = {}
    for row in ws.values:
        if header:
            header = False
            continue
        values = list(row)
        network = values[0]
        hospital = values[1]
        name = values[2]
        if name in hospitalNames:
            continue
        hospitalNames.append(name)
        hospitalID[name] = hospital
        hospitalNetwork[hospital] = network
        hospitalAuth[hospital] = networkAuth[network]

    # Next, collect some wards for the public hospitals
    try:
        ws = wb['Public Hospital Departments']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Public Hospital Departments')
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    hospitalWards = {}
    hospitalWardIDs = {}
    header = True
    for row in ws.values:
        if header:
            header = False
            continue
        values = list(row)
        hospital = values[0]
        ward = values[1]
        name = values[2]
        if hospital not in hospitalWards:
            hospitalWards[hospital] = {}
        hospitalWards[hospital][ward] = values[2:4]
        if hospital not in hospitalWardIDs:
            hospitalWardIDs[hospital] = {}
        hospitalWardIDs[hospital][name] = ward

    # Next get the private hospitals
    try:
        ws = wb['Private Hospitals']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Private Hospitals')
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    header = True
    for row in ws.values:
        if header:
            header = False
            continue
        values = list(row)
        hospital = values[0]
        name = values[1]
        auth = values[2]
        if name in hospitalNames:
            continue
        hospitalNames.append(name)
        hospitalID[name] = hospital
        hospitalAuth[hospital] = auth

    # Next, collect some wards for the private hospitals
    try:
        ws = wb['Private Hospital Departments']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Private Hospital Departments')
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    header = True
    for row in ws.values:
        if header:
            header = False
            continue
        values = list(row)
        hospital = values[0]
        ward = values[1]
        name = values[2]
        if hospital not in hospitalWards:
            hospitalWards[hospital] = {}
        hospitalWards[hospital][ward] = values[2:4]
        if hospital not in hospitalWardIDs:
            hospitalWardIDs[hospital] = {}
        hospitalWardIDs[hospital][name] = ward

    try:
        ws = wb['HL7_PID']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'HL7_PID')
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    # Then collect the PID segments
    header = True
    patients = {}
    for row in ws.values:
        if header:
            header = False
            continue
        values = list(row)
        patients[values[0]] = values[1]
    logging.info('workbook loaded\n')

    # Then read in the configuration from mkHL7v2.cfg
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    hospitals = {}
    networkNextUR = {}
    try:
        config.read(os.path.join(outputDir, 'mkHL7v2.cfg'))
        for section in config.sections():
            if section == 'receiver':
                receivingApp = config[section]['receivingApp']
                receivingFac = config[section]['receivingFac']
                receivingVersion = config[section]['receivingVersion']
            elif section == 'patients':
                NoOfPatients = config[section]['number']
                start = config[section]['start']
                end = config[section]['end']
                minLOS = int(config[section]['minLOS'])
                maxLOS = int(config[section]['maxLOS'])
            elif section in networkNames:
                thisNetworkID = networkID[section]
                networkNextUR[thisNetworkID] = int(config[section]['nextUR'])
            elif section in hospitalNames:
                hospital = hospitalID[section]
                hospitals[hospital] = {}
                if hospital not in hospitalNetwork:
                    hospitals[hospital]['nextUR'] = int(config[section]['nextUR'])
                hospitals[hospital]['admitting'] = []
                for row in csv.reader([config[section]['admitting']], csv.excel):
                    admitting = row
                    break
                for ward in admitting:
                    if ward not in hospitalWardIDs[hospital]:
                        continue
                    wardID = hospitalWardIDs[hospital][ward]
                    hospitals[hospital]['admitting'].append(wardID)
                hospitals[hospital]['transfer'] = []
                for row in csv.reader([config[section]['transfer']], csv.excel):
                    transfer = row
                    break
                for ward in transfer:
                    if ward not in hospitalWardIDs[hospital]:
                        continue
                    wardID = hospitalWardIDs[hospital][ward]
                    hospitals[hospital]['transfer'].append(wardID)
    except (configparser.MissingSectionHeaderError, configparser.NoSectionError,
            configparser.NoOptionError, configparser.ParsingError) as detail:
        logging.fatal('%s', detail)
        logging.fatal('%s', section)
        logging.fatal('%s', repr(config[section]))
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(EX_CONFIG)

    # Create a template MSH segment
    MSH  = 'MSH|^~\\&|<sendApp>|<sendFac>|' + receivingApp + '|' + receivingFac + '|'
    MSH += '<dateTime>||'                # MSH-7 and MSH-8 [skip security]
    MSH += '<message>|'                    # MSH-9 - Message Type
    MSH += '<dateTime><controlID>|'    # MSH-10
    MSH += 'P|'                        # MSH-11 (P by default)
    MSH += receivingVersion                    # MSH-12 (configured version by default)

    # Create a template EVN segment
    EVN = 'EVN||<dateTime>'            # EVN - date/time

    # Create a template PV1 segment
    PV1  = 'PV1|1|I|<ward>'                # Inpatient and Ward

    # Now we make some HL7 messages
    controlID = 0
    with open(os.path.join(outputDir, outputfile), 'wt', newline='\r', encoding='utf-8') as HL7file:
        for patient, PID in patients.items():
            thisLOS = minLOS
            thisMaxLOS = random.randrange(minLOS, maxLOS - 1) + 1
            thisStart = start
            hospital = random.choice(list(hospitals))
            sendFac = hospitalAuth[hospital]
            ward = random.choice(hospitals[hospital]['admitting'])
            wardName = hospitalWards[hospital][ward][0]
            sendApp = hospitalWards[hospital][ward][1]
            dateTime = thisStart + f'{random.randrange(24):02d}{random.randrange(60):02d}{random.randrange(60):02d}'
            createDateTime = thisStart + f'{random.randrange(24):02d}{random.randrange(60):02d}{random.randrange(60):02d}'
            if dateTime < createDateTime:
                tmp = dateTime
                dateTime = createDateTime
                createDateTime = tmp
            # Create the patient
            thisMSH = MSH.replace('<sendApp>', sendApp).replace('<sendFac>', sendFac)
            thisMSH = thisMSH.replace('<message>', 'ADT^A28')
            thisMSH = thisMSH.replace('<dateTime>', createDateTime).replace('<controlID>', f'{controlID:06d}')
            controlID += 1
            controlID %= 100000
            thisEVN = EVN.replace('<dateTime>', createDateTime)
            if hospital in hospitalNetwork:
                network = hospitalNetwork[hospital]
                UR = networkNextUR[network]
                networkNextUR[network] += 1
            else:
                UR = hospitals[hospital]['nextUR']
                hospitals[hospital]['nextUR'] += 1
            PID = PID.replace('<UR>', str(UR)).replace('<AUTH>', sendFac)
            thisHL7 = '\r'.join([thisMSH, thisEVN, PID])
            print(thisHL7, file=HL7file)

            # Admit the patient
            thisMSH = MSH.replace('<sendApp>', sendApp).replace('<sendFac>', sendFac)
            thisMSH = thisMSH.replace('<message>', 'ADT^A01')
            thisMSH = thisMSH.replace('<dateTime>', dateTime).replace('<controlID>', f'{controlID:06d}')
            controlID += 1
            controlID %= 100000
            thisEVN = EVN.replace('<dateTime>', dateTime)
            thisPV1 = PV1.replace('<ward>', wardName)
            thisHL7 = '\r'.join([thisMSH, thisEVN, PID, thisPV1])
            print(thisHL7, file=HL7file)

            # Transfer the patient if there's time
            nextEvent = random.randrange(2, 5)
            if len(hospitals[hospital]['transfer']) > 1:
                while thisLOS + nextEvent < thisMaxLOS:
                    nextDate = datetime.datetime.strptime(thisStart, '%Y%m%d') + datetime.timedelta(days=nextEvent)
                    thisStart = nextDate.strftime('%Y%m%d')
                    # Transfer the patient
                    oldWard = ward
                    ward = random.choice(hospitals[hospital]['transfer'])
                    while ward == oldWard:
                        ward = random.choice(hospitals[hospital]['transfer'])
                    wardName = hospitalWards[hospital][ward][0]
                    sendApp = hospitalWards[hospital][ward][1]
                    dateTime = thisStart + f'{random.randrange(24):02d}{random.randrange(60):02d}{random.randrange(60):02d}'
                    thisMSH = MSH.replace('<sendApp>', sendApp).replace('<sendFac>', sendFac)
                    thisMSH = thisMSH.replace('<message>', 'ADT^A08')
                    thisMSH = thisMSH.replace('<dateTime>', dateTime).replace('<controlID>', f'{controlID:06d}')
                    controlID += 1
                    controlID %= 100000
                    thisEVN = EVN.replace('<dateTime>', dateTime)
                    thisPV1 = PV1.replace('<ward>', wardName)
                    thisHL7 = '\r'.join([thisMSH, thisEVN, PID, thisPV1])
                    print(thisHL7, file=HL7file)
                    thisLOS += nextEvent
                    nextEvent = random.randrange(2, 5)
            # Discharge the patient
            nextDate = datetime.datetime.strptime(thisStart, '%Y%m%d') + datetime.timedelta(days=nextEvent)
            thisStart = nextDate.strftime('%Y%m%d')
            dateTime = thisStart + f'{random.randrange(24):02d}{random.randrange(60):02d}{random.randrange(60):02d}'
            thisMSH = MSH.replace('<sendApp>', sendApp).replace('<sendFac>', sendFac)
            thisMSH = thisMSH.replace('<message>', 'ADT^A03')
            thisMSH = thisMSH.replace('<dateTime>', dateTime).replace('<controlID>', f'{controlID:06d}')
            controlID += 1
            controlID %= 100000
            thisEVN = EVN.replace('<dateTime>', dateTime)
            thisHL7 = '\r'.join([thisMSH, thisEVN, PID, thisPV1])
            print(thisHL7, file=HL7file)
