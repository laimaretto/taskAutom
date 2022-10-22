# README #

This idea was born because of a need for a simple tool to automate the execution of simple configuration templates on Nokia SROS based routers. Data provided on a DATA file (CSV or Excel) and the configuration templates written in pure Python. Configuration scripts are the result of these templates being rendered with the data.

---
## Setup ##

### System Libraries
These libraries have been tested under Ubuntu 20.04 and Windows10 with Python3.8.

###### Ubuntu
```bash
pip3 install taskAutom
```
###### Windows
For Windows users, make sure you have Python and [PIP](https://pip.pypa.io/en/stable/installing/) installed.
```bash
py -m pip install taskAutom
```

### Edit `servers.yml`
This file has configuration parameters for the Jump Host(s). Add as many as needed. If more than one jump-host is declared, the connections will be load balanced sequentially among them. You can comment out some servers, if needed.

```yml
srvr0:
    name: 'myServer'
    user: 'myUser'
    password: 'myPass'
    ip: '1.1.1.1'
    port: 22
srvr1:
    name: 'myServer'
    user: 'myUser'
    password: 'myPass'
    ip: '2.2.2.2'
    port: 22    
```

---

## Usage ##

The program needs two mandatory inputs: a) DATA file and b) a plugin, which is nothing but a configuration template.

### DATA file

The DATA can be either a CSV file or an Excel file. In both cases you can define a header with column names, or not; it's optional.
- If no header, the file must have in its first column (`_1`), the IP of the routers to which `taskAutom` will connect to.
- If using header, there must be a column named `ip` with the IP addresses of the routers to which `taskAutom` will connect to.
    - You can chose a differnt column name by using the configuration option `-gc/--dataGroupColumn myColName`.

The first column `_1` or the `ip` column (or eventually changed by `-gc`) allows `taskAutom` to group routers by that column when processing data. This is particularly useful if you have the same router along several rows in the DATA file.

If you want `taskAutom` not to group routers by the `[ip|_1]` column, you should use the `-so/--strictOrder yes` CLI parameter: this will process the routers' data in the order of the DATA file as is.

The next columns in the DATA file, are the variables that will be used in the configuration template.

**Example:** this is a CSV for two different routers, including the data to modify their interfaces. A header is being used in this case.

```csv
ip,name,port,interName,ipAddress
10.0.0.1,router1,1/1/1,inter1,192.168.0.1/30
10.0.0.2,router2,1/3/5,inter7,192.168.2.1/30
```

### Plugin

The plugin is a Python code which is fed with each row of the DATA file at a time, in order to render a configuration script. It consists of a function called `construir_cliLine()` which accepts four arguments:
- `m` which is a counter, representing the `row_id` of the data.
- `datos` which is a `Pandas` series; the data itself.
- `lenData` which is the length of the Pandas dataFrame; i.e.: the amount of rows inside the grouped data.
- `mop`, a boolean.

`m` and `lenData` can be used to decide when some part of the code must be ran. `mop` is used when the configuration script needs to be verified before running; `mop=True` when the CLI parameter `-j/--jobType` is `0`.

**Example:** use the previous data, to generate configuration scripts. The example is assuming no header has been defined in the DATA file, so column id is used to identify the proper variable.

```python
def construir_cliLine(m, datos, lenData, mop=None):

	ipSystem   = datos.ip
	router     = datos.name
	port       = datos.port
	intName    = datos.interName
	address    = datos.ipAddress

	cfg        = ""

    if mop and m == 0:
        cfg = "\nHeading_2:Router: " + router + ", " + ipSystem + "\n"

    cfg = cfg + f'/configure router interface {intName} port {port}\n'
    cfg = cfg + f'/configure router interface {intName} address {address}\n'

    if m == lenData-1:
        cfg = cfg + f'/configure router interface {intName} no shutdown\n'

	return cfg
```

#### Notes on plugin

1) When writing plugins,  *do not* to use abbreviated commands. This will potentially led to errors. For example: `/configure rout int system add 10.0.0.1/32` is discouraged. Better off use `/configure router interface system address 10.0.0.1/32`.

2) Common practice: it is better to try to accommodate plugins so that they reflect they purpose. Then use the configuration parameter `--pluginType=[show|config]` to reflect the spirit of the plugin.

3) In general, use `--cmdVerify=yes`. Only disable `cmdVerify` if facing problems.

