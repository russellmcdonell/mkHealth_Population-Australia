# pylint: disable=invalid-name, line-too-long, pointless-string-statement, global-statement

'''
make random Australian patients for test data
This data is intended to fill out the patient demographic information in test databases or test files.

SYNOPSIS
    from randPatients import patients, patientKeys, mkRandPatients

    numPatients = 5000
    extendNames = useShortStreetTypes = makeRandom = addUR = False
    inputDir = 'data/.'
    addressFile = 'GNAF_CORE.psv'
    minAge = 15
    maxAge = 80
    UsedIDs = {}
    UsedIDs['medicareNo'] = set()
    UsedIDs['IHI'] = set()
    UsedIDs['dvaNo'] = set()
    UsedIDs['crnNo'] = set()
    mkFamilies = False
    mkRandPatients(inputDir, addressFile, numPatients, extendNames, useShortStreetTypes, makeRandom, minAge, maxAge, mkFamilies, UsedIDs, addUR)

The randPatients() subroutine makes random patients, with a date of birth, address, gender, medicareNo, IHI, dvaNo, dvaType,
phone number, email address, height, weight, waist and hips which can be used as test data.
randPatiens also allocate 'race', being Aboriginality (Indiginous Status) in proportions that reflect
the Aboriginal and Torres Straigt Islander populations in Australia.
The patient's given name is randomly selected from over 5000 real given names (1200 male, 4200 female)
and the family name is randomly selected from over 384,000 real Australian family names.
There is an option to add two sequential letters to both given name and family
name to ensure no real name are accidentally created in the data.

The address is selected from 15M Australian addresses taken from the G-NAF CORE dataset - GNAF-CORE.psv.
Street types and their abbreviations are taken from METEOR identifier: 429840
(Streets, in G-NAF CORE, with other street types are discarded)
ABS data is also used - MB_2021_AUST.csv for Mesh Block to SA1/2/3/4/State mapping.

However there is an option to create random addresses.
Random addresses are created by randomly selecting an SA1 code from the G-NAF dataset.
This ensures appropriate proportions of addresses per state and rural/suburban split.
The state is derived from the SA1 code and a valid longitude and latitude for that SA1 region is chosen, again from the G-NAF dataset.
Next a random, valid postcode from the G-NAF dataset is chosen, but it must be a postcode that only exists in another state.
Then a random, valid suburb is chosen from the G-NAF datast, but it must be in a state that is different again; a third state.
Then a random, valid street name is chosen from the G-NAF dataset, but it must not exist in the chosen postcode.
Finally, a random, valid street type is chosen from the G-NAF dataset, but not one that is ever paired with this street name in the chosen state.
To make random addresses plausible, but improbable, the street number is a random number between 999900 and 999999.

Every patient is assigned a random mobile, home phone number, business phone number and email address.
Each patient is randomly assigned a birthdate between 'minAge' and 'maxAge' years prior to today plus a gender based upon the gender of the given name.
Then 2% of males are reassigned to gender 'U' - unknown. Each patient is also given a marital status; single if the patient is less than 18 years old.
For the rest, 51% as assigned 'married', 32% 'single', 10% 'devorced' and 7% 'widowed'.
The patient is also assigned height, weight, waist and hips measurments, based upon their age.

There is an options to assign an average of 4.5 patients to each address, with most patients having the same family name.

mkRandPatients() stores all this data in the dictionary patients{}. The keys are stored in the list patientKeys[].
randPatient() also creates test patient information in formats suitable for inclusion in databases, files, HL7 messages and ASTM/LIS2 messages.
The data can be accessed as follows

from randPatients import patients, patientKeys, mkRandPatients

numPatients = 5000
extendNames = useShortStreetTypes = makeRandom = addUR = False
inputDir = 'data/.'
addressFile = 'GNAF_CORE.psv'
minAge = 15
maxAge = 80
mkFamilies = False
UsedIDs = {}
UsedIDs['medicareNo'] = set()
UsedIDs['IHI'] = set()
UsedIDs['dvaNo'] = set()
UsedIDs['crnNo'] = set()
mkRandPatients(inputDir, addressFile, numPatients, extendNames, useShortStreetTypes, makeRandom, minAge, maxAge, mkFamilies, UsedIDs, addUR)

import random

key = random.choice(patientKeys)
title = patients[key]['title']
givenName = patients[key]['givenName']
familyName = patients[key]['familyName']
streetNo = patients[key]['streetNo']
streetName = patients[key]['streetName']
streetType = patients[key]['streetType']
shortStreetType = patients[key]['shortStreetType']
suburb = patients[key]['suburb']
state = patients[key]['state']
postcode = patients[key]['postcode']
longitude = patients[key]['longitude']
latitude = patients[key]['latitude']
meshblock = patients[key]['meshblock']
sa1 = patients[key]['sa1']
country = patients[key]['country']
mobile = patients[key]['mobile']
homePhone = patients[key]['homePhone']
businessPhone = patients[key]['businessPhone']
email = patients[key]['email']
birthdate = patients[key]['birthdate']
sex = patients[key]['sex']
medicareNo = patients[key]['medicareNo']
IHI = patients[key]['IHI']
dvaNo = patients[key]['dvaNo']
dvaType = patients[key]['dvaType']
crnNo = patients[key]['crnNo']
PEN = patients[key]['PEN']
SEN = patients[key]['SEN']
HC = patients[key]['HC']
married = patients[key]['married']
race = patients[key]['race']
height = patients[key]['height']
weight = patients[key]['weight']
waist = patients[key]['waist']
hips = patients[key]['hips']
LIS2 = patients[key]['LIS2']
PID = patients[key]['PID']
LIST = patients[key]['LIST']


For databases and files a list of patient data can be accessed as patients[key]['LIST']. The list is assembled in the following order
title,familyName,givenName,birthdate,sex,streetNo,streetName,streetType,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,mobile,homePhone,businessPhone,email,medicareNo,IHI,dvaNo,dvaType,crnNo,SN,HC,height,weight,waist,hips,married,race

For LIS2 (was ASTM E1394-97) messages the formatted patient data can be accessed as patients[key]['LIS2'].
The formatted data contains many of the fields in the 'P' record; namely field 1 - Record Type ('P'), fields - 2 Sequence Number (1),
field 3 - Practice-Assigned Patient ID (Medical Record number - if addUR is true a template of <UR> for Medical Record Number(MR), otherwise blank)
field 5 - Patient ID Number 3 (medicare number), field 6 - Patient Name, field 8 - Birthdate, field 9 - Patient Sex, field 10 - Patient Race-Ethic Origin (Aborigniality/Indeginous Status),
field 11 - Patient Address, field 13 - Patient Telphone Number, field 17 - Patient Height, field 18 - Patient Weight and field 30 - Marital Status.
The first two identifier fields are 'tagged'; field 3 - Practice Assigned Patient ID ('<P-3>') and field 4 - Laboratory Assigned Patient ID ('<P-4>').
These tags should be replaced with valid data.
All other fields are not populated (left as empty fields) and can be filled in later if the additional information is available.
If useShortStreetTypes is True, then the street type in field 11 - Patient Address will be the abbreviation of the street type (e.g. 'RD').

For HL7 messages the formated patient data can be accessed as patients[key]['PID'].
The formatted data contains many of the fields in the PID segment, field 0 - Segment Name ('PID'), field 1 - Sequence Number (1),
PID-3 Patient Identifier List (Medicare Number and Individual Health Identifier and, if addUR is True, a template (<UR>^^^<AUTH>^MR) for a Medical Record Number(MR)),
PID-5 Patient Name, PID-7 Data/time of birth, PID-8 Administrative Sex, PID-10 Race (Aboriginality/Indiginous Status), PID-13 Home Phone (and mobile and email),
PID-14 - Business Phone, PID-16 Marital Status and PID-30 - Patient Death Indicator ('N').
However in field 5 - Patient Name, the only components populated with random data are PID-5.1 - Family Name and PID-5.2 - Given Name.
PID-5.7 - Name Type Code is populated with the letter 'L' for Legal Name.
In PID-11 - Patient Address, the only components populated with randome data are PID-11.1 - Street Address, PID-11.3 - City, PID-11.4 - State or Province and
PID-11.5 - Zip or Postal Code.  No subcomponents of PID-11.1 are populated.
PID-11-6 - Country is populated with 'AUS' and PID-11.7 - Address Type is set to 'M' for Mailing Address.
If useShortStreetTypes is True, then the street type in PID-11.1 - Street Address will be the abbreviation of the street type (e.g. 'RD').



RANDOMIZATION LOGIC
After randomly selecting the given name and family name for the next patient mkRandPatients() checks that the selected patient
doesn't already exist in the dictionary patients{}.
If the patient does exist in patients{}, mkRandPatients() goes back and selects a new patient name,
and keeps selecting new patient names until a combination is found that doesn't already exist in patients{}.
This isn't striclty statistically sound as some names are more common than others is real life.
In an attempt to compensate, name selections is biased, based upon the popularity of each name.

In theory you could call mkRandPatients() with numPatients set to 800 million to create 800 million different patients,
if you didn't want IHI, medicare and DVA number.
But it would take forever to find that last, unused combination of male given name and family name.
In reality, a few thousand patients is normally enough for most tests.
NOTE: numPatients is limited in the software to 8 million because of the limitations of the test IHI numbers range.

The mkRandPatients() subroute also populates the list patientKeys[], with the keys from the dictionary patients{}.
It is useful when you wish to select a random patient or for setting additional fields/status in the patients{} dictionary.

For example

for me in (patientKeys):
    patients[me]['orderStatus'] = ''
    patients[me]['orderID'] = -1

'''

