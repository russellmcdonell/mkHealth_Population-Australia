#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement
'''
A script to create a CSV file of randomly created clinic and medical practitioner records

SYNOPSIS
$ python mkDrClinic.py [-D dataDir|--dataDir=dataDir] [-A addressFile|--addressFile=addressFile]
                       [-O outputDir|--outputDir=outputDir] [-o outputfile|--outputfile=outputfile]
                       [-P|--Patients] [-r|--makeRandom] [-b|-both] [-i|--HPI] [-x|--extendNames]
                       [-v loggingLevel|--loggingLevel=loggingLevel]
                       [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

OPTIONS
-D dataDir|--dataDir=dataDir
The directory containing the source names and address data (default='data')

-A addressFile|--addressFile=addressFile
The file of GNAF_CORE addresses (or subset) (default='GNAF_CORE.psv')

-O outputDir|--outputDir=outputDir
The directory in which the output file will be created (default='output')
[mkDrPMI.cfg will be read from this directory]

-o outputfile|--outfile=outputfile
The output file to be created (default='clinicDoctors.csv')

-P|--Patients
Add a number of patients for each doctor

-r|--makeRandom [P|A]
Make random Australian addresses

-i|--HPI
Add Australian HPI-I, providerNo, presriberNo and HPI-O numbers

-x|--extendName
Extend names with sequential letters

-v loggingLevel|--verbose=loggingLevel
Set the level of logging that you want.

-L logDir|--logDir=logDir
The name of the folder for the logging file

-l logfile|--logfile=logfile
The name of a logging file where you want all messages captured.
'''

import sys
import os
import csv
import argparse
import logging
import configparser
import random
import string
from randPatients import patients, patientKeys, mkRandPatients, mkRandAddress, mkLuhn


# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0           # successful termination
EX_WARN = 1         # non-fatal termination with warnings

EX_USAGE = 64        # command line usage error
EX_DATAERR = 65      # data format error
EX_NOINPUT = 66      # cannot open input
EX_NOUSER = 67       # addressee unknown
EX_NOHOST = 68       # host name unknown
EX_UNAVAILABLE = 69  # service unavailable
EX_SOFTWARE = 70     # internal software error
EX_OSERR = 71        # system error (e.g., can't fork)
EX_OSFILE = 72       # critical OS file missing
EX_CANTCREAT = 73    # can't create (user) output file
EX_IOERR = 74        # input/output error
EX_TEMPFAIL = 75     # temp failure; user is invited to retry
EX_PROTOCOL = 76     # remote error in protocol
EX_NOPERM = 77       # permission denied
EX_CONFIG = 78       # configuration error


def mkProviderNo(thisProviderNo):
    '''
    Add a provider location and checksum to a provider number
    '''
    weights = [3, 5, 8, 4, 2, 1]
    providerLocation = '0123456789ABCDEFGHJKLMNPQRTUVWXY'
    csumChar = 'YXWTLKJHFBA'

    csum = 0
    for i, weight in enumerate(weights):
        csum += int(thisProviderNo[i:i+1]) * weight
        providerLoc = random.choice(range(len(providerLocation)))
        csum += providerLoc * 6
    csum %= 11

    return f'{providerNo}{providerLocation[providerLoc:providerLoc+1]}{csumChar[csum:csum+1]}'


def mkPrescriberNo(prescriberNo):
    '''
    Add a check digit to a PBS prescriber number
    '''
    cdigit = '01234567890'
    csum = 0
    if prescriberNo[0] == '0':
        csum = (int(prescriberNo[1]) * 5 + int(prescriberNo[2]) * 8 + int(prescriberNo[3]) * 4 + int(prescriberNo[4]) * 2 + int(prescriberNo[5])) % 11
    else:
        csum = int(prescriberNo[0]) + int(prescriberNo[1]) * 3 + int(prescriberNo[2]) * 7 + int(prescriberNo[3]) * 9 + int(prescriberNo[4]) + int(prescriberNo[5]) * 3
    csum %= 10
    return prescriberNo + cdigit[csum]



