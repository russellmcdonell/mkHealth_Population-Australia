# mkHealth_Population-Australia
Create test demographic data representing the Australian healthcare ecosystem

## The scripts and data in this repository create test demographic data.
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
The simplest starting point is to create a list of test patients using **mkPMI**

<br/><br/>
Incorporates or developed using [G-NAF Core](https://geoscape.com.au/data/g-naf-core/) © [Geoscape Australia](https://geoscape.com.au/) 2023 Copyright and Disclaimer Notice. Licensed by Geoscape Australia under the Open G-NAF Core [End User Licence Agreement](https://geoscape.com.au/wp-content/uploads/2022/08/EULA-G-NAF-Core-1.pdf).