#!/usr/bin/env python3

# Copyright (C) 2015-2022 Lucas Aimaretto / laimaretto@gmail.com
#
# This is taskAutom
#
# taskAutom is free software: you can redistribute it and/or modify
# it under the terms of the 3-clause BSD License.
#
# taskAutom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY of any kind whatsoever.
#

import json
import os
import time
import threading
from multiprocessing.pool import ThreadPool
import logging
import importlib
import re
import argparse
from getpass import getpass
import re
import calendar
import random
import sys

# installed
import sshtunnel
import paramiko
from netmiko import ConnectHandler
from scp import SCPClient
import pandas as pd
import yaml
import docx
from docx.enum.style import WD_STYLE_TYPE 
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Pt


#logging.basicConfig(level=logging.DEBUG,format='[%(levelname)s] (%(threadName)-10s) %(message)s')

# Variables Login
IP_LOCALHOST          	 = "127.0.0.1"

ROUTER_TELNET_PORT       = 23
ROUTER_SSH_PORT          = 22
ROUTER_FTP_PORT          = 21

# --- General Timers
ALU_TIME_LOGIN           = 5
SAM_TIME_LOGIN           = 10
ALU_TIME_DIFF			 = 1
PROMPT_TIMEOUT           = ALU_TIME_LOGIN

# --- General Prompts
ALU_PROMPT_CLOSED         = [b"closed by foreign host"]
ALU_PROMPT_LOGOUT		  = [b"# logout"]
ALU_PROMPT_FTP_LOGOUT     = [b"221 Bye!"]
ALU_PROMPT_LOGIN          = [b"Login:"]
ALU_PROMPT_FTP_LOGIN      = [b"220 FTP server ready"]
ALU_PROMPT_FTP_BIN_MODE   = [b"binary mode"]
ALU_PROMPT_FTP_TXFER      = [b"226 Transfer complete"]
ALU_PROMPT_FTP            = [b"ftp>"]

ALU_PROMPT_PASS           = [b"Password:"]
ALU_PROMPT                = [b"(A:|B:)(.+)(>|#)"]

ALU_TIMOS_LOGIN           = [b"(TiMOS-[A-Z]-\d{1,2}.\d{1,2}.R\d{1,2})"]
ALU_HOSTNAME              = [b"(A:|B:)(.+)(>|#)"]

# --- Extras
CH_CR					  = "\n"
CH_COMA 				  = ","
LOG_GLOBAL                = []
LOG_CONSOLE               = []
YES                       = 'yes'
NO                        = 'no'

# - Parameters per vendor
DICT_VENDOR = dict(
	nokia_sros=dict(
		START_SCRIPT     = "", 
		FIRST_LINE       = "/environment no more\n",
		LAST_LINE        = "\nexit all\n",
		FIN_SCRIPT       = "",
		VERSION 	     = "show version", # no \n in the end
		VERSION_REGEX    = "(TiMOS-[A-Z]-\d{1,2}.\d{1,2}.R\d{1,2})",
		HOSTNAME         = "/show chassis | match Name", # no \n in the end
		HOSTNAME_REGEX   = "Name\s+.\s(\S+)",
		HW_TYPE          = "/show chassis | match Type", # no \n in the end
		HW_TYPE_REGEX    = "Type\s+.\s(.+)",
		SHOW_REGEX       = "(\/show|show)\s.+",
		SEND_CMD_REGEX   = r"#\s+$",
		MAJOR_ERROR_LIST = ["^FAILED:.+","^ERROR:.+","^Error:.+","invalid token","not allowed"],
		MINOR_ERROR_LIST = ["^MINOR:.+"],
		INFO_ERROR_LIST  = ["^INFO:.+"],
		REMOTE_PORT      = 22,
		SFTP_PORT        = 22,
	),
	nokia_sros_telnet=dict(
		START_SCRIPT     = "", 
		FIRST_LINE       = "\n/environment no more\n",
		LAST_LINE        = "\nexit all\n",
		FIN_SCRIPT       = "",
		VERSION 	     = "show version", # no \n in the end
		VERSION_REGEX    = "(TiMOS-[A-Z]-\d{1,2}.\d{1,2}.R\d{1,2})",
		HOSTNAME         = "/show chassis | match Name", # no \n in the end
		HOSTNAME_REGEX   = "Name\s+.\s(\S+)",
		HW_TYPE          = "/show chassis | match Type", # no \n in the end
		HW_TYPE_REGEX    = "Type\s+.\s(.+)",
		SHOW_REGEX       = "(\/show|show)\s.+",
		SEND_CMD_REGEX   = r"#\s+$",
		MAJOR_ERROR_LIST = ["^FAILED:.+","^ERROR:.+","^Error:.+","invalid token","not allowed"],
		MINOR_ERROR_LIST = ["^MINOR:.+"],
		INFO_ERROR_LIST  = ["^INFO:.+"],
		REMOTE_PORT      = 23,
		SFTP_PORT        = 22,
	),
)

####

