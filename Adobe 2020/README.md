# Import Adobe 2020 Title

## About
These recipes are based on: https://github.com/autopkg/adobe-ccp-recipes

But with the death of Creative Cloud Packager (https://macmule.com/2018/10/15/adobe-creative-cloud-2019-the-death-of-creative-cloud-packager-device-licensing/), have been rejigged to work with locally downloaded pkgs.

## Pre-reqs

1) Build the wanted Adobe 2020 titles from the Adobe Admin Console.

*Please Note:* These should be of the **Managed Install** variety, as a Self Service package does not create the required `_Uninstall.pkg` which is needed by the [Adobe2020Versioner.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Versioner.py) processor. See [this issue](https://github.com/autopkg/dataJAR-recipes/issues/39) for more info.

2) For each Adobe package title, use the naming convention of:

Adobe*AppName*2020

For example:

- AdobeAcrobatDC2020    
- AdobeAfterEffects2020   
- AdobeAnimate2020    
- AdobeAudition2020   
- AdobeBridge2020   
- AdobeCharacterAnimator2020   
- AdobeDimension2020    
- AdobeDreamweaver2020   
- AdobeIllustrator2020    
- AdobeInCopy2020   
- AdobeInDesign2020  
- AdobeLightroom2020  
- AdobeLightroomClassic2020   
- AdobeMediaEncoder2020   
- AdobePhotoshop2020    
- AdobePrelude2020   
- AdobePremierePro2020   
- AdobePremiereRush2020   
- AdobeXD2020

3) Mount the Adobe downloader DMG and run the download application. Once downloaded, unzip the file if your browser does not auto unzip the downloads from the Adobe Admin Console. This must be in your `~/Downloads` folder.

*Please Note:* Keep the name of the unzipped directory the same as the the installer/uninstaller package within.

Also, these packages should only contain a maximum of the Creative Cloud Desktop App (CCDA) and only **one** other App (e.g. CCDA and Photoshop). Most of the Adobe Templates for packages aren't compatible with this.

5) Create the respective munki or jss recipe overrides. The override name **must** be the same as the Adobe 2020 pkg. 

For example:

`AdobeAcrobatDC2020.jss.recipe`
`AdobeAcrobatDC2020.munki.recipe`

*Please Note:* The [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) script assumes your autopkg overrides live in `~/Library/AutoPkg/RecipeOverrides`.

6) The `NAME` input variable must also match the Adobe package title.

## Usage

With the pre-reqs met, you can run the [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) script found in this repo.

You will need to pass to [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) the recipe type, which would be either jss or munki.

For example:

`/path/to/Adobe2020Importer.py jss` or `/path/to/Adobe2020Importer.py munki`

## Process
[Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) will:

1. Check the running users ~/Downloads folder for folders matching the pattern: Adobe&ast;2020, exiting if nothing found.
2. Create an empty recipe list at ~/Downloads/adobe2020_list.txt
3. Check that the Adobe&ast;2020 folders contain a sub directory called Build containing a pkg called \*\_Install.pkg, skipping this pkg if not found.
4. If step 3 passes for a pkg, next we look for an override named Adobe&ast;2020.jss.recipe or Adobe&ast;2020.munki.recipe in ~/Library/AutoPkg/RecipeOverrides (depending on what option was passed to [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py), skipping this pkg if not found.
5. If step 4 is successful, the Override added to the ~/Downloads/adobecc2020_list.txt recipe list. Steps 3-5 are repeated for all Adobe&ast;2020 folders found within ~/Downloads.
6. If any items are added to the ~/Downloads/adobe2020_list.txt recipe list, this is then ran with a report written to ~/Downloads/adobe2020_report.plist

## Note

You should be able to periodically download updated packages from the Adobe Admin Console, completing the pre-req steps, and then run [Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py).

[Adobe2020Importer.py](https://github.com/autopkg/dataJAR-recipes/blob/master/Adobe%202020/Adobe2020Importer.py) will only import items which are newer than you have within your JPS or Munki repo.







