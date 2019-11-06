# Import Adobe 2020 Title

## About
These recipes are based on: https://github.com/autopkg/adobe-ccp-recipes

But with the death of Creative Cloud Packager (https://macmule.com/2018/10/15/adobe-creative-cloud-2019-the-death-of-creative-cloud-packager-device-licensing/), have been rejigged to work with locally downloaded pkg's.

## Pre-reqs

1. Download the wanted Adobe 2020 Titles to your ~/Downloads folder from the Adobe Admin Console, with the naming convention of:

• Adobe*AppName*2020

For example:

AdobeAcrobatDC2020    
AdobeAfterEffects2020   
AdobeAnimate2020    
AdobeAudition2020   
AdobeBridge2020   
AdobeCharacterAnimator2020   
AdobeDimension2020    
AdobeDreamweaver2020   
AdobeIllustrator2020    
AdobeInCopy2020   
AdobeInDesign2020  
AdobeLightroom2020  
AdobeLightroomClassic2020   
AdobeMediaEncoder2020   
AdobePhotoshop2020    
AdobePrelude2020   
AdobePremierePro2020   
AdobePremiereRush2020   
AdobeXD2020

These will need to be unzipped, if your browser does not unzip the downloads from the Adobe Admin Console.

*Please Note:* Keep the name of the unzipped directory the same as the the installer/uninstaller package within. 

2. Create the respective munki or jss recipe overrides, & name them the same as the Adobe 2020 pkg.

For example:

`AdobeAcrobatDC2020.jss.recipe`
`AdobeAcrobatDC2020.munki.recipe`

## Usage
With the pre-reqs met, you can run the [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) script found in this repo.

You will need to pass to [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) the recipe type, which would be either jss or munki.

For example:

`/path/to/Adobe2020Importer.py jss` or `/path/to/Adobe2020Importer.py munki`

## Process
[Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) will:

1. Check the running users ~/Downloads folder for folders matching the pattern: Adobe\*2020, exiting if nothing found.
2. Creates an empty recipe list at ~/Downloads/adobe2020_list.txt
3. Check that the Adobe&ast;2020 folders contain an sub directory called Build containing a pkg called \*\_Install.pkg, skipping this pkg if not found.
4. If step 3 passes for a pkg, next we look for an override named Adobe\*2020.jss.recipe or Adobe\*2020.munki.recipe (depending on what option was passed to [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py), skipping this pkg if not found.
5. If step 4 is successful, the Override added to the ~/Downloads/adobecc2020_list.txt recipe list. Steps 3-5 are repeated for all Adobe&ast;2020 folders found within ~/Downloads.
6. If any items are added to the ~/Downloads/adobe2020_list.txt recipe list, this is then ran with a report written to ~/Downloads/adobe2020_report.plist

## Note
You should be able to periodically downloaded updated packages from the Adobe Admin Console & then run [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py).

With [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) only importing items which are newer than you have within your JPS or Munki repo.