def fncPrintResults(routers, timeTotalStart, dictParam, DIRECTORY_LOG_INFO='', ALU_FILE_OUT_CSV=''):

	separator = "\n------ * ------"

	outTxt    = ""

	outTxt = outTxt + separator + '\n'

	#### GLOBALS

	outTxt = outTxt + "Global Parameters:\n"

	outTxt = outTxt + "  Template File:              " + dictParam['pyFile'] + '\n'
	if bool(dictParam['pluginType']):
		outTxt = outTxt + "  Template Type:              " + dictParam['pluginType'] + '\n'
	outTxt = outTxt + "  DATA File:                  " + dictParam['data'] + '\n'
	outTxt = outTxt + "  DATA UseHeader:             " + dictParam['useHeader'] + '\n'
	outTxt = outTxt + "  Folder logInfo:             " + dictParam['logInfo'] + '\n'
	outTxt = outTxt + "  Text File:                  " + dictParam['logInfo'] + "/job0_" + dictParam['pyFileAlone'] + ".txt" + '\n'

	if dictParam['genMop'] == 'yes':
		outTxt = outTxt + "  MOP filename                " + dictParam['logInfo'] + "/job0_" + dictParam['pyFileAlone'] + ".docx\n"

	if bool(dictParam['inventoryFile']):
		outTxt = outTxt + "  Inventory file              " + str(dictParam['inventoryFile']) + "\n"


	outTxt = outTxt + "  Verify Commands:            " + dictParam['cmdVerify'] + '\n'	
	outTxt = outTxt + "  Strict Order:               " + dictParam['strictOrder'] + '\n'
	outTxt = outTxt + "  Pass Data By Row:           " + dictParam['passByRow'] + '\n'

	if dictParam['strictOrder'] == 'yes':
		outTxt = outTxt + "  Halt-on-Error:              " + dictParam['haltOnError'] + '\n'

	if dictParam['cronTime']['type'] is not None:
		outTxt = outTxt + "  CRON Config:                " + str(dictParam['cronTime']) + '\n'

	outTxt = outTxt + "  Total Threads:              " + str(dictParam['progNumThreads']) + '\n'

	if dictParam['strictOrder'] == 'no':
		outTxt = outTxt + "  Total Routers:              " + str(len(routers)) + '\n'
	else:
		outTxt = outTxt + "  Total Lines:                " + str(len(routers)) + '\n'

	#### CONNECTION

	outTxt = outTxt + "\nDefault Connection Parameters:\n"

	if dictParam['inventoryFile'] != None:
		outTxt = outTxt + "(Override by inventory file: " + dictParam['inventoryFile'] + ")\n\n"
	
	if dictParam['useSSHTunnel'] == 'yes':
		outTxt = outTxt + "  Use SSH tunnel:             " + str(dictParam['useSSHTunnel']) +" ("+ str(len(dictParam['jumpHosts'])) +")" + '\n'
	else:
		outTxt = outTxt + "  Use SSH tunnel:             " + str(dictParam['useSSHTunnel']) + '\n'
	
	outTxt = outTxt + "  Read Timeout:               " + str(dictParam['readTimeOut']) + '\n'
	outTxt = outTxt + "  Time Between Routers:       " + str(dictParam['timeBetweenRouters']) + '\n'
	outTxt = outTxt + "  Username:                   " + str(dictParam['username']) + '\n'
	outTxt = outTxt + "  Password Filename:          " + str(dictParam['passwordFile']) + '\n'
	outTxt = outTxt + "  Device Type:                " + str(dictParam['deviceType']) + '\n'

	if dictParam['outputJob'] > 0:

		timeTotalEnd 	= time.time()
		timeTotal 		= timeTotalEnd - timeTotalStart		

		outTxt = outTxt + separator + '\n'

		routers = LOG_GLOBAL
		columns=['DateTime','logInfo','Plugin','pluginType','cmdVerify','IP','Timos','HostName','HwType','User','Reason','id','port','jumpHost','deviceType','txLines','rxLines','time','readTimeOut','servers']
		df = pd.DataFrame(routers,columns=columns)

		outTxt = outTxt + "\nTiming:\n"

		outTxt = outTxt + "  timeMin                     " + fncFormatTime(df['time'].min()) + '\n'
		outTxt = outTxt + "  timeAvg:                    " + fncFormatTime(df['time'].mean()) + '\n'
		outTxt = outTxt + "  timeMax:                    " + fncFormatTime(df['time'].max()) + '\n'
		outTxt = outTxt + "  timeTotal:                  " + fncFormatTime(timeTotal) + '\n'
		outTxt = outTxt + "  timeTotal/totalRouters:     " + fncFormatTime(timeTotal/len(routers)) + '\n'

		outTxt = outTxt + separator + '\n'

		df['threads']     = dictParam['progNumThreads']

		df.to_csv(ALU_FILE_OUT_CSV,index=False)

		dfFailed = df[df['Reason'] != 'SendSuccess']

		if dictParam['strictOrder'] == 'no':
			outTxt = outTxt + "\nFailed routers:             " + str(len(dfFailed)) + '\n'
		else:
			outTxt = outTxt + "\nFailed lines:               " + str(len(dfFailed)) + '\n'

		if dictParam['strictOrder'] == 'yes' and dictParam['haltOnError'] == 'yes' and dictParam['aluLogReason'] not in ['SendSucces','ReadTimeout']:
			outTxt = outTxt + "   --> HaltOnError: " + dictParam['aluLogReason'] + ' <--\n'

		if len(dfFailed) > 0:
			outTxt = outTxt + dfFailed.to_string(max_colwidth=20) + '\n'

		outTxt = outTxt + separator

		df['Reason'] = df['Reason'].str.replace('(\w+:\d+|\d+.\d+.\d+.\d+:\d{1,6}|\d+.\d+.\d+.\d+)','',regex=True)
		df['Reason'] = df.apply(lambda x: x['Reason'].replace(x['HostName'],''), axis=1)
		dfGroup = df.groupby(['Reason']).agg({'Reason':['count'],'time':['min','max']})

		outTxt = outTxt + '\n' + dfGroup.to_string(max_colwidth=20) + '\n'

		with open(DIRECTORY_LOG_INFO + '00_report.txt','w') as f:
			f.write(outTxt)

		with open(DIRECTORY_LOG_INFO + '00_log_console.txt','w') as f:
			for k in LOG_CONSOLE:
				f.write(k+'\n')

		with open(DIRECTORY_LOG_INFO + '00_report.json', 'w') as f:
			dictParam['password'] = '*****'
			json.dump(dictParam, f)

	outTxt = outTxt + separator + '\n'

	print(outTxt)

def fncFormatTime(timeFloat, adjust=True):

	move = 100

	if adjust==True:

		unit = 's'

		if timeFloat > 120:
			timeFloat = timeFloat / 60
			unit = 'm'

		timeFloat = float(int(timeFloat*move))/move	

		return str( timeFloat ) + unit

	else:

		return float(int(timeFloat*move))/move

def fncPrintConsole(inText, show=1):
	#logging.debug(inText)
	localtime   = time.localtime()
	if show:
		output = str(time.strftime("%H:%M:%S", localtime)) + "| " + inText
		print(output)
		LOG_CONSOLE.append(output)

def run_mi_thread(i, CliLine, ip, dictParam):
	"""[summary]

	Args:
		i ([type]): [description]
		CliLine ([type]): [description]
		ip ([type]): [description]
		dictParam ([dict]): [Dictionary with connection parameters]
	"""
	time.sleep(random.random())
	aluLogReason = myConnection(i, CliLine, ip, dictParam).run()

	return aluLogReason

def getListOfRouters(data, dictParam):
	"""
	Function to obtain the unique list of routers.
	If using headers, the data will be otained from such column
	If not using headers, data will be otained from the first column.

	## If using strictOrder, we get the list of routers as is, with out any filtering ##
	## This is so, because later on, we do a for-loop on this list.

	Args:
		data: Pandas Data File
		dictParam: configuration parameters of taskAutom

	Returns:
		[list]: list of routers.
	"""

	groupColumn = dictParam['dataGroupColumn']

	if dictParam['strictOrder'] == 'yes':

		if dictParam['useHeader'] == 'yes':
			try:
				routers = list(data[groupColumn])
			except Exception as e:
				print("No column header " + str(e) + " in file " + dictParam['data'] + ". Quitting...\n")
				quit()
		else:
			routers = list(data[0])

	else:

		if dictParam['useHeader'] == 'yes':
			try:
				routers = list(data[groupColumn].unique())
			except Exception as e:
				print("No column header " + str(e) + " in file " + dictParam['data'] + ". Quitting...\n")
				quit()				
		else:
			routers = list(data[0].unique())

	return routers

def verifyCronTime(cronTime):
	"""[We verify cronTime before moving on]

	Args:
		cronTime ([list]): [list of parameters]

	Returns:
		[list]
	"""

	dCron = {}

	if cronTime in ['',[],None]:
		dCron['type'] = None
		return dCron
	else:
		cronType = cronTime[0]
		if cronType not in ['oneshot','periodic']:
			print("CronType con only be either 'oneshot' or 'interval'. Quitting ...")
			quit()

		dCron['type'] = cronType
		
		if cronType == 'oneshot':
			if len(cronTime)!=7:
				print('Wrong cronTime length for oneshot. Quitting ...')
				quit()
			else:
				dCron['cronName']   = str(cronTime[1])
				dCron['month']      = str(cronTime[2])
				dCron['weekday']    = str(cronTime[3])
				dCron['dayOfMonth'] = int(cronTime[4])
				dCron['hour']       = int(cronTime[5])
				dCron['minute']     = int(cronTime[6])

		elif cronType == 'periodic':
			if len(cronTime)!=3:
				print('Wrong cronTime length for periodic. Quitting ...')
				quit()
			else:
				dCron['cronName']   = str(cronTime[1])
				dCron['interval']   = int(cronTime[2])			

	if dCron['cronName'][0] in [str(x) for x in range(0,10)]:
		print('Wrong CRON name. First char cannot be a number. Quitting ...')
		quit()		
	elif not re.compile(r'^\S+$').search(dCron['cronName']):
		print('Wrong CRON name. Quitting ...')
		quit()
	
	if dCron['type'] == 'oneshot':

		if dCron['month'] not in [calendar.month_name[x].lower() for x in range(1,13)]:
			print('Wrong month name. Quitting ...')
			quit()

		if dCron['weekday'] not in [calendar.day_name[x].lower() for x in range(0,7)]:
			print('Wrong weekDay name. Quitting ...')
			quit()		

		if dCron['dayOfMonth'] not in list(range(1,32)):
			print('Wrong dayOfMonth value. Quitting ...')
			quit()			

		if dCron['hour'] not in list(range(0,24)):
			print('Wrong hour value. Quitting ...')
			quit()

		if dCron['minute'] not in list(range(0,60)):
			print('Wrong minute value. Quitting ...')
			quit()

	elif dCron['type'] == 'periodic':

		if dCron['interval'] not in list(range(30,42949672)):
			print('Wrong interval value. Quitting ...')
			quit()

	return dCron