### Inventory

By default, `taskAutom` connects to each and every router that exists inside the DATA data file. Optionally, an inventory file can be provided, with per router connection parameters. If so, the default connection values are overridden by those inside the inventory file.

ip|username|password|useSSHTunnel|readTimeOut|deviceType|jumpHost|
--|--------|--------|------------|----------|--------|---------
10.0.0.1|user1|pass1|yes|15|nokia_sros|server1|1000
10.0.0.2|user2|pass2|no|90|nokia_sros_telnet|

If fieds in the inventory CSV file are left empty, default values are used.

### MOP

When writing a plugin, is important to help `taskAutom` understand which string should be considered as a title. You do so be adding a prefix `Heading_2` to the `tiltle` variable, under the `if mop:` statement. After this, a MOP is created with the intended information. There is also the possibility of using the prefix `Heading_3`.

---

## Result ##

If `taskAutom` is invoked with option `-j/--jobType 0`, a text file with the rendered output, will be genereated.

```bash
$ taskAutom -d example/example.csv -py example/example.py -l test -j 0

Router: router1, 10.0.0.1
/configure router interface inter1 port 1/1/1
/configure router interface inter1 address 192.168.0.1

Router: router2, 10.0.0.2
/configure router interface inter7 port 1/3/5
/configure router interface inter7 address 192.168.2.1
```

Otherwise, if `taskAutom` is invoked with option `-j/--jobType 2`, it will connect to each and every router, and execute the commands. User and password must be provided in this case.

---

## Configuration Options

`taskAutom` can be configured through CLI as shown below.

```bash
$ python3 taskAutom.py -h
usage: PROG [options]

Task Automation Parameters.

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         Version
  -j {0,2}, --jobType {0,2}
                        Type of job
  -d DATA, --data DATA  DATA File with parameters. Either CSV or XLSX. If XLSX, enable -xls option with sheet name.
  -py PYFILE, --pyFile PYFILE
                        PY Template File
  -gc DATAGROUPCOLUMN, --dataGroupColumn DATAGROUPCOLUMN
                        Only valid if using headers. Name of column, in the DATA file, to group routers by. In general one should use the field where the IP of the router is. Default=ip
  -uh {no,yes}, --useHeader {no,yes}
                        When reading data, consider first row as header. Default=yes
  -xls XLSNAME, --xlsName XLSNAME
                        Excel sheet name
  -u USERNAME, --username USERNAME
                        Username to connect to router.
  -th THREADS, --threads THREADS
                        Number of threads. Default=1
  -log LOGINFO, --logInfo LOGINFO
                        Description for log folder
  -jh JUMPHOSTSFILE, --jumpHostsFile JUMPHOSTSFILE
                        jumpHosts file. Default=servers.yml
  -inv INVENTORYFILE, --inventoryFile INVENTORYFILE
                        inventory.csv file with per router connection parameters. Default=None
  -pt {show,config}, --pluginType {show,config}
                        Type of plugin.
  -gm {no,yes}, --genMop {no,yes}
                        Generate MOP. Default=no
  -crt CRONTIME [CRONTIME ...], --cronTime CRONTIME [CRONTIME ...]
                        Data for CRON: name(ie: test), month(ie april), weekday(ie monday), day-of-month(ie 28), hour(ie 17), minute(ie 45).
  -rto READTIMEOUT, --readTimeOut READTIMEOUT
                        Read Timeout. Time in seconds which to wait for data from router. Default=10
  -tun {no,yes}, --sshTunnel {no,yes}
                        Use SSH Tunnel to routers. Default=yes
  -dt {nokia_sros,nokia_sros_telnet}, --deviceType {nokia_sros,nokia_sros_telnet}
                        Device Type. Default=nokia_sros
  -so {no,yes}, --strictOrder {no,yes}
                        Follow strict order of routers inside the csvFile. If enabled, threads = 1. Default=no
  -hoe {no,yes}, --haltOnError {no,yes}
                        If using --strictOrder, halts if error found on execution. Default=no
  -cv {no,yes}, --cmdVerify {no,yes}
                        Enable cmdVerify when interacting with router. Disable only if connection problems. Default=yes
  -sd {no,yes}, --sshDebug {no,yes}
                        Enables debuging of SSH interaction with the network. Stored on debug.log. Default=no

```