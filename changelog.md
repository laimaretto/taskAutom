# Versions #

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