def verifyServers(jumpHostsFile):
	"""We verify the SERVERS dictionary before moving on.

	Args:
		SERVERS ([str]): [Name of the file containing servers information in YML format.]

	Returns:
		[dict]: [Dictionary with servers information]
	"""

	try:
		with open(jumpHostsFile,'r') as f:
			servers = yaml.load(f, Loader=yaml.FullLoader)
	except:
		print("Missing " + jumpHostsFile + " file. Quitting..")
		quit()

	fields = ['name','user','password','ip','port']
	for k in servers.keys():
		for f in fields:
			if f in servers[k].keys():
				if not servers[k][f]:
					print('Missing value for field "' + str(f) + '" in server "' + str(k) + '". Quitting...')
					quit()
			else:
				print('Missing field "' + str(f) + '" in server "' + str(k) + '". Quitting...')
				quit()

	# If before checking is ok, we create a new dictionary with correlative keys for those values...
	return servers

def verifyData(dictParam):
	"""[Verify DATA file]

	Args:
		csvFile ([str]): [Name of CSV file]

	Returns:
		[list]: [List of Routers]
	"""

	if dictParam['useHeader'] == 'yes':
		useHeader = 0
	else:
		useHeader = None

	if dictParam['xlsName'] == None:
	
		# We have CSV
		try:
			routers = pd.read_csv(dictParam['data'], header=useHeader)
		except Exception as e:
			print(e)
			print("Error trying to open file " + dictParam['data'] + ". Quitting...\n")
			quit()
	
	else:

		# We have XLSX
		try:
			routers = pd.read_excel(dictParam['data'], sheet_name=dictParam['xlsName'], header=useHeader)
		except Exception as e:
			print(e)
			print("Error trying to open file " + dictParam['data'] + ". Quitting...\n")
			quit()

	return routers

def verifyPlugin(pyFile):
	"""[Verifies the plugin template]

	Args:
		pyFile ([str]): [Name of config template]

	Returns:
		[module]: [The module]
	"""

	try:
		if pyFile.split(".")[-1] == "py":
			# if '/' in pyFile:
			# 	pyFile = pyFile.replace('/','.')
			print(pyFile)
			spec = importlib.util.spec_from_file_location("construir_cliLine",pyFile)
			mod  = importlib.util.module_from_spec(spec)
			sys.modules["construir_cliLine"] = mod
			spec.loader.exec_module(mod)
			#mod  = importlib.import_module(".","showInterface")
			print(mod)
		else:
			print("Missing config file. Verify extension of the file to be '.py'. Quitting...")
			quit()
	except Exception as e:
		print(e)
		print("----\nError importing plugin. Quitting ...")
		quit()

	return mod

def verifyConfigFile(config_file):
	""" This function checks the whole text in order to search for ASCII 
	characters (7bit) since 8bit chars won't allow a proper boot process.
	"""

	charset_allowed = [chr(c) for c in range(128)]

	for i,line in enumerate(config_file.split('\n')):
		for character in line:
			if character not in charset_allowed:
				return i+1, line, character

	return -1,-1

def verifyInventory(inventoryFile, jumpHostsFile):

	columns = ['ip','username','password','deviceType','useSSHTunnel','readTimeOut','jumpHost']

	try:
		df = pd.read_csv(inventoryFile)
	except:
		print("Inventory: The file " + inventoryFile + " was not found. Quitting ...")
		quit()

	for col in df.columns:
		if col not in columns:
			print("Inventory: The field '" + col +  "' is not a valid one. Valids are: " + str(columns) + ". Quitting...")
			quit()

	for col in columns:
		if col not in df.columns:
			print("Inventory: The inventory file ("+inventoryFile+") is missing the field '" + col +  "'. Quitting...")
			quit()			

	df2 = df.copy()
	df2 = df2.fillna("")

	for row in df2.itertuples():

		ip   = row.ip
		jh   = row.jumpHost
		dt   = row.deviceType
		tun  = row.useSSHTunnel
		rto  = row.readTimeOut

		if tun not in ['yes','no','']:
			print("Inventory: The router " + ip + " is not using a valid sshTunnel option. For default, leave empty. Quitting...")
			quit()			

		if tun == 'yes':

			serversList = list(verifyServers(jumpHostsFile).keys()) + ['']

			if jh not in serversList:
				print("Inventory: The router " + ip + " is using sshtunnel and has not a valid jumpHost. If empty, using default. Available: " + str(serversList) + ". Quitting...")
				quit()

		if dt not in list(DICT_VENDOR.keys()) + ['']:
			print("Inventory: The router " + ip + " is not using a valid deviceType. For default, leave empty. Quitting...")
			quit()

		if rto != '':
			try:
				int(rto)
			except:
				print("Inventory: The router " + ip + " has not a valid ReadTimeOut. For default, leave empty. Quitting...")
				quit()				


	df3 = df2.set_index('ip').transpose().to_dict()

	return df3

def renderMop(aluCliLineJob0, dictParam):
	"""[Generates a MOP based on the CSV and plugin information]

	Args:
		aluCliLineJob0 ([file]): [configLines]
		pyFile ([str]):  [The plugin for this MOP]

	Returns:
		None
	"""

	# Verify if DIRECTORY_LOGS exists.
	if not os.path.exists(dictParam['logInfo']):
		os.makedirs(dictParam['logInfo'])

	job0docx = dictParam['logInfo'] + "/job0_" + dictParam['pyFileAlone'] + ".docx"
	job0text = dictParam['logInfo'] + "/job0_" + dictParam['pyFileAlone'] + ".txt"

	if dictParam['genMop'] == 'yes':

		print("\nGenerating MOP: " + job0docx)
		config = aluCliLineJob0.split('\n')
		config = [x for x in config if len(x) > 0]

		myDoc = docx.Document()
		myStyles = myDoc.styles  

		styleConsole = myStyles.add_style('Console', WD_STYLE_TYPE.PARAGRAPH)
		styleConsole.font.name = 'Courier'
		styleConsole.font.size = Pt(9)
		styleConsole.paragraph_format.keep_together = True

		styleConsole.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
		#styleConsole.paragraph_format.line_spacing = Pt(10)
		#styleConsole.paragraph_format.line_spacing = .2
		styleConsole.paragraph_format.space_after = Pt(2)

		myDoc.add_heading('MOP for ' + dictParam['pyFile'], 0)

		for i,row in enumerate(config):

			if i == 0:
				myDoc.add_heading('Configuraciones',1)

			if 'Heading_2' in row.split(":")[0]:
				row = ''.join(row.split(":")[1:])
				subtitle = myDoc.add_paragraph(row)
				subtitle.style = myDoc.styles['Heading 2']
				subtitle.paragraph_format.line_spacing = 1.5

			elif 'Heading_3' in row.split(":")[0]:
				row = ''.join(row.split(":")[1:])
				subtitle = myDoc.add_paragraph(row)
				subtitle.style = myDoc.styles['Heading 3']
				subtitle.paragraph_format.line_spacing = 1.5

			else:
				configText = myDoc.add_paragraph(row)
				configText.style = myDoc.styles['Console']

		myDoc.save(job0docx)
		print("MOP done...")

	with open(job0text,'w') as f:
		f.write(aluCliLineJob0)

