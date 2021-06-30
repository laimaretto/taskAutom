# Versions #

## [7.9.6] - 2021-06-29

logData

- time was being reported as string; now as float.

## [7.9.5] - 2021-06-28

logData

- Better handling of logData.
- Better support for vendors other than Nokia (nokia_sros)

## [7.9] - 2021-06-16

Inventory File

- Posibility of implementing per router connection parameters.
- If inventory file is being used, default connection values overridden by those in the inventory file.
    - If a router exists in data CSV, but not in the inventory file, default values are used.

## [7.8] - 2021-06-14

Implement strict Order

### Added

- Implement the StrictOrder possibility, following the order of lines inside the CSV;
- Implement the HaltOnError possibility, only available if StrictOrder enabled. If result is neither `SendSuccess` nor `ReadTimeout`, then halts.
- Function `renderCliLine`.
- Use of `dictParam` as dictionary to pass parameters over functions

## [7.7] - 2021-05-26
  
Improvement on connection handling
 
### Added

- SSHTunnelForwarder `allow_agent = False`
- Generation of MOP now based on new CLI parameter `-gm`
- Better handling of connection states based on Exceptions in function `routerRunRoutine()`
- New versions in `requirements.txt`
- Function `verifyConfigFile()` to check for scpecial chars in config file.


