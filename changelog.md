# Versions #

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