def renderCliLine(IPconnect, dictParam, mod, data, i):
	"""
	This function renders the script, based both on the Data file (data) and the plugin (py)
	There are several possibilities for treating the data, depending on the following.

	- groupColumn: how data is filtered
	- strictOrder: if we follow the order described inside the data file
	- useHeader: do we pay attention the headers or use numerals instead?
	- passByRow: do we pass to the module the complete date or only rowByRow? Only valid when strictOrder=no.

	Args:
		IPconnect (_type_): IP of router (or eventually, the grouped data value)
		dictParam (_type_): dictionary of parameters
		mod (_type_):       plugin
		data (_type_):      Pandas DataFrame
		i (_type_):         id which identifies the IPconnect value

	Returns:
		_type_: _description_
	"""

	#   i             0         1        2        3             4                 5     6  7
	#   0     10.3.0.41    ZONA_X  0.0.0.0  0.0.1.3      ROUTER_A  TiMOS-C-16.0.R6      1  4
	#   1     10.3.0.42    ZONA_Y  0.0.0.0  0.0.1.3      ROUTER_B  TiMOS-C-16.0.R6   9886  4
	#   2     10.3.0.43    ZONA_Y  0.0.0.0  0.0.1.3      ROUTER_C  TiMOS-C-16.0.R6   9886  4
	#   3     10.3.0.44    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_D  TiMOS-B-7.0.R7    9886  4
	#   4     10.3.0.45    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_E  TiMOS-B-7.0.R7    9886  4
	#   5     10.3.0.46    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_F  TiMOS-B-9.0.R3    9886  4
	#   6     10.3.0.47    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_G  TiMOS-B-9.0.R3    9886  4
	#   7     10.3.0.48    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_H  TiMOS-B-7.0.R7    9886  4
	#   8     10.3.0.49    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_I  TiMOS-C-19.10.R8  9886  4
	#   9     10.3.0.50    ZONA_Y  0.0.1.3  0.0.1.3      ROUTER_J  TiMOS-B-7.0.R7    9886  4


	aluCliLine  = ""
	groupColumn = dictParam['dataGroupColumn']
	jobType     = dictParam['outputJob'] 
	strictOrder = dictParam['strictOrder']
	useHeader   = dictParam['useHeader']
	plugin      = dictParam['pyFile']
	dataFile    = dictParam['data']
	passByRow   = dictParam['passByRow']

	if jobType == 2:
		mop = None
	elif jobType == 0:
		if i == -1:
			mop = None
		else:
			mop = 1

	if strictOrder == 'no':

		# Since strictOrder = no, then we pass to the module
		# all the data, filterd by IPconnect

		if useHeader == 'yes':
			pluginData = data[data[groupColumn] == IPconnect]
		else:
			pluginData = data[data[0] == IPconnect]

		if passByRow == 'yes':

			# since passByRow is yes, we pass the data to the module row by row
			# hence we apply in here the itertuples() for-loop, which is the default mode.
			# The length of data is len(data)
			# The row order is 'j'

			for j, item in enumerate(pluginData.itertuples()):
				try:
					aluCliLine = aluCliLine + mod.construir_cliLine(j, item, len(pluginData), mop)
				except Exception as e:
					print('\nError: ' + str(e))
					print('Row: ' + str(item))
					print(f'Error trying to use plugin {plugin}.\nVerify variables inside of it, or the data file {dataFile}. Quitting...\n')
					quit()

		else:

			# since passByRow is no, we pass the complete.
			# the itertuples() for-loop, will be needed inside the plugin.
			# this is only possible with strictMode == no.
			# The length of data is len(data)
			# The row order is 'j'
			try:
				aluCliLine = aluCliLine + mod.construir_cliLine(i, pluginData, len(pluginData), mop)
			except Exception as e:
				print('\nError: ' + str(e))
				print(f'Error trying to use plugin {plugin}.\nVerify variables inside of it, or the data file {dataFile}. Quitting...\n')
				quit()			

	else:

		# Since strictOrder = yes, then we pass to the module
		# all the data, row by row, by id i, which comes from 
		# fncRun(). 
		# Then the length of data is always 1.
		# The row order is 0

		try:
			pluginData = list(data.itertuples())[i]
			aluCliLine = mod.construir_cliLine(0, pluginData, 1, mop)
		except Exception as e:
			print('\nError: ' + str(e))
			print('Row: ' + str(pluginData))
			print(f'Error trying to use plugin {plugin}.\nVerify variables inside of it, or the data file {dataFile}. Quitting...\n')
			quit()

	try:
		if len(aluCliLine) > 0:
			if aluCliLine[-1] == "\n":
				aluCliLine = aluCliLine[:-1]
	except:
		print(f'Error trying analyze the DATA file {dataFile}.\nVerify it and make sure that the table is consistent. Quitting...\n')
		quit()		

	if jobType == 2:	

		if len(dictParam['cronTime']) == 0:
			
			pass

		return aluCliLine

	elif jobType == 0:

		return aluCliLine
###