import sys
import io
import os
import csv
import zipfile
import random
import logging
import datetime
from streetTypes import streetTypeAbbrev


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


# Lower and Upper Percentiles at 0mths, 6mths, 24mths, 18yrs (216mths), 50yrs (600mths), 80yrs (960mths)
heightPercentils = {'M':[[47.0, 54.0], [64.0, 72.0], [81.0, 94.0], [165.0, 190.0], [169.0, 188.0], [162.0, 182.0]],
             'F':[[46.0, 55.0], [62.0, 70.0], [81.0, 93.0], [155.0, 175.0], [153.0, 174.0], [145.0, 168.0]]}
weightPercentils = {'M':[[2.5, 4.5], [6.8, 10.0], [9.5, 15.0], [45.0, 87.0], [62.0, 112.0], [59.0, 100.0]],
             'F':[[2.8, 4.2], [6.0,  9.5], [9.5, 15.0], [45.0, 87.0], [51.0, 104.0], [48.0, 95.0]]}

patients = {}
patientKeys = []
MB = {}                    # key=Mesh Block 2016 code, value=SA1 code
SA1s = {}                # key=SA1, value=set of tuples (longitude, latitude, mesh block)
SA1list = []            # A list of SA1s (for random selection)
SA3s = {}                # key=SA3, value=list of SA1s for each SA3
SA3postcodes = {}        # key=SA3, value=set of postcodes for each SA3
SA2s = {}               # key=SA2, value=SA2 name
SA4s = {}               # key=SA4, value=SA4 name
SA2inSA4 = {}           # key=SA4, value=set(SA2)
postcodes = {}            # key=postcode, value=set of the states each postcode occurs in
postcodesList = []        # A list of postcodes (for random selection)
suburbs = {}            # key=suburb, value=set of the states each suburb occurs in
suburbsList = []        # A list of suburbs (for random selection)
streetNames = {}        # key=Street Name, value=set of the postcode each streetname occurs in
streetNamesList = []    # A list of Street Names (for random selection)
streetNameTypes = {}    # key=Street Name, value=dict(key=Street Type, value=set(of the states where this Street Name combinatiion occurs
addresses = {}            # key=SA1, value=set of tuples (StreetNumber, StreetName, StreetType, StreetSuffix, Suburb, State, Postcode, Country, mb, longitude, latitude)
familyNames = []
boysnames = []
girlsnames = []
dvaStates = {'NSW':'N', 'VIC':'V', 'QLD':'Q', 'WA':'W', 'SA':'S', 'TAS':'T', 'ACT':'N', 'NT':'S'}
dvaWars = [' ', 'A', 'GW', 'X', 'SM', 'SS', 'KM', 'PX', 'P', 'IV']
dvaLinks = [' ', 'A', 'B', 'C', 'D', 'E']
dvaTypes = ['GOL', 'WHT', 'ORN']
# Map all the overseas territories into NSW and WA
OTstates = {'2':'NSW', '6':'WA'}
SA1states = {'1':'NSW', '2':'VIC', '3':'QLD', '4':'SA', '5':'WA', '6':'TAS', '7':'NT', '8':'ACT', '9':'WA'}


