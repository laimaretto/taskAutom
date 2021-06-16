# README #

This idea was born because of a need for a simple tool to automate execution of simple configuration teamplates on Nokia SROS based routers. Data provided on a CSV file and the configuration templates written in pure Python. Configuration scripts are the result of these templates being rendered with the CSV data.

## Setup ##

#### System Libraries
These libraries have been tested under Ubuntu 20.04 and Python3.8.

```bash
sudo pip3 install -r requirements.txt
```

For Windows users, make sure you have Python and [PIP](https://pip.pypa.io/en/stable/installing/) installed.

#### Edit `servers.yml`
This file has configuration parameters for the Jump Host(s). Add as many as needed. First server is `0`, next one is `1` and so on, so forth. If more than one jump-host is declared, the connections will be load balanced sequentially among them.

```yml
0:
    name: 'myServer'
    user: 'myUser'
    password: 'myPass'
    ip: 'a.b.c.d'
    port: 22
```

You can comment out some servers, if needed.

#### Compile
You can run `taskAutom` directly from the CLI using Python. However, compiling improves performance.

```bash
python3 -m nuitka taskAutom.py
```
Compiling has been tested succesfully under Ubuntu. Don't know if this is directly supported under Windows. If it fails, let me know. Nevertheless, as mentioned, you can run `taskAutom` directly from the CLI using Python

## Usage ##

The program needs two inputs: a) CSV file with data and b) a plugin, which is nothing but a configuration template.

#### CSV

The CSV file must have in its first column, the IP system of the routers to which `taskAutom` will connect to. The next columns, are the variables that will be used in the configuration template. The CSV must not include a header.
Example: this is a CSV for two different routers, including the data to modify their interfaces.

```csv
10.0.0.1,router1,1/1/1,inter1,192.168.0.1/30
10.0.0.2,router2,1/3/5,inter7,192.168.2.1/30
```

#### Plugin

The plugin is a Python code which is fed with each row of the CSV at a time, in order to render a configuration script. It consists of a function called `construir_cliLine()` which accepts three arguments: `m` which is a counter, `datos` which is a row vector, and `mop`. `m` can be used when some code needs to be ran only once; `mop` is used when the configuration script needs to be verified before running.

Example: use the previous data, to generate configuration scripts.

```python
def construir_cliLine(m, datos, mop=None):

	ipSystem   = datos[0]
	router     = datos[1]
	port       = datos[2]
	intName    = datos[3]
	address    = datos[4]

	cfg        = ""

	if mop and m == 0:
		cfg = "\nHeading_2:Router: " + router + ", " + ipSystem + "\n"

	cfg = cfg + "/configure router interface " + intName + " port " + port + "\n"
	cfg = cfg + "/configure router interface " + intName + " address " + address + "\n"

	return cfg
```

#### Inventory

By default, `taskAutom` connects to each router that exists inside the CSV data file. But an inventory file can be provided, with per router connection parameters. If so, the default connection values are overridden by those inside the inventory file.

ip|username|password|useSSHTunnel|telnetTimeout|delayFactor|clientType|jumpHost
--|--------|--------|------------|-------------|-----------|----------|--------
1.1.1.1|user1|pass1|yes||0.5|ssh|server1
2.2.2.2|user2|pass2|no|90||tel|

If fieds in the CSV are left empty, those are replaced by default values.

#### Result

If `taskAutom` is invoked with option `jobType=0`, a text file with the rendered output, will be genereated.

```bash
$ taskAutom -csv listExample.csv -py confExample.py -j 0
Router: router1, 10.0.0.1
/configure router interface inter1 port 1/1/1
/configure router interface inter1 address 192.168.0.1

Router: router2, 10.0.0.2
/configure router interface inter7 port 1/3/5
/configure router interface inter7 address 192.168.2.1
```

Otherwise, if `taskAutom` is invoked with option `jobType=2`, it will connect to each and every router, and execute the commands. User and password must be provided in this case.

##### MOP

When writing a plugin, is important to help `taskAutom` understand which string should be considered as a title. You do so be adding a prefix `Heading_2` to the `tiltle` variable, under the `if mop:` statement. After this, a MOP is created with the intended information. There is also the possibility of using the prefix `Heading_3`.

#### Configuration Options

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
  -csv CSVFILE, --csvFile CSVFILE
                        CSV File with parameters
  -py PYFILE, --pyFile PYFILE
                        PY Template File
  -log LOGINFO, --logInfo LOGINFO
                        Description for log folder
  -jh JUMPHOSTSFILE, --jumpHostsFile JUMPHOSTSFILE
                        jumpHosts file. Default=servers.yml
  -inv INVENTORYFILE, --inventoryFile INVENTORYFILE
                        inventory.csv file with per router connection parameters. Default=None
  -crt CRONTIME [CRONTIME ...], --cronTime CRONTIME [CRONTIME ...]
                        Data for CRON: name(ie: test), month(ie april), weekday(ie monday), day-of-month(ie 28), hour(ie 17), minute(ie 45).
  -u USERNAME, --username USERNAME
                        Username
  -th THREADS, --threads THREADS
                        Number of threads. Default=1
  -to TELNETTIMEOUT, --telnetTimeout TELNETTIMEOUT
                        Telnet Timeout [sec]. Default=90
  -df DELAYFACTOR, --delayFactor DELAYFACTOR
                        SSH delay factor. Default=1
  -tun {no,yes}, --sshTunnel {no,yes}
                        Use SSH Tunnel to routers. Default=yes
  -ct {tel,ssh}, --clientType {tel,ssh}
                        Connection type. Default=tel
  -gm {no,yes}, --genMop {no,yes}
                        Generate MOP. Default=no
  -so {no,yes}, --strictOrder {no,yes}
                        Follow strict order of routers inside the csvFile. If enabled, threads = 1. Default=no
  -hoe {no,yes}, --haltOnError {no,yes}
                        If using --strictOrder, halts if error found on execution. Default=no
```