class myConnection(threading.Thread):
	"""
	[Class for connection Object]
	"""

	def __init__(self, thrdNum, config_line, systemIP, dictParam):

		threading.Thread.__init__(self)
		self.script 	      = DICT_VENDOR[dictParam['deviceType']]['START_SCRIPT'] + DICT_VENDOR[dictParam['deviceType']]['FIRST_LINE'] + config_line + DICT_VENDOR[dictParam['deviceType']]['LAST_LINE'] + DICT_VENDOR[dictParam['deviceType']]['FIN_SCRIPT']
		self.outputJob 	      = dictParam['outputJob']
		self.DIRECTORY_LOGS   = dictParam['DIRECTORY_LOGS']
		self.ALU_FILE_OUT_CSV = dictParam['ALU_FILE_OUT_CSV']
		self.logInfo          = dictParam['logInfo']
		self.LOG_TIME         = dictParam['LOG_TIME']
		self.plugin           = dictParam['pyFile']

		# local generated variables
		self.connInfo = {
			'systemIP':systemIP,
			'useSSHTunnel':dictParam['useSSHTunnel'],
			'localPort':-1,
			'remotePort':-1,
			'controlPlaneAccess': False,
			'aluLogged': False,
			'username':dictParam['username'],
			'password':dictParam['password'],
			'aluLogReason':"N/A",
			'hostname':"N/A",
			'timos':"N/A",
			'hwType':"N/A",
			'cronTime':dictParam['cronTime'],
			'sshServer': None,
			'conn2rtr': None,
			'jumpHosts':dictParam['jumpHosts'],
			'inventory':dictParam['inventory'],
			'strictOrder':dictParam['strictOrder'],
			'deviceType':dictParam['deviceType'],
			'pluginType':dictParam['pluginType'],
			'cmdVerify':dictParam['cmdVerify'],
			'readTimeOut':dictParam['readTimeOut'],
			'tDiff':0,
			'runStatus':1,
			'strConn': "Con-" + str(thrdNum) + "| ",
			'num':thrdNum,
			'outRx':'',
			'outRxJson':{},
		}

		# Do we you use jumpHosts?
		if self.connInfo['useSSHTunnel'] == 'yes' or dictParam['inventoryFile'] != None:
			self.connInfo['jumpHost'] = [x for i,x in enumerate(self.connInfo['jumpHosts']) if self.connInfo['num'] % len(self.connInfo['jumpHosts']) == i][0]
		else:
			self.connInfo['jumpHost'] = -1

		# ### Update per router data with information from inventory
		if dictParam['inventoryFile'] != None and self.connInfo['systemIP'] in self.connInfo['inventory'].keys():
			self.tempDict = self.connInfo['inventory'][systemIP]
			for key in self.tempDict.keys():
				if self.tempDict[key] != '':
					self.connInfo[key] = self.tempDict[key]

		# SFTP Port
		self.connInfo['sftpPort'] = DICT_VENDOR[self.connInfo['deviceType']]['SFTP_PORT']

		# Identify connection ports
		if ":" in self.connInfo['systemIP']:
			self.connInfo['remotePort'] = int( self.connInfo['systemIP'].split(":")[1] )			
			self.connInfo['systemIP']   = self.connInfo['systemIP'].split(":")[0]
		else:
			self.connInfo['remotePort'] = DICT_VENDOR[self.connInfo['deviceType']]['REMOTE_PORT']

		# --- Users
		self.ROUTER_USER1    = [self.connInfo['username'],self.connInfo['password']]
		self.ROUTER_USER2    = ["extraUser1","extraPassword1"]
		self.ROUTER_USER3    = ["extraUser2","extraPassword2"]
		self.ROUTER_USER     = [self.ROUTER_USER1]

		# We create a variable to detect if CRON has been established ...
		#self.useCron    = len(self.connInfo['cronTime'])
		
	def run(self):

		# We update the connection info dictionary, after we've set up the connection towards the router...
		self.connInfo.update(self.fncConnectToRouter(self.connInfo))

		if bool(self.connInfo['conn2rtr']) is True and self.connInfo['aluLogged'] is True:
			
			fncPrintConsole(self.connInfo['strConn'] + "#### Auth ok for " + self.connInfo['systemIP'] +  " ...")

			self.connInfo['timos']      = self.fncAuxGetVal(self.connInfo, 'timos')
			self.connInfo['hostname']   = self.fncAuxGetVal(self.connInfo, 'hostname')
			self.connInfo['timosMajor'] = self.fncAuxGetVal(self.connInfo, 'timosMajor')
			self.connInfo['hwType']     = self.fncAuxGetVal(self.connInfo, 'hwType')
			
			if self.outputJob == 2:

				fncPrintConsole(self.connInfo['strConn'] + "#### Running routine for " + self.connInfo['systemIP'] +  " ...")

				if self.connInfo['cronTime']['type'] is not None:

					self.s = self.fncUploadFile(self.script, self.connInfo)

					self.sftpStatus               = self.s[0]
					self.connInfo['aluLogReason'] = self.s[1]
					self.scriptName               = self.s[2]

					if self.sftpStatus == 1:

						self.script   = self.runCron(self.scriptName, self.connInfo)
						self.connInfo = self.routerRunRoutine(self.script, self.connInfo)

				else:
					
					self.connInfo = self.routerRunRoutine(self.script, self.connInfo)
	
				if self.connInfo['runStatus'] == 1:

					fncPrintConsole(self.connInfo['strConn'] + "Logout: " + str(self.connInfo['aluLogReason']))

				else:

					fncPrintConsole(self.connInfo['strConn'] + str(self.connInfo['aluLogReason']))

		self.logData(self.connInfo, self.script, self.logInfo, self.LOG_TIME, self.plugin)

		#######################
		# closing connections #

		if bool(self.connInfo['conn2rtr']) is True or self.connInfo['aluLogged'] is True:
			self.connInfo['conn2rtr'].disconnect()

		if self.connInfo['useSSHTunnel'] == 'yes' and bool(self.connInfo['sshServer']) == True:
			self.connInfo['sshServer'].stop()

		#                     #
		#######################

		return self.connInfo['aluLogReason']

	def fncWriteToConnection(self, inText, connInfo):

		conn2rtr           = connInfo['conn2rtr']
		pluginType         = connInfo['pluginType']
		readTimeOut        = connInfo['readTimeOut']

		expectString       = DICT_VENDOR[connInfo['deviceType']]['SEND_CMD_REGEX']

		outputTxt  = ''
		outputJson = {}		

		if connInfo['cmdVerify'] == 'yes':
			cmdVerify = True
		else:
			cmdVerify = False

		# ### Writes to a connection. 

		if type(inText) == type([]):

			if pluginType == 'config':

				try:
					outputTxt    = conn2rtr.send_config_set(config_commands=inText, enter_config_mode=False, cmd_verify=cmdVerify, read_timeout=readTimeOut)
					aluLogReason = ""
					runStatus    = 1
				except Exception as e:
					outputTxt	 = ''
					aluLogReason = str(e)
					runStatus    = -1						

			elif pluginType == 'show':
				
				try:
					for cmd in inText:
						rx        = conn2rtr.send_command(cmd, expect_string=expectString, cmd_verify=cmdVerify, read_timeout=readTimeOut)
						outputTxt = outputTxt + '\n' + cmd + '\n' + rx
						outputJson[cmd] = rx
					aluLogReason = ""
					runStatus    = 1
				except Exception as e:
					outputTxt    = ''
					aluLogReason = str(e)
					runStatus    = -1

		elif type(inText) == type(''):
			
			try:
				outputTxt    = conn2rtr.send_command(inText, expect_string=expectString, cmd_verify=cmdVerify, read_timeout=readTimeOut)
				aluLogReason = ""
				runStatus    = 1					
			except Exception as e:
				outputTxt    = ''
				aluLogReason = str(e)
				runStatus    = -1

		return runStatus, aluLogReason, outputTxt, outputJson

	def fncAuxGetVal(self, connInfo, what):

		if what == "timos":

			inText  = DICT_VENDOR[connInfo['deviceType']]['VERSION']
			runStatus, aluLogReason, rx, _ = self.fncWriteToConnection(inText, connInfo)
			inRegex = DICT_VENDOR[connInfo['deviceType']]['VERSION_REGEX']
			match   = re.compile(inRegex).search(rx)

			try:
				timos   = match.groups()[0]
			except:
				timos   = "not-matched"

			return timos

		elif what == 'hostname':

			inText  = DICT_VENDOR[connInfo['deviceType']]['HOSTNAME']
			runStatus, aluLogReason, rx, _ = self.fncWriteToConnection(inText, connInfo)
			inRegex = DICT_VENDOR[connInfo['deviceType']]['HOSTNAME_REGEX']
			match   = re.compile(inRegex).search(rx)

			try:
				hostname = match.groups()[0]
			except:
				hostname = "host_" + str(connInfo['num']) + "_not-matched"

			return hostname

		elif what == 'hwType':

			inText  = DICT_VENDOR[connInfo['deviceType']]['HW_TYPE']
			runStatus, aluLogReason, rx, _ = self.fncWriteToConnection(inText, connInfo)
			inRegex = DICT_VENDOR[connInfo['deviceType']]['HW_TYPE_REGEX']
			match   = re.compile(inRegex).search(rx)

			try:
				hwType = match.groups()[0]
			except:
				hwType = "not-matched"

			return hwType			

		elif what == "timosMajor":

			try:
				timosMajor = int(self.connInfo['timos'].split("-")[2].split(".")[0])
			except:
				timosMajor = "not-matched"

			return timosMajor	

	def fncConnectToRouter(self, connInfo):
		"""[We update the connection info dictionary, after we've set up the connection towards the router]

		Args:
			connInfo ([dict]): [Contains all conection related relevant information ]

		Returns:
			[dict]: [Updated connInfo dictionary]
		"""

		### SSH Tunnel

		if connInfo['useSSHTunnel'] == 'yes':

			connInfo = self.fncSshServer(connInfo)

		else:

			fncPrintConsole(connInfo['strConn'] + "Using direct " + connInfo['deviceType'] + " access: ")
			fncPrintConsole(connInfo['strConn'] + "Trying router " + connInfo['systemIP'] + ":" + str(connInfo['remotePort']) )

			connInfo['controlPlaneAccess'] 	= True	
			connInfo['localPort'] 			= connInfo['remotePort']
			connInfo['sshServer']    		= None

		### Connect to router

		if connInfo['controlPlaneAccess'] is True:

			connInfo = self.routerLogin(connInfo)

		else:

			connInfo['conn2rtr']     = None
			connInfo['aluLogged'] 	 = False
			connInfo['username']     = "N/A"
			connInfo['password']     = "N/A"

		return connInfo

	def fncUploadFile(self, datos, connInfo):
		### upload configFile via SFTP

		fileRemote = connInfo['hostname'] + "_commands.cfg"
		fileLocal  = self.DIRECTORY_LOGS + fileRemote

		# We write here the contents of the data to be run inside the CRON
		# We hence don't log it thereafter.
		with open(fileLocal,'w') as fc:
			fc.write(datos)

		out = [-1,'sftpError',fileRemote]

		if connInfo['useSSHTunnel'] == 'yes':

			sshSftp       = self.fncSshServer(connInfo, sftp=True)
			sftpPort      = sshSftp['localPort']
			sshServerSftp = sshSftp['server']

			transport = paramiko.Transport((IP_LOCALHOST,sftpPort))
			transport.connect(None,connInfo['username'],connInfo['password'])

			# The routers with timos above 6.X do support SFTP.
			# Otherwise we need to use SCP.

			if connInfo['timosMajor'] > 6:
				fncPrintConsole(connInfo['strConn'] + "uploading file: SFTP: " + str(sftpPort))
				sftp = paramiko.SFTPClient.from_transport(transport)
			else:
				fncPrintConsole(connInfo['strConn'] + "uploading file: SCP: " + str(sftpPort))
				sftp = SCPClient(transport)

			try:
				sftp.put(fileLocal,'cf3:/' + fileRemote)
				out = [1,'sftpOk',fileRemote]
			except:
				out = [-1,'sftpError',fileRemote]

			sftp.close()
			transport.close()
			sshServerSftp.stop()

		else:

			transport = paramiko.Transport((connInfo['systemIP'], connInfo['sftpPort']))
			transport.connect(None,connInfo['username'],connInfo['password'])

			if connInfo['timosMajor'] > 6:
				fncPrintConsole(connInfo['strConn'] + "uploading file: SFTP: " + str(connInfo['sftpPort']))
				sftp = paramiko.SFTPClient.from_transport(transport)
			else:
				fncPrintConsole(connInfo['strConn'] + "uploading file: SCP: " + str(connInfo['sftpPort']))
				sftp = SCPClient(transport)

			try:
				sftp.put(fileLocal,'cf3:/' + fileRemote)
				out = [1,'sftpOk',fileRemote]
			except:
				out = [-1,'sftpError',fileRemote]

			sftp.close()
			transport.close()

		return out

	def fncSshServer(self, connInfo, sftp=False):

		controlPlaneAccess = False
		localPort 		   = -1
		server             = -1	
		aluLogReason       = '-1'		

		jumpHost = connInfo['jumpHost']
		servers  = connInfo['jumpHosts']

		tempIp   = servers[jumpHost]['ip']
		tempPort = servers[jumpHost]['port']
		tempUser = servers[jumpHost]['user']
		tempPass = servers[jumpHost]['password']

		if sftp:
			remotePort = connInfo['sftpPort']
		else:
			remotePort = connInfo['remotePort']

		systemIP = connInfo['systemIP']

		try:

			server = sshtunnel.SSHTunnelForwarder( 	(tempIp, tempPort), 
												ssh_username = tempUser, 
												ssh_password = tempPass, 
												remote_bind_address = (systemIP, remotePort),
												allow_agent = False,
											)

		except Exception as e:

			aluLogReason = str(e)
			server = -1
			fncPrintConsole(connInfo['strConn'] + str(aluLogReason))

		if server != -1:
			server.start()
			localPort = server.local_bind_port

			fncPrintConsole(connInfo['strConn'] + "Trying sshServerTunnel on port: " + str(localPort))
			fncPrintConsole(connInfo['strConn'] + "Trying router " + IP_LOCALHOST + ":" + str(localPort) + " -> " + connInfo['systemIP'] + ":" + str(connInfo['remotePort']))

			server.check_tunnels()

			if server.tunnel_is_up[('0.0.0.0',localPort)] == False:
				fncPrintConsole(connInfo['strConn'] + "Error SSH Tunnel")
				aluLogReason = 'Error SSH Tunnel'
				server.stop()
			else:
				controlPlaneAccess = True

		connInfo['aluLogReason']       = aluLogReason
		connInfo['controlPlaneAccess'] = controlPlaneAccess
		connInfo['localPort']          = localPort
		connInfo['server']             = server

		return connInfo

	def routerLogin(self, connInfo):

		conn2rtr   = None
		aluLogged  = False
		index      = 0

		systemIP   = connInfo['systemIP']
		deviceType = connInfo['deviceType']	

		if connInfo['useSSHTunnel'] == 'yes':
			ip   = IP_LOCALHOST
			port = connInfo['localPort']
		else:
			ip   = connInfo['systemIP']
			port = connInfo['remotePort']

		while aluLogged == False and index < len(self.ROUTER_USER):

			tempUser = self.ROUTER_USER[index][0]
			tempPass = self.ROUTER_USER[index][1]
			index 	 = index + 1

			try:
				conn2rtr = ConnectHandler(device_type=deviceType, host=ip, port=port, username=tempUser, password=tempPass, fast_cli=False)
				aluLogged    = True
				aluLogReason = "LoggedOk"
				aluLogUser   = tempUser
				aluPass      = tempPass
			except Exception as e:
				conn2rtr     = None
				aluLogged 	 = False
				aluLogReason = str(e)				
				aluLogUser   = tempUser
				aluPass      = "PassN/A"
				fncPrintConsole(connInfo['strConn'] + aluLogReason + ": " + systemIP)

		connInfo['conn2rtr']     = conn2rtr
		connInfo['aluLogged']    = aluLogged
		connInfo['aluLogUser']   = aluLogUser
		connInfo['aluLogReason'] = aluLogReason
		connInfo['tempPass']     = tempPass

		return connInfo

	def routerRunRoutine(self, datos, connInfo):

		# Sending script to ALU
		tStart 		 = time.time()

		major_error_list = DICT_VENDOR[connInfo['deviceType']]['MAJOR_ERROR_LIST']
		minor_error_list = DICT_VENDOR[connInfo['deviceType']]['MINOR_ERROR_LIST']
		info_error_list  = DICT_VENDOR[connInfo['deviceType']]['INFO_ERROR_LIST']

		if connInfo['cronTime']['type'] is not None:
			fncPrintConsole(connInfo['strConn'] + "Establishing script with CRON...", show=1)
		else:
			fncPrintConsole(connInfo['strConn'] + "Running script per line...", show=1)

		datos = datos.split('\n')
		runStatus, aluLogReason, outRx, outRxJson = self.fncWriteToConnection(datos, connInfo)

		tEnd  = time.time()
		tDiff = tEnd - tStart

		## Analizing output only if writing to connection was successfull
		if aluLogReason == "":
			
			if any([re.compile(error, flags=re.MULTILINE).search(outRx) for error in major_error_list]):
				aluLogReason = "MajorFailed"
			elif any([re.compile(error, flags=re.MULTILINE).search(outRx) for error in minor_error_list]):				
				aluLogReason = "MinorFailed"
			elif any([re.compile(error, flags=re.MULTILINE).search(outRx) for error in info_error_list]):
				aluLogReason = "InfoFailed"
			else:
				aluLogReason = "SendSuccess"

		fncPrintConsole(connInfo['strConn'] + "Time: " + fncFormatTime(tDiff) + ". Result: " + aluLogReason, show=1)

		connInfo['aluLogReason'] = aluLogReason
		connInfo['runStatus']    = runStatus
		connInfo['tDiff']        = tDiff
		connInfo['outRx']        = outRx
		connInfo['outRxJson']    = outRxJson

		return connInfo

	def logData(self, connInfo, script, logInfo, LOG_TIME, plugin):

		# Filenames
		aluFileCommands  = self.DIRECTORY_LOGS + connInfo['hostname'] + "_commands.cfg"
		aluFileOutRx	 = self.DIRECTORY_LOGS + connInfo['hostname'] + "_rx.txt"
		aluFileOutRxJson = self.DIRECTORY_LOGS + connInfo['hostname'] + "_rx.json"

		outRx     = connInfo['outRx']
		outRxJson = connInfo['outRxJson']

		if connInfo['aluLogged'] == True and connInfo['cronTime']['type'] is None:

			with open(aluFileCommands,'a') as fc:
				fc.write(script)

		if connInfo['aluLogged'] == True:

			with open(aluFileOutRx,'a') as fw:
				fw.write(outRx)

		if connInfo['aluLogged'] == True and outRxJson != {}:

			if not os.path.isfile(aluFileOutRxJson):
				with open(aluFileOutRxJson,'w') as fj:
					outRxJson['name'] = connInfo['hostname']
					outRxJson['ip']   = connInfo['systemIP']
					json.dump(outRxJson,fj)
			else:
				with open(aluFileOutRxJson) as fj:
					data      = json.load(fj)
				with open(aluFileOutRxJson,'w') as fj:
					outRxJson = dict(list(outRxJson.items()) + list(data.items()))
					json.dump(outRxJson,fj)

		if connInfo['useSSHTunnel'] == 'yes':

			serverName = connInfo['jumpHost']
			lenServers = len(connInfo['jumpHosts'])

		else:

			serverName = '-1'
			lenServers = '-1'

		aluCsvLine = [
			LOG_TIME,
			logInfo,
			plugin,
			connInfo['pluginType'],
			connInfo['cmdVerify'],
			connInfo['systemIP'],
			connInfo['timos'],
			connInfo['hostname'],
			connInfo['hwType'],
			connInfo['username'],
			connInfo['aluLogReason'],
			str(connInfo['num']),
			str(connInfo['localPort']),
			serverName,
			connInfo['deviceType'],
			str(len(script.split('\n'))),
			str(len(outRx.split('\n'))),
			float(fncFormatTime(connInfo['tDiff'], adjust=False)),
			str(connInfo['readTimeOut']),
			str(lenServers),
			]

		fncPrintConsole(connInfo['strConn'] + "logData: " + str(aluCsvLine))

		LOG_GLOBAL.append(aluCsvLine)

	def sshStop(self, connInfo):
		self.sshServer.stop()
		fncPrintConsole(connInfo['strConn'] + "SSH" + str(connInfo['num']) + " stopped ...")

	def runCron(self, script, connInfo):

		def setScript(cronName, script):

			cfg = ""
			cfg = cfg + f'script "{cronName}" owner "taskAutom"\nshutdown\n'
			cfg = cfg + f'location cf3:\{script}\n'
			cfg = cfg + 'no shutdown\n'
			cfg = cfg + 'exit\n'
			return cfg

		def action(cronName):

			cfg = ""
			cfg = cfg + f'action "{cronName}" owner "taskAutom"\nshutdown\n'
			cfg = cfg + 'results cf3:\\resultTestCron.txt\n'
			cfg = cfg + f'script "{cronName}" owner "taskAutom"\n'
			cfg = cfg + 'no shutdown\n'
			cfg = cfg + 'exit\n'
			return cfg

		def policy(cronName):

			cfg = ""
			cfg = cfg + f'script-policy "{cronName}" owner "taskAutom"\nshutdown\n'
			cfg = cfg + 'results cf3:\\resultTestCron.txt\n'
			cfg = cfg + f'script "{cronName}" owner "taskAutom"\n'
			cfg = cfg + 'no shutdown\n'
			cfg = cfg + 'exit\n'
			return cfg

		def schedule(connInfo):

			timos    = connInfo['timosMajor']
			cronName = connInfo['cronTime']['cronName']
			cronType = connInfo['cronTime']['type']

			cfg = ""
			cfg = cfg + f'schedule "{cronName}" owner "taskAutom"\nshutdown\n'

			if timos > 7:
				cfg = cfg + f'script-policy "{cronName}" owner "taskAutom"\n'
			else:
				cfg = cfg + f'action "{cronName}" owner "taskAutom"\n'

			if cronType == 'oneshot':

				dayOfMonth = str(connInfo['cronTime']['dayOfMonth'])
				hour       = str(connInfo['cronTime']['hour'])
				minute     = str(connInfo['cronTime']['minute'])
				month      = str(connInfo['cronTime']['month'])
				weekday    = str(connInfo['cronTime']['weekday'])
			
				cfg = cfg + 'type oneshot\n'
				cfg = cfg + f'day-of-month "{dayOfMonth}"\n'
				cfg = cfg + f'hour "{hour}"\n'
				cfg = cfg + f'minute "{minute}"\n'
				cfg = cfg + f'month "{month}"\n'
				cfg = cfg + f'weekday "{weekday}"\n'
				cfg = cfg + 'no shutdown \n'
				cfg = cfg + 'exit\n'
				cfg = cfg + 'exit all\n'
				cfg = cfg + 'admin save\n'

			elif cronType == 'periodic':

				interval = str(connInfo['cronTime']['interval'])

				cfg = cfg + 'type periodic\n'
				cfg = cfg + f'interval {interval}\n'
				cfg = cfg + 'no shutdown \n'
				cfg = cfg + 'exit all\n'
				cfg = cfg + 'admin save\n'				


			return cfg

		cronName   = connInfo['cronTime']['cronName']

		start_script = DICT_VENDOR[connInfo['deviceType']]['START_SCRIPT']

		cfg = ""

		if connInfo['timosMajor'] > 7:

			cfg = cfg + "/configure system script-control\n"
			cfg = cfg + setScript(cronName, script)
			cfg = cfg + policy(cronName)
			cfg = cfg + "/configure system cron\n"
			cfg = cfg + schedule(connInfo)

		else:

			cfg = cfg + "/configure cron\n"
			cfg = cfg + setScript(cronName, script)
			cfg = cfg + action(cronName)
			cfg = cfg + schedule(connInfo)

		cfg = "/environment no more\n" + cfg

		return cfg

