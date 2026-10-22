# mkHealth_Population-Australia

Create test demographic data representing the Australian healthcare ecosystem

## The scripts and data in this repository create test demographic data

* Boys names (1.2K) and girls names (4.3K) are taken from lists that include the frequency of occurance
* Surnames are selected from a list of 382K Australian surnames that inclukde the frequency of occurence.
* Addresses are taken from the Australian Geocoded National Address File (G-NAF)
  * [G-NAF Core](https://geoscape.com.au/data/g-naf-core/) © [Geoscape Australia](https://geoscape.com.au/) 2023 Copyright and Disclaimer Notice. Licensed by Geoscape Australia under the Open G-NAF Core [End User Licence Agreement](https://geoscape.com.au/wp-content/uploads/2022/08/EULA-G-NAF-Core-1.pdf).
* Administrative sex is derived from whether a boys name or a girls name is randomly selected
* Birthdate is randomly selected
* Height, weight and hips measurements are randomly selected from percentiles based upon age

G-NAF Core can be downloaded from [Australian Government Data website](https://data.gov.au/search?q=G-NAF)

## selectGNAF.py

Not all the data in G-NAF Core is required for this project. The script **selectGNAF.py** can read in G-NAF Core (GNAF_CORE.psv) and output a smaller file of just the required columns.

Often you only need a small data set, so there is no point is selecting from the whole of G-NAF Core; a subset will suffice. And sometimes you only want addresses from a particular state or territory and a subset of G-NAF Core, containing only the addresses from that state or territory will suffice.

**selectGNAF.py** lets you select subsets of G-NAF Core [GNAF_CORE.psv] or a subset of a subset of G-NAF Core that has already been created by **selectGNAF.py**. [A good strategy is to run **selectGNAF.py** on G-NAF CORE, with no options selected, to create a cutdown version. You can then use that cutdown version to create specific subsets]

    $ python3 selectGNAF.py -h
    usage: selectGNAF.py [-h] [-I GNAFINPUTFILE] -O GNAFOUTPUTFILE
                     [-n NOOFADDRESSES] [-s STATES] [-v {0,1,2,3,4}]
                     [-o logfile]

This repository includes some subsets, created using **selectGNAF.py**, from the Febrary 2023 release of G-NAF Core.

## mkPMI

The simplest starting point is to create a list of test patients using **mkPMI.py** which create patient where all the patients have Australian addreses and all of the Australian health idenifiers (Medicare number, DVA number, IHI etc).
**mkPMI.py** tries to reflect the internals of a Patient Master Index (PMI). Each patient has a UR(MRN) number. By default these are unique. However **mkPMI.py** has an options for creating multiple patients with the same UR; just in case you are looking to create test data for testing an Enterprise Master Patient Index (EMPI) application or a PMI Consolidation solution. **mkPMI.py** also has options to create alias and merged patient. For merged patients the 'Merged' column will contain the UR number of the 'merged to' patient (the real patient). For Aliases, the 'Alias' column will contain the UR number of the real patient. To support these concepts, each row of data has a unique Person Identification Number (PID). The concept here is that a new name is created with a PID and a UR, but new clinical/administrative data (admission/encounters) are store against the PID. The UR can change with merges, updates etc. The holistic view of the patient's data is linked to the set of PIDs, which are linked to the primary PMI record.

## mkAltPMI

**mkAltPMI.py** extends the concept of creating test data for testing an Enterprise Master Patient Index (EMPI) application of a PMI Consolidation solution.
**mkAltPMI.py** takes a list of patient created by **mkPMI.py** and creates an 'enhanced' subset; some patients from the original list and some new ones. This is mean to reflect data from a departmental application, which is not integrated with the main Patient Administration System (PAS). Patients created in departmental systems can relect patients in the PAS, possibly with spelling error, address errors, birthdate errors etc. And the UR(MRN) from the PAS is often recorded as an althernate UR number, with the usual typing errors and digital dislexia. **mkPMIAltUR.py** can be configured to create numerous different errors, intended to challenge any EMPI/PMI Consolidation solution.

## mkHealthPopulation

**mkHealthPopulation.py** extends this concept further, creating test data for Health Care Networks, associated public hospital and associated private hospitals. All hospital have departments, with staff (doctors and nurses). The output format is an Excel workbook, with spreadsheets for 'Health Networks', 'Public Hospitals', 'Public Hospital Departments', 'Public Hospital Staff', 'Private Hospitals', 'Private Hospital Departments', 'Private Hospital Staff', 'GP Clinics', 'GP Clinic Staff', 'Specialist Services', 'Specialists' and 'Patients'. There is also structured data for common use cases for this data. The 'HL7_PID' worksheet contains an HL7 PID segment for each patient in the 'Patients' worksheet. All the patient identifiers are encoded in PID-3, but the 'MR' value, if required, has to be assigned from the context in which the PID segment is being used. To accomodate this there can be in the an 'MR' repetition in PID-3 with two templates, being "\<UR\>" and "\<AUTH\>" which must be replace with the UR number for this patient and the assigning authority code. The 'Heath Networks' worksheet has an 'authroity' code for each Heathcare Network on the assumption that all public hospitals in the Healthcare Network are using the same Patient Master Index (PMI). The 'Private Hospitals', 'Specialist Services' and 'GP Clinic' worksheets also contain an 'authority' code. The 'LIS2_P' worksheet contains a LIS-2 'P' segment for each patient, for test messages to laboratory systems that use the LIS-2 (ASTM E1395) messaging standard. Again, there can be a template of "\<UR\>" which must be replace with the patient's UR number for this patient.

Tge 'HL7_PRD' worksheet contains an HL7 PRD segment for each clinician. There are also spreadsheets of HL7 FHIR structures for each associated FHIR resource - 'Organization', 'HealthcareService', 'Location', 'Practitioner', 'PractitionerRole' and 'Patient'. There are also 'CareTeam' HL7 FHIR resources; all the staff in each clinic are a care team for each patient who attends the clinic. There are also 'template' CareTeam resources; one for each set of all staff in each hospital deparment. However, these will only be come care teams when a patient is addmitted to the associated department. Hence, the specific patient details are "templated" with 'ReplaceWithIHI', 'ReplaceWithGivenName' and 'ReplaceWithFamilyName'.

The 'healthPopulation.xlsx' workbook can be read in Python using the 'openpyxl' module.

    from openpyxl import load_workbook
    wb = load_workbook('healthPopulation.xlsx')

Each worksheeet can then be read using the following code template

    ws = wb['XXX']
    data =  ws.iter_rows(values_only=True)
    headings = next(data)
    for row in data:
      if row[0] is None:              # End of worksheet
        break
      thisDict = dict(zip(headings, row))     # This row of data as a dictionary

You can then build your data model to your particular requirements. For instance, for Patients you could create a Patients{} where the key is the Patient's IHI.

    Patients = {}
    ws = wb['Patients']
    data =  ws.iter_rows(values_only=True)
    headings = next(data)
    for row in data:
      if row[0] is None:              # End of the Patients worksheet
        break
      thisPatient = dict(zip(headings, row))     # This row of Patient data as a dictionary
      thisPatientIHI = thisPatient['Patient IHI']
      Patients[thisPatientIHI] = thisPatient
  
However, a patient may occur more than once, with the same IHI, in the Patients worksheet. The first four columns of the Patients worksheet are 'Network HPI-O', 'Local Public Hospital HPI-O', 'GP Clinic HPI-O' and 'GP HPI-I'. The last two columns define the patient's attendance at a specific GP Clinic to see a specific GP. Patient's can attend multiple clinics and can see multiple GPs in each attended clinic. The remaining columns in the Patients worksheet will be unchanged for a given 'Patient IHI'. Hence, a more complete data model might be ...

    Patients = {}
    ws = wb['Patients']
    data =  ws.iter_rows(values_only=True)
    headings = next(data)
    for row in data:
        if row[0] is None:              # End of the Patients worksheet
            break
        thisPatient = dict(zip(headings, row))     # This row of Patient data as a dictionary
        thisPatientIHI = thisPatient['Patient IHI']
        if thisPatientIHI not in Patients:
            thisPatient['attended'] = []
            Patients[thisPatientIHI] = thisPatient
      Patients[thisPatientIHI]['attended'].append([thisPatient['GP Clinic HPI-O'], thisPatient['GP HPI-I']])

Similarly, hospital staff can work in multiple departments and at one public hospital and multiple departments at zero or more public hospitals.
Hence, an 'Staff HPI-I' value may occur multiple times in the 'xxx Staff' worksheets, but each time with a different/unique 'Provider No'.
Also, public hospital doctor can work in one public hospital, multiple departments in zero or more private hospitals and zero or more Specialist Services.
Again, an 'HPI-I' value may occur multiple times in the 'xxx Staff' worksheets and the 'Specialists' worksheet,
but each time with a different/unique 'Provider No'.
And GPs can work in mulitple GP clinicls, so a 'GP HPI-I' may occur multiple times in the 'GP Staff' worksheet,
but each time with a different/unique 'Provider No.'

## mkHL7v2

**mkHL7v2.py** builds on the output of **mkHealthPopulation.py**. It reads a health population workbook and creates, for each patient, a set of HL7 ADT messages; A27-Add person information, A01-Admit/visit notification, A08-Update patient information (for a ward transfers) and A03-Discharge/end visit. **mkHL7v2.py** is an example of what can be done with a health population.

Incorporates or developed using [G-NAF Core](https://geoscape.com.au/data/g-naf-core/) © [Geoscape Australia](https://geoscape.com.au/) 2023 Copyright and Disclaimer Notice. Licensed by Geoscape Australia under the Open G-NAF Core [End User Licence Agreement](https://geoscape.com.au/wp-content/uploads/2022/08/EULA-G-NAF-Core-1.pdf).
