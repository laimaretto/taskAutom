# Versions #
## [8.3.1] - 2025-05-21
- New parameter `-lt/--logTime`. To indicate the use of timestamp in `logfolder` created. 
- `logsDirTimestamp` added to each json file per router as a new key `DateTime`.


## [8.3.0] - 2025-01-23

- Update of libraries:
    - `sshtunnel==0.4.0`
    - `netmiko==4.5.0`
    - `pandas>=1.5.2,<=2.0.3`
    - `pyyaml==6.0.2`
    - `python-docx==0.8.11`
- The following functions have be cleaned-up/reordered:
    - `fncWriteToConnection(self, inText, connInfo)`: this function now applies try/except per each sent command to the router. If ok, among others, returns `SendingOk`.
    - `_getData(inText,connInfo)`: if it receives a `SendingOk`, breaks.
    - `fncSshServer(self, connInfo, sftp=False)`: better code, avoiding unnecesary try/excepts.
    - `routerLogin(self, connInfo)`: better code, avoiding unnecesary try/excepts. Also, if a router cannot be logged-in, returns `CannotLog` (before it would return `LoggedOk` even if it was not true).
    - `routerRunRoutine(self, connInfo)`: an unused paramater `runStatus` has been removed


## [8.2.3] - 2024-12-11
- Getting the Python version, operating system and the library versions. Saving to `00_reports.json` file
- Update `README.md`
- Create img/ and uploading images for `README.md`
- Updating License

## [8.2.2] - 2024-03-18

- The HwType is now added to the json file per router as a new key.

## [8.2.1] - 2024-03-16

- Update of libraries:
    - `pandas  >= 1.5.2,<=2.0.3`
    - `netmiko == 4.3.0`
- The Timos version is now added to the json file per router as a new key.
- The default hostname is now `NA_#`, where # is the threadnumber. This changes if the hostname is detected later on.

## [8.1.1] - 2023-09-17

- Update to have taskAutom support access to SRLinux devices. A new device type `nokia_srl` has been included under the `DICT_VENDOR` general dictionary.
- Netmiko, by default, disables pagination either by using `environment no more` or `environment more false`. The `FIRST_LINE=""` from now on for device type `nokia_sros`.
    - The device_type `md_nokia_sros` has been removed from the `-dt` option.
- `00_report.json` now includes timing information.

## [8.0.6] - 2023-06-24

- The function `fncPrintResults()` now created a new data file, `00_faildeDataFile`, which is a subset of the original data file. Thisincludes only the devices which have presented errors during exectuion.ssh-tunnels.
- The function `checkCredentials()` has been refactored to better guide users when dealing with jobTypes.

## [8.0.5] - 2023-06-22

- The method `fncSshServer()` has been refactored. Better detection of problematic connections over ssh-tunnels.

## [8.0.4] - 2023-06-22

- The method `fncUploadFile()` decides between SCP or SFTP depending on the Timos version. If taskAutom cannot detect the Timos version, SCP will be selected.
- The method `fncUploadFile()` will assume `cf3:/` for the remote file, if no CF is specified in the `ftpRemoteFilename`.

## [8.0.3] - 2023-06-02

- The method `routerRunRoutine()` will search for the string `#FINSCRIPT` after checking for correctness of execution (ie, `majorFailed`). If further the execution is incomplete, then the total result will be, following the example, labeled as `majorFailed:Incomplete`.

## [8.0.2] - 2023-06-02

- The profile for the device type `nokia_sros` and `nokia_sros_telnet` include now as a last line, a `FIN_SCRIPT` string `#FINSCRIPT`. The idea is that the method `routerRunRoutine()` will check for that string. If not detected, taskAutom will assume that the execution of the script is incomplete, either because the command was not correctly sent over to the router; or because the output received from the router was cut somehow.

## [8.0.1] - 2023-05-30

- Using latest version of netmiko, 4.2.0
- Update of the method `routerLogin()`, to use the new method from netmiko, `ConnLogOnly()`. If `sshDebug` is True, then a debug file will be created under `logsDirectory` with per-thread information.

## [7.19.4] - 2023-05-06

- Update function `renderCliLine()`

## [7.19.3] - 2023-05-05