####################################
# Main Functions                   #
####################################

def getDictParam():

	parser = argparse.ArgumentParser(description='taskAutom Parameters.', prog='taskAutom', usage='%(prog)s [options]')
	parser.add_argument('-v'  ,'--version',     help='Version', action='version', version='Lucas Aimaretto - (c)2022 - laimaretto@gmail.com - Version: 7.17.6' )

	groupJobTypes = parser.add_argument_group('JobTypes')
	groupJobTypes.add_argument('-j'  ,'--jobType',       type=int, required=True, choices=[0,2], default=0, help='Type of job. j=0 to check data and plugin; j=2, to execute.')

	groupPugin = parser.add_argument_group('Plugin')
	groupPugin.add_argument('-pt' ,'--pluginType',    type=str, help='Type of plugin.', choices=['show','config'])
	groupPugin.add_argument('-py' ,'--pyFile' ,       type=str, required=True, help='PY Template File')

	groupData = parser.add_argument_group('Data Related')
	groupData.add_argument('-d'  ,'--data',          type=str, required=True, help='DATA File with parameters. Either CSV or XLSX. If XLSX, enable -xls option with sheet name.')
	groupData.add_argument('-log','--logInfo' ,      type=str, required=True, help='Description for log folder. Logs, MOP and scripts will be stored here.', )
	groupData.add_argument('-gc' ,'--dataGroupColumn',type=str, help='Only valid if using headers. Name of column, in the data file, to filter routers by. In general one should use the field where the IP of the router is. Default=ip', default='ip')
	groupData.add_argument('-uh', '--useHeader',     type=str, help='When reading data, consider first row as header. Default=yes', default='yes', choices=['no','yes'])
	groupData.add_argument('-xls' ,'--xlsSheetName',      type=str, help='Excel sheet name')
	groupData.add_argument('-so', '--strictOrder',   type=str, help='Follow strict order of routers inside the data file, row by row. If enabled, threads=1. Default=no', default='no', choices=['no','yes'])
	groupData.add_argument('-hoe','--haltOnError',   type=str, help='If using --strictOrder=yes, halts if error found on execution. Default=no', default='no', choices=['no','yes'])
	groupData.add_argument('-pbr', '--passByRow',    type=str, help='Pass data to the plugin by row (and filtered by -gc/--dataGroupColumn). Only valid with --strictOrder=no. Default=yes', default='yes', choices=['yes','no'])	

	credentialsGroup = parser.add_argument_group('Credentials')
	credentialsGroup.add_argument('-u'  ,'--username',      type=str, help='Username to connect to router.', )
	credentialsGroup.add_argument('-pf' ,'--passwordFile',  type=str, help='Filename containing the default password to access the routers. If the file contains several lines of text, only the first line will be considered as the password. Default=None', default=None)
	
	connGroup = parser.add_argument_group('Connection parameters')
	connGroup.add_argument('-th' ,'--threads' ,      type=int, help='Number of threads. Default=1', default=1,)
	connGroup.add_argument('-tun','--sshTunnel',     type=str, help='Use SSH Tunnel to routers. Default=yes', default='yes', choices=['no','yes'])
	connGroup.add_argument('-jh' ,'--jumpHostsFile', type=str, help='jumpHosts file. Default=servers.yml', default='servers.yml')
	connGroup.add_argument('-dt', '--deviceType',    type=str, help='Device Type. Default=nokia_sros', default='nokia_sros', choices=['nokia_sros','nokia_sros_telnet'])
	connGroup.add_argument('-cv', '--cmdVerify',     type=str, help='Enable --cmdVerify when interacting with router. Disable only if connection problems. Default=yes', default='yes', choices=['no','yes'])
	connGroup.add_argument('-rto' ,'--readTimeOut',  type=int, help='Read Timeout. Time in seconds which to wait for data from router. Default=10', default=10,)
	connGroup.add_argument('-tbr' ,'--timeBetweenRouters',  type=int, help='Time to wait before sending scripts to the router. Default=0', default=0,)


	miscGroup = parser.add_argument_group('Misc')
	miscGroup.add_argument('-inv','--inventoryFile', type=str, help='Inventory file with per router connection parameters. Default=None', default=None)
	miscGroup.add_argument('-gm', '--genMop',        type=str, help='Generate MOP document in docx format. Default=no', default='no', choices=['no','yes'])
	miscGroup.add_argument('-crt','--cronTime',      type=str, nargs='+' , help='Data for CRON: name(ie: test), type(ie: oneshot or interval).\nIf type=oneshot, need to define: month(ie april), weekday(ie monday), day-of-month(ie 28), hour(ie 17), minute(ie 45). If type=interval, interval in seconds.', default=[])
	miscGroup.add_argument('-sd', '--sshDebug',      type=str, help='Enables debuging of SSH interaction with the network. Stored on debug.log. Default=no', default='no', choices=['no','yes'])

	args = parser.parse_args()

	### reading parameters

	dictParam = dict(
		outputJob 			= args.jobType,
		data                = args.data,
		xlsName             = args.xlsSheetName,
		useHeader           = args.useHeader,
		passByRow           = args.passByRow,
		pyFile              = args.pyFile,
		username 			= args.username,
		passwordFile        = args.passwordFile,
		password 			= None,
		progNumThreads		= args.threads,
		logInfo 			= args.logInfo,
		useSSHTunnel 		= args.sshTunnel,
		cronTime            = args.cronTime,
		jumpHostsFile       = args.jumpHostsFile,
		genMop              = args.genMop,
		strictOrder         = args.strictOrder,
		haltOnError         = args.haltOnError,
		inventoryFile       = args.inventoryFile,
		deviceType          = args.deviceType,
		pluginType          = args.pluginType,
		cmdVerify           = args.cmdVerify,
		sshDebug            = args.sshDebug,
		dataGroupColumn     = args.dataGroupColumn,
		readTimeOut         = args.readTimeOut,
		timeBetweenRouters  = args.timeBetweenRouters,
	)

	dictParam['pyFileAlone'] = dictParam['pyFile'].split('/')[-1]

	################
	# Checking...

	# CronTime
	dictParam['cronTime'] = verifyCronTime(dictParam['cronTime'])
	if dictParam['cronTime']['type'] is not None:
		dictParam['pluginType']  = 'config'
		dictParam['strictOrder'] = 'no'

	# Servers
	dictParam['jumpHosts'] = {}
	if dictParam['useSSHTunnel'] == 'yes' or dictParam['inventoryFile'] != None:
		dictParam['jumpHosts'] = verifyServers(dictParam['jumpHostsFile'])

	# Inventory
	dictParam['inventory'] = {}
	if dictParam['inventoryFile'] != None:
		dictParam['inventory'] = verifyInventory(dictParam['inventoryFile'], dictParam['jumpHostsFile'])

	# Strict Order
	if dictParam['strictOrder'] == 'yes':
		dictParam['progNumThreads'] = 1
		dictParam['passByRow'] = 'yes'	

	return dictParam

