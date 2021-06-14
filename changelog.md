# Versions #

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


