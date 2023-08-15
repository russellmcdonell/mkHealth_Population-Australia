#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement

'''
A script to create a CSV file of randomly created patient records

SYNOPSIS
$ python mkPMI.py [-D dataDir|--dataDir=dataDir] [-A addressFile|--addressFile=addressFile]
                  [-O outputDir|--outputDir=outputDir] [-M PMIoutputfile|--PMIfile=PMIoutputfile]
                  [-r|--makeRandom] [-b|-both] [-a|alias2alias] [-m|-merge2merge] [-i|--IHI] [-x|--extendNames] [-e|--errors]
                  [-v loggingLevel|--loggingLevel=loggingLevel]
                  [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

OPTIONS
-D dataDir|--dataDir=dataDir
The directory containing the source names and address data (default='data')

-A addressFile|--addressFile=addressFile
The file of GNAF_CORE addresses (or subset) (default='GNAF_CORE.psv')

-O outputDir|--outputDir=outputDir
The directory in which the output file will be created (default='output')

-M PMIoutputfile|--PMIfile=PMIoutputfile
The PMI output file to be created (default='master.csv')

-r|--makeRandom
Make random Australian addresses

-b|--both
PMI records can be both Alias records and Merged records

-a|--alias2alias
PMI records can be Aliases of Alias records

-m|--merge2merge
PMI records can be Merges to already Merged records

-i|--IHI
Add Australian IHI number

-x|--extendNames
Extend names with sequential letters

-e|--errors
Create errors, such as duplicate UR records, merged and aliases that point to non-existent records or point to deleted records.

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


def clone(thisMe, other) :
    '''
    Clone other onto thisMe
    '''
# namely: familyName,givenName,birthdate,sex,streetNo,streetName,streetType,suburb,state,postcode,longitude,latitude,country,mobile,homePhone,businessPhone,email,medicareNo,IHI,dvaNo,dvaType,height,weight,waist,hips,married,race,deathDate

    thisCloneInfo = ''
    patients[thisMe]['familyName'] = patients[other]['familyName']
    patients[thisMe]['givenName'] = patients[other]['givenName']
    if random.random() < 0.2 :                # Sometimes the birthdate is wrong
        (thisYear, thisMonth, thisDay) = patients[other]['birthdate'].split('-')
        thisYear = int(thisYear)
        thisMonth = int(thisMonth)
        thisDay = int(thisDay)
        thisBirthdate = datetime.date(thisYear, thisMonth, thisDay)
        if random.random() < 0.4 :                # Sometimes the thisYear is wrong
            thisBirthdate += datetime.timedelta(thisDays=365)*(int(random.random()*5.0) - 2)
        if random.random() < 0.3 :                # Sometimes the thisMonth is wrong
            thisBirthdate += datetime.timedelta(thisDays=31)*(int(random.random()*5.0) - 2)
        if random.random() < 0.3 :                # Sometimes the thisDay is wrong
            thisBirthdate += datetime.timedelta(thisDays=1)*(int(random.random()*5.0) - 2)
        if thisBirthdate < datetime.date.tothisDay() :
            patients[thisMe]['birthdate'] = thisBirthdate.isoformat()
    else :
        thisCloneInfo = 'bd'
        patients[thisMe]['birthdate'] = patients[other]['birthdate']
    patients[thisMe]['sex'] = patients[other]['sex']
    if thisCloneInfo == '' :
        thisCloneInfo = 'sex'
    else :
        thisCloneInfo += ',sex'
    if random.random() < 0.8 :                # Often the address is correct
        if thisCloneInfo == '' :
            thisCloneInfo = 'addr'
        else :
            thisCloneInfo += ',addr'
        patients[thisMe]['streetNo'] = patients[other]['streetNo']
        patients[thisMe]['streetName'] = patients[other]['streetName']
        patients[thisMe]['streetType'] = patients[other]['streetType']
        patients[thisMe]['shortStreetType'] = patients[other]['shortStreetType']
        patients[thisMe]['suburb'] = patients[other]['suburb']
        patients[thisMe]['state'] = patients[other]['state']
        patients[thisMe]['postcode'] = patients[other]['postcode']
        patients[thisMe]['longitude'] = patients[other]['longitude']
        patients[thisMe]['latitude'] = patients[other]['latitude']
        patients[thisMe]['country'] = patients[other]['country']
    if random.random() < 0.2 :                # Sometimes the phone numbers are wrong
        if thisCloneInfo == '' :
            thisCloneInfo = 'ph'
        else :
            thisCloneInfo += ',ph'
        patients[thisMe]['mobile'] = patients[other]['mobile']
        patients[thisMe]['homePhone'] = patients[other]['homePhone']
        patients[thisMe]['businessPhone'] = patients[other]['businessPhone']
        patients[thisMe]['email'] = patients[other]['email']
    patients[thisMe]['mobile'] = patients[other]['mobile']
    patients[thisMe]['homePhone'] = patients[other]['homePhone']
    patients[thisMe]['businessPhone'] = patients[other]['businessPhone']
    patients[thisMe]['email'] = patients[other]['email']
    if IHI :
        if thisCloneInfo == '' :
            thisCloneInfo = 'IHI'
        else :
            thisCloneInfo += ',IHI'
        patients[thisMe]['IHI'] = patients[other]['IHI']
    patients[thisMe]['medicareNo'] = patients[other]['medicareNo']
    patients[thisMe]['dvaNo'] = patients[other]['dvaNo']
    patients[thisMe]['dvaType'] = patients[other]['dvaType']
    height = float(patients[other]['height'])
    patients[thisMe]['height'] = f'{random.normalvariate(height, height/50.0):.0f}'
    oldWeight = float(patients[other]['weight'])
    weight = random.normalvariate(oldWeight, oldWeight/20.0)
    patients[thisMe]['weight'] = f'{weight:.1f}'
    waist = height * 0.49                    # a ratio for all ages, both genders for normal, health persons
    waist = waist * (weight/oldWeight)    # scaled by the percentage weight percentage
    if patients[thisMe]['sex'] == 'M' :
        hips = waist / random.normalvariate(0.90, 0.10)
    else :
        hips = waist / random.normalvariate(0.75, 0.10)
    patients[thisMe]['hips'] = hips
    patients[thisMe]['race'] = patients[other]['race']
    patients[thisMe]['married'] = patients[other]['married']
    patients[thisMe]['deathDate'] = patients[other]['deathDate']
    return 'name,' + thisCloneInfo


def csvString(thisRow) :
    '''
    Convert this row to a CSV compliant string
    '''

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(thisRow)
    return si.getvalue().rstrip('\r\n')



if __name__ == '__main__' :
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
                        help='The name of the output directory [mkPMI.cfg will be read from this directory] (default="output")')
    parser.add_argument('-M', '--PMIoutputfile', dest='PMIoutputfile', default='master.csv',
                        help='The name of the PMI csv file to be created(default="master.csv")')
    parser.add_argument('-r', '--makeRandom', dest='makeRandom', action='store_true', help='Make random Australian addresses')
    parser.add_argument('-b', '--both', dest='both', action='store_true', help='PMI records can be both merged and an alias')
    parser.add_argument('-a', '--alias2alias', dest='alias2alias', action='store_true', help='Allow aliases to aliased or merged patient')
    parser.add_argument('-m', '--merg2merge', dest='merge2merge', action='store_true', help='Allow merges to aliased or merged patient')
    parser.add_argument('-i', '--IHI', dest='IHI', action='store_true', help='Add Australian IHI number')
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
    if args.loggingLevel :    # Change the logging level from "WARN" if the -v vebose option is specified
        loggingLevel = args.loggingLevel
        if args.logfile :        # and send it to a file if the -o logfile option is specified
            # Check that the logDir exists
            if not os.path.isdir(args.logDir):
                logging.critical('Usage error - logDir (%s) does not exits', args.logDir)
                logging.shutdown()
                sys.exit(EX_USAGE)
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else :
        if args.logfile :        # send the default (WARN) logging to a file if the -o logfile option is specified
            # Check that the logDir exists
            if not os.path.isdir(args.logDir):
                logging.critical('Usage error - logDir (%s) does not exits', args.logDir)
                logging.shutdown()
                sys.exit(EX_USAGE)
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p',
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else :
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')

    dataDir = args.dataDir
    addressFile = args.addressFile
    outputDir = args.outputDir
    PMIoutputfile = args.PMIoutputfile
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
    # Check that the outputDir exists
    if not os.path.isdir(outputDir):
        logging.critical('Usage error - outputDir (%s) does not exits', outputDir)
        logging.shutdown()
        sys.exit(EX_USAGE)

    # Then read in the configuration from mkPMI.cfg
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    try :
        config.read(os.path.join(outputDir, 'mkPMI.cfg'))
        startPID = config.getint('PMI', 'startPID')
        startUR = config.getint('PMI', 'startUR')
        endUR = config.getint('PMI', 'endUR')
        skipUR = config.getint('PMI', 'skipUR')
        if IHI :
            startIHI = config.getint('IHI', 'startIHI') % 10000000
            skipIHI = config.getint('IHI', 'skipIHI')
            percentIHI = config.getfloat('IHI', 'percentIHI')
            if (percentIHI > 100.0) or (percentIHI < 0.0) :
                percentIHI = 10.0
        fields = config.get('Fields', 'PMIfields')
        dialect = csv.Sniffer().sniff(fields)
        dialect.skipinitialspace = True
        for row in csv.reader([fields], dialect) :
            fields = row
            break
        minAge = config.getint('AgeRange', 'minAge')
        maxAge = config.getint('AgeRange', 'maxAge')
        aliases = config.getfloat('Profile', 'aliases')
        if (aliases > 100.0) or (aliases < 0.0) :
            aliases = 10.0
        merged = config.getfloat('Profile', 'merged')
        if (merged > 100.0) or (merged < 0.0) :
            merged = 5.0
        deleted = config.getfloat('Profile', 'deleted')
        if (deleted > 100.0) or (deleted < 0.0) :
            deleted = 2.0
        deceased = config.getfloat('Profile', 'deceased')
        if (deceased > 100.0) or (deceased < 0.0) :
            deceased = 2.0
        if errors :
            dupUR = config.getfloat('Errors', 'dupUR')
            if (dupUR > 100.0) or (dupUR < 0.0) :
                dupUR = 2.0
            potDup = config.getfloat('Errors', 'potDup')
            if (potDup > 100.0) or (potDup < 0.0) :
                potDup = 7.0
            orphanAliases = config.getfloat('Errors', 'orphanAliases')
            if (orphanAliases > 100.0) or (orphanAliases < 0.0) :
                orphanAliases = 5.0
            orphanMerges = config.getfloat('Errors', 'orphanMerges')
            if (orphanMerges > 100.0) or (orphanMerges < 0.0) :
                orphanMerges = 3.0
            undelAliases = config.getfloat('Errors', 'undeletedAliases')
            if (undelAliases > 100.0) or (undelAliases < 0.0) :
                undelAliases = 15.0
            undelMerges = config.getfloat('Errors', 'undeletedMerges')
            if (undelMerges > 100.0) or (undelMerges < 0.0) :
                undelMerges = 25.0
            familyNameErrors = config.getfloat('Errors', 'familyNameErrors')
            if (familyNameErrors > 100.0) or (familyNameErrors < 0.0) :
                familyNameErrors = 2.0
            givenNameErrors = config.getfloat('Errors', 'givenNameErrors')
            if (givenNameErrors > 100.0) or (givenNameErrors < 0.0) :
                givenNameErrors = 2.0
    except (configparser.MissingSectionHeaderError, configparser.NoSectionError, configparser.NoOptionError, configparser.ParsingError) as detail :
        logging.fatal('%s', detail)
        logging.shutdown()
        sys.exit(EX_CONFIG)

    startPID = int(startPID)
    startUR = int(startUR)
    endUR = int(endUR)
    skipUR = int(skipUR)
    if skipUR < 1 :
        skipUR = 1
    if IHI :
        IHIno = int(startIHI)
        skipIHI = int(skipIHI)
        if skipIHI < 1 :
            skipIHI = 1
    URno = startUR
    PID = startPID
    patient = 0
    noOfPMIrecords = int(((endUR - startUR)/skipUR)*1.5)

    UsedIDs = {}
    mkRandPatients(dataDir, addressFile, noOfPMIrecords, extendNames, False, makeRandom, minAge, maxAge, UsedIDs, False)        # Create enough random patient

    # Create the PMI
    with open(os.path.join(outputDir, PMIoutputfile), 'wt', newline='', encoding='utf-8') as csvfile :
        csvwriter = csv.writer(csvfile, dialect=csv.excel)
        PMIfields = ['PID', 'UR', 'Alias', 'Merged', 'Deleted']
        if IHI :
            PMIfields.append('IHI')
        PMIfields += fields
        csvwriter.writerow(PMIfields)
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
        potDupCount = 0
        actDupCount = 0
        orphMcount = 0
        orphAcount = 0
        undelMcount = 0
        undelAcount = 0
        GNEcount = 0
        FNEcount = 0
        clones = []
        while URno < endUR :
            me = patientKeys[patient]
            patients[me]['PID'] = PID        # Create a new patient records
            patients[me]['UR'] = URno
            patients[me]['Alias'] = None
            patients[me]['Merged'] = None
            patients[me]['Deleted'] = None
            if IHI :
                if random.random()*100 < percentIHI :                    # Check IHI required
                    patients[me]['IHI'] = f'{800360990000000 + IHIno:d}{mkLuhn(str(800360990000000 + IHIno)):d}'
                    if skipIHI == 0 :
                        IHIno += 1
                    elif skipIHI < 3 :
                        IHIno += skipIHI
                    else :
                        IHIno += random.randrange(skipIHI - 1, skipIHI + 1)
                    IHIno %= 10000000
                else :
                    patients[me]['IHI'] = None
            if random.random()*100 < deceased :                    # Check if time for a deceased person
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
            else :
                patients[me]['deathDate'] = None

            infoText = ''
            cloneInfo = ''
            rCount += 1
            if patient < 10 :            # Make sure we have a small pool of not alias/not merged/not deleted records
                masterMe.append(me)            # Keep track of not alias/not merged/not deleted patients
                masterDelMe.append(me)            # Keep track of not alias/not merged, but may be deleted, patients
            else :
                dupMe = None
                isAlias  = False
                isMerge  = False
                if random.random()*100 < aliases :                    # Check if time for an alias record
                    if alias2alias :
                        dupMe =  patientKeys[random.randrange(0, patient)]
                    else :
                        dupMe =  random.choice(masterDelMe)
                    patients[me]['Alias'] = patients[dupMe]['UR']
                    infoText = 'to Alias'
                    isAlias = True
                    aCount += 1

                    # Duplicate some patient data
                    cloneInfo = clone(me, dupMe)

                    # Then change a name (family name for females, given name for everything else)
                    if patients[me]['sex'] == 'F' :
                        familyName = selectFamilyName()
                        infoText += ' fn'
                        if patients[me]['married'] == 'M' :                # Two options if married
                            prevName = re.search(r' \(| \[', patients[me]['familyName'])
                            if prevName :
                                patients[me]['familyName'] = patients[me]['familyName'][0:prevName.start()]        # remove previous name
                            if random.random() < 0.5 :
                                patients[me]['familyName'] = f"{patients[me]['familyName']} ({familyName})"    # add previous name
                            else :
                                patients[me]['familyName'] = f"{patients[me]['familyName']} (nee {familyName})"    # add previous name
                        else :
                            hyphen = re.search('-', patients[me]['familyName'])
                            if hyphen :
                                patients[me]['familyName'] = patients[me]['familyName'][0:hyphen.start()]        # de-hyphenate
                            patients[me]['familyName'] += '-' + familyName                    # hyphenate
                    else :
                        infoText += ' gn'
                        givenName = selectBoysname()
                        patients[me]['givenName'] = givenName            # simple substitution
                    if patients[dupMe]['Deleted'] == 'D' :
                        if errors and (random.random()*100 < undelAliases) :        # Check if time for an undeleted alias of a deleted record
                            infoText += ',of Del'
                            undelAcount += 1
                        else :
                            patients[me]['Deleted'] = 'D'
                    elif errors and (random.random()*100 < orphanAliases) :            # Check if time for an orphaned alias record
                        infoText += ',badUR'
                        if len(skippedUR) > 0 :
                            patients[me]['UR'] = random.choice(skippedUR)
                            del skippedUR[skippedUR.index(patients[me]['UR'])]
                        else :
                            patients[me]['UR'] += 'X'
                        orphAcount += 1
                if ((dupMe is None) or both) and (random.random()*100 < merged) :    # Check if time for a merged record
                    if dupMe is None :
                        if merge2merge :
                            dupMe =  patientKeys[random.randrange(0, patient)]
                        else :
                            dupMe =  random.choice(masterDelMe)
                        # Duplicate some patient data
                        cloneInfo = clone(me, dupMe)

                    patients[me]['Merged'] = patients[dupMe]['UR']
                    if infoText == '' :
                        infoText = 'to Merged'
                    else :
                        infoText += ',to Merged'
                    mCount += 1
                    isMerge = True
                    if isAlias :
                        bCount += 1

                    if patients[dupMe]['Deleted'] == 'D' :
                        if errors and (random.random()*100 < undelMerges) :    # Check if time for an undeleted merge of a deleted record
                            infoText += ',of Del'
                            undelMcount += 1
                        else :
                            patients[me]['Deleted'] = 'D'
                    elif errors and (random.random()*100 < orphanMerges) :        # Check if time for an orphaned merged record
                        infoText += ',badUR'
                        if len(skippedUR) > 0 :
                            patients[me]['UR'] =  random.choice(skippedUR)
                            del skippedUR[skippedUR.index(patients[me]['UR'])]
                        else :
                            patients[me]['UR'] += 'X'
                        orphMcount += 1
                isDel = False
                if random.random()*100 < deleted :                    # Check if time for a deleted record
                    patients[me]['Deleted'] = 'D'
                    if infoText == '' :
                        infoText = 'to Deleted'
                    else :
                        infoText += ',to Deleted'
                    mCount += 1
                    isDel = True
                    dCount += 1
                    if isAlias :
                        if isAlias and isMerge :
                            dBcount += 1
                        else :
                            dAcount += 1
                    elif isMerge :
                        dMcount += 1
                    else :
                        masterDelMe.append(me)        # Keep track of deleted, but not alias/not merged patients
                elif errors and (dupMe is None) :
                    if random.random()*100 < dupUR :            # Check if time for a duplicate UR record
                        dupMe =  random.choice(masterMe)
                        patients[me]['UR'] = patients[dupMe]['UR']
                        if infoText == '':
                            infoText = 'to DupUR'
                        else:
                            infoText += ',to DupUR'
                        dupCount += 1
                        skippedUR.append(URno)
                    elif random.random()*100 < potDup :            # Check if time for a potential duplicate
                        dupMe =  random.choice(masterMe)
                        if infoText == '':
                            infoText = 'to potDup'
                        else:
                            infoText += ',to DupUR'
                        actDup = False

                        # Duplicate some patient data
                        cloneInfo = clone(me, dupMe)

                        actDup = True
                        if random.random() < 0.3 :            # Sometimes the marital status is wrong
                            infoText += ' married'
                            if patients[me]['married'] == 'M' :
                                patients[me]['married'] = 'S'
                            else :
                                patients[me]['married'] = 'M'
                            actDup = False
                        if patients[me]['birthdate'] != patients[dupMe]['birthdate'] :
                            if infoText == 'to potDup' :
                                infoText += ' bd'
                            else :
                                infoText += ',bd'
                            actDup = False
                        if random.random() < 0.25 :            # Sometimes the given name is wrong
                            givenName = patients[me]['givenName']
                            if patients[me]['sex'] == 'F' :
                                patients[me]['givenName'] = selectGirlsname()
                            else :
                                patients[me]['givenName'] = selectBoysname()
                            if patients[me]['givenName'] == givenName :
                                actDup = True
                            else :
                                if infoText == 'to potDup' :
                                    infoText += ' gn'
                                else :
                                    infoText += ',gn'
                            actDup = False
                        if random.random() < 0.333 :            # Sometimes the family name is wrong
                            familyName = patients[me]['familyName']
                            patients[me]['familyName'] = selectFamilyName()
                            if patients[me]['familyName'] == familyName :
                                actDup = True
                            else :
                                if infoText == 'to potDup' :
                                    infoText += ' fn'
                                else :
                                    infoText += ',fn'
                            actDup = False
                        if random.random() < 0.5 :            # Sometimes the sex is wrong
                            if infoText == 'to potDup' :
                                infoText += ' sex'
                            else :
                                infoText += ',sex'
                            if patients[me]['sex'] == 'M' :
                                patients[me]['sex'] = 'F'
                            else :
                                patients[me]['sex'] = 'M'
                            actDup = False
                        thisKey = patients[me]['familyName'] + '~' + patients[me]['givenName'] + '~'
                        thisKey += patients[me]['sex'] + '~' + patients[me]['birthdate']
                        if thisKey in clones :
                            actDupCount += 1
                        else :
                            clones.append(thisKey)
                            if actDup :
                                actDupCount += 1
                            else :
                                potDupCount += 1
                    else :
                        masterMe.append(me)        # Keep track of not alias/not merged/not deleted patients
                if errors and (dupMe is None) and (not isDel) :
                    if random.random()*100 < familyNameErrors :        # Check if time for a family name error
                        infoText = 'fn error'
                        FNEcount += 1
                        prevName = re.search(r' \(| \[', patients[me]['familyName'])
                        if prevName :
                            patients[me]['familyName'] = patients[me]['familyName'][0:prevName.start()]        # remove previous name
                        if (patients[me]['sex'] == 'F') and (patients[me]['married'] == 'M') :
                            familyName = selectFamilyName()
                            if random.random() < 0.3 :
                                patients[me]['familyName'] = f"{patients[me]['familyName']} ({familyName})"    # previous name in round brackets
                            elif random.random() < 0.6 :
                                patients[me]['familyName'] = f"{patients[me]['familyName']} [{familyName}]"    # previous name in square brackets
                            else :
                                patients[me]['familyName'] = f"{patients[me]['familyName']} (nee {familyName})"    # previous name as (nee ...)
                        else :
                            suffix = re.search(' ', patients[me]['familyName'])
                            if (not suffix) and (random.random() < 0.2) :
                                patients[me]['familyName'] += ' III'
                            elif (not suffix) and (random.random() < 0.5) :
                                patients[me]['familyName'] += ' JNR'
                            elif random.random() < 0.95 :
                                if suffix :            # Remove suffix
                                    patients[me]['familyName'] = patients[me]['familyName'][0:suffix.start()]        # remove suffix name
                                patients[me]['familyName'] += '-' + selectFamilyName()
                            else :
                                if suffix :            # Remove suffix
                                    patients[me]['familyName'] = patients[me]['familyName'][0:suffix.start()]        # remove suffix name
                                patients[me]['familyName'] += '^' + selectFamilyName()
                    if random.random()*100 < givenNameErrors :        # Check if time for a given name error
                        if infoText == '' :
                            infoText = 'gn error'
                        else :
                            infoText += ',gn error'
                        GNEcount += 1
                        prevNickname = re.search(r' \(| \*', patients[me]['familyName'])
                        if (not prevNickname) and (patients[me]['givenName'] in nicknames) :
                            nickname = random.choice(nicknames[patients[me]['givenName']])
                            if random.random() < 0.5 :
                                patients[me]['givenName'] += ' *' + nickname
                            else :
                                patients[me]['givenName'] += ' (' + nickname + ')'
                        else :
                            (year, month, day) = patients[me]['birthdate'].split('-')
                            year = int(year)
                            month = int(month)
                            day = int(day)
                            birthdate = datetime.date(year, month, day)
                            today = datetime.date.today()
                            age = today - birthdate
                            if age < datetime.timedelta(days=60) :        # a baby
                                patients[me]['givenName'] = 'TWIN 1'
                            else :
                                if prevNickname :                # Remove previous nick name
                                    patients[me]['givenName'] = patients[me]['givenName'][0:prevNickname.start()]
                                hyphen = re.search('-', patients[me]['givenName'])
                                if hyphen :                    # Remove second name
                                    patients[me]['givenName'] = patients[me]['givenName'][0:hyphen.start()]
                                if patients[me]['sex'] == 'M' :
                                    patients[me]['givenName'] += ' (' + selectBoysname() + ')'
                                else :
                                    patients[me]['givenName'] += ' (' + selectGirlsname() + ')'
            PMI = []
            for field in (PMIfields) :
                PMI.append(patients[me][field])
            csvwriter.writerow(PMI)
            if infoText != '' :
                if dupMe is not None :
                    if cloneInfo != '' :
                        dupPMI = [f'cloned ({cloneInfo})']
                    else :
                        dupPMI = ['cloned']
                    for field in (PMIfields) :
                        dupPMI.append(patients[dupMe][field])
                    logging.info(csvString(dupPMI))
                info = [infoText] + PMI
                logging.info(csvString(info))
            patient += 1
            PID += 1
            if skipUR == 0 :
                URno += 1
            elif skipUR < 3 :
                URno += skipUR
            else :
                URno += random.randrange(skipUR - 1, skipUR + 1)

    # Report the results
    print(f'{rCount}\tPMI Records created')
    print(f'{aCount}\t\talias records')
    print(f'{mCount}\t\tmerged records')
    if both :
        print(f'\t\tof which {bCount} were both aliases and merged records')
    print(f'{dCount}\t\tdeleted records')
    print(f'\t\tof which {dAcount} were aliases records')
    print(f'\t\tand {dMcount} were merged records')
    if both :
        print(f'\t\t\tof which {dBcount} were both aliases and merged records')
    if errors :
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
        print(f'{GNEcount}\tNon-standard given names')
        print(f'{FNEcount}\tNon-standard family names')
    logging.shutdown()
    sys.exit(EX_OK)