def checkCredentials(dictParam):

	if dictParam['outputJob'] == 0:

		#fncRun(dictParam)
		pass

	elif (	
		dictParam['outputJob'] == 2 and 
		dictParam['username'] and 
		dictParam['passwordFile'] is None and 
		dictParam['logInfo'] and 
		(
			dictParam['pluginType'] or dictParam['cronTime']
		)
		):

		print("\n#######################################")
		print("# About to run. Ctrl+C if not sure... #")
		print("#######################################\n")
		dictParam['password'] = getpass("### -> PASSWORD (default user: " + dictParam['username'] + "): ")

		#fncRun(dictParam)
		pass

	elif (
		dictParam['outputJob'] == 2 and 
		dictParam['username'] and 
		dictParam['passwordFile'] is not None and 
		dictParam['logInfo'] and 
		(
			dictParam['pluginType'] or dictParam['cronTime']
		)		
	):	

		# Trying to open the password file to obtain the password
		with open(dictParam['passwordFile']) as pf:
			dictParam['password'] = pf.readlines()[0].rstrip()
		
		#fncRun(dictParam)
		pass

	else:

		print("Not enough paramteres.\nAt least define --username, --logInfo and --pluginType.\nRun: taskAutom -h for help.\nQuitting...")
		quit()

	return dictParam

