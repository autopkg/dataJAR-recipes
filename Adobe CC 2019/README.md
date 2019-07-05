# Import Adobe CC 2019 Title

## About
These recipes are based on: https://github.com/autopkg/adobe-ccp-recipes

But with the death of Creative Cloud Packager (https://macmule.com/2018/10/15/adobe-creative-cloud-2019-the-death-of-creative-cloud-packager-device-licensing/), have been rejigged to work with locally downloaded pkg's.

## Pre-reqs

1. Download the wanted Adobe CC 2019 Titles to your ~/Downloads folder from the Adobe Admin Console, with the naming convention of:

• Adobe*AppName*CC2019

For example:

AdobeAcrobatDCCC2019    
AdobeAfterEffectsCC2019    
AdobeAnimateCC2019    
AdobeAuditionCC2019    
AdobeBridgeCC2019    
AdobeCharacterAnimatorCC2019    
AdobeDimensionCC2019    
AdobeDreamweaverCC2019    
AdobeIllustratorCC2019    
AdobeInCopyCC2019    
AdobeInDesignCC2019    
AdobeLightroomCC2019    
AdobeLightroomClassicCC2019    
AdobeMediaEncoderCC2019    
AdobePhotoshopCC2019    
AdobePreludeCC2019    
AdobePremiereProCC2019    
AdobePremiereRushCC2019    
AdobeXDCC2019

These will need to be unzipped, if your browser does not unzip the downloads from the Adobe Admin Console.

2. Create the respective munki or jss recipe overrides, & name them the same as the Adobe CC 2019 pkg.

For example:

`AdobeAcrobatDCCC2019.jss.recipe`
`AdobeAcrobatDCCC2019.munki.recipe`

## Usage
With the pre-reqs met, you can run the [AdobeCC2019Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20CC%202019/AdobeCC2019Importer.py) script found in this repo.

You will need to pass to [AdobeCC2019Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20CC%202019/AdobeCC2019Importer.py) the recipe type, which would be either jss or munki.

For example:

`/path/to/AdobeCC2019Importer.py jss` or `/path/to/AdobeCC2019Importer.py munki`

## Process
[AdobeCC2019Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20CC%202019/AdobeCC2019Importer.py) will:

1. Check the running users ~/Downloads folder for folders matching the pattern: Adobe\*CC2019, exiting if nothing found.
2. Creates an empty recipe list at ~/Downloads/adobecc2019_list.txt
3. Check that the Adobe&ast;CC2019 folders contain an sub directory called Build containing a pkg called \*\_Install.pkg, skipping this pkg if not found.
4. If step 3 passes for a pkg, next we look for an override named Adobe\*CC2019.jss.recipe or Adobe\*CC2019.munki.recipe (depending on what option was passed to [AdobeCC2019Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20CC%202019/AdobeCC2019Importer.py), skipping this pkg if not found.
5. If step 4 is successful, the Override added to the ~/Downloads/adobecc2019_list.txt recipe list. Steps 3-5 are repeated for all Adobe&ast;CC2019 folders found within ~/Downloads.
6. If any items are added to the ~/Downloads/adobecc2019_list.txt recipe list, this is then ran with a report written to ~/Downloads/adobecc2019_report.plist

## Note
You should be able to periodically downloaded updated packages from the Adobe Admin Console & then run [AdobeCC2019Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20CC%202019/AdobeCC2019Importer.py).

With [AdobeCC2019Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%20CC%202019/AdobeCC2019Importer.py) only importing items which are newer than you have within your JPS or Munki repo.







