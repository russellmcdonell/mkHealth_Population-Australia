#!/usr/bin/env python

# pylint: disable=invalid-name, line-too-long, pointless-string-statement, unused-variable, broad-exception-caught, too-many-lines

'''
A script to create an Excel spreadsheet of randomly created health networks, hospitals, clinics, specialists, GPs and patients

SYNOPSIS
$ python mkHealthPopulation.py [-D dataDir|--dataDir=dataDir] [-A addressFile|--addressFile=addressFile]
                               [-O outputDir|--outputDir=outputDir] [-o outputfile|--outputfile=outputfile]
                               [-r|--makeRandom] [-P|--Patients] [-i|--IHI] [-x extendType|--extendNames=extendType] [-a|--addUR]
                               [-v loggingLevel|--loggingLevel=loggingLevel]
                               [-L logDir|--logDir=logDir] [-l logfile|--logfile=logfile]

OPTIONS
-D dataDir|--dataDir=dataDir
The directory containing the source names and address data (default='data')

-A addressFile|--addressFile=addressFile
The file of GNAF_CORE addresses (or subset) (default='GNAF_CORE.psv')

-O outputDir|--outputDir=outputDir
The directory in which the output file will be created (default='output')
[mkHealthPopulation.cfg will be read from this directory]

-o outputfile|--outputfile=outputfile
The output file to be created (default='healthPopulation.xlsx')

-r|--makeRandom
Make up Australian addresses by random selection of street, suburb, state, postcode
This will break any concept of patients living near their healthcare providers and the generated data will not reflect real-world geographic distributions.

-P|--Patients
Output Patients for each GP doctor

-i|--IHI
Add Australian IHI number

-x extendType|--extendNames=extendType
Extend names with sequential letters (extendType==1) or 3 digit numbers (extendType==2)

-a|--addUR
Add a template for the UR number  in the PID and LIS2 segments

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
import json
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from fhir.resources.organization import Organization
from fhir.resources.healthcareservice import HealthcareService
from fhir.resources.location import Location
from fhir.resources.practitioner import Practitioner
from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources.careteam import CareTeam
from fhir.resources.patient import Patient
from randPatients import patients, patientKeys, mkRandPatients, mkRandAddress, mkLuhn, SA3postcodes, SA2inSA4, SA1s



# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0                   # successful termination
EX_WARN = 1                 # non-fatal termination with warnings

EX_USAGE = 64               # command line usage error
EX_DATAERR = 65             # data format error
EX_NOINPUT = 66             # cannot open input
EX_NOUSER = 67              # addressee unknown
EX_NOHOST = 68              # host name unknown
EX_UNAVAILABLE = 69         # service unavailable
EX_SOFTWARE = 70            # internal software error
EX_OSERR = 71               # system error (e.g., can't fork)
EX_OSFILE = 72              # critical OS file missing
EX_CANTCREAT = 73           # can't create (user) output file
EX_IOERR = 74               # input/output error
EX_TEMPFAIL = 75            # temp failure; user is invited to retry
EX_PROTOCOL = 76            # remote error in protocol
EX_NOPERM = 77              # permission denied
EX_CONFIG = 78              # configuration error


def mkProviderNo(thisProviderNo):
    '''
    Add a provider location and checksum to a provider number
    '''

    global usedProviderNo

    weights = [3, 5, 8, 4, 2, 1]
    providerLocation = '0123456789ABCDEFGHJKLMNPQRTUVWXY'
    csumChar = 'YXWTLKJHFBA'

    csum = 0
    for i, weight in enumerate(weights):
        csum += int(thisProviderNo[i]) * weight
    providerLoc = usedProviderNo[thisProviderNo]
    csum += providerLoc * 6
    csum %= 11
    return f'{thisProviderNo}{providerLocation[providerLoc:providerLoc+1]}{csumChar[csum:csum+1]}'


def mkPrescriberNo(prescriberNo):
    '''
    Add a check digit to a PBS prescriber number
    '''
    cdigit = 'YXWTLKJHFBA'
    csum = 0
    if (prescriberNo[0] == '0') and (len(prescriberNo) == 7):      # DHS issued Hospital Provider Number - 7 digits plus checksum letter
        csum = (int(prescriberNo[1]) * 5 + int(prescriberNo[2]) * 8 + int(prescriberNo[3]) * 4 + int(prescriberNo[4]) * 2 + int(prescriberNo[5]) + int(prescriberNo[6]) * 6) % 11
        return prescriberNo + cdigit[csum]
    else:                           # PBS Prescriber Number - 6 digits plus check sum number
        csum = int(prescriberNo[0]) + int(prescriberNo[1]) * 3 + int(prescriberNo[2]) * 7 + int(prescriberNo[3]) * 9 + int(prescriberNo[4]) + int(prescriberNo[5]) * 3
        csum %= 10
        return prescriberNo + f'{csum:d}'


def createOrganization(orgRecord, HPIO, partOfHPIO, orgName, addr, organizationType):
    '''
    Create the FHIR_Organization resource
    '''

    logging.info('Creating organization %s', orgName)

    rowData = patients[patientKeys[orgRecord]]
    organization_dict = {'resourceType':'Organization',
        'id': HPIO}
    if addr is None:
        organization_dict.update({
            'text': {
                'status': 'generated',
                'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{orgName}</td></tr>" + \
                    f"<tr><td>Address</td><td>{rowData['streetNo']} {rowData['streetName']} {rowData['shortStreetType']}</td></tr>" + \
                    f"<tr><td></td><td>{rowData['suburb']}</td></tr><tr><td></td><td>{rowData['state']}</td></tr><tr><td></td><td>{rowData['postcode']}</td></tr></tbody></table></div>"
            }
        })
    else:
        organization_dict.update({
            'text': {
                'status': 'generated',
                'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{orgName}</td></tr>" + \
                    f"<tr><td>Address</td><td>{addr['streetNo']} {addr['streetName']} {addr['shortStreetType']}</td></tr>" + \
                    f"<tr><td></td><td>{addr['suburb']}</td></tr><tr><td></td><td>{addr['state']}</td></tr><tr><td></td><td>{addr['postcode']}</td></tr></tbody></table></div>"
            }
        })
    organization_dict.update({
        'identifier': [
            {
                'use':'official',
                'type': {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org.au/CodeSystem/v2-0203',
                            'code': 'NOI',
                            'display': 'National Organisation Identifier'
                        }
                    ],
                    'text': 'HPI-O'
                },
                'system': 'http://ns.electronichealth.net.au/id/hi/hpio/1.0',
                'value': HPIO
            }
        ],
        'active': True
    })
    if organizationType == 'public hospital':
        organization_dict.update({
            'type': [
                        {
                        'coding': [
                            {
                                'system': 'http://snomed.info/sct',
                                'code': '257622000',
                                'display': HealthcareRoles['257622000']
                            }
                        ]
                    }
                ],
            'name': orgName
        })
    elif organizationType == 'private hospital':
        organization_dict.update({
            'type': [
                        {
                        'coding': [
                            {
                                'system': 'http://snomed.info/sct',
                                'code': '309895006',
                                'display': HealthcareRoles['309895006']
                            }
                        ]
                    }
                ],
            'name': orgName
        })
    elif organizationType == 'department':
        organization_dict.update({
            'type': [
                        {
                        'coding': [
                            {
                                'system': 'http://snomed.info/sct',
                                'code': departmentRoles[orgName],
                                'display': HealthcareRoles[departmentRoles[orgName]]
                            }
                        ]
                    }
                ],
            'name': orgName
        })
    elif organizationType == 'clinic':
        organization_dict.update({
            'type': [
                        {
                        'coding': [
                            {
                                'system': 'http://snomed.info/sct',
                                'code': '288565001',
                                'display': HealthcareRoles['288565001']
                            }
                        ]
                    }
                ],
            'name': orgName
        })
    elif organizationType == 'specialist':
        organization_dict.update({
            'type': [
                        {
                        'coding': [
                            {
                                'system': 'http://snomed.info/sct',
                                'code': '83891005',
                                'display': HealthcareRoles['83891005']
                            }
                        ]
                    }
                ],
            'name': orgName
        })
    organization_dict.update({
        'name': orgName
    })
    if addr is None:
        organization_dict.update({
            'contact': [
                {
                'telecom': [
                    {
                        'system': 'phone',
                        'value': rowData['businessPhone'],
                        'use': 'work'
                    }
                ],
                'address': {
                    'use': 'work',
                    'type': 'postal',
                    'text': rowData['streetNo'] + ' ' + rowData['streetName'] + ' ' + rowData['shortStreetType'] + ', ' + rowData['suburb'] + ', ' + rowData['state'] + '     ' + rowData['postcode'],
                    'line': [rowData['streetNo'] + ' ' + rowData['streetName'] + ' ' + rowData['shortStreetType']],
                    'city': rowData['suburb'],
                    'state': rowData['state'],
                    'postalCode': rowData['postcode'],
                    'country': rowData['country']
                }
            }]
        })
    else:
        organization_dict.update({
            'contact': [{
                'telecom': [
                    {
                        'system': 'phone',
                        'value': rowData['businessPhone'],
                        'use': 'work'
                    }
                ],
                'address': {
                    'use': 'work',
                    'type': 'postal',
                    'text': addr['streetNo'] + ' ' + addr['streetName'] + ' ' + addr['shortStreetType'] + ', ' + addr['suburb'] + ', ' + addr['state'] + '     ' + addr['postcode'],
                    'line': [addr['streetNo'] + ' ' + addr['streetName'] + ' ' + addr['shortStreetType']],
                    'city': addr['suburb'],
                    'state': addr['state'],
                    'postalCode': addr['postcode'],
                    'country': addr['country']
                }
            }]
        })
    if partOfHPIO is not None:
        organization_dict.update({
            'partOf': { 'reference': 'Organization/' + partOfHPIO }
        })

    organization = Organization.model_validate(organization_dict)
    try:
        organization_json = json.dumps(organization_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        print(organization_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(organization_dict, indent=4))

    # Return the resources
    if len(organization_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(organization_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return organization_json


def createLocation(locRecord, HPIO, locName, addr, managingHPIO):
    '''
    Create a FHIR_Location resource
    '''
    rowData = patients[patientKeys[locRecord]]
    location_dict = {'resourceType':'Location',
        'id': HPIO,
        'text': {
            'status': 'generated',
            'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{locName}</td></tr>" + \
                f"<tr><td>Address</td><td>{addr['streetNo']} {addr['streetName']} {addr['shortStreetType']}</td></tr>" + \
                f"<tr><td></td><td>{addr['suburb']}</td></tr><tr><td></td><td>{addr['state']}</td></tr><tr><td></td><td>{addr['postcode']}</td></tr></tbody></table></div>"
        },
        'status': 'active',
        'name': locName,
        'address': {
                'use': 'work',
                'type': 'postal',
                'text': addr['streetNo'] + ' ' + addr['streetName'] + ' ' + addr['shortStreetType'] + ', ' + addr['suburb'] + ', ' + addr['state'] + '     ' + addr['postcode'],
                'line': [addr['streetNo'] + ' ' + addr['streetName'] + ' ' + addr['shortStreetType']],
                'city': addr['suburb'],
                'state': addr['state'],
                'postalCode': addr['postcode'],
                'country': addr['country']
        },
        'position': {
                'longitude': float(addr['longitude']),
                'latitude': float(addr['latitude'])
        }
    }
    if managingHPIO is not None:
        location_dict.update({
            'managingOrganization': { 'reference': 'Organization/' + managingHPIO }
        })
    location = Location.model_validate(location_dict)
    try:
        location_json = json.dumps(location_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(location_dict, indent=4))

    # Return the resources
    if len(location_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(location_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return location_json


def createHealthcareService(serviceRecord, HPIO, serviceName, serviceType, serviceSpecialty):
    '''
    Create the FHIR_HealthcareService resource
    '''
    rowData = patients[patientKeys[serviceRecord]]
    healthcareService_dict = {'resourceType':'HealthcareService',
        'id': HPIO,
        'text': {
            'status': 'generated',
            'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{serviceName}</td></tr>" + \
                f"<tr><td>Address</td><td>{rowData['streetNo']} {rowData['streetName']} {rowData['shortStreetType']}</td></tr>" + \
                f"<tr><td></td><td>{rowData['suburb']}</td></tr><tr><td></td><td>{rowData['state']}</td></tr><tr><td></td><td>{rowData['postcode']}</td></tr></tbody></table></div>"
        },
        'identifier': [
            {
                'use':'official',
                'type': {
                    'coding': [
                        {
                            'system': 'http://terminology.hl7.org.au/CodeSystem/v2-0203',
                            'code': 'NOI',
                            'display': 'National Organisation Identifier'
                        }
                    ],
                    'text': 'HPI-O'
                },
                'system': 'http://ns.electronichealth.net.au/id/hi/hpio/1.0',
                'value': HPIO
            }
        ],
        'active': True,
        'providedBy': {
                'reference': 'Organization/' + HPIO
        },
    }
    if serviceType == 'department':
        deptName = serviceName.split('@')[0]
        healthcareService_dict.update({
            'type': [
                {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': departmentRoles[deptName],
                            'display': HealthcareRoles[departmentRoles[deptName]]
                        }
                    ]
                }
            ]
        })
    elif serviceType == 'clinic':
        healthcareService_dict.update({
            'type': [
                {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '288565001',
                            'display': HealthcareRoles['288565001']
                        }
                    ]
                }
            ]
        })
    elif serviceType == 'specialist':
        healthcareService_dict.update({
            'type': [
                {
                    'coding': [
                        {
                            'system': 'http://snomed.info/sct',
                            'code': '288565001',
                            'display': HealthcareRoles['288565001']
                        }
                    ]
                }
            ]
        })
    healthcareService_dict.update({
        'specialty': [
            {
                'coding': [
                    {
                        'system': 'http://snomed.info/sct',
                        'code': serviceSpecialty,
                        'display': Specialties[serviceSpecialty]
                    }
                ]
            }
        ],
        'location': [
            {
                'reference': 'Location/' + HPIO
            }
        ],
        'name': serviceName,
        'contact': [
            {
                'telecom': [
                    {
                    'system': 'phone',
                    'value': rowData['businessPhone'],
                    'use': 'work'
                    }
                ]
            }
        ]
    })

    healthcareService = HealthcareService.model_validate(healthcareService_dict)
    try:
        healthcareService_json = json.dumps(healthcareService_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(healthcareService_dict, indent=4))

    # Return the resources
    if len(healthcareService_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(healthcareService_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return healthcareService_json


sexName = {'M': 'male', 'F': 'female', 'U': 'unknown'}
def createPractitioner(pracRecord, HPII, pracProviderNos, pracPrescriberNo, pracAhpraNo):
    '''
    Create FHIR_Practitioner resource
    '''

    logging.info('Creating Practitioner :%s', HPII)

    rowData = patients[patientKeys[pracRecord]]
    pracTitle = rowData['title']
    family = rowData['familyName']
    given = rowData['givenName']
    sex = sexName[rowData['sex']]
    practitioner_dict = {'resourceType':'Practitioner',
        'id': HPII,
        'text': {
            'status': 'generated',
            'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{pracTitle} {given} {family}</td></tr></tbody></table></div>"
        },
        'identifier': [
            {
                'type': {
                    'coding': [
                        {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'NPI',
                        'display': 'National Provider Identifier'}
                    ],
                    'text': 'HPI-I'
                },
                'system': 'http://ns.electronichealth.net.au/id/hi/hpii/1.0',
                'value': HPII
            },
            {
                'type': {
                    'coding': [
                        {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'PRES',
                        'display': 'Prescriber Number'}
                    ],
                    'text': 'Prescriber Number'
                },
                'system': 'http://ns.electronichealth.net.au/id/medicare-prescriber-number',
                'value': mkPrescriberNo(pracPrescriberNo)
            },
            {
                'type': {
                    'coding': [
                        {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                        'code': 'AHPRA',
                        'display': 'Australian Health Practitioner Regulation Agency Registration Number'}
                    ],
                    'text': 'Ahpra Registration Number'
                },
                'system': 'http://hl7.or.au/id/ahpra-registration-number',
                'value': 'MED' + str(pracAhpraNo)
            }
        ]
    }
    for providerNo in pracProviderNos:
        practitioner_dict['identifier'].append({
            'type': {
                'coding': [
                    {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': 'UPIN',
                    'display': 'Provider Number'}
                ],
                'text': 'Medicare Provider Number'
            },
            'system': 'http://ns.electronichealth.net.au/id/medicare-provider-number',
            'value': providerNo
                    
            })
    practitioner_dict.update({
        'active': True,
        'name': [
            {'use': 'official',
            'text': given + ' ' + family,
            'family': family,
            'given': [given],
            'prefix': [pracTitle]}
        ],
        'telecom': [
            {'system': 'phone',
            'value': rowData['businessPhone'],
            'use': 'work'},
            {'system': 'phone',
            'value': rowData['mobile'],
            'use': 'mobile'},
            {'system': 'email',
            'value': rowData['email'],
            'use': 'work'}
        ],
        'gender': sex,
        'birthDate': rowData['birthdate']
    })
    practitioner = Practitioner.model_validate(practitioner_dict)
    try:
        practitioner_json = json.dumps(practitioner_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(practitioner_dict, indent=4))

    # Return the resources
    if len(practitioner_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(practitioner_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return practitioner_json


def createPractitionerRole(roleRecord, HPII, HPIO, roleRole, rolespecialty):
    '''
    Create FHIR_PractitionerRole resource
    '''
    rowData = patients[patientKeys[roleRecord]]
    roleTitle = rowData['title']
    family = rowData['familyName']
    given = rowData['givenName']
    practitionerRole_dict = {'resourceType':'PractitionerRole',
        'id': HPII + '-' + HPIO,
        'text': {
            'status': 'generated',
            'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{roleTitle} {given} {family}</td></tr></tbody></table></div>"
        },
        'active': True,
        'practitioner': {
            'reference': 'Practitioner/' + HPII
        },
        'organization': {
            'reference': 'Organization/' + HPIO
        },
        'code': [
            {
                'coding': [
                    {
                        'system': 'http://snomed.info/sct',
                        'code': roleRole,
                        'display': Roles[roleRole]
                    }
                ]
            }
        ],
        'specialty': [
            {
                'coding': [
                    {
                        'system': 'http://snomed.info/sct',
                        'code': rolespecialty,
                        'display': Specialties[rolespecialty]
                    }
                ]
            }
        ],
        'contact': [
            {
                'telecom': [
                    {
                        'system': 'phone',
                        'value': rowData['businessPhone'],
                        'use': 'work'
                    },
                    {
                        'system': 'phone',
                        'value': rowData['mobile'],
                        'use': 'mobile'
                    },
                    {
                        'system': 'email',
                        'value': rowData['email'],
                        'use': 'work'
                    }
                ]
            }
        ]
    }

    practitionerRole = PractitionerRole.model_validate(practitionerRole_dict)
    try:
        practitionerRole_json = json.dumps(practitionerRole_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(practitionerRole_dict, indent=4))

    # Return the resources
    if len(practitionerRole_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(practitionerRole_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return practitionerRole_json


def createCareTeam(teamRecord, teamIHI, HPIO):
    '''
    Create the FHIR_CareTeam resource
    '''
    if len(careTeams[HPIO]) == 0:
        return
    if teamRecord is None:        # Template
        teamName = 'ReplaceWithGivenName ReplaceWithFamilyName'
    else:
        rowData = patients[patientKeys[teamRecord]]
        family = rowData['familyName']
        given = rowData['givenName']
        teamName = given + ' ' + family
    careteam_dict = {'resourceType':'CareTeam',
        'id': teamIHI + '-' + HPIO,
        'status': 'active',
        'name': teamName,
        'subject': {
            'reference': 'Patient/' + teamIHI
        },
        'participant': [
        ]
    }
    for teamMember in careTeams[HPIO]:
        careteam_dict['participant'].append({
            'member': {
                'reference': 'Practitioner/' + teamMember
            }
        })
    careteam_dict.update({
        'managingOrganization': [
            {'reference': 'Organization/' + HPIO }
        ]
    })

    careteam = CareTeam.model_validate(careteam_dict)
    try:
        careteam_json = json.dumps(careteam_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(careteam_dict, indent=4))

    # Return the resources
    if len(careteam_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(careteam_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return careteam_json


marriedName = {'D': 'Divorced', 'M': 'Married', 'S': 'Never Married', 'W': 'Wodowed'}
raceName = {'1': 'Aboriginal but not Torres Straight Islander origin', '2': 'Torres Straight Islander but not Aboriginal origin',
            '3': 'Both Aboriginal and Torres Straight Islander origin', '4': 'Neither Aboriginal nor Torres Straight Islander origin',
            '9': 'Not stated/inadequately described'}
dvaName = {'GOL': 'Gold Card', 'WHT': 'White Card', 'ORN': 'Repatriation Pharaceutical Benefits Card'}
dvaCode = {'GOL': 'DVG', 'WHT': 'DVW', 'ORN': 'DVO'}
dvaColor = {'GOL': 'Gold', 'WHT': 'White', 'ORN': 'Orange'}
def createPatient(patientRecord, patientIHI, patientGPs):
    '''
    Create the FHIR_Patient resource
    '''

    logging.info('Creating Patient :%s', patientIHI)

    rowData = patients[patientKeys[patientRecord]]
    patientTitle = rowData['title']
    family = rowData['familyName']
    given = rowData['givenName']
    race = rowData['race']
    sex = sexName[rowData['sex']]
    birthdate = rowData['birthdate']
    born = birthdate.split('-')
    line = rowData['streetNo'] + ' ' + rowData['streetName'] + ' ' + rowData['shortStreetType']
    city = rowData['suburb']
    state = rowData['state']
    postcode = rowData['postcode']
    medicareNo = rowData['medicareNo']
    dvaNo = rowData['dvaNo']
    dvaType = rowData['dvaType']
    PEN = rowData['PEN']
    SEN = rowData['SEN']
    HC = rowData['HC']
    married = rowData['married']
    patient_dict = {
        'resourceType':'Patient',
        'id': patientIHI,
        'text': {
            'status': 'generated',
            'div': f"<div xmlns='http://www.w3.org/1999/xhtml'><table><tbody><tr><td>Name</td><td>{patientTitle} {given} {family}</td></tr>" + \
                    f"<tr><td>Born</td><td>{born[2]}/{born[1]}/{born[0]}</td></tr>" + \
                    f"<tr><td>Address</td><td>{line}</td></tr>" + \
                    f"<tr><td></td><td>{city}</td></tr><tr><td></td><td>{state}</td></tr><tr><td></td><td>{postcode}</td></tr></tbody></table></div>"
        } ,
        'extension': [
            {
                'url': 'http://hl7.org.au/fhir/StructureDefinition/indigenous-status',
                'valueCoding': {
                    'system': 'https://healthterminologies.gov.au/fhir/CodeSystem/australian-indigenous-status-1',
                    'code': race,
                    'display': raceName[race]
                }
            }
        ],
        'identifier': [
            {
                'extension': [
                    {
                        'url': 'http://hl7.org.au/fhir/StructureDefinition/ihi-status',
                        'valueCoding': {
                            'system': 'https://healthterminologies.gov.au/fhir/CodeSystem/ihi-status-1',
                            'code': 'Active',
                            'display': 'Active'
                        }
                    },
                    {
                        'url': 'http://hl7.org.au/fhir/StructureDefinition/ihi-record-status',
                        'valueCoding': {
                            'system': 'https://healthterminologies.gov.au/fhir/CodeSystem/ihi-record-status-1',
                            'code': 'Verified',
                            'display': 'Verified'
                        }
                    }
                ],
                'type': {
                    'coding': [
                        {
                            'system': 'http://hl7.org.au/fhir/v2/0203',
                            'code': 'NI',
                            'display': 'National Unique Individual Identifier'
                        }
                    ],
                    'text': 'IHI'
                },
                'system': 'http://ns.electronichealth.net.au/id/hi/ihi/1.0',
                'value': patientIHI
            }
        ],
        'active': True,
        'name': [
            {
                'use': 'official',
                'text': patientTitle + ' ' + given + ' ' + family,
                'family': family,
                'given': [given],
                'prefix': [patientTitle]
            }
        ],
        'telecom': [
            {
                'system': 'phone',
                'value': rowData['homePhone'],
                'use': 'home'
            }, {
                'system': 'phone',
                'value': rowData['businessPhone'],
                'use': 'work'
            }, {
                'system': 'phone',
                'value': rowData['mobile'],
                'use': 'mobile'
            }, {
                'system': 'email',
                'value': rowData['email'],
                'use': 'home'
            }
        ],
        'gender': sex,
        'birthDate': birthdate,
        'address': [
            {
                'use': 'home',
                'type': 'postal',
                'text': line + ', ' + city + ', ' + state + '     ' + postcode,
                'line': [line],
                'city': city,
                'state': state,
                'postalCode': postcode
            }
        ],
        'maritalStatus': {
            'coding': [
                {
                    'system': 'http://terminology.hl7.org/CodeSystem/v3-MaritalStatus',
                    'code': married,
                    'display': marriedName[married]
                }
            ],
            'text': marriedName[married]
        },
        'generalPractitioner': [
        ]
    }
    if medicareNo is not None:
        patient_dict['identifier'].append({
            'type': {
                'coding': [
                    {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': 'MC',
                    'display': "Patient's Medicare Number"}
                ],
                'text': 'MC'
            },
            'system': 'http://ns.electronichealth.net.au/id/medicare-number',
            'value': medicareNo
        })
    if dvaNo is not None:
        patient_dict['identifier'].append({
            'type': {
                'coding': [
                    {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': dvaCode[dvaType],
                    'display': 'DVA ' + dvaName[dvaType] + 'Number'}
                ],
                'text': 'DVA Number (' + dvaColor[dvaType] + ')'
            },
            'system': 'http://ns.electronichealth.net.au/id/dva',
            'value': dvaNo
        })
    if PEN is not None:
        patient_dict['identifier'].append({
            'type': {
                'coding': [
                    {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': 'MC',
                    'display': "Patient's Pensioner Concession Number"}
                ],
                'text': 'PEN'
            },
            'system': 'http://ns.electronichealth.net.au/id/centrelink-customer-reference-number',
            'value': PEN
        })
    if SEN is not None:
        patient_dict['identifier'].append({
            'type': {
                'coding': [
                    {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': 'MC',
                    'display': "Patient's Senior's Healthcare Concession Number"}
                ],
                'text': 'PEN'
            },
            'system': 'http://ns.electronichealth.net.au/id/centrelink-customer-reference-number',
            'value': SEN
        })
    if HC is not None:
        patient_dict['identifier'].append({
            'type': {
                'coding': [
                    {'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': 'MC',
                    'display': "Patient's Healthcare Card Number"}
                ],
                'text': 'HC'
            },
            'system': 'http://ns.electronichealth.net.au/id/centrelink-customer-reference-number',
            'value': HC
        })
    for GP in patientGPs:
        patient_dict['generalPractitioner'].append({
            'reference': 'PractitionerRole/' + GP 
        })

    patient = Patient.model_validate(patient_dict)
    try:
        patient_json = json.dumps(patient_dict)
    except Exception as e:
        logging.critical('Bad JSON:%s', e.args)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)
    # print(json.dumps(patient_dict, indent=4))

    # Return the resources
    if len(patient_json) > 32767:
        logging.critical('Maximum string length for an Excel cell exceeded')
        print(patient_dict)
        sys.stdout.flush()
        logging.shutdown()
        sys.exit(EX_DATAERR)

    return patient_json


def mkDepartments(networkHPIO, localHospitalHPIO, hospitalHPIO, thisAddr, hospitalName, privateHospitalName, isPublic):

    global hospitals, deptHPIOs, patients, patientKeys, record, departmentSpecialties, Specialties, departmentFields
    global publicHospitalDepartments, privateHospitalDepartments, FHIR_Organization, FHIR_HealthcareService
    global localSpecialists, localNurses, localGPs, usedProviderNo, usedAhpraNo, publicHospialStaff, privateHospitalStafff
    global FHIR_PractitionerRole, Roles

    # Now create some departments and staff for this hospital
    # department fields:hospital_HPI-O,department_HPI-O,departmentName,application,departmentSpecialty,specialtyDescription
    outputRow = []
    if isPublic:
        noOfDepartments = len(hospitals[f'{networkName} hospitals'][hospitalName]['departments'])
    else:
        noOfDepartments = len(hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['departments'])
    for thisDepartment in range(noOfDepartments):
        if isPublic:
            department = hospitals[f'{networkName} hospitals'][hospitalName]['departments'][thisDepartment]
            outputRow = [networkHPIO, hospitalHPIO]
        else:
            department = hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['departments'][thisDepartment]
            outputRow = [networkHPIO, localHospitalHPIO, hospitalHPIO]
        record += 1
        IHI = patients[patientKeys[record]]['IHI']
        departmentHPIO = IHI[:5] + '2' + IHI[6:-1]
        departmentHPIO = f'{departmentHPIO}{mkLuhn(departmentHPIO):d}'
        deptHPIOs.add(departmentHPIO)
        careTeams[departmentHPIO] = set()
        outputRow.append(departmentHPIO)
        outputRow.append(department)
        if department in ['Emergency', 'Medical', 'Midwifery', 'Surgical', 'Paediatric', 'Intensive Care']:
            outputRow.append('PAS')
        else:
            outputRow.append(department[:4].upper())
        outputRow.append(departmentSpecialties[department])
        outputRow.append(Specialties[departmentSpecialties[department]])
        hospitalPhone = patients[patientKeys[record]]['businessPhone']
        for field in departmentFields:
            outputRow.append(patients[patientKeys[record]][field])
        if isPublic:
            publicHospitalDepartments.append(outputRow)
        else:
            privateHospitalDepartments.append(outputRow)
        FHIR_Organization.append([departmentHPIO, createOrganization(record, departmentHPIO, hospitalHPIO, department, thisAddr, 'department')])
        specialty = departmentSpecialties[department]
        FHIR_HealthcareService.append([departmentHPIO, createHealthcareService(record, departmentHPIO, department + '@' + hospitalName, 'department', specialty)])

        # Now create some staff
        # staff fields:department_HPI-O,staffSpecialty,specialtyDescription,role,roleDescription,HPI-I,providerNo,prescriberNo,ahpraNo,title,familyName,givenName,birthdate,sex,workMobile,businessPhone,workEmail
        if isPublic:
            noOfHospitalSpecialists = random.randrange(hospitals[f'{networkName} hospitals'][hospitalName]['minSpecialists'], hospitals[f'{networkName} hospitals'][hospitalName]['maxSpecialists'])
        else:
            noOfHospitalSpecialists = random.randrange(hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['minSpecialists'], hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['maxSpecialists'])
        deptSpecialists = set()
        for thisHospitalSpecialist in range(noOfHospitalSpecialists):
            outputRow = []
            if isPublic:
                outputRow = [networkHPIO, hospitalHPIO, departmentHPIO]
            else:
                outputRow = [networkHPIO, localHospitalHPIO, hospitalHPIO, departmentHPIO]
            hospitalSpecialistHPII = None
            providerNo = None
            prescriberNo = None
            ahpraNo = None
            availableSpecialists = set(localSpecialists[localHospitalHPIO].keys()) - deptSpecialists
            if (len(availableSpecialists) > 20) and (random.random() < 0.2):
                thisRecord = random.choice(list(availableSpecialists))
                hospitalSpecialistHPII = localSpecialists[localHospitalHPIO][thisRecord]['HPI-I']
                providerNo = localSpecialists[localHospitalHPIO][thisRecord]['providerNo']
                usedProviderNo[providerNo] += 1
                if usedProviderNo[providerNo] == 30:
                    providerNo = None
                prescriberNo = localSpecialists[localHospitalHPIO][thisRecord]['prescriberNo']
                ahpraNo = localSpecialists[localHospitalHPIO][thisRecord]['ahpraNo']
            else:
                record += 1
                thisRecord = record
                localSpecialists[localHospitalHPIO][thisRecord] = {}
            deptSpecialists.add(thisRecord)
            if hospitalSpecialistHPII is None:
                IHI = patients[patientKeys[thisRecord]]['IHI']
                hospitalSpecialistHPII = IHI[:5] + '1' + IHI[6:-1]
                hospitalSpecialistHPII = f'{hospitalSpecialistHPII}{mkLuhn(hospitalSpecialistHPII):d}'
                localSpecialists[localHospitalHPIO][thisRecord]['HPI-I'] = hospitalSpecialistHPII
            if hospitalSpecialistHPII not in practitionerDetails:
                practitionerDetails[hospitalSpecialistHPII] = {}
                practitionerDetails[hospitalSpecialistHPII]['providerNos'] = []
                practitionerDetails[hospitalSpecialistHPII]['record'] = thisRecord
            careTeams[departmentHPIO].add(hospitalSpecialistHPII)
            outputRow.append(hospitalSpecialistHPII)
            outputRow.append(departmentSpecialties[department])
            outputRow.append(Specialties[departmentSpecialties[department]])
            role = departmentSpecialistRoles[department]
            outputRow.append(role)
            outputRow.append(Roles[role])
            if providerNo is None:
                while True:        # Loop if the providerNo is not distinct
                    providerNo = f'{random.randint(100000, 999999):06d}'
                    if providerNo not in usedProviderNo:
                        break
                    logging.debug('Searching for a free provider number for a hospital doctor')
                usedProviderNo[providerNo] = 0
                localSpecialists[localHospitalHPIO][thisRecord]['providerNo'] = providerNo
            practitionerDetails[hospitalSpecialistHPII]['providerNos'].append(mkProviderNo(providerNo))
            outputRow.append(mkProviderNo(providerNo))
            if prescriberNo is None:
                prescriberNo = mkPrescriberNo(providerNo)
                localSpecialists[localHospitalHPIO][thisRecord]['prescriberNo'] = prescriberNo
            if 'prescriberNo' not in practitionerDetails[hospitalSpecialistHPII]:
                practitionerDetails[hospitalSpecialistHPII]['prescriberNo'] = prescriberNo
            outputRow.append(prescriberNo)
            if ahpraNo is None:
                while True:        # Loop if the ahpraNo is not distinct
                    ahpraNo = random.randint(9000000000, 9999999999)
                    if ahpraNo not in usedAhpraNo:
                        break
                    logging.debug('Searching for a free AHPRA number for a hospital doctor')
                localSpecialists[localHospitalHPIO][thisRecord]['ahpraNo'] = ahpraNo
                usedAhpraNo.add(ahpraNo)
            if 'ahpraNo' not in practitionerDetails[hospitalSpecialistHPII]:
                practitionerDetails[hospitalSpecialistHPII]['ahpraNo'] = 'MED' + str(ahpraNo)
            outputRow.append('MED' + str(ahpraNo))
            outputRow.append('Dr.')
            patients[patientKeys[thisRecord]]['businessPhone'] = hospitalPhone
            for field in drFields:
                outputRow.append(patients[patientKeys[thisRecord]][field])
            if isPublic:
                publicHospitalStaff.append(outputRow)
            else:
                privateHospitalStaff.append(outputRow)
            PRD = 'PRD||' + patients[patientKeys[thisRecord]]['familyName'] + '^' + patients[patientKeys[thisRecord]]['givenName'] + '^^^DR^^L'            # PRD-2 Provider Name
            PRD += '|' + thisAddr['streetNo'] + ' ' + thisAddr['streetName'] + ' ' + thisAddr['streetType']
            PRD += '^^' + thisAddr['suburb'] + '^' + thisAddr['state'] + '^' + thisAddr['postcode'] + '^AUS^M'   # PRD-3 Provider Address
            PRD += '||^PRN^PH^^^^^^' + patients[patientKeys[thisRecord]]['homePhone']
            PRD += '~^PRN^CP^^^^^^' + patients[patientKeys[thisRecord]]['mobile']
            PRD += '~^NET^Internet^' + patients[patientKeys[thisRecord]]['email']
            PRD += '~^WPN^PH^^^^^^' + patients[patientKeys[thisRecord]]['businessPhone']            # PRD-5 home phone, mbile, email, business phone
            PRD += '||' + mkProviderNo(providerNo) + '^AUSHICPR^UPIN'
            PRD += '~' + prescriberNo + '^AUSHIC^NPI'                                 # PRD-7 Provider identifiers
            PRDrow = []
            PRDrow.append(hospitalSpecialistHPII)
            PRDrow.append(PRD)
            HL7_PRD.append(PRDrow)
            FHIR_PractitionerRole.append([hospitalSpecialistHPII, createPractitionerRole(thisRecord, departmentHPIO, hospitalSpecialistHPII, role, departmentSpecialties[department])])

        outputRow = []
        if isPublic:
            noOfNurses = random.randrange(hospitals[f'{networkName} hospitals'][hospitalName]['minNurses'], hospitals[f'{networkName} hospitals'][hospitalName]['maxNurses'])
            outputRow = [networkHPIO, hospitalHPIO, departmentHPIO]
        else:
            noOfNurses = random.randrange(hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['minNurses'], hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['maxNurses'])
            outputRow = [networkHPIO, localHospitalHPIO, hospitalHPIO, departmentHPIO]
        deptNurses = set()
        for thisNurse in range(noOfNurses):
            outputRow = []
            if isPublic:
                outputRow = [networkHPIO, hospitalHPIO, departmentHPIO]
            else:
                outputRow = [networkHPIO, localHospitalHPIO, hospitalHPIO, departmentHPIO]
            nurseHPII = None
            nurseProviderNo = None
            nursePrescriberNo = None
            nurseAHPRANo = None
            availableNurses = set(localNurses[localHospitalHPIO].keys()) - deptNurses
            if (len(availableNurses) > 20) and (random.random() < 0.2):
                thisRecord = random.choice(list(availableNurses))
                nurseHPII = localNurses[localHospitalHPIO][thisRecord]['nurseHPII']
                nurseProviderNo = localNurses[localHospitalHPIO][thisRecord]['nurseProviderNo']
                usedProviderNo[nurseProviderNo] += 1
                if usedProviderNo[nurseProviderNo] == 30:
                    usedProviderNo[nurseProviderNo] = None
                nursePrescriberNo = localNurses[localHospitalHPIO][thisRecord]['nursePrescriberNo']
            else:
                record += 1
                thisRecord = record
                localNurses[localHospitalHPIO][thisRecord] = {}
            deptNurses.add(thisRecord)
            if nurseHPII is None:
                IHI = patients[patientKeys[thisRecord]]['IHI']
                nurseHPII = IHI[:5] + '1' + IHI[6:-1]
                nurseHPII = f'{nurseHPII}{mkLuhn(nurseHPII):d}'
                localNurses[localHospitalHPIO][thisRecord]['nurseHPII'] = nurseHPII
            if nurseHPII not in practitionerDetails:
                practitionerDetails[nurseHPII] = {}
                practitionerDetails[nurseHPII]['providerNos'] = []
                practitionerDetails[nurseHPII]['record'] = thisRecord
            careTeams[departmentHPIO].add(nurseHPII)
            outputRow.append(nurseHPII)
            outputRow.append(departmentSpecialties[department])
            outputRow.append(Specialties[departmentSpecialties[department]])
            role = '106292003'     # Nurse
            outputRow.append(role)
            outputRow.append(Roles[role])
            if nurseProviderNo is None:
                while True:        # Loop if the providerNo is not distinct
                    nurseProviderNo = f'{random.randint(100000, 999999):06d}'
                    if nurseProviderNo not in usedProviderNo:
                        break
                    logging.debug('Searching for a free provider number for a hospital nurse')
                usedProviderNo[nurseProviderNo] = 0
                localNurses[localHospitalHPIO][thisRecord]['nurseProviderNo'] = nurseProviderNo
            practitionerDetails[nurseHPII]['providerNos'].append(mkProviderNo(nurseProviderNo))
            outputRow.append(mkProviderNo(nurseProviderNo))
            if nursePrescriberNo is None:
                nursePrescriberNo = mkPrescriberNo(nurseProviderNo)
                localNurses[localHospitalHPIO][thisRecord]['nursePrescriberNo'] = nursePrescriberNo
            if 'prescriberNo' not in practitionerDetails[nurseHPII]:
                practitionerDetails[nurseHPII]['prescriberNo'] = nursePrescriberNo
            outputRow.append(nursePrescriberNo)
            if nurseAHPRANo is None:
                while True:        # Loop if the ahpraNo is not distinct
                    ahpraNo = random.randint(9000000000, 9999999999)
                    if ahpraNo not in usedAhpraNo:
                        break
                    logging.debug('Searching for a free AHPRA number for a hospital nurse')
                usedAhpraNo.add(ahpraNo)
                nurseAHPRANo = 'MED' + str(ahpraNo)
                localNurses[localHospitalHPIO][thisRecord]['nurseAHPRANo'] = nurseAHPRANo
            if 'ahpraNo' not in practitionerDetails[nurseHPII]:
                practitionerDetails[nurseHPII]['ahpraNo'] = nurseAHPRANo
            outputRow.append(nurseAHPRANo)
            outputRow.append('Nrs.')
            patients[patientKeys[thisRecord]]['businessPhone'] = hospitalPhone
            for field in drFields:
                outputRow.append(patients[patientKeys[thisRecord]][field])
            if isPublic:
                publicHospitalStaff.append(outputRow)
            else:
                privateHospitalStaff.append(outputRow)
            PRD = 'PRD||' + patients[patientKeys[thisRecord]]['familyName'] + '^' + patients[patientKeys[thisRecord]]['givenName'] + '^^^DR^^L'            # PRD-2 Provider Name
            PRD += '|' + thisAddr['streetNo'] + ' ' + thisAddr['streetName'] + ' ' + thisAddr['streetType']
            PRD += '^^' + thisAddr['suburb'] + '^' + thisAddr['state'] + '^' + thisAddr['postcode'] + '^AUS^M'   # PRD-3 Provider Address
            PRD += '||^PRN^PH^^^^^^' + patients[patientKeys[thisRecord]]['homePhone']
            PRD += '~^PRN^CP^^^^^^' + patients[patientKeys[thisRecord]]['mobile']
            PRD += '~^NET^Internet^' + patients[patientKeys[thisRecord]]['email']
            PRD += '~^WPN^PH^^^^^^' + patients[patientKeys[thisRecord]]['businessPhone']            # PRD-5 home phone, mbile, email, business phone
            PRD += '||' + mkProviderNo(nurseProviderNo) + '^AUSHICPR^UPIN'
            PRD += '~' + nursePrescriberNo + '^AUSHIC^NPI'                                 # PRD-7 Provider identifiers
            PRDrow = []
            PRDrow.append(nurseHPII)
            PRDrow.append(PRD)
            HL7_PRD.append(PRDrow)
            FHIR_PractitionerRole.append([nurseHPII, createPractitionerRole(thisRecord, departmentHPIO, nurseHPII, role, departmentSpecialties[department])])
    return


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
                        help='The name of the output directory [mkHealthPopulation.cfg will be read from this directory] (default="output")')
    parser.add_argument('-o', '--outfile', metavar='outputfile', dest='outputfile', default='healthPopulation.xlsx',
                        help='The name of health population Excel file to be created (default=healthPopulation.xlsx)')
    parser.add_argument('-r', '--makeRandom', dest='makeRandom', action='store_true',
                        help='Make up Australian addresses by random selection of street, suburb, state, postcode')
    parser.add_argument('-P', '--Patients', dest='Patients',
                        action='store_true', help='Output Patients for each doctor')
    parser.add_argument('-i', '--HPI', dest='HPI', action='store_true',
                        help='Add Australian HPI-I, providerNo, prescriberNo and HPI-O numbers')
    parser.add_argument('-x', '--extendNames', dest='extendNames', type=int, choices=range(1, 3),
                        help='Extend names with sequential letters (-x 1) or 3 digits (-x 2)')
    parser.add_argument('-a', '--addUR', dest='addUR',
                        action='store_true', help='Add a template for the UR number in PID and LIS2 segments')
    parser.add_argument('-v', '--verbose', dest='loggingLevel', type=int, choices=range(0, 5),
                        help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument('-L', '--logDir', dest='logDir', default='logs',
                        help='The name of a directory for the logging file(default="logs")')
    parser.add_argument('-l', '--logfile', metavar='logfile',
                        dest='logfile', help='The name of a logging file')
    args = parser.parse_args()

    # Set up logging
    logging_levels = {0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARNING, 3: logging.INFO, 4: logging.DEBUG}
    logfmt = progName + ' [%(asctime)s]: %(message)s'
    if args.loggingLevel:   # Change the logging level from "WARN" as the -v vebose option was specified
        loggingLevel = args.loggingLevel
        if args.logfile:        # and send it to a file if the -o logfile option is specified
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel],
                                filemode='w', filename=os.path.join(args.logDir, args.logfile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else:                   # send the default (WARN) logging to a file if the -o logfile option is specified
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
    addUR = args.addUR

    # Then read in the configuration from mkHealthPopulation.cfg
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    maxDepartments = 0
    try:
        config.read(os.path.join(outputDir, 'mkHealthPopulation.cfg'))
        minNetworks = config.getint('Networks', 'minNetworks')
        maxNetworks = config.getint('Networks', 'maxNetworks') + 1
        for row in csv.reader([config.get('Networks', 'networkNames')], csv.excel):
            networkNames = row
            break
        for row in csv.reader([config.get('Networks', 'postcodes')], csv.excel):
            networkPostcodes = row
            break
        hospitals = {}
        for networkName in networkNames:
            hospitals[f'{networkName} hospitals'] = {}
            hospitals[f'{networkName} private hospitals'] = {}
            hospitals[f'{networkName} hospitals']['minHospitals'] = config.getint(f'{networkName} Hospitals', 'minHospitals')
            hospitals[f'{networkName} hospitals']['maxHospitals'] = config.getint(f'{networkName} Hospitals', 'maxHospitals') + 1
            for row in csv.reader([config.get(f'{networkName} Hospitals', 'hospitalNames')], csv.excel):
                hospitals[f'{networkName} hospitals']['hospitalNames'] = row
                break
            for row in csv.reader([config.get(f'{networkName} Hospitals', 'hospitalPostcodes')], csv.excel):
                hospitals[f'{networkName} hospitals']['hospitalPostcodes'] = row
                break
            for hospitalName in hospitals[f'{networkName} hospitals']['hospitalNames']:
                hospitals[f'{networkName} hospitals'][hospitalName] = {}
                hospitals[f'{networkName} private hospitals'][hospitalName] = {}
                for row in csv.reader([config.get(hospitalName, 'departments')], csv.excel):
                    hospitals[f'{networkName} hospitals'][hospitalName]['departments'] = row
                    if len(row) > maxDepartments:
                        maxDepartments = len(row)
                    break
                hospitals[f'{networkName} hospitals'][hospitalName]['minSpecialists'] = config.getint(hospitalName, 'minSpecialists')
                hospitals[f'{networkName} hospitals'][hospitalName]['maxSpecialists'] = config.getint(hospitalName, 'maxSpecialists') + 1
                hospitals[f'{networkName} hospitals'][hospitalName]['minNurses'] = config.getint(hospitalName, 'minNurses')
                hospitals[f'{networkName} hospitals'][hospitalName]['maxNurses'] = config.getint(hospitalName, 'maxNurses') + 1
                hospitals[f'{networkName} hospitals'][hospitalName]['minPrivateHospitals'] = config.getint(hospitalName, 'minPrivateHospitals')
                hospitals[f'{networkName} hospitals'][hospitalName]['maxPrivateHospitals'] = config.getint(hospitalName, 'maxPrivateHospitals') + 1
                for row in csv.reader([config.get(hospitalName, 'privateHospitalNames')], csv.excel):
                    hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames'] = row
                    break
                if hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames'] == ['none']:
                    hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames'] = []
                for row in csv.reader([config.get(hospitalName, 'privateHospitalPostcodes')], csv.excel):
                    hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalPostcodes'] = row
                    break
                for privateHospitalName in hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames']:
                    hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName] = {}
                    for row in csv.reader([config.get(privateHospitalName, 'departments')], csv.excel):
                        hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['departments'] = row
                        if len(row) > maxDepartments:
                            maxDepartments = len(row)
                        break
                    hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['minSpecialists'] = config.getint(privateHospitalName, 'minSpecialists')
                    hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['maxSpecialists'] = config.getint(privateHospitalName, 'maxSpecialists') + 1
                    hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['minNurses'] = config.getint(privateHospitalName, 'minNurses')
                    hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['maxNurses'] = config.getint(privateHospitalName, 'maxNurses') + 1

        minSpecialistServices = config.getint('SpecialistServices', 'minSpecialistServices')
        maxSpecialistServices = config.getint('SpecialistServices', 'maxSpecialistServices') + 1
        minSpecialists = config.getint('SpecialistServices', 'minSpecialists')
        maxSpecialists = config.getint('SpecialistServices', 'maxSpecialists') + 1
        minClinics = config.getint('Clinics', 'minClinics')
        maxClinics = config.getint('Clinics', 'maxClinics') + 1
        minDr = config.getint('Clinics', 'minDr')
        maxDr = config.getint('Clinics', 'maxDr') + 1
        minPatients = config.getint('Clinics', 'minPatients')
        maxPatients = config.getint('Clinics', 'maxPatients') + 1
        minAge = config.getint('Patients', 'minAge')
        maxAge = config.getint('Patients', 'maxAge') + 1

        departmentSpecialties = dict(config['DepartmentSpecialties'])
        departmentSpecialistRoles = dict(config['DepartmentSpecialistRoles'])
        departmentRoles = dict(config['DepartmentRoles'])
        GPspecialties = dict(config['GPspecialty'])
        SpecialistRoles = dict(config['SpecialistRoles'])
        for specialty in SpecialistRoles:
            for row in csv.reader([SpecialistRoles[specialty]], csv.excel):
                SpecialistRoles[specialty] = row
                break
        Specialties = dict(config['Specialties'])
        Roles = dict(config['Roles'])
        HealthcareRoles = dict(config['HealthcareRoles'])

        addressFields = config.get('Fields', 'addressFields')
        addressFieldNames = config.get('Fields', 'addressFieldNames')
        networkFields = config.get('Fields', 'networkFields')
        networkFieldNames = config.get('Fields', 'networkFieldNames')
        hospitalFields = config.get('Fields', 'hospitalFields')
        hospitalFieldNames = config.get('Fields', 'hospitalFieldNames')
        departmentFields = config.get('Fields', 'departmentFields')
        departmentFieldNames = config.get('Fields', 'departmentFieldNames')
        clinicFields = config.get('Fields', 'clinicFields')
        clinicFieldNames = config.get('Fields', 'clinicFieldNames')
        drFields = config.get('Fields', 'drFields')
        drFieldNames = config.get('Fields', 'drFieldNames')
        patientFields1 = config.get('Fields', 'patientFields1')
        patientFields1Names = config.get('Fields', 'patientFields1Names')
        patientFields2 = config.get('Fields', 'patientFields2')
        patientFields2Names = config.get('Fields', 'patientFields2Names')

        for row in csv.reader([addressFields], csv.excel):
            addressFields = row
            break
        for row in csv.reader([addressFieldNames], csv.excel):
            addressFieldNames = row
            break
        if len(addressFields) != len(addressFieldNames):
            logging.fatal('Incorrect number of addressFieldNames for addressFields')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([networkFields], csv.excel):
            networkFields = row
            break
        for row in csv.reader([networkFieldNames], csv.excel):
            networkFieldNames = row
            break
        if len(networkFields) != len(networkFieldNames):
            logging.fatal('Incorrect number of networkFieldName for networkFields')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([hospitalFields], csv.excel):
            hospitalFields = row
            break
        for row in csv.reader([hospitalFieldNames], csv.excel):
            hospitalFieldNames = row
            break
        if len(hospitalFields) != len(hospitalFieldNames):
            logging.fatal('Incorrect number of hospitalFieldName for hospitalFields')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([departmentFields], csv.excel):
            departmentFields = row
            break
        for row in csv.reader([departmentFieldNames], csv.excel):
            departmentFieldNames = row
            break
        if len(departmentFields) != len(departmentFieldNames):
            logging.fatal('Incorrect number of departmentFieldName for departmentFields')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([clinicFields], csv.excel):
            clinicFields = row
            break
        for row in csv.reader([clinicFieldNames], csv.excel):
            clinicFieldNames = row
            break
        if len(clinicFields) != len(clinicFieldNames):
            logging.fatal('Incorrect number of clinicFieldName for clinicFields')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([drFields], csv.excel):
            drFields = row
            break
        for row in csv.reader([drFieldNames], csv.excel):
            drFieldNames = row
            break
        if len(drFields) != len(drFieldNames):
            logging.fatal('Incorrect number of drFieldName for drFields')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([patientFields1], csv.excel):
            patientFields1 = row
            break
        for row in csv.reader([patientFields1Names], csv.excel):
            patientFields1Names = row
            break
        if len(patientFields1) != len(patientFields1Names):
            logging.fatal('Incorrect number of patientFields1Names for patientFields1')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        for row in csv.reader([patientFields2], csv.excel):
            patientFields2 = row
            break
        for row in csv.reader([patientFields2Names], csv.excel):
            patientFields2Names = row
            break
        if len(patientFields2) != len(patientFields2Names):
            logging.fatal('Incorrect number of patientFields2Names for patientFields2')
            logging.shutdown()
            sys.exit(EX_CONFIG)
    except (configparser.MissingSectionHeaderError, configparser.NoSectionError,
            configparser.NoOptionError, configparser.ParsingError) as detail:
        logging.fatal('%s', detail)
        logging.shutdown()
        sys.exit(EX_CONFIG)

    noOfNetworks = random.randrange(minNetworks, maxNetworks)
    noOfRecords = noOfNetworks
    maxPublicHospitals = 0
    maxPrivateHospitals = 0
    maxHospitalSpecialists = 0
    maxHospitalNurses = 0
    for thisNetwork in range(noOfNetworks):
        networkName = networkNames[thisNetwork]
        maxPublicHospitals = max(maxPublicHospitals, hospitals[f'{networkName} hospitals']['maxHospitals'])
        for hospitalName in hospitals[f'{networkName} hospitals']['hospitalNames']:
            maxPrivateHospitals = max(maxPrivateHospitals, hospitals[f'{networkName} hospitals'][hospitalName]['maxPrivateHospitals'])
            maxHospitalSpecialists = max(maxHospitalSpecialists, hospitals[f'{networkName} hospitals'][hospitalName]['maxSpecialists'])
            maxHospitalNurses = max(maxHospitalNurses, hospitals[f'{networkName} hospitals'][hospitalName]['maxNurses'])
            for privateHospitalName in hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames']:
                maxHospitalSpecialists = max(maxHospitalSpecialists, hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['maxSpecialists'])
                maxHospitalNurses = max(maxHospitalNurses, hospitals[f'{networkName} private hospitals'][hospitalName][privateHospitalName]['maxNurses'])
    maxHospitals = maxPublicHospitals + maxPrivateHospitals
    noOfRecords += noOfNetworks * maxHospitals
    noOfRecords += noOfNetworks * maxHospitals * maxDepartments
    noOfRecords += noOfNetworks * maxHospitals * maxDepartments * maxHospitalSpecialists
    noOfRecords += noOfNetworks * maxHospitals * maxDepartments * maxHospitalNurses
    noOfRecords += noOfNetworks * maxPublicHospitals * maxSpecialistServices
    noOfRecords += noOfNetworks * maxPublicHospitals * maxSpecialistServices * maxSpecialists
    noOfRecords += noOfNetworks * maxPublicHospitals * maxClinics
    noOfRecords += noOfNetworks * maxPublicHospitals * maxClinics * maxDr

    if Patients:
        noOfRecords += noOfNetworks * maxPublicHospitals * maxClinics * maxDr * maxPatients

    UsedIDs = {}                            # No IDs have been used yet
    # Make random patients with long street names
    logging.info('Creating %d demographic records', noOfRecords)
    mkRandPatients(dataDir, addressFile, noOfRecords, extendNames, False, makeRandom, minAge, maxAge, False, UsedIDs, addUR)        # Create enough random patient


    # Create the Networks, hospitals, clinics, specialists, doctors (and patients if required) worksheets
    wb = Workbook()
    sheets = []
    healthNetworks = wb.active
    healthNetworks.title = 'Health Networks'
    healthNetworks.append(['Network HPI-O', 'Network Name', 'authority'] + addressFieldNames + networkFieldNames)
    healthNetworks.freeze_panes = 'A2'
    sheets.append('Health Networks')

    publicHospitals = wb.create_sheet('Public Hospitals')
    publicHospitals.append(['Network HPI-O', 'Hospital HPI-O', 'Hospital Name'] + addressFieldNames + hospitalFieldNames)
    publicHospitals.freeze_panes = 'A2'
    sheets.append('Public Hospitals')
    publicHospitalDepartments = wb.create_sheet('Public Hospital Departments')
    publicHospitalDepartments.append(['Network HPI-O', 'Hospital HPI-O', 'Department HPI-O', 'Department Name', 'application', 'Department Specialty', 'Specialty Description'] + hospitalFieldNames)
    publicHospitalDepartments.freeze_panes = 'A2'
    sheets.append('Public Hospital Departments')
    publicHospitalStaff = wb.create_sheet('Public Hospital Staff')
    publicHospitalStaff.append(['Network HPI-O', 'Hospital HPI-O', 'Department HPI-O',  'Hospital Staff HPI-I','Staff Specialty', 'Specialty Description', 'Role', 'Role Description',
                                'Provider No', 'Prescriber No', 'AHPRA No', 'Title'] + drFieldNames)
    publicHospitalStaff.freeze_panes = 'A2'
    sheets.append('Public Hospital Staff')

    privateHospitals = wb.create_sheet('Private Hospitals')
    privateHospitals.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'Private Hospital HPI-O', 'Hospital Name', 'authority'] + addressFieldNames + hospitalFieldNames)
    privateHospitals.freeze_panes = 'A2'
    sheets.append('Private Hospitals')
    privateHospitalDepartments = wb.create_sheet('Private Hospital Departments')
    privateHospitalDepartments.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'Private Hospital HPI-O', 'Department HPI-O', 'Department Name', 'application', 'Department Specialty', 'Specialty Description'] + hospitalFieldNames)
    privateHospitalDepartments.freeze_panes = 'A2'
    sheets.append('Private Hospital Departments')
    privateHospitalStaff = wb.create_sheet('Private Hospital Staff')
    privateHospitalStaff.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'Private Hospital HPI-O', 'Department HPI-O', 'Hospital Staff HPI-I', 'Staff Specialty', 'Specialty Description', 'Role', 'Role Description',
                                 'Provider No', 'Prescriber No', 'AHPRA No', 'Title'] + drFieldNames)
    privateHospitalStaff.freeze_panes = 'A2'
    sheets.append('Private Hospital Staff')

    specialistServices = wb.create_sheet('Specialist Services')
    specialistServices.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'Specialist Service HPI-O', 'Specialist Service Name', 'authority', 'application', 'Service Specialty', 'Specialty Description'] + addressFieldNames + clinicFieldNames)
    specialistServices.freeze_panes = 'A2'
    sheets.append('Specialist Services')
    specialists = wb.create_sheet('Specialists')
    specialists.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'Specialist Service HPI-O', 'Specialist HPI-I', 'Specialist Specialty', 'Specialty Description', 'Role', 'Role Description',
                        'Provider No', 'Prescriber No', 'AHPRA No', 'Title'] + drFieldNames)
    specialists.freeze_panes = 'A2'
    sheets.append('Specialists')

    gpClinics = wb.create_sheet('GP Clinics')
    gpClinics.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'GP Clinic HPI-O', 'Clinic Name', 'authority', 'application', 'Clinic Specialty', 'Specialty Description'] + addressFieldNames + clinicFieldNames)
    gpClinics.freeze_panes = 'A2'
    sheets.append('GP Clinics')
    gpClinicStaff = wb.create_sheet('GP Clinic Staff')
    gpClinicStaff.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'GP Clinic HPI-O', 'GP HPI-I', 'Staff Specialty', 'Specialty Description', 'Role', 'Role Description', 'Provider No',
                        'Prescriber No', 'AHPRA No', 'Title'] + drFieldNames)
    gpClinicStaff.freeze_panes = 'A2'
    sheets.append('GP Clinic Staff')

    if Patients:
        clinicPatients = wb.create_sheet('Patients')
        clinicPatients.append(['Network HPI-O', 'Local Public Hospital HPI-O', 'GP Clinic HPI-O', 'GP HPI-I', 'Patient IHI'] + patientFields1Names + addressFieldNames + patientFields2Names)
        clinicPatients.freeze_panes = 'A2'
        sheets.append('Patients')
        HL7_PID = wb.create_sheet('HL7_PID')
        HL7_PID.append(['IHI', 'PID'])
        HL7_PID.freeze_panes = 'A2'
        LIS2_P = wb.create_sheet('LIS2_P')
        LIS2_P.append(['IHI', 'P'])
        LIS2_P.freeze_panes = 'A2'

    HL7_PRD = wb.create_sheet('HL7_PRD')
    HL7_PRD.append(['HPI-I', 'PRD'])
    HL7_PRD.freeze_panes = 'A2'

    FHIR_Organization = wb.create_sheet('FHIR_Organization')
    FHIR_Organization.append(['HPI-O', 'Organization'])
    FHIR_Organization.freeze_panes = 'A2'
    FHIR_HealthcareService = wb.create_sheet('FHIR_HealthcareService')
    FHIR_HealthcareService.append(['HPI-O', 'HealthcareService'])
    FHIR_HealthcareService.freeze_panes = 'A2'
    FHIR_Location = wb.create_sheet('FHIR_Location')
    FHIR_Location.append(['HPI-O', 'Location'])
    FHIR_Location.freeze_panes = 'A2'
    FHIR_Practitioner = wb.create_sheet('FHIR_Practitioner')
    FHIR_Practitioner.append(['HPI-I', 'Practitioner'])
    FHIR_Practitioner.freeze_panes = 'A2'
    FHIR_PractitionerRole = wb.create_sheet('FHIR_PractitionerRole')
    FHIR_PractitionerRole.append(['HPI-I', 'PractitionerRole'])
    FHIR_PractitionerRole.freeze_panes = 'A2'
    FHIR_CareTeam = wb.create_sheet('FHIR_CareTeam')
    FHIR_CareTeam.append(['IHI', 'HPI-O', 'CareTeam'])
    FHIR_CareTeam.freeze_panes = 'A2'
    if Patients:
        FHIR_Patient = wb.create_sheet('FHIR_Patient')
        FHIR_Patient.append(['IHI', 'Patient'])
        FHIR_Patient.freeze_panes = 'A2'

    record = 0
    usedProviderNo = {}                     # Provider numbers that have been used  - cannot reuse them (location character can be different)
    usedAhpraNo = set()                     # AHPRA numbers that have been used - cannot reuse them
    usedIHI = set()                         # IHI that have already been used - can be reuse
    usedSpecServiceNames = set()            # Specialist Service Names that have already been used - cannot reuse
    usedGPclinicNames = set()               # GP Clinic Names that have already been used - cannot reuse

    localSpecialists = {}                   # Doctors who can work in Public Hospitals, Private Hospitals, and Specialist Clinics, but must be local
                                            # HPI-I and AHPRA numbers must be preserved, but Medicare Provider number must be different for each setting
    localNurses = {}                        # Nurses who can work in Public Hospitals and Private Hospitals, but must be local
    localGPs = {}                           # GPs who can work in multiple GP Clinics, but must be local
    localPatients = {}                      # Patients who can be associated with multiple GP Clinics/GPs, but must be local

    usedPubDrHPIO = set()                   # Public Doctor HPI-O that have already been used - can reuse
    usedPrivDrHPIO = set()                  # Private Doctor HPI-O that have already been used - can reuse
    usedNrsHPIO = set()                     # Nurse HPI-O that have already been used - can reuse

    deptHPIOs = set()                       # Department HPI-Os that need a templated FHIR CareTeam Resource
    careTeams = {}                          # The list of Practitioners in each Organization for FHIR CareTeam Resource
    patientDetails = {}                     # The patient details plus the list of GPs for FHIR Patient Resource
    practitionerDetails = {}                # The practitioner details plus the list of provider numbers for FHIR Practitioner Resource
    for thisNetwork in range(noOfNetworks):
        # healthNetworks fields:network_HPI-O,networkName,authority,streetNo,streetName,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,businessPhone
        outputRow = []
        # Assign HPI-O as organization ID
        IHI = patients[patientKeys[record]]['IHI']
        networkHPIO = IHI[:5] + '2' + IHI[6:-1]  # network HPI-O
        networkHPIO = f'{networkHPIO}{mkLuhn(networkHPIO):d}'
        outputRow.append(networkHPIO)
        if thisNetwork == len(networkNames):
            logging.fatal('Insufficient networkNames in configuration')
            logging.shutdown()
            sys.exit(EX_CONFIG)
        if thisNetwork == len(networkPostcodes):
            logging.fatal('Insufficient networkPostcodes in configuration')
            logging.shutdown()
            sys.exit(EX_CONFIG)

        # Network - select an SA3
        networkSA3 = None
        for thisSA3 in SA3postcodes:
            if networkPostcodes[thisNetwork] in SA3postcodes[thisSA3]:
                networkSA3 = thisSA3
                break
        if networkSA3 is None:
            logging.fatal('Network postcode (%s) not in address file', networkPostcodes[thisNetwork])
            logging.shutdown()
            sys.exit(EX_CONFIG)
        networkName = networkNames[thisNetwork]
        outputRow.append(networkName)
        initials = networkName.split(' ')
        authority = ''
        for initial in initials:
            authority += initial[0].upper()
        outputRow.append(authority)
        # Start with the address (less postcode)
        thisAddr = mkRandAddress(networkSA3, True, makeRandom)
        for field in addressFields:
            outputRow.append(thisAddr[field])
        # And the network specific fields
        for field in networkFields:
            outputRow.append(patients[patientKeys[record]][field])
        healthNetworks.append(outputRow)
        FHIR_Organization.append([networkHPIO, createOrganization(record, networkHPIO, None, networkName, None, 'network')])

        # Now create some hospitals - some public and some private
        createdPrivateHospitals = set()             # In case two public hospitals are close to the same private hospital
        hospitals[f'{networkName} hospitals']['hospitalSA3'] = []
        publicHospitalNo = 0
        noOfHospitals = random.randrange(hospitals[f'{networkName} hospitals']['minHospitals'], hospitals[f'{networkName} hospitals']['maxHospitals'])
        # public hospital fields:network_HPI-O,hospital_HPI-O,hospitalName,streetNo,streetName,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,businessPhone
        # private hospital fields:hospital_HPI-O,hospitalName,authority,streetNo,streetName,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,businessPhone
        for thisHospital in range(noOfHospitals):
            outputRow = [networkHPIO]
            # Assign HPI-O organization ID
            record += 1
            IHI = patients[patientKeys[record]]['IHI']
            hospitalHPIO = IHI[:5] + '2' + IHI[6:-1]
            hospitalHPIO = f'{hospitalHPIO}{mkLuhn(hospitalHPIO):d}'
            outputRow.append(hospitalHPIO)
            localSpecialists[hospitalHPIO] = {}
            localNurses[hospitalHPIO] = {}
            localGPs[hospitalHPIO] = {}
            localPatients[hospitalHPIO] = {}
            # Assign a name and select a different SA2 in this SA4
            if publicHospitalNo == len(hospitals[f'{networkName} hospitals']['hospitalNames']):
                logging.fatal(f'Insufficient hospitalNames for {networkName} network in configuration')
                logging.shutdown()
                sys.exit(EX_CONFIG)
            if publicHospitalNo == len(hospitals[f'{networkName} hospitals']['hospitalPostcodes']):
                logging.fatal(f'Insufficient hospitalPostcodes for {networkName} network in configuration')
                logging.shutdown()
                sys.exit(EX_CONFIG)
            hospitalName = hospitals[f'{networkName} hospitals']['hospitalNames'][publicHospitalNo]
            hospitalPostcode = hospitals[f'{networkName} hospitals']['hospitalPostcodes'][publicHospitalNo]
            publicHospitalNo += 1
            outputRow.append(hospitalName)
            # Create an address - check that the postcode is in our address file
            hospitalSA3 = None
            for thisSA3 in SA3postcodes:
                if hospitalPostcode in SA3postcodes[thisSA3]:
                    hospitalSA3 = thisSA3
                    break
            if hospitalSA3 is None:
                logging.fatal('Hospital postcode (%s) not in address file', hospitalPostcode)
                logging.shutdown()
                sys.exit(EX_CONFIG)
            hospitals[f'{networkName} hospitals']['hospitalSA3'].append(hospitalSA3)
            thisAddr = mkRandAddress(hospitalSA3, True, makeRandom)
            for field in addressFields:
                outputRow.append(thisAddr[field])
            for field in hospitalFields:
                outputRow.append(patients[patientKeys[record]][field])
            publicHospitals.append(outputRow)
            FHIR_Organization.append([hospitalHPIO, createOrganization(record, hospitalHPIO, networkHPIO, hospitalName, thisAddr, 'public hospital')])
            FHIR_Location.append([hospitalHPIO, createLocation(record, hospitalHPIO, hospitalName, thisAddr, networkHPIO)])

            mkDepartments(networkHPIO, hospitalHPIO, hospitalHPIO, thisAddr, hospitalName, '', True)

            # Now make the private hospitals for this local public hospital
            privateHospitalNo = 0
            localPublicHospitalHPIO = hospitalHPIO
            noOfPrivateHospitals = random.randrange(hospitals[f'{networkName} hospitals'][hospitalName]['minPrivateHospitals'], hospitals[f'{networkName} hospitals'][hospitalName]['maxPrivateHospitals'])
            for thisPrivateHospital in range(noOfPrivateHospitals):
                outputRow = [networkHPIO, localPublicHospitalHPIO]
                # Assign HPI-O organization ID
                record += 1
                IHI = patients[patientKeys[record]]['IHI']
                privateHospitalHPIO = IHI[:5] + '2' + IHI[6:-1]
                privateHospitalHPIO = f'{privateHospitalHPIO}{mkLuhn(privateHospitalHPIO):d}'
                outputRow.append(privateHospitalHPIO)
                # Assign a name and select a different SA2 in this SA4
                if privateHospitalNo == len(hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames']):
                    logging.fatal(f'Insufficient privateHospitalNames for public hospital {hospitalName} in {hospitalName} section in configuration')
                    logging.shutdown()
                    sys.exit(EX_CONFIG)
                if privateHospitalNo == len(hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalPostcodes']):
                    logging.fatal(f'Insufficient privateHospitalPostcodes for public hospital {hospitalName} in {hospitalName} section in configuration')
                    logging.shutdown()
                    sys.exit(EX_CONFIG)
                privateHospitalName = hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalNames'][privateHospitalNo]
                if privateHospitalName in createdPrivateHospitals:          # Skip if this private hospital has already been created
                    continue
                createdPrivateHospitals.add(privateHospitalName)
                privateHospitalPostcode = hospitals[f'{networkName} private hospitals'][hospitalName]['hospitalPostcodes'][privateHospitalNo]
                privateHospitalNo += 1
                outputRow.append(privateHospitalName)
                initials = privateHospitalName.split(' ')
                authority = ''
                for initial in initials:
                    authority += initial[0].upper()
                outputRow.append(authority)
                # Create an address - check that the postcode is in our address file
                privateHospitalSA3 = None
                for thisSA3 in SA3postcodes:
                    if privateHospitalPostcode in SA3postcodes[thisSA3]:
                        privateHospitalSA3 = thisSA3
                        break
                if privateHospitalSA3 is None:
                    logging.fatal('Private Hospital postcode (%s)  for Private Hospital %s not in address file', privateHospitalPostcode, privateHospitalName)
                    logging.shutdown()
                    sys.exit(EX_CONFIG)
                thisAddr = mkRandAddress(privateHospitalSA3, True, makeRandom)
                for field in addressFields:
                    outputRow.append(thisAddr[field])
                for field in hospitalFields:
                    outputRow.append(patients[patientKeys[record]][field])
                privateHospitals.append(outputRow)
                FHIR_Organization.append([privateHospitalHPIO, createOrganization(record, privateHospitalHPIO, None, privateHospitalName, thisAddr, 'private hospital')])
                FHIR_Location.append([privateHospitalHPIO, createLocation(record, privateHospitalHPIO, privateHospitalName, thisAddr, None)])

                mkDepartments(networkHPIO, localPublicHospitalHPIO, privateHospitalHPIO, thisAddr, hospitalName, privateHospitalName, False)

            # Now the local Specialty Services
            noOfSpecialistServices = random.randrange(minSpecialistServices, maxSpecialistServices)
            for thisSpecialistClinic in range(noOfSpecialistServices):
                outputRow = [networkHPIO, localPublicHospitalHPIO]
                # Consultants a have Specialist Service as their organization
                # specialist services fields:specialistService_HPI-O,specialistServiceName,serviceSpecialty,specialtyDescripion,streetNo,streetName,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,businessMobile,businessPhone,businessEmail
                record += 1
                IHI = patients[patientKeys[record]]['IHI']
                specialistServiceHPIO = IHI[:5] + '2' + IHI[6:-1]
                specialistServiceHPIO = f'{specialistServiceHPIO}{mkLuhn(specialistServiceHPIO):d}'
                careTeams[specialistServiceHPIO] = set()
                outputRow.append(specialistServiceHPIO)
                uniqueName = False
                while not uniqueName:
                    # Create a local address close to this hospital
                    thisAddr = mkRandAddress(hospitalSA3, True, makeRandom)
                    # Assign a business name being "suburb specialty services"
                    # Pick a specialty
                    specialty = random.choice(list(SpecialistRoles))
                    # Create the Service Name
                    name = thisAddr['suburb'] + ' ' + HealthcareRoles[SpecialistRoles[specialty][1]]
                    if name not in usedSpecServiceNames:
                        uniqueName = True
                        usedSpecServiceNames.add(name)
                outputRow.append(name)
                initials = name.split(' ')
                authority = ''
                for initial in initials:
                    authority += initial[0].upper()
                outputRow.append(authority)
                outputRow.append('PAS')
                # Add the specialty
                outputRow.append(specialty)
                outputRow.append(Specialties[specialty])
                businessPhone = patients[patientKeys[record]]['businessPhone']
                # Add the address
                for field in addressFields:
                    outputRow.append(thisAddr[field])
                for field in clinicFields:
                    outputRow.append(patients[patientKeys[record]][field])
                specialistServices.append(outputRow)
                FHIR_Organization.append([specialistServiceHPIO, createOrganization(record, specialistServiceHPIO, None, name, thisAddr, 'specialist')])
                FHIR_Location.append([specialistServiceHPIO, createLocation(record, specialistServiceHPIO, name, thisAddr, None)])
                FHIR_HealthcareService.append([specialistServiceHPIO, createHealthcareService(record, specialistServiceHPIO, name, 'specialist', specialty)])

                # Now output the Specialist
                # specialists fields:specialistService_HPI-O,specialistSpecialty,specialtyDescripion,role,roleDescription,HPI-I,providerNo,title,familyName,givenName,birthdate,sex
                clinicSpecialists = set()               # Can't have two records for the same specialist in this clinic
                noOfSpecialists = random.randrange(minSpecialists, maxSpecialists)
                for thisSpecialist in range(noOfSpecialists):       # Give each specalist clinic between 1 and 5 specialists
                    outputRow = [networkHPIO, localPublicHospitalHPIO, specialistServiceHPIO]
                    specialistHPII = None
                    providerNo = None
                    prescriberNo = None
                    ahpraNo = None
                    avaliableSpecialists = set(localSpecialists[localPublicHospitalHPIO].keys()) - clinicSpecialists
                    if (len(avaliableSpecialists) > 20) and (random.random() < 0.3):
                        thisRecord = random.choice(list(avaliableSpecialists))
                        specialistHPII = localSpecialists[localPublicHospitalHPIO][thisRecord]['HPI-I']
                        prescriberNo = localSpecialists[localPublicHospitalHPIO][thisRecord]['prescriberNo']
                        providerNo = localSpecialists[localPublicHospitalHPIO][thisRecord]['providerNo']
                        usedProviderNo[providerNo] += 1
                        if usedProviderNo[providerNo] == 30:
                            providerNo = None
                        ahpraNo = localSpecialists[localPublicHospitalHPIO][thisRecord]['ahpraNo']
                    else:
                        record += 1
                        thisRecord = record
                        localSpecialists[localPublicHospitalHPIO][thisRecord] = {}
                    clinicSpecialists.add(thisRecord)
                    if specialistHPII is None:
                        IHI = patients[patientKeys[thisRecord]]['IHI']
                        specialistHPII = IHI[:5] + '1' + IHI[6:-1]
                        specialistHPII = f'{specialistHPII}{mkLuhn(specialistHPII):d}'
                        localSpecialists[localPublicHospitalHPIO][thisRecord]['HPI-I'] = specialistHPII
                    if specialistHPII not in practitionerDetails:
                        practitionerDetails[specialistHPII] = {}
                        practitionerDetails[specialistHPII]['providerNos'] = []
                        practitionerDetails[specialistHPII]['record'] = thisRecord
                    careTeams[specialistServiceHPIO].add(specialistHPII)
                    outputRow.append(specialistHPII)
                    outputRow.append(specialty)
                    outputRow.append(Specialties[specialty])
                    role = SpecialistRoles[specialty][0]
                    outputRow.append(role)
                    outputRow.append(Roles[role])
                    if providerNo is None:
                        while True:        # Loop if the providerNo is not distinct
                            providerNo = f'{random.randint(100000, 999999):06d}'
                            if providerNo not in usedProviderNo:
                                break
                            logging.debug('Searching for a free provider number for a specialist')
                        usedProviderNo[providerNo] = 0
                        localSpecialists[localPublicHospitalHPIO][thisRecord]['providerNo'] = providerNo
                    practitionerDetails[specialistHPII]['providerNos'].append(mkProviderNo(providerNo))
                    outputRow.append(mkProviderNo(providerNo))
                    if prescriberNo is None:
                        prescriberNo = mkPrescriberNo(providerNo)
                        localSpecialists[localPublicHospitalHPIO][thisRecord]['prescriberNo'] = prescriberNo
                    if 'prescriberNo' not in practitionerDetails[specialistHPII]:
                        practitionerDetails[specialistHPII]['prescriberNo'] = prescriberNo
                    outputRow.append(prescriberNo)
                    if ahpraNo is None:
                        while True:        # Loop if the ahpraNo is not distinct
                            ahpraNo = random.randint(9000000000, 9999999999)
                            if ahpraNo not in usedAhpraNo:
                                break
                            logging.debug('Searching for a free AHPRA number for a specialist')
                        usedAhpraNo.add(ahpraNo)
                        localSpecialists[localPublicHospitalHPIO][thisRecord]['ahpraNo'] = ahpraNo
                    if 'ahpraNo' not in practitionerDetails[specialistHPII]:
                        practitionerDetails[specialistHPII]['ahpraNo'] = ahpraNo
                    outputRow.append('MED' + str(ahpraNo))
                    if patients[patientKeys[thisRecord]]['sex'] == 'F':
                        title = 'Ms.'
                    else:
                        title = 'Mr.'
                    outputRow.append(title)
                    patients[patientKeys[thisRecord]]['businessPhone'] = businessPhone
                    # And the Dr fields
                    for field in drFields:
                        outputRow.append(patients[patientKeys[thisRecord]][field])
                    specialists.append(outputRow)
                    PRD = 'PRD||' + patients[patientKeys[thisRecord]]['familyName'] + '^' + patients[patientKeys[thisRecord]]['givenName'] + '^^^DR^^L'            # PRD-2 Provider Name
                    PRD += '|' + thisAddr['streetNo'] + ' ' + thisAddr['streetName'] + ' ' + thisAddr['streetType']
                    PRD += '^^' + thisAddr['suburb'] + '^' + thisAddr['state'] + '^' + thisAddr['postcode'] + '^AUS^M'   # PRD-3 Provider Address
                    PRD += '||^PRN^PH^^^^^^' + patients[patientKeys[thisRecord]]['homePhone']
                    PRD += '~^PRN^CP^^^^^^' + patients[patientKeys[thisRecord]]['mobile']
                    PRD += '~^NET^Internet^' + patients[patientKeys[thisRecord]]['email']
                    PRD += '~^WPN^PH^^^^^^' + patients[patientKeys[thisRecord]]['businessPhone']            # PRD-5 home phone, mbile, email, business phone
                    PRD += '||' + mkProviderNo(providerNo) + '^AUSHICPR^UPIN'
                    PRD += '~' + prescriberNo + '^AUSHIC^NPI'                                 # PRD-7 Provider identifiers
                    PRDrow = []
                    PRDrow.append(specialistHPII)
                    PRDrow.append(PRD)
                    HL7_PRD.append(PRDrow)
                    FHIR_PractitionerRole.append([specialistHPII, createPractitionerRole(thisRecord, specialistServiceHPIO, specialistHPII, role, specialty)])

            # Now do the local GP clinics for this local public hospital
            noOfGPclinics = random.randrange(minClinics, maxClinics)
            # clinics fields:clinic_HPI-O,clinicName,authority,application,clinicSpecialty,specialtyDescription,streetNo,streetName,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,businessPhone,email])
            for thisClinic in range(noOfGPclinics):
                outputRow = [networkHPIO, localPublicHospitalHPIO]
                # HPI-O as the organization ID
                record += 1
                IHI = patients[patientKeys[record]]['IHI']
                gpClinicHPIO = IHI[:5] + '2' + IHI[6:-1]
                gpClinicHPIO = f'{gpClinicHPIO}{mkLuhn(gpClinicHPIO):d}'
                careTeams[gpClinicHPIO] = set()
                outputRow.append(gpClinicHPIO)
                uniqueName = False
                while not uniqueName:
                    # Create a local address close to this hospital
                    clinicAddr = mkRandAddress(hospitalSA3, True, makeRandom)
                    # Create a clinic from street or suburb plus Medical/Medical Clinic/Medical Centre
                    if random.random() < 0.7:            # street or suburb
                        clinicName = clinicAddr['streetName'] + ' ' + clinicAddr['streetType']
                    else:
                        clinicName = clinicAddr['suburb']
                    clinicName += ' Medical'
                    if random.random() < 0.4:            # Clinic or Centre or nothing
                        clinicName += ' Clinic'
                    elif random.random() < 0.4:            # Clinic or Centre or nothing
                        clinicName += ' Centre'
                    if clinicName in usedGPclinicNames:
                        logging.debug('Searching of an unused GP clinic name - %s is not unique', clinicName)
                        continue
                    usedGPclinicNames.add(clinicName)
                    uniqueName = True
                    outputRow.append(clinicName)
                initials = clinicName.split(' ')
                authority = ''
                for initial in initials:
                    authority += initial[0].upper()
                outputRow.append(authority)
                outputRow.append('PAS')
                outputRow.append('408443003')
                outputRow.append('General medical practice')
                clinicPhone = patients[patientKeys[record]]['businessPhone']
                for field in addressFields:
                    outputRow.append(clinicAddr[field])
                # And the clinic specific fields
                for field in clinicFields:
                    outputRow.append(patients[patientKeys[record]][field])
                gpClinics.append(outputRow)
                FHIR_Organization.append([gpClinicHPIO, createOrganization(record, gpClinicHPIO, None, clinicName, clinicAddr, 'clinic')])
                FHIR_Location.append([gpClinicHPIO, createLocation(record, gpClinicHPIO, clinicName, clinicAddr, None)])
                FHIR_HealthcareService.append([gpClinicHPIO, createHealthcareService(record, gpClinicHPIO, clinicName, 'clinic', '408443003')])

                # Now the clinic doctors and their patients
                noOfDoctors = random.randrange(minDr, maxDr)
                clinicGPs = set()               # Cannot have the same GP as two records in the one clinic
                for thisDoctor in range(noOfDoctors):
                    # clinic Staff fields:clinic_HPI-O,staffSpecialty,specialtyDescripion,role,roleDescription,HPI-I,providerNo,title,familyName,givenName,birthdate,sex,workMobile,businessPhone,workEmail
                    outputRow = [networkHPIO, localPublicHospitalHPIO, gpClinicHPIO]
                    gpHPII = None
                    providerNo = None
                    prescriberNo = None
                    ahpraNo = None
                    availableGPs = set(localGPs[localPublicHospitalHPIO].keys()) - clinicGPs
                    if (len(availableGPs) > 20) and (random.random() < 0.2):  # 20% chance to pick from available GPs
                        thisRecord = random.choice(list(availableGPs))
                        gpHPII = localGPs[localPublicHospitalHPIO][thisRecord]['gpHPII']
                        providerNo = localGPs[localPublicHospitalHPIO][thisRecord]['providerNo']
                        usedProviderNo[providerNo] += 1
                        if usedProviderNo[providerNo] == 30:
                            providerNo = None
                        prescriberNo = localGPs[localPublicHospitalHPIO][thisRecord]['prescriberNo']
                        ahpraNo = localGPs[localPublicHospitalHPIO][thisRecord]['ahpraNo']
                    else:
                        record += 1
                        thisRecord = record
                        localGPs[localPublicHospitalHPIO][thisRecord] = {}
                    clinicGPs.add(thisRecord)
                    if gpHPII is None:
                        IHI = patients[patientKeys[thisRecord]]['IHI']
                        gpHPII = IHI[:5] + '1' + IHI[6:-1]
                        gpHPII = f'{gpHPII}{mkLuhn(gpHPII):d}'
                        localGPs[localPublicHospitalHPIO][thisRecord]['gpHPII'] = gpHPII
                    if gpHPII not in practitionerDetails:
                        practitionerDetails[gpHPII] = {}
                        practitionerDetails[gpHPII]['providerNos'] = []
                        practitionerDetails[gpHPII]['record'] = thisRecord
                    careTeams[gpClinicHPIO].add(gpHPII)
                    outputRow.append(gpHPII)
                    # Pick a specialty
                    specialty = random.choice(list(GPspecialties))
                    outputRow.append(specialty)
                    outputRow.append(Specialties[specialty])
                    role = GPspecialties[specialty]
                    outputRow.append(role)
                    outputRow.append(Roles[role])
                    # Doctors have their own HPI-I codes
                    if providerNo is None:
                        while True:        # Loop if the providerNo is not distinct
                            providerNo = f'{random.randint(100000, 999999):06d}'
                            if providerNo not in usedProviderNo:
                                break
                            logging.debug('Searching for a free provider number for a GP')
                        usedProviderNo[providerNo] = 0
                        localGPs[localPublicHospitalHPIO][thisRecord]['providerNo'] = providerNo
                    practitionerDetails[gpHPII]['providerNos'].append(mkProviderNo(providerNo))
                    outputRow.append(mkProviderNo(providerNo))
                    if prescriberNo is None:
                        prescriberNo = mkPrescriberNo(providerNo)
                        localGPs[localPublicHospitalHPIO][thisRecord]['prescriberNo'] = prescriberNo                    
                    practitionerDetails[gpHPII]['prescriberNo'] = prescriberNo
                    outputRow.append(prescriberNo)
                    if ahpraNo is None:
                        while True:        # Loop if the ahpraNo is not distinct
                            ahpraNo = random.randint(9000000000, 9999999999)
                            if ahpraNo not in usedAhpraNo:
                                break
                            logging.debug('Searching for a free AHPRA number for a GP')
                        usedAhpraNo.add(ahpraNo)
                        localGPs[localPublicHospitalHPIO][thisRecord]['ahpraNo'] = ahpraNo
                    practitionerDetails[gpHPII]['ahpraNo'] = ahpraNo
                    outputRow.append('MED' + str(ahpraNo))
                    outputRow.append('Dr.')
                    patients[patientKeys[thisRecord]]['businessPhone'] = clinicPhone
                    # And the Dr fields
                    for field in drFields:
                        outputRow.append(patients[patientKeys[thisRecord]][field])
                    gpClinicStaff.append(outputRow)
                    PRD = 'PRD||' + patients[patientKeys[thisRecord]]['familyName'] + '^' + patients[patientKeys[thisRecord]]['givenName'] + '^^^DR^^L'            # PRD-2 Provider Name
                    PRD += '|' + clinicAddr['streetNo'] + ' ' + clinicAddr['streetName'] + ' ' + clinicAddr['streetType']
                    PRD += '^^' + clinicAddr['suburb'] + '^' + clinicAddr['state'] + '^' + clinicAddr['postcode'] + '^AUS^M'   # PRD-3 Provider Address
                    PRD += '||^PRN^PH^^^^^^' + patients[patientKeys[thisRecord]]['homePhone']
                    PRD += '~^PRN^CP^^^^^^' + patients[patientKeys[thisRecord]]['mobile']
                    PRD += '~^NET^Internet^' + patients[patientKeys[thisRecord]]['email']
                    PRD += '~^WPN^PH^^^^^^' + patients[patientKeys[thisRecord]]['businessPhone']            # PRD-5 home phone, mbile, email, business phone
                    PRD += '||' + mkProviderNo(providerNo) + '^AUSHICPR^UPIN'
                    PRD += '~' + prescriberNo + '^AUSHIC^NPI'                                 # PRD-7 Provider identifiers
                    PRDrow = []
                    PRDrow.append(gpHPII)
                    PRDrow.append(PRD)
                    HL7_PRD.append(PRDrow)
                    FHIR_PractitionerRole.append([gpHPII, createPractitionerRole(thisRecord, gpClinicHPIO, gpHPII, role, specialty)])

                    # And finally the patients for this GP and the patient's careteam
                    if Patients:
                        # patients fields:clinic_HPI-O,GP_HPI-I,IHI,title,familyName,givenName,birthdate,sex,streetNo,streetName,shortStreetType,suburb,state,postcode,longitude,latitude,meshblock,sa1,country,mobile,homePhone,businessPhone,email,medicareNo,dvaNo,dvaType,height,weight,waist,hips,married,race
                        noOfPatients = random.randrange(minPatients, maxPatients)
                        gpPatients = set()              # Can't have two records for the same patient for this GP
                        for thisPatient in range(noOfPatients):
                            patientIHI = None
                            availablePatients = set(localPatients[localPublicHospitalHPIO].keys()) - gpPatients
                            if (len(availablePatients) > 20) and (random.random() < 0.1):
                                thisRecord = random.choice(list(availablePatients))
                                patientIHI = localPatients[localPublicHospitalHPIO][thisRecord]['Patient IHI']
                            else:
                                newPatient = True
                                record += 1
                                thisRecord = record
                                # Create a local address close to this patient
                                patientAddr = mkRandAddress(hospitalSA3, True, makeRandom)
                                for field in patientAddr:
                                    patients[patientKeys[thisRecord]][field] = patientAddr[field]
                                PIDsegment = patients[patientKeys[thisRecord]]['PID']
                                PIDfields = PIDsegment.split('|')
                                # Update the address (PID-11)
                                PIDfields[11] = f"{patientAddr['streetNo']} {patientAddr['streetName']} {patientAddr['shortStreetType']}^^{patientAddr['suburb']}^{patientAddr['state']}^{patientAddr['postcode']}^AUS^M"
                                patients[patientKeys[thisRecord]]['PID'] = '|'.join(PIDfields)
                                # Update LIS2 P-11
                                Psegment = patients[patientKeys[thisRecord]]['LIS2']
                                Pfields = Psegment.split('|')
                                Pfields[10] = f"{patientAddr['streetNo']} {patientAddr['streetName']} {patientAddr['shortStreetType']}^{patientAddr['suburb']}^{patientAddr['state']}^{patientAddr['postcode']}^AUS"
                                patients[patientKeys[thisRecord]]['LIS2'] = '|'.join(Pfields)
                                localPatients[localPublicHospitalHPIO][thisRecord] = {}
                            gpPatients.add(thisRecord)
                            if patientIHI is None:
                                patientIHI = patients[patientKeys[thisRecord]]['IHI']
                                localPatients[localPublicHospitalHPIO][thisRecord]['Patient IHI'] = patientIHI
                            PIDrow = []
                            PIDrow.append(patientIHI)
                            thisPID = patients[patientKeys[thisRecord]]['PID']
                            PIDrow.append(thisPID)
                            HL7_PID.append(PIDrow)
                            Prow = []
                            Prow.append(patientIHI)
                            thisLIS2 = patients[patientKeys[thisRecord]]['LIS2']
                            Prow.append(thisLIS2)
                            LIS2_P.append(Prow)
                            if patientIHI not in patientDetails:
                                patientDetails[patientIHI] = {}
                                patientDetails[patientIHI]['GPs'] = []
                            patientDetails[patientIHI]['record'] = thisRecord
                            outputRow = [networkHPIO, localPublicHospitalHPIO, gpClinicHPIO, gpHPII, patientIHI]
                            for field in patientFields1:
                                outputRow.append(patients[patientKeys[thisRecord]][field])
                            for field in addressFields:
                                outputRow.append(patients[patientKeys[thisRecord]][field])
                            for field in patientFields2:
                                outputRow.append(patients[patientKeys[thisRecord]][field])
                            clinicPatients.append(outputRow)
                            patientDetails[patientIHI]['GPs'].append(gpHPII + '-' + gpClinicHPIO)
                            FHIR_CareTeam.append([patientIHI, gpClinicHPIO, createCareTeam(thisRecord, patientIHI, gpClinicHPIO)])

    # Then the FHIR details
    for HPII, details in practitionerDetails.items():
        thisRecord = details['record']
        providerNos = details['providerNos']
        prescriberNo = details['prescriberNo']
        ahpraNo = details['ahpraNo']
        FHIR_Practitioner.append([HPII, createPractitioner(thisRecord, HPII, providerNos, prescriberNo, ahpraNo)])

    if Patients:
        for patientIHI, IHIdetails in patientDetails.items():
            thisRecord = IHIdetails['record']
            GPs = IHIdetails['GPs']
            FHIR_Patient.append([patientIHI, createPatient(thisRecord, patientIHI, GPs)])

    # Then template for department care teams
    for deptHPIO in deptHPIOs:
        FHIR_CareTeam.append(['ReplaceWithIHI', deptHPIO, createCareTeam(None, 'ReplaceWithIHI', deptHPIO)])

    for thisSheet in sheets:
        ws = wb[thisSheet]
        column_widths = []
        for row in ws.iter_rows():
            for i, cell in enumerate(row):
                if len(column_widths) <= i:
                    column_widths.append(0)
                if cell.value:
                    column_widths[i] = max(column_widths[i], len(str(cell.value)))
        for i, column_width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = column_width

    wb.save(os.path.join(outputDir, outputfile))
    logging.shutdown()
    sys.exit(EX_OK)
