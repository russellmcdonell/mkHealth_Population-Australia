#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement, broad-exception-caught, too-many-lines

'''
A script to create a secondary PMI CSV file of randomly created patient records.

This script it very tightly coupled to the mkPMI script. It reads in a master PMI file which it assumes has been created by the mkPMI script.
It is not essential that the master PMI file has been created by the mkPMI script. However it is essential that the master PMI file
has a header row which names the columns, and that the file contain columns named 'UR', 'familyName', 'givenName', 'birthdate' and 'sex'.
If the master PMI file contains columns named 'Alias' and/or 'Merged' then those column must contain UR numbers from the master PMI file.
If the master PMI file contains a column named 'Deleted' then that column must contain the letter 'D' to indicate a deleted record.


SYNOPSIS
$ python mkAltPMI.py [-D dataDir|--dataDir=dataDir] [-A addressFile|--addressFile=addressFile]
                     [-I inputDir|--inputDir=inputDir] [-M masterPMIinputfile|--masterPMIfile=masterPMIinputfile]
                     [-O outputDir|--outputDir=outputDir] [-S secondaryPMIoutputfile|--secondaryPMIfile=secondaryPMIoutputfile]
                     [-r|--makeRandom] [-b|-both] [-a|alias2alias] [-m|-merge2merge] [-i|--IHI] [-x|--extendNames] [-e|--errors]
                     [-v loggingLevel|--loggingLevel=loggingLevel]
                     [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

OPTIONS
-D dataDir|--dataDir=dataDir
The directory containing the source names and address data (default='data')

-A addressFile|--addressFile=addressFile
The file of GNAF_CORE addresses (or subset) (default='GNAF_CORE.psv')

-I inputDir|--inputDir=inputDir
The directory containing the master PMI file (default='input')

-M masterPMIinputfile|--masterPMIfile=masterPMIinputfile
The masterPMI file to be read. Default = master.csv

-O outputDir|--outputDir=outputDir
The directory where the output will be created (default='output')

-S secondaryPMIoutputfile|--secondaryPMIfile=secondaryPMIoutputfile
The secondaryPMI file to be created. Default = secondary.csv

-r|--makeRandom
Make random Australian addresses

-b|--both
secondary PMI records can be both Alias records and Merged records

-a|--alias2alias
secondary PMI records can be Aliases of Alias records

-m|--merge2merge
secondary PMI records can be Merges to already Merged records

-i|--IHI
Add alt Australian IHI number

-x|--extendNames
Extend names with sequential letters

-e|--errors
Create errors, such as duplicat UR records, merged and aliases that point to non-existent records or point to deleted records.

-v loggingLevel|--verbose=loggingLevel
Set the level of logging that you want.

-L logDir|--logDir=logDir
The name of the folder for the logging file

-l logfile|--logfile=logfile
The name of a logging file where you want all messages captured.
'''

import sys
import csv
import io
import os
import argparse
import logging
import configparser
import random
import datetime
import re
from names import nicknames
from randPatients import patients, patientKeys, mkRandPatients, selectFamilyName, selectBoysname, selectGirlsname, mkLuhn


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


def masterClone(thisMe, thisLinkMe):
    '''
Clone thisLinkMe onto thisMe
    '''
