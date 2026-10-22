# mkHealth Population-Australia

## Version 2.0 - 15-Oct-2026

**Major data model change - some worksheet names have changed, many column names have changed**.  

Healthcare Networks have public hospitals. Each public hospital is now the hub of a local community of healthcare services, being zero or more local private hospital, zero or more local Specialist Services and zero or more local GP clinics with Patients, all in the same geographical area. Private Hospitals, Specialist Services and GP clinics all have a column of 'Local Public Hospital HPI-O' which is the only common linkage. GPs, looking for a local Specialist must choose a Specialist Service with a matching 'Local Public Hospital HPI-O' key.

* Made extendNames a choice of two sequential letters or three digits
* Added postcodes for healthcare networks
* Changed 'associated' to '{networkName} hospitals' - now each healthcare network has a set of named associated public hospitals, each with it's own configuration. The same hospital name can not exist in two or more healthcare networks.
If healthcare networks 'A' and 'B' both have '**Childrens Hospital**' then you have to give them different names e.g. '**Childrens Hospital(A)**' and '**Childrens Hospital(B)**'
* Changed 'private' to '{networkName} private hospitals' and move 'privateHospitalNames' and 'privateHospitalPostcode' from the network level to each public hospital configuration. Now each public hospital becomes the "local public hospital" for the private hospitals, the GP clinics and the local specialist services. The same hospital name can not exist in two or more healthcare networks. If healthcare networks have 'A' and 'B' both have private hospitals named 'Ramsay Health Care' then you have to give them differen names e.g. '**Ramsay Health Care (A)**' and '**Ramsay Health Care (B)**'.
* Allowed hospital staff to work in more than one department within a hospital and to work in more than one local public or private hospital. (Each HPI-I may exist multiple times in multiple worksheets).
* Allowed doctors to work in specialist services and public hospitals and private hospitals. (Each HPI-I may exist multiple times in multiple worksheetes).
* Allowed patients to attend more than one GP Clinic and see more than one GP. (Each 'Patient IHI' may exist multiple time in the 'Patients' worksheet)

## Version 1.6 - 22-Sep-2026

* Fixed bug in Medicare Provider number
* Added column heading configuration

## Version 1.5 - 05-Jan-2026

* Upgraded FHIR resources in mkHealthPopulation to FHIR R5

## Version 1.4 - 16-Oct-2023

* Added FHIR resources to mkHealthPopulation

## Version 1.3 - 21-Sep-2023

* Added mkHealthPopulation
* Added mkHL7v2

## Version 1.2 - 14-Aug-2023

* Added selectGNAF (for subset of addresses)

## Version 1.1 - 08-May-2023

* Added mkPMI

## Version 1.0 - 06-May-2023

* Initial version