if __name__ == '__main__':
    '''
The main code
    '''

    # Save the program name
    progName = sys.argv[0]
    progName = progName[0:-3]        # Strip off the .py ending

    parser = argparse.ArgumentParser()
    parser.add_argument('-D', '--dataDir', dest='dataDir', default='data',
                        help='The name of the directory containing source names and address data(default="data")')
    parser.add_argument('-A', '--addressFile', dest='addressFile', default='GNAF_CORE.psv',
                        help='The file of GNAF_CORE addresses (or subset) (default="GNAF_CORE.psv})')
    parser.add_argument('-O', '--outputDir', dest='outputDir', default='output',
                        help='The name of the output directory [mkDrPMI.cfg will be read from this directory] (default="output")')
    parser.add_argument('-o', '--outfile', metavar='outputfile', dest='outputfile', default='clinicDoctors.csv', help='The name of the clinic and doctors csv file to be created')
    parser.add_argument('-P', '--Patients', dest='Patients', action='store_true', help='Output Patients for each doctor')
    parser.add_argument('-r', '--makeRandom', dest='makeRandom', action='store_true', help='Make random Australian addresses')
    parser.add_argument('-i', '--HPI', dest='HPI', action='store_true', help='Add Australian HPI-I, providerNo, prescriberNo and HPI-O numbers')
    parser.add_argument('-x', '--extendNames', dest='extendNames', action='store_true', help='Extend names with sequential letters')
    parser.add_argument('-v', '--verbose', dest='loggingLevel', type=int, choices=range(0,5), help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument('-L', '--logDir', dest='logDir', default='logs', help='The name of a directory for the logging file(default="logs")')
    parser.add_argument('-l', '--logfile', metavar='logfile', dest='logfile', help='The name of a logging file')
    args = parser.parse_args()

    # Set up logging
    logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if args.loggingLevel:   # Change the logging level from "WARN" as the -v vebose option was specified
        loggingLevel = args.loggingLevel
        if args.logfile:        # and send it to a file if the -o logfile option is specified
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
                               filemode='w', filename=os.path.join(args.lodDir, args.logfile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else:                   # Send the default (WARN) logging to a file if the -o logfile option is specified
        if args.logfile:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', filemode='w',
                                filename=os.path.join(args.logDir, args.logfile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')

    # Parse the remaining command line options
    dataDir = args.dataDir
    addressFile = args.addressFile
    outputDir = args.outputDir
    outputfile = args.outputfile
    makeRandom = args.makeRandom
    Patients = args.Patients
    HPI = args.HPI
    extendNames = args.extendNames

    # Then read in the configuration from mkDrClinic.cfg
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    try:
        config.read(os.path.join(outputDir, 'mkDrClinic.cfg'))
        startClinic = config.getint('Clinic', 'startClinic')
        endClinic = config.getint('Clinic', 'endClinic')
        skipClinic = config.getint('Clinic', 'skipClinic')
        maxDr = config.getint('Clinic', 'maxDr')
        maxSpec = config.getint('Clinic', 'maxSpec')
        if HPI:
            startHPIO = config.getint('HPIO', 'startHPIO') % 10000000
            skipHPIO = config.getint('HPIO', 'skipHPIO')
            percentHPIO = config.getfloat('HPIO', 'percentHPIO')
            if (percentHPIO > 100.0) or (percentHPIO < 0.0):
                percentHPIO = 10.0
            startHPII = config.getint('HPII', 'startHPII') % 10000000
            skipHPII = config.getint('HPII', 'skipHPII')
            percentHPII = config.getfloat('HPII', 'percentHPII')
            if (percentHPII > 100.0) or (percentHPII < 0.0):
                percentHPII = 10.0
        startDr = config.getint('Dr', 'startDr')
        skipDr = config.getint('Dr', 'skipDr')
        if Patients:
            minPatients = config.getint('Patients', 'minPatients')
            maxPatients = config.getint('Patients', 'maxPatients')
        fields = config.get('Fields', 'fields')
        drFields = config.get('Fields', 'drFields')
        clinicFields = config.get('Fields', 'clinicFields')
        dialect = csv.Sniffer().sniff(fields)
        dialect.skipinitialspace = True
        for row in csv.reader([fields], dialect):
            fields = row
            break
        dialect = csv.Sniffer().sniff(drFields)
        dialect.skipinitialspace = True
        for row in csv.reader([drFields], dialect):
            drFields = row
            break
        dialect = csv.Sniffer().sniff(clinicFields)
        dialect.skipinitialspace = True
        for row in csv.reader([clinicFields], dialect):
            clinicFields = row
            break
        minAge = config.getint('AgeRange', 'minAge')
        maxAge = config.getint('AgeRange', 'maxAge')
    except (configparser.MissingSectionHeaderError, configparser.NoSectionError, configparser.NoOptionError, configparser.ParsingError) as detail :
        logging.fatal('%s', detail)
        sys.exit(EX_CONFIG)

    startClinic = int(startClinic)
    endClinic = int(endClinic)
    skipClinic = int(skipClinic)
    maxDr = int(maxDr)
    ClinicId = startClinic
    if HPI:
        HPIOno = startHPIO
    if skipClinic < 1:
        skipClinic = 1
    startDr = int(startDr)
    skipDr = int(skipDr)
    if skipDr < 1:
        skipDr = 1
    DrId = startDr
    if HPI:
        HPIIno = startHPII
    if Patients:
        minPatients = int(minPatients)
        maxPatients = int(maxPatients)
    personNo = 0
    noOfClinics = int(((endClinic - startClinic)/skipClinic)*2)            # Number of clinics
    noOfRecords = noOfClinics + noOfClinics * int(((maxDr)/2)*2)           # Plus number of doctors for each clinic
    noOfRecords += noOfClinics * int((maxSpec + 2)/2)                # Plus the number of specialists working in each clinic
    if Patients:
        noOfRecords += noOfRecords * int(((maxPatients - minPatients)/2)*2)    # Plus number of patients per doctor, for each doctor, for each clinic

    UsedIDs = {}
    mkRandPatients(dataDir, addressFile, noOfRecords, extendNames, False, makeRandom, minAge, maxAge, UsedIDs, False)        # Create enough random patient

    # Create the Clinic and Doctor records
    cCount = 0
    dCount = 0
    pCount = 0
    usedProviderNo = set()
    usedAhpraNo = set()
    with open(os.path.join(outputDir, outputfile), 'wt', encoding='utf-8', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, dialect=csv.excel)
        fileFields = ['ClinicId']
        if HPI:
            fileFields += ['HPI-O']
        fileFields += ['ClinicName', 'DrId', 'providerNo', 'prescriberNo', 'ahpraNo']
        if HPI:
            fileFields += ['HPI-I']
        if Patients:
            if HPI:
                fileFields += ['IHI']
        fileFields += ['givenName', 'familyName'] + fields
        csvwriter.writerow(fileFields)
        while ClinicId < endClinic:
            me = patientKeys[personNo]
            personNo += 1
            patients[me]['ClinicId'] = ClinicId
            if HPI:
                if random.random()*100 < percentHPIO:                    # Check HPI-O required
                    patients[me]['HPI-O'] = f"{800362990000000 + HPIOno:d}{mkLuhn(f'{800362990000000 + HPIOno:d}'):d}"
                else:
                    patients[me]['HPI-O'] = None

            # Create an clinic from street or suburb plus Medical/Medical Clinic/Medical Centre
            if random.random() < 0.7:            # street or suburb
                clinic = patients[me]['streetName'] + ' ' + patients[me]['streetType']
            else:
                clinic = patients[me]['suburb']
            clinic += ' Medical'
            if random.random() < 0.4:            # Clinic or Centre or nothing
                clinic += ' Clinic'
            elif random.random() < 0.4:            # Clinic or Centre or nothing
                clinic += ' Centre'
            patients[me]['ClinicName'] = clinic
            email = string.capwords(clinic) + '@his4ehr.com'
            patients[me]['email'] = email.replace(' ', '')
            patients[me]['DrId'] = None
            if HPI:
                patients[me]['HPI-I'] = None
            patients[me]['providerNo'] = None
            patients[me]['prescriberNo'] = None
            patients[me]['ahpraNo'] = None
            patients[me]['IHI'] = None
            patients[me]['familyName'] = None
            patients[me]['givenName'] = None
            cCount += 1
            clinic = []
            for field in (fileFields):
                if field in (fields):
                    if field in (clinicFields):
                        clinic.append(patients[me][field])
                    else:
                        clinic.append(None)
                else:
                    clinic.append(patients[me][field])
            csvwriter.writerow(clinic)
            clinicSA1 = patients[me]['sa1']

            # Create a number of specialist who work in the clinic but don't have patients
            for spec in (range(random.randrange(2, maxSpec + 1))):
                me = patientKeys[personNo]
                personNo += 1
                thisAddr = mkRandAddress(clinicSA1, True, makeRandom)
                patients[me]['streetNo'] = thisAddr['streetNo']
                patients[me]['streetName'] = thisAddr['streetName']
                patients[me]['streetType'] = thisAddr['streetType']
                patients[me]['shortStreetType'] = thisAddr['shortStreetType']
                patients[me]['suburb'] = thisAddr['suburb']
                patients[me]['state'] = thisAddr['state']
                patients[me]['postcode'] = thisAddr['postcode']
                patients[me]['country'] = 'AUS'
                patients[me]['longitude'] = thisAddr['longitude']
                patients[me]['latitude'] = thisAddr['latitude']
                patients[me]['ClinicId'] = ClinicId
                if HPI:
                    patients[me]['HPI-O'] = None
                patients[me]['ClinicName'] = None
                patients[me]['DrId'] = DrId
                if HPI:
                    if random.random()*100 < percentHPII:                    # Check HPI-I required
                        patients[me]['HPI-I'] = f"{800361990000000 + HPIIno:d}{mkLuhn(f'{800361990000000 + HPIIno:d}'):d}"
                    else:
                        patients[me]['HPI-I'] = None
                while True:        # Loop if the providerNo is not distinct
                    providerNo = random.randint(100000, 999999)
                    if providerNo not in usedProviderNo:
                        break
                usedProviderNo.add(providerNo)
                providerNo = str(providerNo).zfill(6)
                patients[me]['providerNo'] = mkProviderNo(providerNo)
                patients[me]['prescriberNo'] = mkPrescriberNo(providerNo)
                while True:        # Loop if the ahpraNo is not distinct
                    ahpraNo = random.randint(9000000000, 9999999999)
                    if ahpraNo not in usedAhpraNo:
                        break
                usedAhpraNo.add(ahpraNo)
                patients[me]['ahpraNo'] = 'MED' + str(ahpraNo)
                dCount += 1
                doctor = []
                for field in (fileFields):
                    if field in (fields):
                        if field in (drFields):
                            doctor.append(patients[me][field])
                        else:
                            doctor.append(None)
                    else:
                        doctor.append(patients[me][field])
                csvwriter.writerow(doctor)

                if skipDr == 0:
                    DrId += 1
                elif skipDr < 3:
                    DrId += skipDr
                else:
                    DrId += random.randrange(skipDr - 1, skipDr + 1)
                if HPI:
                    if skipHPII == 0:
                        HPIIno += 1
                    elif skipHPII < 3:
                        HPIIno += skipHPII
                    else:
                        HPIIno += random.randrange(skipHPII - 1, skipHPII + 1)
                    HPIIno %= 10000000

            for dr in (range(random.randrange(1, maxDr + 1))):
                me = patientKeys[personNo]
                personNo += 1
                thisAddr = mkRandAddress(clinicSA1, True, makeRandom)
                patients[me]['streetNo'] = thisAddr['streetNo']
                patients[me]['streetName'] = thisAddr['streetName']
                patients[me]['streetType'] = thisAddr['streetType']
                patients[me]['shortStreetType'] = thisAddr['shortStreetType']
                patients[me]['suburb'] = thisAddr['suburb']
                patients[me]['state'] = thisAddr['state']
                patients[me]['postcode'] = thisAddr['postcode']
                patients[me]['country'] = 'AUS'
                patients[me]['longitude'] = thisAddr['longitude']
                patients[me]['latitude'] = thisAddr['latitude']
                patients[me]['ClinicId'] = ClinicId
                if HPI:
                    patients[me]['HPI-O'] = None
                patients[me]['ClinicName'] = None
                patients[me]['DrId'] = DrId
                if HPI:
                    if random.random()*100 < percentHPII:                    # Check HPI-I required
                        patients[me]['HPI-I'] = f"{800361990000000 + HPIIno}{mkLuhn(f'{800361990000000 + HPIIno:d}'):d}"
                    else:
                        patients[me]['HPI-I'] = None
                while True:        # Loop if the providerNo is not distinct
                    providerNo = random.randint(100000, 999999)
                    if providerNo not in usedProviderNo:
                        break
                usedProviderNo.add(providerNo)
                providerNo = str(providerNo).zfill(6)
                patients[me]['providerNo'] = mkProviderNo(providerNo)
                patients[me]['prescriberNo'] = mkPrescriberNo(providerNo)
                while True:        # Loop if the ahpraNo is not distinct
                    ahpraNo = random.randint(9000000000, 9999999999)
                    if ahpraNo not in usedAhpraNo:
                        break
                usedAhpraNo.add(ahpraNo)
                patients[me]['ahpraNo'] = 'MED' + str(ahpraNo)
                dCount += 1
                doctor = []
                for field in (fileFields):
                    if field in (fields):
                        if field in (drFields):
                            doctor.append(patients[me][field])
                        else:
                            doctor.append(None)
                    else:
                        doctor.append(patients[me][field])
                csvwriter.writerow(doctor)

                if Patients:
                    for patient in (range(random.randrange(minPatients, maxPatients + 1))):
                        me = patientKeys[personNo]
                        personNo += 1
                        thisAddr = mkRandAddress(clinicSA1, True, makeRandom)
                        patients[me]['streetNo'] = thisAddr['streetNo']
                        patients[me]['streetName'] = thisAddr['streetName']
                        patients[me]['streetType'] = thisAddr['streetType']
                        patients[me]['shortStreetType'] = thisAddr['shortStreetType']
                        patients[me]['suburb'] = thisAddr['suburb']
                        patients[me]['state'] = thisAddr['state']
                        patients[me]['postcode'] = thisAddr['postcode']
                        patients[me]['country'] = 'AUS'
                        patients[me]['longitude'] = thisAddr['longitude']
                        patients[me]['latitude'] = thisAddr['latitude']
                        patients[me]['ClinicId'] = ClinicId
                        if HPI:
                            patients[me]['HPI-O'] = None
                        patients[me]['ClinicName'] = None
                        patients[me]['DrId'] = None
                        if HPI:
                            patients[me]['HPI-I'] = None
                        patients[me]['providerNo'] = None
                        patients[me]['prescriberNo'] = None
                        patients[me]['ahpraNo'] = None
                        pCount += 1
                        thisPatient = []
                        for field in (fileFields):
                            thisPatient.append(patients[me][field])
                        csvwriter.writerow(thisPatient)


                if skipDr == 0:
                    DrId += 1
                elif skipDr < 3:
                    DrId += skipDr
                else:
                    DrId += random.randrange(skipDr - 1, skipDr + 1)
                if HPI:
                    if skipHPII == 0:
                        HPIIno += 1
                    elif skipHPII < 3:
                        HPIIno += skipHPII
                    else:
                        HPIIno += random.randrange(skipHPII - 1, skipHPII + 1)
                    HPIIno %= 10000000

            if skipClinic == 0:
                ClinicId += 1
            elif skipClinic < 3:
                ClinicId += skipClinic
            else:
                ClinicId += random.randrange(skipClinic - 1, skipClinic + 1)
            if HPI:
                if skipHPIO == 0:
                    HPIOno += 1
                elif skipHPIO < 3:
                    HPIOno += skipHPIO
                else:
                    HPIOno += random.randrange(skipHPIO - 1, skipHPIO + 1)
                HPIOno %= 10000000

    # Report the results
    print(f'{cCount}\tclinic records created')
    print(f'{dCount}\tdoctor records created')
    if Patients:
        print(f'{pCount}\tpatient records created')