# namely: givenName,familyName,birthdate,sex,streetNo,streetName,streetType,suburb,state,postcode,longitude,latitude,country,mobile,homePhone,businessPhone,email,medicareNo,IHI,dvaNo,dvaType,height,weight,waist,hips,married,race,deathDate

    thisCloneInfo = ''
    patients[thisMe]['givenName'] = master[thisLinkMe]['givenName']
    patients[thisMe]['familyName'] = master[thisLinkMe]['familyName']
    if random.random() < 0.8:                # Often the address is correct
        thisCloneInfo = 'addr'
        if 'streetNo' in PMIfields:
            patients[thisMe]['streetNo'] = master[thisLinkMe]['streetNo']
        if 'streetName' in PMIfields:
            patients[thisMe]['streetName'] = master[thisLinkMe]['streetName']
        if 'streetType' in PMIfields:
            patients[thisMe]['streetType'] = master[thisLinkMe]['streetType']
        if 'shortStreetType' in PMIfields:
            patients[thisMe]['shortStreetType'] = master[thisLinkMe]['shortStreetType']
        if 'suburb' in PMIfields:
            patients[thisMe]['suburb'] = master[thisLinkMe]['suburb']
        if 'state' in PMIfields:
            patients[thisMe]['state'] = master[thisLinkMe]['state']
        if 'postcode' in PMIfields:
            patients[thisMe]['postcode'] = master[thisLinkMe]['postcode']
        if 'longitude' in PMIfields:
            patients[thisMe]['longitude'] = master[thisLinkMe]['longitude']
        if 'latitude' in PMIfields:
            patients[thisMe]['latitude'] = master[thisLinkMe]['latitude']
        if 'country' in PMIfields:
            patients[thisMe]['country'] = master[thisLinkMe]['country']
    if random.random() < 0.2:                # Sometimes the birthdate is wrong
        (thisYear, thisMonth, thisDay) = master[thisLinkMe]['birthdate'].split('-')
        thisYear = int(thisYear)
        thisMonth = int(thisMonth)
        thisDay = int(thisDay)
        thisBirthdate = datetime.date(thisYear, thisMonth, thisDay)
        if random.random() < 0.4:                # Sometimes the year is wrong
            thisBirthdate += datetime.timedelta(days=365)*(int(random.random()*5.0) - 2)
        if random.random() < 0.3:                # Sometimes the month is wrong
            thisBirthdate += datetime.timedelta(days=31)*(int(random.random()*5.0) - 2)
        if random.random() < 0.3:                # Sometimes the day is wrong
            thisBirthdate += datetime.timedelta(days=1)*(int(random.random()*5.0) - 2)
        if thisBirthdate < datetime.date.today():
            patients[thisMe]['birthdate'] = thisBirthdate.isoformat()
    else:
        if thisCloneInfo == '':
            thisCloneInfo = 'bd'
        else:
            thisCloneInfo += ',bd'
        patients[thisMe]['birthdate'] = master[thisLinkMe]['birthdate']
    patients[thisMe]['sex'] = master[thisLinkMe]['sex']
    if thisCloneInfo == '':
        thisCloneInfo = 'sex'
    else:
        thisCloneInfo += ',sex'
    if 'mobile' in PMIfields:
        patients[thisMe]['mobile'] = master[thisLinkMe]['mobile']
    if 'homePhone' in PMIfields:
        patients[thisMe]['homePhone'] = master[thisLinkMe]['homePhone']
    if 'businessPhone' in PMIfields:
        patients[thisMe]['businessPhone'] = master[thisLinkMe]['businessPhone']
    if 'email' in PMIfields:
        patients[thisMe]['email'] = master[thisLinkMe]['email']
    if 'medicareNo' in PMIfields:
        patients[thisMe]['medicareNo'] = master[thisLinkMe]['medicareNo']
    if 'IHI' in PMIfields:
        patients[thisMe]['IHI'] = master[thisLinkMe]['IHI']
    if 'dvaNo' in PMIfields:
        patients[thisMe]['dvaNo'] = master[thisLinkMe]['dvaNo']
    if 'dvaType' in PMIfields:
        patients[thisMe]['dvaType'] = master[thisLinkMe]['dvaType']
    if 'height' in PMIfields:
        height = float(master[thisLinkMe]['height'])
        patients[thisMe]['height'] = f'{random.normalvariate(height, height/50.0):.0f}'
    if 'weight' in PMIfields:
        weight = float(master[thisLinkMe]['weight'])
        patients[thisMe]['weight'] = f'{random.normalvariate(weight, weight/20.0):.0f}'
    if 'waist' in PMIfields:
        waist = float(master[thisLinkMe]['waist'])
        patients[thisMe]['waist'] = f'{random.normalvariate(waist, waist/25.0):.0f}'
    if 'hips' in PMIfields:
        hips = float(master[thisLinkMe]['hips'])
        patients[thisMe]['hips'] = f'{random.normalvariate(hips, waist/25.0):.0f}'
    if 'married' in PMIfields:
        patients[thisMe]['married'] = master[thisLinkMe]['married']
    if 'race' in PMIfields:
        patients[thisMe]['race'] = master[thisLinkMe]['race']
    if 'deathDate' in PMIfields:
        patients[thisMe]['deathDate'] = master[thisLinkMe]['deathDate']
    return 'name,' + thisCloneInfo


def clone(thisMe, other):
    '''
Clone other onto thisMe
    '''
# namely: givenName,familyName,birthdate,sex,streetNo,streetName,streetType,suburb,state,postcode,longitude,latitude,country,mobile,homePhone,businessPhone,email,medicareNo,IHI,dvaNo,dvaType,height,weight,waist,hips,married,race,deathDate

    thisCloneInfo = ''
    patients[thisMe]['givenName'] = patients[other]['givenName']
    patients[thisMe]['familyName'] = patients[other]['familyName']
    if random.random() < 0.8:                # Often the address is correct
        if thisCloneInfo == '':
            thisCloneInfo = 'addr'
        else:
            thisCloneInfo += ',addr'
        if 'streetNo' in PMIfields:
            patients[thisMe]['streetNo'] = patients[other]['streetNo']
        if 'streetName' in PMIfields:
            patients[thisMe]['streetName'] = patients[other]['streetName']
        if 'streetType' in PMIfields:
            patients[thisMe]['streetType'] = patients[other]['streetType']
        if 'shortStreetType' in PMIfields:
            patients[thisMe]['shortStreetType'] = patients[other]['shortStreetType']
        if 'suburb' in PMIfields:
            patients[thisMe]['suburb'] = patients[other]['suburb']
        if 'state' in PMIfields:
            patients[thisMe]['state'] = patients[other]['state']
        if 'postcode' in PMIfields:
            patients[thisMe]['postcode'] = patients[other]['postcode']
        if 'longitude' in PMIfields:
            patients[thisMe]['longitude'] = patients[other]['longitude']
        if 'latitude' in PMIfields:
            patients[thisMe]['latitude'] = patients[other]['latitude']
        if 'country' in PMIfields:
            patients[thisMe]['country'] = patients[other]['country']
    if random.random() < 0.2:                # Sometimes the phone numbers are wrong
        if thisCloneInfo == '':
            thisCloneInfo = 'ph'
        else:
            thisCloneInfo += ',ph'
        if 'mobile' in PMIfields:
            patients[thisMe]['mobile'] = patients[other]['mobile']
        if 'homePhone' in PMIfields:
            patients[thisMe]['homePhone'] = patients[other]['homePhone']
        if 'businessPhone' in PMIfields:
            patients[thisMe]['businessPhone'] = patients[other]['businessPhone']
        if 'email' in PMIfields:
            patients[thisMe]['email'] = patients[other]['email']
    if thisCloneInfo == '':
        thisCloneInfo = 'bd'
    else:
        thisCloneInfo += ',bd'
    if random.random() < 0.2:                # Sometimes the birthdate is wrong
        (thisYear, thisMonth, thisDay) = patients[other]['birthdate'].split('-')
        thisYear = int(thisYear)
        thisMonth = int(thisMonth)
        thisDay = int(thisDay)
        thisBirthdate = datetime.date(thisYear, thisMonth, thisDay)
        if random.random() < 0.4:                # Sometimes the year is wrong
            thisBirthdate += datetime.timedelta(days=365)*(int(random.random()*5.0) - 2)
        if random.random() < 0.3:                # Sometimes the month is wrong
            thisBirthdate += datetime.timedelta(days=31)*(int(random.random()*5.0) - 2)
        if random.random() < 0.3:                # Sometimes the day is wrong
            thisBirthdate += datetime.timedelta(days=1)*(int(random.random()*5.0) - 2)
        patients[thisMe]['birthdate'] = thisBirthdate.isoformat()
    else:
        patients[thisMe]['birthdate'] = patients[other]['birthdate']
    if thisCloneInfo == '':
        thisCloneInfo = 'sex'
    else:
        thisCloneInfo += ',sex'
    patients[thisMe]['sex'] = patients[other]['sex']
    if thisCloneInfo == '':
        thisCloneInfo = 'mc,etc'
    else:
        thisCloneInfo += ',mc,etc'
    if 'medicareNo' in PMIfields:
        patients[thisMe]['medicareNo'] = patients[other]['medicareNo']
    if 'IHI' in PMIfields:
        patients[thisMe]['IHI'] = patients[other]['IHI']
    if 'dvaNo' in PMIfields:
        patients[thisMe]['dvaNo'] = patients[other]['dvaNo']
    if 'dvaType' in PMIfields:
        patients[thisMe]['dvaType'] = patients[other]['dvaType']
    if 'height' in PMIfields:
        height = float(patients[other]['height'])
        patients[thisMe]['height'] = f'{random.normalvariate(height, height/50.0):.0f}'
    if 'weight' in PMIfields:
        weight = float(patients[other]['weight'])
        patients[thisMe]['weight'] = f'{random.normalvariate(weight, weight/20.0):.0f}'
    if 'waist' in PMIfields:
        waist = float(patients[other]['waist'])
        patients[thisMe]['waist'] = f'{random.normalvariate(waist, waist/25.0):.0f}'
    if 'hips' in PMIfields:
        hips = float(patients[other]['hips'])
        patients[thisMe]['hips'] = f'{random.normalvariate(hips, hips/25.0):.0f}'
    if 'married' in PMIfields:
        patients[thisMe]['married'] = patients[other]['married']
    if 'race' in PMIfields:
        patients[thisMe]['race'] = patients[other]['race']
    if 'deathDate' in PMIfields:
        patients[thisMe]['deathDate'] = patients[other]['deathDate']
    return 'name,' + thisCloneInfo