- The global dictionary `dictParam` has been updated with new default keywords.
- New function `buildScripts(dictParam)`, which can be used when importing taskAutom:
    - `from src.taskAutom import taskAutom as ta`.
    - `dictParam['pluginFilename']  = 'myPlugin.py'`
    - `dictParam['dataFile']        = 'myData.xlsx'`
    - `dictParam['xlsSheetName']    = 'tabName'`
    - `d = ta.buildScripts(dictParam)`
    - This will allow to use the same plugins and data files when using taskAutom at the console, but within a python code.

## [7.19.2] - 2023-05-03

- Parameter `-j/--jobType` is now 0 by default.
- Parameter `-pt/--pluginType` is now `show` by default.
- The json report file now includes the version of taskAutom.

## [7.19.1] - 2023-02-09

- Better inventory file checkinng.
- The class `myConnection` now receives fewer arguments, namely dictonaries `routerInfo` and `dictParam`.
    - `routerInfo` holds all the necesary arguments to establish the connection towards the router, ie, username and password. But also, now, the `pluginScript` which is the script to be executed on the router.
    - `dictParam` holds all the global parameters such as log folder name, logTime, dataFileName, pluginName, sshServers, etc.
    - This change follows this idea: even if an inventory is defined, the `pluginScript` is created before being sent over to the class by the combination of the `dataFilename` and the `pluginFilename`. The idea here is that in the near future, the inventory could establish per-router plugins and/or data files. So in one run of taskAutom, different routers will be executing different scripts.
- The method `fncUploadFile()` has been modified so that jobTypes 2 and 3 have better control over the sent files via SCP/SFTP.
- The method `logData()` is better now. Log data is a pandas DataFrame being built from a dictionary, which varies depending on the jobType. The function `fncPrintResults()` now performs a `pd.concat(LOG_GLOBAL)`.
- The function `getListOfRouters()` no longer provides, only, a list of routers, but also a list of dictionaries which conform the real inventory. The `key` in that dictionary is the IP of each and every router with a predefined set of subkeys: username, password, deviceType, useSSHTunnel, readtimeout, jumphost and systemIP.
    - If the the jobType is 2, an extra subkey `pluginScript` will be added. If jobType 3, a list of tuples with `[(locaFile,remoteFile)]` will be added. These are the files to be uploaded via SCP/SFTP.
    - If there is an external inventroy file, ie `-inv inv.csv`, the `dictParam['inventory']` will be updated with the information contained inside `inv.csv`.
- The function `verifyInventory()`  has been modified to return a dictionary which is compatible with the one required by the function `getListOfRouters()`.
- New global dictionary `DICT_PARAM` which can be used when using taskAutom as an import inside a python code.
- Basic MD-CLI support under Nokia, when using `deviceType = md_nokia_sros`.

    

## [7.18.3] - 2023-02-02

- Better inventory file checking.

## [7.18.2] - 2023-02-01

- The regex for timos and hostname have been changed
- New paramter to control log file names `-fn/--logFileName`.
- Retrieving aux values now tries `auxRetry` times.

## [7.18.1] - 2023-01-30

- Variables obtained through `argparse` are set to `True/False` depending on the input being `yes/no`. So now the treatment is hanlde as a boolen when needed.
- New functionality to bulk updload files through SCP/SFTP.
    - For this a new `dataFile` structure is needed with the following minimum columns: `ip|ftpLocalFilename|ftpRemoteFilename`.
- Code reordering.

## [7.17.13] - 2023-01-27

- CRON config update.

## [7.17.11] - 2023-01-27

- CRON config now applies different configuration if `timosMajor` > 8.

## [7.17.10] - 2023-01-13

- Better detection of individual connections' status, for logging purposes.
- `-tbr/--timeBetweenRouters` now in milliseconds.
    - tweaking the number of threads and the time between routers, will allow to maximize the number of connections, specially when using at jump-server. 

## [7.17.6] - 2023-01-05

- Better support for CRON, either `oneshot` or `periodic`.

## [7.17.2] - 2022-12-19

- Better help description when invoking the `-h` paramter on the CLI.

## [7.17.1] - 2022-12-15