def getAustralianAddresses(inputDir, addressFile, numPatients):
    '''
Read in Australian Address from the G-NAF CORE data in the addressFile
    '''

    # Declare any globals to which we are going to do assignment!
    global postcodesList, streetNamesList, SA1list

    # Read in Mesh Block data
    # MB_CODE_2021,MB_CATEGORY_2021,CHANGE_FLAG_2021,CHANGE_LABEL_2021,SA1_CODE_2021,SA2_CODE_2021,SA2_NAME_2021,SA3_CODE_2021,SA3_NAME_2021,SA4_CODE_2021,SA4_NAME_2021,GCCSA_CODE_2021,GCCSA_NAME_2021,STATE_CODE_2021,STATE_NAME_2021,AUS_CODE_2021,AUS_NAME_2021,AREA_ALBERS_SQKM,ASGS_LOCI_URI_2021
    logging.info('Reading Mesh Blocks')
    with zipfile.ZipFile(os.path.join(inputDir, 'MB_2021_AUST.zip')) as zf:
        with zf.open('MB_2021_AUST.csv', 'r') as mb:
            mbReader = csv.DictReader(io.TextIOWrapper(mb, encoding='utf-8-sig'), dialect=csv.excel)
            for row in mbReader:
                MB[row['MB_CODE_2021']] = row['SA1_CODE_2021']
                SA2code = row['SA2_CODE_2021']
                SA2name = row['SA2_NAME_2021']
                SA2s[SA2code] = SA2name
                SA4code = row['SA4_CODE_2021']
                SA4name = row['SA4_NAME_2021']
                SA4s[SA4code] = SA4name
                if SA4code not in SA2inSA4:
                    SA2inSA4[SA4code] = set()
                SA2inSA4[SA4code].add(SA2code)

    # Read in the G-NAF CORE addresses
    # ADDRESS_DETAIL_PID|DATE_CREATED|ADDRESS_LABEL|ADDRESS_SITE_NAME|BUILDING_NAME|FLAT_TYPE|FLAT_NUMBER|LEVEL_TYPE|LEVEL_NUMBER|NUMBER_FIRST|NUMBER_LAST|LOT_NUMBER|STREET_NAME|STREET_TYPE|STREET_SUFFIX|LOCALITY_NAME|STATE|POSTCODE|LEGAL_PARCEL_ID|MB_CODE|ALIAS_PRINCIPAL|PRINCIPAL_PID|PRIMARY_SECONDARY|PRIMARY_PID|GEOCODE_TYPE|LONGITUDE|LATITUDE
    logging.info('Reading addresses')
    count = 0
    if addressFile is None:
        addressFile = 'GNAF_CORE.psv'
    with open(os.path.join(inputDir, addressFile), 'rt', encoding='utf-8-sig') as gnafCore:
        gnafReader = csv.DictReader(gnafCore, delimiter='|')
        for row in gnafReader:
            if row['MB_CODE'] not in MB:
                continue
            if row['STREET_TYPE'] not in streetTypeAbbrev:
                continue
            StreetNumber = row['NUMBER_FIRST']
            StreetName = row['STREET_NAME']
            StreetType = row['STREET_TYPE']
            StreetSuffix = row['STREET_SUFFIX']
            Suburb = row['LOCALITY_NAME']
            Postcode = row['POSTCODE']
            # Merge 'Other Territories' back into the nearest state (based on the first digit of the postcode)
            if row['STATE'] == 'OT':
                State = OTstates[Postcode[0:1]]
            else:
                State = row['STATE']
            Country = 'AUS'
            mb = row['MB_CODE']
            longitude = row['LONGITUDE']
            latitude = row['LATITUDE']

            # Collect the postcode and suburb stats
            if Postcode not in postcodes:
                postcodes[Postcode] = set()
            postcodes[Postcode].add(State)
            if Suburb not in suburbs:
                suburbs[Suburb] = set()
            suburbs[Suburb].add(State)

            # Collect the SA1 and SA3 stats
            sa1 = MB[mb]
            if sa1 not in SA1s:
                SA1s[sa1] = set()
            SA1s[sa1].add((longitude, latitude, mb))
            sa3 = sa1[:5]
            if sa3 not in SA3s:
                SA3s[sa3] = set()
            SA3s[sa3].add(sa1)
            if sa3 not in SA3postcodes:
                SA3postcodes[sa3] = set()
            SA3postcodes[sa3].add(Postcode)

            # Collect the Street Name and Street Type stats
            if StreetName not in streetNames:
                streetNames[StreetName] = set()
            streetNames[StreetName].add(Postcode)
            if StreetName not in streetNameTypes:
                streetNameTypes[StreetName] = {}
            if StreetType not in streetNameTypes[StreetName]:
                streetNameTypes[StreetName][StreetType] = set()
            streetNameTypes[StreetName][StreetType].add(State)

            # Assemble the address
            if sa1 not in addresses:
                addresses[sa1] = []
            addresses[sa1].append((StreetNumber, StreetName, StreetType, StreetSuffix, Suburb, State, Postcode, Country, mb, longitude, latitude))
            count += 1
            if (count % 100000) == 0:
                logging.info('%d addresses read in', count)
    SA1list = list(SA1s)
    postcodesList = list(postcodes)
    streetNamesList = list(streetNames)
    return