def fncRun(dictParam):
	"""[summary]

	Args:
		dictParam ([dict]): [Dictionary with parameters for the connections]
	Returns:
		[int]: 0
	"""
	dictParam = checkCredentials(dictParam)

	# DATA file
	data = verifyData(dictParam)

	# Config File
	mod = verifyPlugin(dictParam['pyFile'])

	# We obatin the list of routers to trigger connections
	routers = getListOfRouters(data, dictParam)

	# We take initial time 
	timeTotalStart 	= time.time()

	# Generar threads
	threads_list 	= ThreadPool(dictParam['progNumThreads'])
	global global_lock
	global_lock     = threading.Lock()

	## Netmiko Debug
	if dictParam['sshDebug'] == 'yes':
		logging.basicConfig(filename='debug.log', level=logging.DEBUG)
		logger = logging.getLogger("netmiko")

	################
	# Running...
	if dictParam['outputJob'] == 2:

		# logInfo
		dictParam['LOG_TIME']         = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
		dictParam['DIRECTORY_LOGS']   = os.getcwd() + "/logs_" + dictParam['LOG_TIME'] + "_" + dictParam['logInfo'] + "_" + dictParam['pyFileAlone'] + "/"
		dictParam['ALU_FILE_OUT_CSV'] = dictParam['DIRECTORY_LOGS'] + "00_log.csv"

		# Verify if DIRECTORY_LOGS exists. If so, ask for different name ...
		if os.path.exists(dictParam['DIRECTORY_LOGS']):
			print("Folder " + dictParam['DIRECTORY_LOGS'] + " already exists.\nUse a different folder name.\nQuitting ...")
			quit()
		else:
			os.makedirs(dictParam['DIRECTORY_LOGS'])
			open(dictParam['ALU_FILE_OUT_CSV'],'w').close()

		###############
		# Let's run ....
		for i, IPconnect in enumerate(routers):

			# The rendering behavior of the script = f(data,plugin,groupColumn) depends on
			#
			# - strictOrder = yes/no
			# - passByRow   = yes/no
			#
			# Depending on that, taskAutom will handle differently the data and
			# the order of connections.

			aluCliLine = renderCliLine(IPconnect, dictParam, mod, data, i)

			# Wait before sending scripts to the routers ...
			if dictParam['timeBetweenRouters'] > 0:
				print("Waiting " + str(dictParam['timeBetweenRouters']) + "s ...")
				time.sleep(dictParam['timeBetweenRouters'])

			# running routine
			if dictParam['strictOrder'] == 'no':
				threads_list.apply_async(run_mi_thread, args=(i, aluCliLine, IPconnect, dictParam))
			else:
				aluLogReason = run_mi_thread(i, aluCliLine, IPconnect, dictParam)

				if dictParam['haltOnError'] == 'yes' and aluLogReason not in ['SendSuccess']:
					dictParam['aluLogReason'] = aluLogReason
					break

		if dictParam['strictOrder'] == 'no':
			threads_list.close()
			### The .join() implies that processes/threads need to finish themselves before moving on.
			threads_list.join()

		print("all done")
		fncPrintResults(routers, timeTotalStart, dictParam, dictParam['DIRECTORY_LOGS'], dictParam['ALU_FILE_OUT_CSV'])

	elif dictParam['outputJob'] == 0:

		aluCliLineJob0 = ""

		# Verify if DIRECTORY_LOGS exists.
		if not os.path.exists(dictParam['logInfo']):
			os.makedirs(dictParam['logInfo'])		

		for i, IPconnect in enumerate(routers):

			# We firt do a rendeCli() for the router IPConnect and save the file
			tempFname = dictParam['logInfo'] + '/' + 'job0_' + IPconnect + '.cfg'
			tempCfg   = renderCliLine(IPconnect, dictParam, mod, data, i=-1)

			with open(tempFname,'w') as f:
				f.write(tempCfg)

			# We do a second call the the renderCli() to save a global file.
			aluCliLineJob0 = aluCliLineJob0 + renderCliLine(IPconnect, dictParam, mod, data, i)

		verif = verifyConfigFile(aluCliLineJob0)

		if verif != (-1,-1):
			print("\nWrong config file for router " + str(IPconnect) + "\nCheck (n,line,char): " + str(verif) + "\nQuitting...")
			quit()			

		renderMop(aluCliLineJob0, dictParam)
		fncPrintResults(routers, timeTotalStart, dictParam)

	return dictParam

def main():

	### Ready to go ...
	dictParam = getDictParam()
	fncRun(dictParam)

### To be run from the python shell
if __name__ == '__main__':
	main()