def csvString(thisRow):
    '''
    Convert this row to a CSV compliant string
    '''

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(thisRow)
    return si.getvalue().rstrip('\r\n')



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
                        help='The file of GNAF_CORE addresses (or subset) (default="GNAF_CORE.psv")')
    parser.add_argument('-I', '--inputDir', dest='inputDir', default='input',
                        help='The name of the directory containing the master PMI csv inputfile)default="input"')
    parser.add_argument('-M', '--masterPMIfile', dest='masterPMIinputfile', default='master.csv',
                        help='The name of the master PMI csv file to be read(default="master.csv"')
    parser.add_argument('-O', '--outputDir', dest='outputDir', default='output',
                        help='The name of the output directory [mkAltPMI.cfg will be read from this directory](default="output")')
    parser.add_argument('-S', '--secondaryPMIfile', dest='secondaryPMIoutputfile', default='secondary.csv',
                        help='The name of the secondary PMI csv file to be created(default="secondary.csv"')
    parser.add_argument('-r', '--makeRandom', dest='makeRandom', action='store_true', help='Make random Australian address')
    parser.add_argument('-b', '--both', dest='both', action='store_true', help='PMI records can be both merged and an alias')
    parser.add_argument('-a', '--alias2alias', dest='alias2alias', action='store_true', help='Allow aliases to aliased or merged patient')
    parser.add_argument('-m', '--merge2merge', dest='merge2merge', action='store_true', help='Allow merges to aliased or merged patient')
    parser.add_argument('-i', '--IHI', dest='IHI', action='store_true', help='Add alt Australian IHI number')
    parser.add_argument('-x', '--extendNames', dest='extendNames', action='store_true', help='Extend names with sequential letters')
    parser.add_argument('-e', '--errors', dest='errors', action='store_true', help='Create PMI with errors')
    parser.add_argument('-v', '--verbose', dest='loggingLevel', type=int, choices=range(0,5),
                        help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument('-L', '--logDir', dest='logDir', default='logs', help='The name of a directory for the logging file(default="logs")')
    parser.add_argument('-l', '--logfile', dest='logfile', help='The name of a logging file')
    args = parser.parse_args()

    # Parse the command line options
    logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if args.loggingLevel:    # Change the logging level from "WARN" if the -v vebose option is specified
        loggingLevel = args.loggingLevel
        if args.logfile:        # and send it to a file if the -o logfile option is specified
            # Check that the logDir exists
            if not os.path.isdir(args.logDir):
                logging.critical('Usage error - logDir (%s) does not exits', args.logDir)
                logging.shutdown()
                sys.exit(EX_USAGE)
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else:
        if args.logfile:        # send the default (WARN) logging to a file if the -o logfile option is specified
            # Check that the logDir exists
            if not os.path.isdir(args.logDir):
                logging.critical('Usage error - logDir (%s) does not exits', args.logDir)
                logging.shutdown()
                sys.exit(EX_USAGE)
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p',
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')

    dataDir = args.dataDir
    addressFile = args.addressFile
    inputDir = args.inputDir
    PMIinputfile = args.masterPMIinputfile
    outputDir = args.outputDir
    PMIoutputfile = args.secondaryPMIoutputfile
    makeRandom = args.makeRandom
    both = args.both
    alias2alias = args.alias2alias
    merge2merge = args.merge2merge
    IHI = args.IHI
    extendNames = args.extendNames
    errors = args.errors

    # Check that the dataDir exists
    if not os.path.isdir(dataDir):
        logging.critical('Usage error - dataDir (%s) does not exits', dataDir)
        logging.shutdown()
        sys.exit(EX_USAGE)
    # Check that the inputDir exists
    if not os.path.isdir(inputDir):
        logging.critical('Usage error - inputDir (%s) does not exits', inputDir)
        logging.shutdown()
        sys.exit(EX_USAGE)
    # Check that the outputDir exists
    if not os.path.isdir(outputDir):
        logging.critical('Usage error - outputDir (%s) does not exits', outputDir)
        logging.shutdown()
        sys.exit(EX_USAGE)

    # Then read in the configuration from mkPMI.cfg
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    try:
        config.read(os.path.join(outputDir, 'mkAltPMI.cfg'))
        startPID = config.getint('PMI', 'startPID')
        startUR = config.getint('PMI', 'startUR')
        endUR = config.getint('PMI', 'endUR')
        skipUR = config.getint('PMI', 'skipUR')
        minAge = config.getint('AgeRange', 'minAge')
        maxAge = config.getint('AgeRange', 'maxAge')
        aliases = config.getfloat('Profile', 'aliases')
        if (aliases > 100.0) or (aliases < 0.0):
            aliases = 10.0
        merged = config.getfloat('Profile', 'merged')
        if (merged > 100.0) or (merged < 0.0):
            merged = 5.0
        deleted = config.getfloat('Profile', 'deleted')
        if (deleted > 100.0) or (deleted < 0.0):
            deleted = 2.0
        hasAltUR = config.getfloat('Profile', 'hasAltUR')
        deceased = config.getfloat('Profile', 'deceased')
        if (deceased > 100.0) or (deceased < 0.0):
            deceased = 2.0
        if (hasAltUR > 100.0) or (hasAltUR < 0.0):
            hasAltUR = 66.6
        if IHI:
            startIHI = config.getint('IHI', 'startIHI')
            skipIHI = config.getint('IHI', 'skipIHI')
            percentIHI = config.getfloat('IHI', 'percentIHI')
        if errors:
            dupUR = config.getfloat('Errors', 'dupUR')
            if (dupUR > 100.0) or (dupUR < 0.0):
                dupUR = 2.0
            potDup = config.getfloat('Errors', 'potDup')
            if (potDup > 100.0) or (potDup < 0.0):
                potDup = 7.0
            orphanAliases = config.getfloat('Errors', 'orphanAliases')
            if (orphanAliases > 100.0) or (orphanAliases < 0.0):
                orphanAliases = 5.0
            orphanMerges = config.getfloat('Errors', 'orphanMerges')
            if (orphanMerges > 100.0) or (orphanMerges < 0.0):
                orphanMerges = 3.0
            undelAliases = config.getfloat('Errors', 'undeletedAliases')
            if (undelAliases > 100.0) or (undelAliases < 0.0):
                undelAliases = 15.0
            undelMerges = config.getfloat('Errors', 'undeletedMerges')
            if (undelMerges > 100.0) or (undelMerges < 0.0):
                undelMerges = 25.0
            familyNameErrors = config.getfloat('Errors', 'familyNameErrors')
            if (familyNameErrors > 100.0) or (familyNameErrors < 0.0):
                familyNameErrors = 2.0
            givenNameErrors = config.getfloat('Errors', 'givenNameErrors')
            if (givenNameErrors > 100.0) or (givenNameErrors < 0.0):
                givenNameErrors = 2.0
            badAltURerrors = config.getfloat('Errors', 'badAltUR')
            if (badAltURerrors > 100.0) or (badAltURerrors < 0.0):
                badAltURerrors = 10.0
            if IHI:
                badAltIHIerrors = config.getfloat('IHI', 'badAltIHI')
                if (badAltIHIerrors > 100.0) or (badAltIHIerrors < 0.0):
                    badAltIHIerrors = 10.0
            aliasAltURerrors = config.getfloat('Errors', 'aliasAltUR')
            if (aliasAltURerrors > 100.0) or (aliasAltURerrors < 0.0):
                aliasAltURerrors = 2.0
            mergedAltURerrors = config.getfloat('Errors', 'mergedAltUR')
            if (mergedAltURerrors > 100.0) or (mergedAltURerrors < 0.0):
                mergedAltURerrors = 3.0
            deletedAltURerrors = config.getfloat('Errors', 'deletedAltUR')
            if (deletedAltURerrors > 100.0) or (deletedAltURerrors < 0.0):
                deletedAltURerrors = 1.0
    except (configparser.MissingSectionHeaderError, configparser.NoSectionError, configparser.NoOptionError, configparser.ParsingError) as detail:
        logging.fatal('%s', detail)
        sys.exit(EX_CONFIG)

    startPID = int(startPID)
    startUR = int(startUR)
    endUR = int(endUR)
    skipUR = int(skipUR)
    if skipUR < 1:
        skipUR = 1
    if IHI:
        IHIno = int(startIHI)
        skipIHI = int(skipIHI)
        if skipIHI < 1:
            skipIHI = 1
    URno = startUR
    PID = startPID
    patient = 0
    noOfPMIrecords = int(((endUR - startUR)/skipUR)*1.5)

    UsedIDs = {}
    mkRandPatients(dataDir, addressFile, noOfPMIrecords, extendNames, False, makeRandom, minAge, maxAge, False, UsedIDs, False)        # Create enough random patient

    # Now read in the master PMI file
    master = {}
    masterIDX = []
    masterHas = {}
    PMIfields = []
    PMIfields.append('PID')
    hasIHI = False
    masterUR = []
    masterAlias = []
    masterMerged = []
    masterDeleted = []
    minUR = 0
    maxUR = 0
    masterSkippedUR = []
    with open(os.path.join(inputDir, PMIinputfile), 'rt', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, dialect=csv.excel)
        header = True
        for row in csvreader:
            if header:
                for i, col in enumerate(row):
                    if col == 'PID':
                        continue
                    if col == 'IHI':
                        hasIHI = True
                    PMIfields.append(col)
                    if col == 'UR':
                        PMIfields.append('AltUR')
                        if IHI:
                            PMIfields.append('AltIHI')
                    masterHas[col] = i
                if 'UR' not in PMIfields:
                    logging.fatal('master PMI file (%s) does not contain a column named "UR"', PMIinputfile)
                    sys.exit(EX_CONFIG)
                if 'familyName' not in PMIfields:
                    logging.fatal('master PMI file (%s) does not contain a column named "familyName""', PMIinputfile)
                    sys.exit(EX_CONFIG)
                if 'givenName' not in PMIfields:
                    logging.fatal('master PMI file (%s) does not contain a column named "givenName"', PMIinputfile)
                    sys.exit(EX_CONFIG)
                if 'birthdate' not in PMIfields:
                    logging.fatal('master PMI file (%s) does not contain a column named "birthdate"', PMIinputfile)
                    sys.exit(EX_CONFIG)
                if 'sex' not in PMIfields:
                    logging.fatal('master PMI file (%s) does not contain a column named "sex"', PMIinputfile)
                    sys.exit(EX_CONFIG)
                if IHI and not hasIHI:
                    logging.fatal('master PMI file (%s) does not contain a column named "IHI"', PMIinputfile)
                    sys.exit(EX_CONFIG)
                header = False
                continue
            if 'Alias' in PMIfields:
                if row[masterHas['Alias']] != '':
                    masterAlias.append(row[masterHas['UR']])
            if 'Merged' in PMIfields:
                if row[masterHas['Merged']] != '':
                    masterMerged.append(row[masterHas['UR']])
            if 'Deleted' in PMIfields:
                if row[masterHas['Deleted']] == 'D':
                    masterDeleted.append(row[masterHas['UR']])
            masterMe = row[masterHas['givenName']] + '~' + row[masterHas['familyName']]
            master[masterMe] = {}
            masterIDX.append(masterMe)
            for col, i in masterHas.items():
                master[masterMe][col] = row[i]
                try:
                    thisUR = int(row[masterHas['UR']])
                    if (minUR == 0) or (minUR > int(row[masterHas['UR']])):
                        minUR = int(row[masterHas['UR']])
                    if (maxUR == 0) or (maxUR < int(row[masterHas['UR']])):
                        maxUR = int(row[masterHas['UR']])
                except Exception as e:
                    thisUR = None

        if errors:
            for ur in range(minUR, maxUR):
                if len(masterSkippedUR) > (endUR - startUR)*2*badAltURerrors/100.0:
                    break
                if (ur not in masterUR) and (ur not in masterAlias) and (ur not in masterMerged) and (ur not in masterDeleted):
                    masterSkippedUR.append(ur)

    # Now create the secondary PMI
    with open(os.path.join(outputDir, PMIoutputfile), 'wt', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile, dialect=csv.excel)
        csvwriter.writerow(PMIfields)
        info = [''] + PMIfields
        logging.info(csvString(info))
        masterMe = []            # not alias/not merged/not deleted patients
        masterDelMe = []        # deleted, but not alias/not merged patients
        skippedUR = []
        rCount = 0
        aCount = 0
        mCount = 0
        dCount = 0
        dAcount = 0
        dMcount = 0
        dBcount = 0
        bCount = 0
        dupCount = 0
        actCount = 0
        potDupCount = 0
        actDupCount = 0
        orphMcount = 0
        orphAcount = 0
        undelMcount = 0
        undelAcount = 0
        FEcount = 0
        SEcount = 0
        badAltCount = 0
        aliasAltCount = 0
        mergedAltCount = 0
        deletedAltCount = 0
        linkedCount = 0
        clones = []
        while URno < endUR:
            me = patientKeys[patient]
            patients[me]['PID'] = PID        # Create a new patient records
            patients[me]['UR'] = URno
            patients[me]['Alias'] = ''
            patients[me]['Merged'] = ''
            patients[me]['Deleted'] = ''
            patients[me]['AltUR'] = ''
            if IHI:
                if random.random()*100 < percentIHI:                    # Check alt IHI required
                    patients[me]['IHI'] = f"{800360990000000 + IHIno:d}{mkLuhn(f'{800360990000000 + IHIno:d}'):d}"
                    if skipIHI == 0:
                        IHIno += 1
                    elif skipIHI < 3:
                        IHIno += skipIHI
                    else:
                        IHIno += random.randrange(skipIHI - 1, skipIHI + 1)
                    IHIno %= 10000000
                else:
                    patients[me]['IHI'] = None
                patients[me]['AltIHI'] = patients[me]['IHI']
            if random.random()*100 < deceased:                    # Check if time for a deceased person
                (year, month, day) = patients[me]['birthdate'].split('-')
                year = int(year)
                month = int(month)
                day = int(day)
                birthdate = datetime.date(year, month, day)
                today = datetime.date.today()
                age = today - birthdate
                deathDay = int(random.random()*age.days)
                deathDate = birthdate + datetime.timedelta(deathDay)
                patients[me]['deathDate'] = deathDate.isoformat()
            else:
                patients[me]['deathDate'] = ''
            infoText = ''
            linkInfo = ''
            cloneInfo = ''
            dupMe = None
            linkMe = None
            rCount += 1
            if patient < 10:            # Make sure we have a small pool of not alias/not merged/not deleted records
                masterMe.append(me)            # Keep track of not alias/not merged/not deleted patients
                masterDelMe.append(me)            # Keep track of deleted, but not alias/not merged patients
            elif random.random()*100 < hasAltUR:                    # Check if time for a linked record
                linkMe =  random.choice(masterIDX)
                del masterIDX[masterIDX.index(linkMe)]
                linkInfo = masterClone(me, linkMe)
                patients[me]['AltUR'] = master[linkMe]['UR']
                linkedCount += 1
                if errors:
                    if IHI:
                        if patients[me]['IHI'] and (random.random()*100 < badAltIHIerrors):        # Check bad alt IHI required
                            if infoText == '':
                                infoText = 'IHI'
                            else:
                                infoText += ',IHI'
                            altIHI = f"{patients[me]['IHI'][0:7]}{random.randrange(1000000000):d}"
                            patients[me]['AltIHI'] = f'{altIHI}{mkLuhn(altIHI):d}'
                        else:
                            patients[me]['AltIHI'] = patients[me]['IHI']
                    if random.random()*100 < badAltURerrors:                # Check if time for a bad AltUR record
                        if infoText == '':
                            infoText = 'AltUR'
                        else:
                            infoText += ',AltUR'
                        if len(masterSkippedUR) > 0:
                            patients[me]['AltUR'] = random.choice(masterSkippedUR)
                            del masterSkippedUR[masterSkippedUR.index(patients[me]['AltUR'])]
                        else:
                            patients[me]['AltUR'] = f"{patients[me]['AltUR']}X"
                        badAltCount += 1
                    elif random.random()*100 < aliasAltURerrors:                # Check if time for an AltUR of an alias record
                        if len(masterAlias) > 0:
                            if infoText == '':
                                infoText = 'aliasAltUR'
                            else:
                                infoText += ',aliasAltUR'
                            patients[me]['AltUR'] = random.choice(masterAlias)
                        else:
                            if infoText == '':
                                infoText = 'AltUR'
                            else:
                                infoText += ',AltUR'
                            patients[me]['AltUR'] = f"{patients[me]['AltUR']}X"
                        aliasAltCount += 1
                    elif random.random()*100 < mergedAltURerrors:                # Check if time for an AltUR of a merged record
                        if len(masterMerged) > 0:
                            if infoText == '':
                                infoText = 'mergedAltUR'
                            else:
                                infoText += ',mergedAltUR'
                            patients[me]['AltUR'] = random.choice(masterMerged)
                        else:
                            if infoText == '':
                                infoText = 'AltUR'
                            else:
                                infoText += ',AltUR'
                            patients[me]['AltUR'] = f"{patients[me]['AltUR']}X"
                        mergedAltCount += 1
                    elif random.random()*100 < deletedAltURerrors:                # Check if time for an AltUR of a deleted record
                        if len(masterDeleted) > 0:
                            if infoText == '':
                                infoText = 'DelAltUR'
                            else:
                                infoText += ',DelAltUR'
                            patients[me]['AltUR'] = random.choice(masterDeleted)
                        else:
                            if infoText == '':
                                infoText = 'AltUR'
                            else:
                                infoText += ',AltUR'
                            patients[me]['AltUR'] = f"{patients[me]['AltUR']}X"
                        deletedAltCount += 1
            else:
                isAlias  = False
                isMerge  = False
                if random.random()*100 < aliases:                    # Check if time for an alias record
                    if alias2alias:
                        dupMe =  patientKeys[random.randrange(0, patient)]
                    else:
                        dupMe =  random.choice(masterDelMe)
                    patients[me]['Alias'] = patients[dupMe]['UR']
                    isAlias = True
                    aCount += 1

                    # Duplicate some patient data
                    cloneInfo = clone(me, dupMe)
                    if errors and IHI:
                        if patients[me]['IHI'] and (random.random()*100 < badAltIHIerrors):        # Check bad alt IHI required
                            if infoText == '':
                                infoText = 'AltIHI'
                            else:
                                infoText += ',AltIHI'
                            altIHI = f"{patients[me]['IHI'][0:7]}{random.randrange(1000000000):d}"
                            patients[me]['AltIHI'] = f'{altIHI}{mkLuhn(altIHI):d}'
                        else:
                            patients[me]['AltIHI'] = patients[me]['IHI']

                    # Then change a name (family name for females, givenName for everything else)
                    if patients[me]['sex'] == 'F':
                        if infoText == '':
                            infoText = 'fn'
                        else:
                            infoText += ',fn'
                        patients[me]['givenName'] = patients[dupMe]['givenName']
                        familyName = selectFamilyName()
                        if patients[me]['married'] == 'M':                # Two options if married
                            prevName = re.search(r' \(| \[', patients[me]['familyName'])
                            if prevName:
                                patients[me]['familyName'] = patients[me]['familyName'][0:prevName.start()]        # remove previous name
                            if random.random() < 0.5:
                                patients[me]['familyName'] = f"{patients[me]['familyName']} ({familyName})"    # add previous name
                            else:
                                patients[me]['familyName'] = f"{patients[me]['familyName']} (nee{familyName})"    # add previous name
                        else:
                            hyphen = re.search('-', patients[me]['familyName'])
                            if hyphen:
                                patients[me]['familyName'] = patients[me]['familyName'][0:hyphen.start()]        # de-hyphenate
                            patients[me]['familyName'] += '-' + familyName                    # hyphenate
                    else:
                        if infoText == '':
                            infoText = 'gn'
                        else:
                            infoText += ',gn'
                        patients[me]['familyName'] = patients[dupMe]['familyName']
                        givenName = selectBoysname()
                        patients[me]['givenName'] = givenName            # simple substitution
                    if patients[dupMe]['Deleted'] == 'D':
                        if errors and (random.random()*100 < undelAliases):        # Check if time for an undeleted alias of a deleted record
                            undelAcount += 1
                        else:
                            patients[me]['Deleted'] = 'D'
                    elif errors and (random.random()*100 < orphanAliases):            # Check if time for an orphaned alias record
                        if infoText == '':
                            infoText = 'UR'
                        else:
                            infoText += ',UR'
                        if len(skippedUR) > 0:
                            patients[me]['UR'] =  random.choice(skippedUR)
                            del skippedUR[skippedUR.index(patients[me]['UR'])]
                        else:
                            patients[me]['UR'] = f"{patients[me]['UR']}X"
                        orphAcount += 1
                if ((dupMe is None) or both) and (random.random()*100 < merged):    # Check if time for a merged record
                    if dupMe is None:
                        if merge2merge:
                            dupMe =  patientKeys[random.randrange(0, patient)]
                        else:
                            dupMe =  random.choice(masterDelMe)
                    patients[me]['Merged'] = patients[dupMe]['UR']
                    mCount += 1
                    isMerge = True
                    if isAlias:
                        bCount += 1

                    # Duplicate some patient data
                    cloneInfo += '/' + clone(me, dupMe)
                    if errors and IHI:
                        if infoText == '':
                            infoText = 'AltIHI'
                        else:
                            infoText += ',AltIHI'
                        if patients[me]['IHI'] and (random.random()*100 < badAltIHIerrors):        # Check bad alt IHI required
                            altIHI = f"{patients[me]['IHI'][0:7]}{random.randrange(1000000000):d}"
                            patients[me]['AltIHI'] = f'{altIHI}{mkLuhn(altIHI):d}'
                        else:
                            patients[me]['AltIHI'] = patients[me]['IHI']

                    if patients[dupMe]['Deleted'] == 'D':
                        if errors and (random.random()*100 < undelMerges):    # Check if time for an undeleted merge of a deleted record
                            undelMcount += 1
                        else:
                            patients[me]['Deleted'] = 'D'
                    elif errors and (random.random()*100 < orphanMerges):        # Check if time for an orphaned merged record
                        if infoText == '':
                            infoText = 'UR'
                        else:
                            infoText += ',IHI'
                        if len(skippedUR) > 0:
                            patients[me]['UR'] = random.choice(skippedUR)
                            del skippedUR[skippedUR.index(patients[me]['UR'])]
                        else:
                            patients[me]['UR'] = f"{patients[me]['UR']}X"
                        orphMcount += 1
                isDel = False
                if random.random()*100 < deleted:                    # Check if time for a deleted record
                    patients[me]['Deleted'] = 'D'
                    isDel = True
                    dCount += 1
                    if isAlias:
                        if isAlias and isMerge:
                            dBcount += 1
                        else:
                            dAcount += 1
                    elif isMerge:
                        dMcount += 1
                    else:
                        masterDelMe.append(me)        # Keep track of deleted, but not alias/not merged patients
                elif errors and (dupMe is None):
                    if random.random()*100 < dupUR:            # Check if time for a duplicate UR record
                        dupMe =  random.choice(masterMe)
                        patients[me]['UR'] = patients[dupMe]['UR']
                        dupCount += 1
                        skippedUR.append(URno)
                    elif random.random()*100 < potDup:
                        dupMe =  masterMe[random.randrange(0, len(masterMe))]
                        actDup = False

                        # Duplicate some patient data
                        cloneInfo = clone(me, dupMe)

                        if random.random() < 0.3:            # Sometimes the marital status is wrong
                            if infoText == '':
                                infoText = 'married'
                            else:
                                infoText += ',married'
                            if patients[me]['married'] == 'M':
                                patients[me]['married'] = 'S'
                            else:
                                patients[me]['married'] = 'M'
                        if patients[me]['birthdate'] != patients[dupMe]['birthdate']:
                            if infoText == '':
                                infoText = 'bd'
                            else:
                                infoText += ',bd'
                        elif random.random() < 0.25:            # Sometimes the givenName is wrong
                            if infoText == '':
                                infoText = 'gn'
                            else:
                                infoText += ',gn'
                            givenName = patients[me]['givenName']
                            if patients[me]['sex'] == 'F':
                                patients[me]['givenName'] = selectGirlsname()
                            else:
                                patients[me]['givenName'] = selectBoysname()
                            if givenName == patients[me]['givenName']:
                                actDup = True
                        elif random.random() < 0.333:            # Sometimes the family name is wrong
                            if infoText == '':
                                infoText = 'fn'
                            else:
                                infoText += ',fn'
                            familyName = patients[me]['familyName']
                            patients[me]['familyName'] = selectFamilyName()
                            if familyName == patients[me]['familyName']:
                                actDup = True
                        elif random.random() < 0.5:            # Sometimes the sex is wrong
                            if infoText == '':
                                infoText = 'sex'
                            else:
                                infoText += ',sex'
                            if patients[me]['sex'] == 'M':
                                patients[me]['sex'] = 'F'
                            else:
                                patients[me]['sex'] = 'M'
                        else:
                            actDup = True
                        thisKey = patients[me]['familyName'] + '~' + patients[me]['givenName'] + '~'
                        thisKey += patients[me]['sex'] + '~' + patients[me]['birthdate']
                        if thisKey in clones:
                            actDupCount += 1
                        else:
                            clones.append(thisKey)
                            if actDup:
                                actDupCount += 1
                            else:
                                potDupCount += 1
                    else:
                        masterMe.append(me)                    # Keep track of not alias/not merged/not deleted patients
                if errors and (dupMe is None) and (not isDel):
                    if random.random()*100 < familyNameErrors:        # Check if time for a family name error
                        if infoText == '':
                            infoText = 'fn error'
                        else:
                            infoText += ',fn error'
                        SEcount += 1
                        prevName = re.search(r' \(| \[', patients[me]['familyName'])
                        if prevName:
                            patients[me]['familyName'] = patients[me]['familyName'][0:prevName.start()]        # remove previous name
                        if (patients[me]['sex'] == 'F') and (patients[me]['married'] == 'M'):
                            familyName = selectFamilyName()
                            if random.random() < 0.3:
                                patients[me]['familyName'] = f"{patients[me]['familyName']} ({familyName})"    # previous name in round brackets
                            elif random.random() < 0.6:
                                patients[me]['familyName'] = f"{patients[me]['familyName']} [{familyName}]"    # previous name in square brackets
                            else:
                                patients[me]['familyName'] = f"{patients[me]['familyName']} (nee {familyName})"    # previous name as (nee ...)
                        else:
                            suffix = re.search(' ', patients[me]['familyName'])
                            if (not suffix) and (random.random() < 0.2):
                                patients[me]['familyName'] += ' III'
                            elif (not suffix) and (random.random() < 0.5):
                                patients[me]['familyName'] += ' JNR'
                            elif random.random() < 0.95:
                                if suffix:
                                    patients[me]['familyName'] = patients[me]['familyName'][0:suffix.start()]        # remove suffix name
                                patients[me]['familyName'] += '-' + selectFamilyName()
                            else:
                                if suffix:
                                    patients[me]['familyName'] = patients[me]['familyName'][0:suffix.start()]        # remove suffix name
                                patients[me]['familyName'] += '^' + selectFamilyName()
                    if random.random()*100 < givenNameErrors:        # Check if time for a givenName error
                        if infoText == '':
                            infoText = 'gn error'
                        else:
                            infoText += ',gn error'
                        FEcount += 1
                        prevNickname = re.search(r' \(| \*', patients[me]['familyName'])
                        if (not prevNickname) and (patients[me]['givenName'] in nicknames):
                            print(me, patients[me]['givenName'])
                            nickname = random.choice(nicknames[patients[me]['givenName']])
                            if random.random() < 0.5:
                                patients[me]['givenName'] += ' *' + nickname
                            else:
                                patients[me]['givenName'] += ' (' + nickname + ')'
                        else:
                            (year, month, day) = patients[me]['birthdate'].split('-')
                            year = int(year)
                            month = int(month)
                            day = int(day)
                            birthdate = datetime.date(year, month, day)
                            today = datetime.date.today()
                            age = today - birthdate
                            if age < datetime.timedelta(days=60):        # a baby
                                patients[me]['givenName'] = 'TWIN 1'
                            else:
                                if prevNickname:         # Remove previous nickname
                                    patients[me]['givenName'] = patients[me]['givenName'][0:prevNickname.start()]
                                hyphen = re.search('-', patients[me]['givenName'])
                                if hyphen:
                                    patients[me]['givenName'] = patients[me]['givenName'][0:hyphen.start()]
                                if patients[me]['sex'] == 'M':
                                    patients[me]['givenName'] += ' (' + selectBoysname() + ')'
                                else:
                                    patients[me]['givenName'] += ' (' + selectGirlsname() + ')'
            PMI = []
            for field in (PMIfields):
                PMI.append(patients[me][field])
            csvwriter.writerow(PMI)
            if infoText != '':
                if linkMe is not None:
                    if linkInfo != '':
                        linkPMI = [f'linked ({cloneInfo})']
                    else:
                        linkPMI = ['linked']
                    for field in (PMIfields):
                        if field in masterHas:
                            linkPMI.append(master[linkMe][field])
                        else:
                            linkPMI.append('')
                    logging.info(csvString(linkPMI))
                if dupMe is not None:
                    if cloneInfo != '':
                        dupPMI = [f'cloned ({cloneInfo})']
                    else:
                        dupPMI = ['cloned']
                    for field in (PMIfields):
                        dupPMI.append(patients[dupMe][field])
                    logging.info(csvString(dupPMI))
                info = [infoText] + PMI
                logging.info(csvString(info))
            patient += 1
            PID += 1
            if skipUR == 0:
                URno += 1
            elif skipUR < 3:
                URno += skipUR
            else:
                nextUR = URno + random.randrange(skipUR - 1, skipUR + 1)
                while URno < nextUR:
                    skippedUR.append(URno)
                    URno += 1

    # Report the results
    print(f'{rCount}\tPMI Records created')
    print(f'{aCount}\t\talias records')
    print(f'{mCount}\t\tmerged records')
    if both:
        print(f'\t\tof which {bCount} were both aliases and merged records')
    print(f'{dCount}\t\tdeleted records')
    print(f'\t\tof which {dAcount} were aliases records')
    print(f'\t\tand {dMcount} were merged records')
    print(f'{linkedCount}\t\trecords linked to the master PMI')
    print(f'\t\tof which {aliasAltCount} were linked to aliases records')
    print(f'\t\tand {mergedAltCount} were linked to merged records')
    print(f'\t\tand {deletedAltCount} were linked to deleted records')
    if both:
        print('f\t\t\tof which {dBcount} were both aliases and merged records')
    if errors:
        print()
        print('Introduced errors')
        print(f'{dupCount}\trecords given a duplicate UR')
        print(f'{actDupCount}\trecords are duplicates records (different UR)')
        print(f'{potDupCount}\t(at least) records are potential duplicates (different UR)')
        print(f'{orphAcount}\torphaned alias records')
        print(f'{orphMcount}\torphaned merged records')
        print(f'{undelAcount}\tundeleted alias of deleted records')
        print(f'{undelMcount}\tundeleted merges of deleted records')
        print()
        print(f'{FEcount}\tNon-standard given names')
        print(f'{SEcount}\tNon-standard family names')