def getFamilyNames(inputDir, numFamilyNames):
    '''
Read in as many real Australian family names as necessary, keeping a profile of popularity
    '''

    # Declare any globals to which we are going to do assignment!

    profile = {}        # key: popularity, value: list of similar names
    # Surname,Count
    dialect = csv.excel
    with open(os.path.join(inputDir, 'AustralianSurnames.csv'), 'rt', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, dialect)
        i = 0
        header = True
        total = 0
        for row in csvreader:
            if header:
                header = False
                continue
            name = row[0]
            count = int(row[1])
            count10 = int(count/200)       # Bucket into groups of similarly popular names
            total += count                  # Total popularity (sample population)
            if count10 in profile:
                profile[count10]['sum'] += count
                profile[count10]['names'].append(name)
            else:
                profile[count10] = {}
                profile[count10]['sum'] = count
                profile[count10]['names'] = [name]
            i += 1
            if i == numFamilyNames:
                break

    if i < numFamilyNames:
        print(f'Insufficient family names ({i}) in AustralianFamilyNames.csv for request ({numFamilyNames:d})')
        logging.shutdown()
        sys.exit(EX_CONFIG)

    revProfile = {}             # key: count of bucket popularity, value: bucket key
    for count, values in profile.items():
        revProfile[values['sum']] = count

    ttotal = total
    for thisSum in reversed(sorted(revProfile.keys())):                     # total bucket popularity in decending order
        familyNames.append([])
        familyNames[-1].append(float(ttotal) / total)                       # pareto fraction popularity (this bucket and all following as fraction of total)
        familyNames[-1].append(profile[revProfile[thisSum]]['names'])       # The names for this pareto fraction
        ttotal -= thisSum
    familyNames.append([])
    familyNames[-1].append(0.0)
    return


def getBoysnames(inputDir):
    '''
Read in as many real boys names as necessary, keeping a profile of popularity
    '''

    # Declare any globals to which we are going to do assignment!

    profile = {}
    dialect = csv.excel
    with open(os.path.join(inputDir, 'boysnames.csv'), 'rt', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, dialect)
        total = 0
        header = True
        for row in csvreader:
            if header:
                header = False
                continue
            name = row[0]
            count = int(row[1])
            count10 = int(count/2000)
            total += count
            if count10 in profile:
                profile[count10]['sum'] += count
                profile[count10]['names'].append(name)
            else:
                profile[count10] = {}
                profile[count10]['sum'] = count
                profile[count10]['names'] = [name]

    revProfile = {}
    for count, values in profile.items():
        revProfile[values['sum']] = count

    ttotal = total
    for thisSum in reversed(sorted(revProfile.keys())):
        boysnames.append([])
        boysnames[-1].append(float(ttotal) / total)
        boysnames[-1].append([])
        boysnames[-1][1] = profile[revProfile[thisSum]]['names']
        ttotal -= thisSum
    boysnames.append([])
    boysnames[-1].append(0.0)
    return


def getGirlsnames(inputDir):
    '''
Read in as many real girls names as necessary, keeping a profile of popularity
    '''

    # Declare any globals to which we are going to do assignment!

    profile = {}
    dialect = csv.excel
    with open(os.path.join(inputDir, 'girlsnames.csv'), 'rt', newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile, dialect)
        total = 0
        header = True
        for row in csvreader:
            if header:
                header = False
                continue
            name = row[0]
            count = int(row[1])
            count10 = int(count/2000)
            total += count
            if count10 in profile:
                profile[count10]['sum'] += count
                profile[count10]['names'].append(name)
            else:
                profile[count10] = {}
                profile[count10]['sum'] = count
                profile[count10]['names'] = [name]

    revProfile = {}
    for count, values in profile.items():
        revProfile[values['sum']] = count

    ttotal = total
    for thisSum in reversed(sorted(revProfile.keys())):
        girlsnames.append([])
        girlsnames[-1].append(float(ttotal) / total)
        girlsnames[-1].append([])
        girlsnames[-1][1] = profile[revProfile[thisSum]]['names']
        ttotal -= thisSum
    girlsnames.append([])
    girlsnames[-1].append(0.0)
    return


def selectFamilyName():
    '''
Randomly select a family name
    '''

    choice = random.random()
    # logging.debug('Family name choice (%f)', choice)
    i = 0
    while familyNames[i + 1][0] > choice:
        # logging.debug('Skipping pareto (%f), names (%s)', familyNames[i][0], familyNames[i][1])
        i += 1
    familyName = random.choice(familyNames[i][1])
    return familyName


def selectBoysname():
    '''
Randomly select a boysname
    '''

    choice = random.random()
    i = 0
    while boysnames[i + 1][0] > choice:
        i += 1
    boysname = random.choice(boysnames[i][1])
    return boysname


def selectGirlsname():
    '''
Randomly select a girlsname
    '''

    choice = random.random()
    i = 0
    while girlsnames[i + 1][0] > choice:
        i += 1
    girlsname = random.choice(girlsnames[i][1])
    return girlsname


def mkLuhn(card):
    '''
    Compute mkLuhn checksum
    '''
    thisSum = 0
    for i in (range(len(card) - 1, -1, -2)):
        digit = int(card[i]) * 2
        thisSum += int(digit / 10)
        thisSum += digit  % 10
    for i in (range(len(card) - 2, -1, -2)):
        thisSum += int(card[i])
    return (thisSum * 9) % 10


weight = [1, 3, 7, 9, 1, 3, 7, 9]

def mkMedicareNo(medicardNo):
    '''
    Compute the Medicare card checksum
    '''

    csum = 0
    for i, thisWeight in enumerate(weight):
        csum += int(medicardNo[i:i+1]) * thisWeight
    csum %= 10

    return f'{medicardNo}{csum}{random.randint(1,7)}{random.randint(1,5)}'



