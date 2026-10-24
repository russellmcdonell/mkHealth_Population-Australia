#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement

'''
A script to create HL7 admission, transfer and discharge messages
from an Excel spreadsheet of randomly created health networks, hospitals, clinics, specialists, GPs and patients
created by mkHealthPopulation.py

SYNOPSIS
$ python mkHL7v2.py [-I inputDir|--inputDir=inputDir] [-i inputfile|--inputfile=inputfile]
                    [-O outputDir|--outputDir=outputDir] [-o outputfile|--outputfile=outputfile]
                    [-N noOfEncounters|--noOfEncounters=noOfEncounters]
                    [-v loggingLevel|--loggingLevel=loggingLevel]
                    [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

OPTIONS
-I inputDir|--inputDir=inputDir
The directory containing input file of synthetic health population - output created by mkHealthPopulation.py
[mkHL7v2.cfg will be read from this directory] (default="output")

-i inputfile|--infile=inputfile
The input file to be read (default='healthPopulation.xlsx')

-O outputDir|--outputDir=outputDir
The directory in which the output file will be created (default='output')

-o outputfile|--outputfile=outputfile
The output file to be created (default='ADT.hl7')

-v loggingLevel|--verbose=loggingLevel
Set the level of logging that you want (0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG).

-N noOfPatientsAdmitted|--noOfPatientsAdmitted=noOfPatientsAdmitted
The number of patients to be admitted/transfered/discharged [encounters] (default=10)

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
from datetime import datetime as dt, timedelta as td
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
    parser.add_argument('-N', '--noOfEncounters', metavar='noOfEncounters', dest='noOfEncounters', type=int, default=10,
                        help='The number of patients to be admitted/transfered/discharged [encounters] (default=10)')
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
    noOfEncounters = args.noOfEncounters

    # Read in the spreadsheet of hospitals and patients
    try:
        wb = load_workbook(filename=os.path.join(inputDir, inputfile))
    except (utils.exceptions.InvalidFileException, IOError):
        logging.fatal('No workbook named %s!', inputfile)
        logging.shutdown()
        sys.exit(EX_CONFIG)

    # Start with the network of public hospitals
    try:
        ws = wb['Health Networks']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Health Networks')
        logging.shutdown()
        sys.exit(EX_CONFIG)

    networks = {}
    networkNames = {}
    data = ws.iter_rows(values_only=True)
    headings = next(data)
    for row in data:
        if row[0] is None:
            break
        thisNetwork = dict(zip(headings, row))
        thisNetworkHPIO = thisNetwork['Network HPI-O']
        networks[thisNetworkHPIO] = thisNetwork
        networkNames[thisNetwork['Network Name']] = thisNetworkHPIO

    # Next get the hospitals
    hospitals = {}
    hospitalNames = {}
    hospitalWards = {}
    for hospitalType in ['Public', 'Private']:
        try:
            ws = wb[f'{hospitalType} Hospitals']
        except KeyError:
            logging.fatal('No workbook spreadsheet named %s!', f'{hospitalType} Hospitals')
            logging.shutdown()
            sys.exit(EX_CONFIG)

        data = ws.iter_rows(values_only=True)
        headings = next(data)
        for row in data:
            if row[0] is None:
                break
            thisHospital = dict(zip(headings, row))
            thisHospital['hospitalType'] = hospitalType
            if hospitalType == 'Public':
                thisHospitalHPIO = thisHospital['Hospital HPI-O']
            else:
                thisHospitalHPIO = thisHospital[f'{hospitalType} Hospital HPI-O']
            thisHospitalName = thisHospital['Hospital Name']
            hospitals[thisHospitalHPIO] = thisHospital
            hospitalNames[thisHospitalName] = thisHospitalHPIO

        # Next, collect some wards for the public hospitals
        try:
            ws = wb[f'{hospitalType} Hospital Departments']
        except KeyError:
            logging.fatal('No workbook spreadsheet named %s!', f'{hospitalType} Hospital Departments')
            logging.shutdown()
            sys.exit(EX_CONFIG)

        data = ws.iter_rows(values_only=True)
        headings = next(data)
        for row in data:
            if row[0] is None:
                break
            thisHospitalWard = dict(zip(headings, row))
            if hospitalType == 'Public':
                thisHospitalHPIO = thisHospitalWard['Hospital HPI-O']
            else:
                thisHospitalHPIO = thisHospitalWard[f'{hospitalType} Hospital HPI-O']
            if thisHospitalHPIO not in hospitalWards:
                hospitalWards[thisHospitalHPIO] = []
            hospitalWards[thisHospitalHPIO].append(thisHospitalWard)

    # Next get some local patients
    localPatients = {}
    try:
        ws = wb['Patients']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'Patients')
        logging.shutdown()
        sys.exit(EX_CONFIG)

    data = ws.iter_rows(values_only=True)
    headings = next(data)
    for row in data:
        if row[0] is None:
            break
        thisPatient = dict(zip(headings, row))
        thisPatientsLocalPublicHospital = thisPatient['Local Public Hospital HPI-O']
        if thisPatientsLocalPublicHospital not in localPatients:
            localPatients[thisPatientsLocalPublicHospital] = []
        localPatients[thisPatientsLocalPublicHospital].append(thisPatient)

    # And finally, collect the HL7 PID segments for the patients
    try:
        ws = wb['HL7_PID']
    except KeyError:
        logging.fatal('No workbook spreadsheet named %s!', 'HL7_PID')
        logging.shutdown()
        logging.shutdown()
        sys.exit(EX_CONFIG)

    patientPIDs = {}
    data = ws.iter_rows(values_only=True)
    headings = next(data)
    for row in data:
        if row[0] is None:
            break
        thisPatient = dict(zip(headings, row))
        thisPatientIHI = thisPatient['IHI']
        patientPIDs[thisPatientIHI] = thisPatient
    logging.info('workbook loaded\n')

    # Then read in the configuration from mkHL7v2.cfg
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    try:
        config.read(os.path.join(outputDir, 'mkHL7v2.cfg'))
        for section in config.sections():
            if section == 'receiver':
                receivingApp = config[section]['receivingApp']
                receivingFac = config[section]['receivingFac']
                version = config[section]['version']
            elif section == 'patients':
                NoOfPatients = config[section]['number']
                start = dt.strptime(config[section]['start'], '%Y%m%d')
                end = dt.strptime(config[section]['end'], '%Y%m%d')
                minLOS = int(config[section]['minLOS'])
                maxLOS = int(config[section]['maxLOS'])
            elif section in networkNames:
                networkHPIO = networkNames[section]
                networks[networkHPIO]['nextUR'] = int(config[section]['nextUR'])
            elif section in hospitalNames:
                hospitalHPIO = hospitalNames[section]
                if hospitals[hospitalHPIO]['hospitalType'] == 'Private':
                    hospitals[hospitalHPIO]['nextUR'] = int(config[section]['nextUR'])
                for row in csv.reader([config[section]['admitting']], csv.excel):
                    hospitals[hospitalHPIO]['admitting'] = row
                for row in csv.reader([config[section]['transfer']], csv.excel):
                    hospitals[hospitalHPIO]['transfer'] = row
            else:
                logging.fatal('Configuration for unknown network or hospital: %s', section)
                logging.shutdown()
                sys.exit(EX_CONFIG)
    except (configparser.MissingSectionHeaderError, configparser.NoSectionError,
            configparser.NoOptionError, configparser.ParsingError) as detail:
        logging.fatal('%s', detail)
        logging.fatal('%s', section)
        logging.fatal('%s', repr(config[section]))
        logging.shutdown()
        sys.exit(EX_CONFIG)

    # Delete any "unconfigured" hospitals or networks
    for hospitalHPIO in list(hospitals.keys()):
        if 'admitting' not in hospitals[hospitalHPIO]:
            del hospitals[hospitalHPIO]
    for networkHPIO in list(networks.keys()):
        if 'nextUR' not in networks[networkHPIO]:
            del networks[networkHPIO]

    # Create a template MSH segment
    MSH  = f'MSH|^~\\&|PAS|<sendingFac>|{receivingApp}|{receivingFac}|'
    MSH += '<dateTime>||'                # MSH-7 and MSH-8 [skip security]
    MSH += '<message>|'                    # MSH-9 - Message Type
    MSH += '<dateTime><controlID>|'    # MSH-10
    MSH += 'P|'                        # MSH-11 (P by default)
    MSH += version                    # MSH-12 (configured version by default)

    # Create a template EVN segment
    EVN = 'EVN||<dateTime>'            # EVN - date/time

    # Create a template PV1 segment
    PV1  = 'PV1|1|I|<ward>'                # Inpatient and Ward

    # Now we make some HL7 messages
    controlID = 0
    with open(os.path.join(outputDir, outputfile), 'wt', newline='\r', encoding='utf-8') as HL7file:
        for encounter in range(noOfEncounters):
            thisLOS = minLOS
            thisMaxLOS = random.randrange(minLOS, maxLOS - 1) + 1
            thisStart = start
            hospitalHPIO = random.choice(list(hospitals.keys()))
            thisHospital = hospitals[hospitalHPIO]
            if thisHospital['hospitalType'] == 'Public':
                thisNetworkHPIO = thisHospital['Network HPI-O']
                authority = networks[thisNetworkHPIO]['authority']
                UR = networks[thisNetworkHPIO]['nextUR']
                networks[thisNetworkHPIO]['nextUR'] += 1
                thisLocalHospitalHPIO = thisHospital['Hospital HPI-O']
            else:
                authority = thisHospital['authority']
                UR = thisHospital['nextUR']
                thisHospital['nextUR'] += 1
                thisLocalHospitalHPIO = thisHospital['Local Public Hospital HPI-O']
            # Next chose a local patient
            thisPatient  = random.choice(localPatients[thisLocalHospitalHPIO])
            thisPatientIHI = thisPatient['Patient IHI']
            PIDrow = patientPIDs[thisPatientIHI]
            PID = PIDrow['PID']
            # Select an admission ward
            ward = random.choice(thisHospital['admitting'])
            dateTime = thisStart + td(hours=random.randrange(24)) + td(minutes=random.randrange(60)) + td(seconds=random.randrange(60))
            createDateTime = thisStart + td(hours=random.randrange(24)) + td(minutes=random.randrange(60)) + td(seconds=random.randrange(60))
            if dateTime < createDateTime:
                tmp = dateTime
                dateTime = createDateTime
                createDateTime = tmp
            # Create the patient
            thisMSH = MSH.replace('<sendFac>', authority)
            thisMSH = thisMSH.replace('<message>', 'ADT^A28')
            thisMSH = thisMSH.replace('<dateTime>', dt.strftime(createDateTime, '%Y%m%d%H%M%S')).replace('<controlID>', f'{controlID:06d}')
            controlID += 1
            controlID %= 100000
            thisEVN = EVN.replace('<dateTime>', dt.strftime(createDateTime, '%Y%m%d%H%M%S'))
            PID = PID.replace('<UR>', str(UR)).replace('<AUTH>', authority)
            thisHL7 = '\r'.join([thisMSH, thisEVN, PID])
            print(thisHL7, file=HL7file)

            # Admit the patient
            thisMSH = MSH.replace('<sendFac>', authority)
            thisMSH = thisMSH.replace('<message>', 'ADT^A01')
            thisMSH = thisMSH.replace('<dateTime>', dt.strftime(dateTime, '%Y%m%d%H%M%S')).replace('<controlID>', f'{controlID:06d}')
            controlID += 1
            controlID %= 100000
            thisEVN = EVN.replace('<dateTime>', dt.strftime(dateTime, '%Y%m%d%H%M%S'))
            thisPV1 = PV1.replace('<ward>', ward)
            thisHL7 = '\r'.join([thisMSH, thisEVN, PID, thisPV1])
            print(thisHL7, file=HL7file)

            # Transfer the patient if there's time
            nextEvent = random.randrange(1, 5)
            if len(thisHospital['transfer']) > 1:
                while thisLOS + nextEvent < thisMaxLOS:
                    nextDate = thisStart + td(days=nextEvent)
                    thisStart = nextDate
                    # Transfer the patient
                    oldWard = ward
                    ward = random.choice(thisHospital['transfer'])
                    while ward == oldWard:
                        ward = random.choice(thisHospital['transfer'])
                    dateTime = thisStart + td(hours=random.randrange(24)) + td(minutes=random.randrange(60)) + td(seconds=random.randrange(60))
                    thisMSH = MSH.replace('<sendFac>', authority)
                    thisMSH = thisMSH.replace('<message>', 'ADT^A08')
                    thisMSH = thisMSH.replace('<dateTime>', dt.strftime(dateTime, '%Y%m%d%H%M%S')).replace('<controlID>', f'{controlID:06d}')
                    controlID += 1
                    controlID %= 100000
                    thisEVN = EVN.replace('<dateTime>', dt.strftime(dateTime, '%Y%m%d%H%M%S'))
                    thisPV1 = PV1.replace('<ward>', ward)
                    thisHL7 = '\r'.join([thisMSH, thisEVN, PID, thisPV1])
                    print(thisHL7, file=HL7file)
                    thisLOS += nextEvent
                    nextEvent = random.randrange(2, 5)
            # Discharge the patient
            nextDate = thisStart + td(days=nextEvent)
            thisStart = nextDate
            dateTime = thisStart + td(hours=random.randrange(24)) + td(minutes=random.randrange(60)) + td(seconds=random.randrange(60))
            thisMSH = MSH.replace('<sendFac>', authority)
            thisMSH = thisMSH.replace('<message>', 'ADT^A03')
            thisMSH = thisMSH.replace('<dateTime>', dt.strftime(dateTime, '%Y%m%d%H%M%S')).replace('<controlID>', f'{controlID:06d}')
            controlID += 1
            controlID %= 100000
            thisEVN = EVN.replace('<dateTime>', dt.strftime(dateTime, '%Y%m%d%H%M%S'))
            thisHL7 = '\r'.join([thisMSH, thisEVN, PID, thisPV1])
            print(thisHL7, file=HL7file)