- the functions `fncConnectToRouter()`, `routerRunRoutine()`, `routerLogin()` and `fncSshServer()`,  now return `connInfo` instead of separate variables
- the variables `controlPlaneAccess` and `aluLogged` are now booleans with default False
- the variables `sshServer` and `conn2rtr` default to `None` and only change if the connections come up.

## [7.16.8] - 2022-12-15

- new parameter `hwType` obtained from `show chassis`
- the `hostname` is no longer obtained from `find_prompt()` but from `show chassis`.

## [7.16.7] - 2022-12-14

- update


## [7.16.6] - 2022-12-06

- update

## [7.16.5] - 2022-12-06

- New function `getDictParam()` that returns the `dictParam` dictionary with all the required parameters for the connections.
- The function `fncRun()` returns the updated version of `dictParam`.

## [7.16.4] - 2022-12-04

- When the execution is finished, a `json` version of the configuration parameters of `taskAutom` is saved under the folder `-l/--logInfo`.

## [7.16.3] - 2022-11-28

- Update of libraries:
    - `python-docx==0.8.11`
    - `pandas==1.5.2`.
    - `openpyxl==3.0.10`
    - `xlrd` removed

## [7.16.2] - 2022-11-25

- When using `strictOrder=no` the default value is passing data row by row to the plugin. The data is filtered by the `groupColumn` parameter. When using the parameter `pbr/passByRow=no` the complete Excel tab is passed over to the plugin. Once in the plugin, the data can be analyzed by Pandas method `iterutples()`.
- Update of libraries:
    - `python-docx==0.8.11`
    - `pandas`.
    - `scp` removed becase installed by netmiko
    - `paramiko` removed becase installed by netmiko


## [7.15.4] - 2022-11-20

- New parameter `-pf/passwordFile`. This allows to store the password in a local file so `taskAutom` will read the password from it. This allows to use `taskAutom` from the crontab.
    - Becareful: the password is stored in plain text format.

## [7.15.3] - 2022-10-22

- From this version on, `taskAutom` needs to be installed by using `pip`, ie, `pip install taskAutom`.

## [7.14.4] - 2022-08-11

- Change of `START_SCRIPT` and `END_SCRIPT` defined in `DICT_VENDOR` for `nokia_sros` and `nokia_sros_telnet`.
- In function `routerRunRoutine()` no more looking for string `END_SCRIPT`.
- New parameter `timeBetweenRouters`. A delay in seconds to wait before executing scripts on a router. Works both for threaded connections or with strict order.
- In function `fncSshServer()` better handling of connection errors with sshtunnel.


## [7.14.3] - 2022-07-05

- Change of `START_SCRIPT` and `END_SCRIPT` defined in `DICT_VENDOR` for `nokia_sros` and `nokia_sros_telnet`.

## [7.14.0] - 2022-06-25

- Upgrade of `netmiko` library to version 4.1.0
    - `delayFactor` and `maxLoops` are no longer used;
    - New parameter `readTimeOut` is used insted. In seconds, sets the amount of time `taskAutom` waits for output from router. Default to 10 seconds.
    - This change also affects the building of the inventory file, if used.
- Upgrade of `paramiko` library to version 2.11.0
- Upgrade of `pandas` library to version 1.4.1
- Better detection of ssh-tunnels under the function `fncSshServer()`.
- Final report shows times in minutes if greater than 120s.
- In the definition of the dictionary `DICT_VENDOR`
    - the `expect_string` was changed to `r'#\s$'`.
    - the start and end scripts are now `"echo SCRIPT_NONO_START\n"` and `"echo SCRIPT_NONO_FIN\n"`.
- The output in json format now includes a new key, with the IP of the router.
- Data file and Plugin can now reside on a different folder other than the root of taskAutom.

## [7.13.1] - 2022-03-17

- When using option `-pt show` a `json` file is created where output is stored. Each `show` command is used as a key inside the json file. This will help for output checking.

## [7.12.2] - 2021-10-14

- Comments in the code
- Show CRON, inventory only if configured.

## [7.12.1] - 2021-10-11

- Remove parameter `clientType` in favor of `deviceType`.
    - Using Netmiko's `nokia_sros_telnet` as device type when a Telnet Connection is needed. If ssh, use `nokia_sros`.
