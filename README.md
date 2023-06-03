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

Not all the data in G-NAF CORE is required for this project. The smaller file 'smallGNAM_CORE.psv' contains just the columns of data that are required.


<br/><br/>
Incorporates or developed using [G-NAF Core](https://geoscape.com.au/data/g-naf-core/) © [Geoscape Australia](https://geoscape.com.au/) 2023 Copyright and Disclaimer Notice. Licensed by Geoscape Australia under the Open G-NAF Core [End User Licence Agreement](https://geoscape.com.au/wp-content/uploads/2022/08/EULA-G-NAF-Core-1.pdf).