def mkRandPatients(inputDir, addressFile, numPatients, extendNames, useShortStreetTypes, makeRandom, minAge, maxAge, mkFamilies, UsedIDs, addUR):

    '''
Make random Australian test patients. Randomly select a given name (51% female, 49% male) and randomly select a family name.
Check that this combination hasn't been used before and if it has, try again.
If extendNames is True, then add two sequential letters to both given name and family name.
Next create a birthdate. There is no bias reflecting real population age distribution.
There is an even number of people aged between 'minAge' and 'maxAge' years.
The patient's sex code (M or F) is taken from the gender of the given name, except that 2% of males are reassigned to the sex code 'U'.

Next randomly select an address from 15M valid Australian addresses taken from G-NAF, or create a random made up address.
Randomly made up addresses consist of an randomly selected SA1 code, matching state plus longitude and latitude with the SA1 region,
plus a randomly selected postcode from another state, plus a randomly selected suburb from a third state,
plus a randomly street name that does not exist in the chosen postcode,
plus a randomly selected street type, but one is never paired with this street name in the chosen state.
To make random addresses plausible, but improbable, the street number is a random number between 999900 and 999999.

Next we create a patient height and weight. This is done by interpolation from height/weight/age graphs, with percentiles. Six data points were
selected (0, 6 months, 2 years, 18 years, 50 years and 80 years), with both the highest percentile and the lowest percentile, for both men and women.
A  high and low percentile for each patient is calculated by extrapolation between these adjacent points, based on age
(or by straigh extension for patients over 80 on the assumption that between 80 and 85 the percentiles don't change).
Then a random height/weight is selected between these two percentiles.
However the calculated height/weight is biased towards the middle using the y = 1.0 - x*x function between x = -1 and x = +1.

Finally, marital status is assigned. All patients less than 18 years old are assigned 'S' for single.
Of the remaining patients, 51% as assigned 'M' for married, 32% assigned 'S' for single,
10% are assigned 'D' for divorced and the remaining 7% are assigned 'W' for widowed.
'''

    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    mobileSuffix = ['156', '157', '158', '159', '110']

    # Computer how many family names are likely to be required
    # In theory you only need n family names and n given names to create n*n patients, and we have 1K girl names
    # However 4 times a many makes the random selection go faster
    if numPatients > 8000000:
        numPatients = 8000000
    numFamilyNames = numPatients / 500
    getFamilyNames(inputDir, numFamilyNames)

    # Then all the boys names, all the girls names and the geocoded address data
    getBoysnames(inputDir)
    getGirlsnames(inputDir)
    getAustralianAddresses(inputDir, addressFile, numPatients)

    # Set up any used identifiers - NOTE: Safety Net and Healthcare Care numbers are just CentreLink Customer Reference numbers
    usedMedicareNo = set()
    usedIHIno = set()
    usedDVAno = set()
    usedCRNno = set()
    if UsedIDs is not None:
        if 'medicareNo' in UsedIDs:
            usedMedicareNo = UsedIDs['medicareNo']
        if 'IHI' in UsedIDs:
            usedIHIno = UsedIDs['IHI']
        if 'dvaNo' in UsedIDs:
            usedDVAno = UsedIDs['dvaNo']
        if 'CRNno' in UsedIDs:
            usedCRNno = UsedIDs['CRNno']

    logging.info('Creating %d demographic records', numPatients)
    familySize = 0
    sameFamilyName = False
    needAddress = True
    for i in range(numPatients):
        firstPass = True
        passes = 0
        while True:    # Loop if the random patient name is not distinct
            # logging.debug('mkFamilies: (%s), firstPass (%s)', mkFamilies, firstPass)
            if random.random() > 0.51:
                givenName = selectGirlsname()
                sex = 'F'
            else:
                givenName = selectBoysname()
                sex = 'M'
            if mkFamilies:
                if firstPass:
                    if familySize < 1:
                        familySize = 1 + int(random.betavariate(2, 5)*6)
                        familyName = selectFamilyName()
                        # logging.debug('New family, family name (%s)', familyName)
                        sameFamilyName = False
                        needAddress = True
                    elif random.random() < 0.1:
                        familyName = selectFamilyName()
                        # logging.debug('Same family, new family name (%s)', familyName)
                        sameFamilyName = False
                        needAddress = False
                    else:
                        sameFamilyName = True
                        needAddress = False
                firstPass = False
            else:
                familyName = selectFamilyName()
            me = givenName + '~' + familyName
            if me not in patients:
                break
            # logging.debug('duplicate name key:%s', me)
            passes += 1
            if (passes % 50) == 0:    # Try an different surname
                if passes > 500: # Too may re-tryies
                    logging.fatal('Not enough names to create different combinations')
                    logging.shutdown()
                    sys.exit(EX_CONFIG)
                if mkFamilies:
                    familyName = selectFamilyName()
        if mkFamilies:
            familySize -= 1
        longGivenName = givenName
        longFamilyName = familyName
        if extendNames:
            letter = random.randrange(25)
            longGivenName = givenName + letters[letter:letter+2]
            if not mkFamilies or not sameFamilyName:
                letter = random.randrange(25)
                longFamilyName = familyName + letters[letter:letter+2]
        patients[me] = {}
        patients[me]['givenName'] = longGivenName.upper()
        patients[me]['familyName'] = longFamilyName.upper()
        today = datetime.date.today()
        if maxAge > minAge:
            ageDays = random.randrange(minAge, maxAge) * 365
            age = datetime.timedelta(days=ageDays)
            birthdate = today - age
        else:
            ageDays = 0
            birthdate = today
        patients[me]['birthdate'] = birthdate.isoformat()
        if (sex == 'M') and (random.random() > 0.98):
            patients[me]['sex'] = 'U'
        else:
            patients[me]['sex'] = sex

        # Create a random address - it does not need to be 'nearby'
        needPhone = False
        if not mkFamilies or needAddress:
            thisAddr = mkRandAddress(None, False, makeRandom)
            needPhone = True
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
        patients[me]['meshblock'] = thisAddr['meshblock']
        patients[me]['sa1'] = thisAddr['sa1']
        if needPhone:
            if patients[me]['postcode'][0:1] == '7':
                patients[me]['homePhone'] = '035550' + f'{random.randrange(10000):04d}'
                patients[me]['businessPhone'] = '037010' + f'{random.randrange(10000):04d}'
            elif patients[me]['postcode'][0:1] == '2':
                patients[me]['homePhone'] = '025550' + f'{random.randrange(10000):04d}'
                patients[me]['businessPhone'] = '027010' + f'{random.randrange(10000):04d}'
            elif patients[me]['postcode'][0:1] == '6':
                patients[me]['homePhone'] = '085550' + f'{random.randrange(10000):04d}'
                patients[me]['businessPhone'] = '087010' + f'{random.randrange(10000):04d}'
            else:
                patients[me]['homePhone'] = '075550' + f'{random.randrange(10000):04d}'
                patients[me]['businessPhone'] = '077010' + f'{random.randrange(10000):04d}'
            homePhone = patients[me]['homePhone']
            businessPhone = patients[me]['businessPhone']
        else:
            patients[me]['homePhone'] = homePhone
            patients[me]['businessPhone'] = businessPhone
        patients[me]['mobile'] = '0491570' + random.choice(mobileSuffix)
        patients[me]['email'] = longGivenName.lower() + '.' + longFamilyName.lower() + '@his4ehr.com'

        while True:        # Loop if the medicareNo is not distinct
            medicareNo = patients[me]['postcode'][0:1]
            if medicareNo in ['0', '7']:
                medicareNo = '5'
            medicareNo += f'{random.randint(0, 9999999):07d}'
            medicareNo = mkMedicareNo(medicareNo)
            if medicareNo not in usedMedicareNo:
                break
        usedMedicareNo.add(medicareNo)
        patients[me]['medicareNo'] = medicareNo
        while True:        # Loop if the IHIno is not distinct
            IHIno = 800360990000000 + random.randint(0, 9999999)
            IHIno = f'{IHIno:d}{mkLuhn(str(IHIno)):d}'
            if IHIno not in usedIHIno:
                break
        usedIHIno.add(IHIno)
        patients[me]['IHI'] = IHIno
        percent = random.random() * 100
        if percent < 5.0:
            while True:        # Loop if the DVA no is not distinct
                dva = dvaStates[patients[me]['state']]
                dva += random.choice(dvaWars)
                if len(dva) > 3:
                    dva += f'{random.randint(0, 9999):04d}'
                elif len(dva) > 2:
                    dva += f'{random.randint(0, 99999):05d}'
                else:
                    dva += f'{random.randint(0, 999999):06d}'
                dva += random.choice(dvaLinks)
                if dva not in usedDVAno:
                    break
            usedDVAno.add(dva)
            patients[me]['dvaNo'] = dva
            if ageDays < 365*21 + 5:
                patients[me]['dvaType'] = 'GOL'
            else:
                patients[me]['dvaType'] = random.choice(dvaTypes)
        else:
            patients[me]['dvaNo'] = None
            patients[me]['dvaType'] = None
        ageYears = today.year - birthdate.year    # Some things (height, weight, marrital status) are age dependant
        ageMonths = ageYears * 12
        if today.month < birthdate.month:
            ageMonths = ageMonths - 1
        elif today.month == birthdate.month:
            if today.day < birthdate.day:
                ageMonths = ageMonths - 1
            if birthdate.month == 2 and birthdate.day == 29 and today.day == 28:
                ageMonths = ageMonths + 1
        percent = random.random() * 100
        patients[me]['crnNo'] = None
        patients[me]['PEN'] = None
        patients[me]['SEN'] = None
        patients[me]['HC'] = None
        if percent < 30.0:          # 30% of Australians have an interaction with CentreLink
            while True:        # Loop if the CRN no is not distinct
                crnNo = random.randint(900000000, 999999999)
                if crnNo not in usedCRNno:
                    break
            usedCRNno.add(crnNo)
            crnNo = str(crnNo) + random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            patients[me]['crnNo'] = crnNo
            percent = random.random() * 100
            if ageMonths > (65 * 12):           # Seniors can have a pensiono or a senior's healthcare card
                if percent < 60.0:              # 60% receive an aged care pension
                    patients[me]['PEN'] = crnNo
                elif percent < 90.0:            # Seniors who don't qualify for the pension do qualify for a senior's healthcare card
                    patients[me]['SEN'] = crnNo
            elif percent < 65.0:                # Non-seniors may qualify for a HealthCare concession card
                patients[me]['HC'] = crnNo
        if ageMonths <= 960:
            if ageMonths <= 6:
                idx = 0
                base = 0
                mths = 6
            elif ageMonths <= 24:
                idx = 1
                base = 6
                mths = 24 - 6
            elif ageMonths <= 216:
                idx = 2
                base = 24
                mths = 216 - 24
            elif ageMonths <= 600:
                idx = 3
                base = 216
                mths = 600 - 216
            else:
                idx = 4
                base = 600
                mths = 960 - 600
            hMin = ((heightPercentils[sex][idx + 1][0] - heightPercentils[sex][idx][0]) / mths) * (ageMonths - base) + heightPercentils[sex][idx][0]
            hMax = ((heightPercentils[sex][idx + 1][1] - heightPercentils[sex][idx][1]) / mths) * (ageMonths - base) + heightPercentils[sex][idx][1]
            wMin = ((weightPercentils[sex][idx + 1][0] - weightPercentils[sex][idx][0]) / mths) * (ageMonths - base) + weightPercentils[sex][idx][0]
            wMax = ((weightPercentils[sex][idx + 1][1] - weightPercentils[sex][idx][1]) / mths) * (ageMonths - base) + weightPercentils[sex][idx][1]
        else:
            hMin = heightPercentils[sex][5][0]
            hMax = heightPercentils[sex][5][1]
            wMin = weightPercentils[sex][5][0]
            wMax = weightPercentils[sex][5][1]
        thisHeight = random.normalvariate((hMin + hMax)/2, (hMax - hMin)/4)
        thisWeight = random.normalvariate((wMin + wMax)/2, (wMax - wMin)/4)
        thisWaist = thisHeight * 0.49                    # a ratio for all ages, both genders for normal, health persons
        thisWaist = thisWaist * (thisWeight/((wMax + wMin)/2))    # scaled by the over/under weight percentage
        if sex == 'M':
            thisHips = thisWaist / random.normalvariate(0.90, 0.10)
        else:
            thisHips = thisWaist / random.normalvariate(0.75, 0.10)
        patients[me]['height'] = f'{thisHeight:.0f}'
        patients[me]['weight'] = f'{thisWeight:.1f}'
        patients[me]['waist'] = f'{thisWaist:.0f}'
        patients[me]['hips'] = f'{thisHips:.0f}'
        if sex == 'F':
            patients[me]['title'] = 'MS'
        else:
            patients[me]['title'] = 'MR'
        if ageMonths <= 216:
            patients[me]['married'] = 'S'
        else:
            percent = random.randrange(100)
            if percent < 51:
                patients[me]['married'] = 'M'
                if sex == 'F':
                    patients[me]['title'] = 'MRS'
            elif percent < 51 + 32:
                patients[me]['married'] = 'S'
            elif percent < 51 + 32 + 10:
                patients[me]['married'] = 'D'
                if (sex == 'F') and (random.randrange(100) < 51):
                    patients[me]['title'] = 'MRS'
            else:
                patients[me]['married'] = 'W'
                if sex == 'F':
                    patients[me]['title'] = 'MRS'
        percent = random.random() * 100
        if percent > 3.0:
            race = '4'
        elif percent > 0.3:
            race = '1'
        elif percent > 0.12:
            race = '2'
        else:
            race = '3'
        patients[me]['race'] = race

        # Setup the HL7 data
        patients[me]['PID'] = 'PID|1||' + patients[me]['medicareNo'] + '^^^AUSHIC^MC~' + patients[me]['IHI'] + '^^^AUSHIC^NI'    # PID-3 Identifiers
        if patients[me]['dvaNo'] is not None:
            patients[me]['PID'] += '~' + patients[me]['dvaNo'] + '^^^AUSDVA'
            if patients[me]['dvaType'] == 'GOL':
                patients[me]['PID'] += '^DVG'
            elif patients[me]['dvaType'] == 'WHT':
                patients[me]['PID'] += '^DVW'
            elif patients[me]['dvaType'] == 'ORN':
                patients[me]['PID'] += '^DVO'
        if patients[me]['crnNo'] is not None:
            patients[me]['PID'] += '~' + patients[me]['crnNo'] + '^^^AUSLINK^AN'
            if patients[me]['PEN'] is not None:
                patients[me]['PID'] += '~' + patients[me]['PEN'] + '^^^^PEN'
            if patients[me]['SEN'] is not None:
                patients[me]['PID'] += '~' + patients[me]['SEN'] + '^^^^SEN'
            if patients[me]['HC'] is not None:
                patients[me]['PID'] += '~' + patients[me]['HC'] + '^^^^HC'
        if addUR:
            # Add a template for a hospital UR number as an extra repetition
            patients[me]['PID'] += '~<UR>' + '^^^<AUTH>^MR'
        patients[me]['PID'] += '||' + patients[me]['familyName'] + '^' + patients[me]['givenName'] + '^^^^^L'            # PID-5 Name
        patients[me]['PID'] += '||' + patients[me]['birthdate'].replace('-', '')                        # PID-7 Date/Time of Birth
        patients[me]['PID'] += '|' + patients[me]['sex']                                        # PID-8 Administrative Sex
        patients[me]['PID'] += '||' + race                                            # PID-10 Race (Aboriginality/Indigenous Status)
        if (useShortStreetTypes is not None) and useShortStreetTypes:
            patients[me]['PID'] += '|' + patients[me]['streetNo'] + ' ' + patients[me]['streetName'] + ' ' + patients[me]['shortStreetType']
        else:
            patients[me]['PID'] += '|' + patients[me]['streetNo'] + ' ' + patients[me]['streetName'] + ' ' + patients[me]['streetType']
        patients[me]['PID'] += '^^' + patients[me]['suburb'] + '^' + patients[me]['state'] + '^' + patients[me]['postcode'] + '^AUS^M'                # PID-11 Patient Address
        patients[me]['PID'] += '||' + '^PRN^PH^^^^^^' + patients[me]['homePhone']                        # PID-13 Phone number - Home, mobile, email
        patients[me]['PID'] += '~^PRN^CP^^^^^^' + patients[me]['mobile']
        patients[me]['PID'] += '~^NET^Internet^' + patients[me]['email']
        patients[me]['PID'] += '|' + '^WPN^PH^^^^^^' + patients[me]['businessPhone']                        # PID-14 Phone number - Business
        patients[me]['PID'] += '||' + patients[me]['married']                                    # PID-16 Marital Status
        patients[me]['PID'] += '||||||||||||||N'                                         # PID-30 Patient Death Indicator

        # Set up the LIS2 data
        patients[me]['LIS2'] = 'P|1|'           # P-1, P-2
        if addUR:
            # Add a template for a hospital UR number
            patients[me]['LIS2'] += '<UR>||'    # P-3, P-4
        else:
            patients[me]['LIS2'] += '||'        # P-3, P-4
        patients[me]['LIS2'] += patients[me]['medicareNo'] + '|' + patients[me]['familyName'] + '^' + patients[me]['givenName']    # P-5, P-6 Patient Name
        patients[me]['LIS2'] += '||' + patients[me]['birthdate'].replace('-', '')                    # P-8 Birthdate
        patients[me]['LIS2'] += '|' + patients[me]['sex'] + '|' + race                            # P-9 Patient Sex, P-10 Patient Race-Ethnic Origin (Aboriginality/Indegenous Status)
        if (useShortStreetTypes is not None) and useShortStreetTypes:
            patients[me]['LIS2'] += '|' + patients[me]['streetNo'] + ' ' + patients[me]['streetName'] + ' ' + patients[me]['shortStreetType']
        else:
            patients[me]['LIS2'] += '|' + patients[me]['streetNo'] + ' ' + patients[me]['streetName'] + ' ' + patients[me]['streetType']
        patients[me]['LIS2'] += '^' + patients[me]['suburb'] + '^' + patients[me]['state'] + '^' + patients[me]['postcode'] + '^AUS'            # P-11 Patient Address
        patients[me]['LIS2'] += '||' + patients[me]['homePhone']                            # P-13 Patient Telephone Number
        patients[me]['LIS2'] += '||||' + patients[me]['height'] + '|' + patients[me]['weight']                # P-17 Patient Height, P-18 Patient Weight
        patients[me]['LIS2'] += '||||||||||||' + patients[me]['married']                        # P-30 Married Status

        # Set up the LIST data
        dataList = []
        dataList.append(patients[me]['title'])
        dataList.append(patients[me]['familyName'])
        dataList.append(patients[me]['givenName'])
        dataList.append(patients[me]['birthdate'])
        dataList.append(patients[me]['sex'])
        dataList.append(patients[me]['streetNo'])
        dataList.append(patients[me]['streetName'])
        dataList.append(patients[me]['streetType'])
        dataList.append(patients[me]['shortStreetType'])
        dataList.append(patients[me]['suburb'])
        dataList.append(patients[me]['state'])
        dataList.append(patients[me]['postcode'])
        dataList.append(patients[me]['longitude'])
        dataList.append(patients[me]['latitude'])
        dataList.append(patients[me]['meshblock'])
        dataList.append(patients[me]['sa1'])
        dataList.append(patients[me]['country'])
        dataList.append(patients[me]['mobile'])
        dataList.append(patients[me]['homePhone'])
        dataList.append(patients[me]['businessPhone'])
        dataList.append(patients[me]['email'])
        dataList.append(patients[me]['medicareNo'])
        dataList.append(patients[me]['IHI'])
        dataList.append(patients[me]['dvaNo'])
        dataList.append(patients[me]['dvaType'])
        dataList.append(patients[me]['crnNo'])
        dataList.append(patients[me]['PEN'])
        dataList.append(patients[me]['SEN'])
        dataList.append(patients[me]['HC'])
        dataList.append(patients[me]['height'])
        dataList.append(patients[me]['weight'])
        dataList.append(patients[me]['waist'])
        dataList.append(patients[me]['hips'])
        dataList.append(patients[me]['married'])
        dataList.append(patients[me]['race'])
        patients[me]['LIST'] = dataList
        patientKeys.append(me)
        if ((i + 1) % 100000) == 0:
            logging.info('%d demographic records created', i + 1)
    logging.info('%d demographic records created', i + 1)
    return