- Rename parameter `sshMaxLoops` in favor of `maxLoops`.
- Remove paramter `telnetTimeout`.
    - all timinig is now controlled by `delayFactor` and/or `maxLoops`.
- Function `connectToRouter()` is simpler now:
    - New function `routerLogin()` which direclty calls `ConnectHandler()` with the appropiate `deviceType`.
    - Functions `routerLoginSSH()` and `routerLoginTelnet()` no longer needed.
- Function `fncWriteToConnection()` is simpler now as the connection handler is always Netmiko's `ConnectHandler()`.
- Function `fncAuxGetVal()` is simpler now.
- Function `routerLogout()` no longer needed.
- PluginType is now a mandatory parameter and no longer optional.
- If `cron` is enabled, then `strictOrder=no` and `pluginType=config`.
- Function `fncSshServer(self, strConn, connInfo, sftp=False)` now has an sftp parameter which becomes True when invoked from within `fncUploadFile()`.
- Function `runCron()` updated so that all commands are compatible with Nokia's echo (and as such detectable by Netmiko's `cmd_verify`).


## [7.11.9] - 2021-09-29

- In function `renderCliLine()` bug corrected when `len(aluCliLine)=0`. 

## [7.11.8] - 2021-09-29

- In function `renderCliLine()` better error message when the plugin cannot be rendered correctly with data.

## [7.11.7] - 2021-09-29

- `00_log.cvs` report includes now the Timos of the device.
- `fncWriteToConnection()` implements now a set of `try|expect` for every possible writing option and returns `runStatus,logReason,output`. This will allow for every method in the class to write appropriately and hence detect if something happened.
- Both functions `routerRunRoutine()` and `fncAuxGetVal()` use now the new version of `fncWriteToConnection()` which detectes better connection problems when writing. This will also help in detecting nodes with connection problems and log them into `00_log.csv` 

## [7.11.5] - 2021-09-15

- In the function `fncConnectToRouter()` the logins either using SSH or Telnet, have been changed to better detect login problems. This will be notified under `aluLogReason`.
- In `fncPrintResults()`, accomodate results better when printing the table.
- Added `openpyxl==3.0.6` and `xlrd==2.0.1` to `requirements.txt`.

## [7.11.4] - 2021-09-15

- If detection of `hostname` fails, append number of connection to avoid mixing logs in the same log file `not-matched_rx.txt`. 

## [7.11.3] - 2021-09-10

- Name of `ip` column customizable on datafile.

## [7.11.2] - 2021-09-02

- Length of Data now as input parameter inside plugin.

## [7.11.1] - 2021-08-31

- Better error detection.

## [7.11.0] - 2021-08-20

- New option `sshDebug`
- Info Error Detection
- `SEND_CMD_REGEX = "#"` for show commands.
- Excel format supported.
    - Default is still `csv`.
- Header supported in input data;
    - If header is to be used, there must be a column called `ip` for the IP addresses of the routers.
    - If header is not used, then the first column of the data file will be assumed to hold the IP addresses of the routers (default behavior).


## [7.10.1] - 2021-07-29

- New option `cmdVerify` with default `yes`.
    - This is enabled by default and should be used, especially, whenever dealing with config-like commands. See [here](https://github.com/ktbyers/netmiko/issues/2429) 

## [7.10.0] - 2021-07-10

- Inside `fncWriteToConnection(self, inText, connInfo)` distinguish between `show` and `config` commands so as to use `send_command()` or `send_config_set()` respetively.
    - This will help in the future to obatin show output data as JSON format.
- New parameter `pluginType`, either `show` or `config` according Netmiko's [documentation](https://ktbyers.github.io/netmiko/docs/netmiko/#netmiko.BaseConnection.send_command)
    - Default set to `config`.
- New parameter `max_loops`: in conjuntion with `delay_factor` and `pluginType` helps in obtaining long output data.
    - Default set to `5000`.
    - `timeOut = max_loops * 0.2 * delay_factor`. See [this](https://github.com/ktbyers/netmiko/blob/develop/netmiko/utilities.py#L628) for explanation.
- Using `connInfo` as input paramter for all the internal methods of the connect class.
- Inside `routerLoginSsh()` using `fast_cli=False` inside the connection handler.
- Change of default cient type to `ssh`.

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


