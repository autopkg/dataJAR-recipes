# DistributionPkgInfo

## Description
Parses a distribution pkg to pull additional information.

## Input Variables
- **pkg_path:**
    - **required:** True
    - **description:** Path to the PKG to parse.

## Output Variables
- **pkg_id:**
    - **description:** The package ID.
- **version:**
    - **description:** The version of the pkg from it's info.

---

# JSONFileReader

## Description
Parses a JSON file, returning the value of the supplied key.

## Input Variables
- **json_key:**
    - **required:** True
    - **description:** Key to look for, and return the value of.
- **json_path:**
    - **required:** True
    - **description:** Path to the JSON file.

## Output Variables
- **json_value:**
    - **description:** Value of the JSON key.