def mkRandAddress(oldSA1, nearby, makeRandom):
    '''
    Select an address randomly and/or make up an invalid address
    '''

    thisAddr = {}

    # Choose a random address. Either an address from the Geocoded National Address Files (G-NAF)
    # Or a completely made up address made up of a random street name, suburb, postcode etc.
    if not makeRandom:
        #streetNo,streetName,streetType,suburb,state,postcode,country,meshblock,longitude,latitude,sa1
        if (oldSA1 is None) or (not nearby):
            # Choose a random address
            sa1 = random.choice(SA1list)
        else:
            # Choose a 'nearby' address - one in the same SA3
            sa1 = random.choice(list(SA3s[oldSA1[:5]]))
        StreetNumber, StreetName, StreetType, StreetSuffix, Suburb, State, Postcode, Country, mb, longitude, latitude = random.choice(addresses[sa1])
        thisAddr['streetNo'] = StreetNumber
        thisAddr['streetName'] = StreetName
        if StreetSuffix == '':
            thisAddr['streetType'] = StreetType
            thisAddr['shortStreetType'] = streetTypeAbbrev[StreetType]
        else:
            thisAddr['streetType'] = StreetType + ' ' + StreetSuffix
            thisAddr['shortStreetType'] = streetTypeAbbrev[StreetType] + ' ' + StreetSuffix
        thisAddr['suburb'] = Suburb
        thisAddr['state'] = State
        thisAddr['postcode'] = Postcode
        thisAddr['country'] = Country
        thisAddr['longitude'] = longitude
        thisAddr['latitude'] = latitude
        thisAddr['meshblock'] = mb
        thisAddr['sa1'] = sa1
    else:
        # Choose an SA1 region, state and postcode
        if (oldSA1 is None) or (not nearby):
            # Choose a random SA1 region
            sa1 = random.choice(SA1list)
            state = SA1states[sa1[:1]]
            # Choose a postcode from a different state
            postcode = random.choice(postcodesList)
            while state in postcodes[postcode]:
                postcode = random.choice(postcodesList)
        else:
            # Choose an SA1 region from the same SA3 region
            sa1 = random.choice(list(SA3s[oldSA1[:5]]))
            state = SA1states[sa1[:1]]
            # Choose a postcode from this SA3 region which may cross a state boarder
            postcode = random.choice(list(SA3postcodes[oldSA1[:5]]))
        thisAddr['sa1'] = sa1
        thisAddr['postcode'] = postcode
        thisAddr['state'] = state

        # Choose a random geolocation from within this SA1
        longitude, latitude, mb = random.choice(list(SA1s[sa1]))
        thisAddr['longitude'] = longitude
        thisAddr['latitude'] = latitude
        thisAddr['meshblock'] = mb
        thisAddr['country'] = 'AUS'

        # Choose a suburb from a different state (and not in the same state(s) as the postcode)
        suburb = random.choice(suburbsList)
        while (state in suburbs[suburb]) or (state in postcodes[postcode]):
            suburb = random.choice(suburbsList)
        thisAddr['suburb'] = suburb.upper()

        # Choose as street name that is not in this postcode
        streetName = random.choice(streetNamesList)
        while postcode in streetNames[streetName]:
            streetName = random.choice(streetNamesList)
        thisAddr['streetName'] = streetName.upper()

        # Choose a street type that is never paired with this street name in this state
        streetType = random.choice(list(streetTypeAbbrev))
        while (streetType in streetNameTypes[streetName]) and (state in streetNameTypes[streetName][streetType]):
            streetType = random.choice(list(streetTypeAbbrev))
        thisAddr['streetType'] = streetType.upper()
        thisAddr['shortStreetType'] = streetTypeAbbrev[streetType]

        # Assign an random, presumably bogus, house number
        thisAddr['streetNo'] = '999' + f'{random.randrange(100):0.2d}'

    return thisAddr
