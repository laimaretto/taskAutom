# Copyright (C) 2015-2020 Lucas Aimaretto / laimaretto@gmail.com
#
# This is taskAutom
#
# taskAutom is free software: you can redistribute it and/or modify
# it under the terms of the 3-clause BSD License.
#
# taskAutom is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY of any kind whatsoever.
#

import paramiko
from sshtunnel import SSHTunnelForwarder
from netmiko import ConnectHandler
from scp import SCPClient
import pandas as pd

import docx
from docx.enum.style import WD_STYLE_TYPE 
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Pt

import yaml
import sys
import telnetlib
import ftplib
import os
import csv
import time
import threading
from multiprocessing.pool import ThreadPool
from operator import itemgetter
from itertools import groupby
import logging
import importlib
import re
import argparse
from getpass import getpass
import re
import calendar
import random
#logging.basicConfig(level=logging.DEBUG,format='[%(levelname)s] (%(threadName)-10s) %(message)s')

# Variables Login
IP_LOCALHOST          	 = "127.0.0.1"

ROUTER_TELNET_PORT       = 23
ROUTER_SSH_PORT          = 22
ROUTER_FTP_PORT          = 21


# --- Users
ROUTER_USER1 			 = [None,None]
ROUTER_USER2 			 = ["extraUser1","extraPassword1"]
ROUTER_USER3 			 = ["extraUser2","extraPassword2"]
#ROUTER_USER  			 = [ROUTER_USER1,ROUTER_USER2,ROUTER_USER3]
ROUTER_USER  			 = [ROUTER_USER1]

# --- Timers
ALU_TIME_LOGIN           = 5
ALU_TELNET_WRITE_TIMEOUT = 0
SAM_TIME_LOGIN           = 10
ALU_TIME_DIFF			 = 1
PROMPT_TIMEOUT           = ALU_TIME_LOGIN

# --- Prompts
ALU_PROMPT_CLOSED         = [b"closed by foreign host"]
ALU_PROMPT_LOGOUT		  = [b"# logout"]
ALU_PROMPT_FTP_LOGOUT     = [b"221 Bye!"]
ALU_PROMPT_LOGIN          = [b"Login:"]
ALU_PROMPT_FTP_LOGIN      = [b"220 FTP server ready"]
ALU_PROMPT_FTP_BIN_MODE   = [b"binary mode"]
ALU_PROMPT_FTP_TXFER      = [b"226 Transfer complete"]
ALU_PROMPT_PASS           = [b"Password:"]
#ALU_PROMPT                = [b"A:.*#",b"A:.*>.*#",b"B:.*#",b"B:.*>.*#"]
ALU_PROMPT                = [b"(A:|B:)(.+)(>|#)"]
ALU_TIMOS_LOGIN           = [b"(TiMOS-[A-Z]-\d{1,2}.\d{1,2}.R\d{1,2})"]
ALU_TIMOS_SSH             = "(TiMOS-[A-Z]-\d{1,2}.\d{1,2}.R\d{1,2})"
ALU_HOSTNAME              = [b"(A:|B:)(.+)(>|#)"]
ALU_HOSTNAME_SSH          = "(A:|B:)(.+)(>|#)"
ALU_PROMPT_FTP            = [b"ftp>"]
ALU_MAJOR_ERROR_LIST      = [b"FAILED:",b"invalid token",b"ERROR:",b"not allowed",b"Error"]
ALU_MINOR_ERROR_LIST	  = [b"MINOR:"]
ALU_START_SCRIPT 		  = "SCRIPT_NONO_START"
ALU_FIN_SCRIPT			  = "SCRIPT_NONO_FIN"

# --- Extras
CH_CR					  = "\n"
CH_COMA 				  = ","

####

def fncPrintResults(outputJob, ALU_TELNET_READ_TIMEOUT, useSSHTunnel, clientType, progNumThreads, aluConfigFileModule, aluFileCsv, routers, timeTotalStart, LogInfo='', cronTime=[], delayFactor=1, DIRECTORY_LOG_INFO='', ALU_FILE_OUT_CSV=''):
	print("\n------ * ------")
	print("Template File:              " + aluConfigFileModule + ".py")
	print("CSV File:                   " + aluFileCsv)
	print("MOP filename                " + "job0_" + aluConfigFileModule + ".docx\n")
	print("Total Routers:              " + str(len(routers)))
	if useSSHTunnel == 1:
		print("Use SSH tunnel:             " + str(useSSHTunnel) +" ("+ str(len(SERVERS)) +")" )
	else:
		print("Use SSH tunnel:             " + str(useSSHTunnel) )
	print("Client Type:                " + str(clientType))
	print("Total Threads:              " + str(progNumThreads))
	print("Telnet Timeout:             " + str(ALU_TELNET_READ_TIMEOUT) + "s")
	print("SSH Delay Factor:           " + str(delayFactor))

	if LogInfo:
		print("Additional Info:            " + LogInfo)
	else:
		print("Additional Info:            " + "None")

	if len(cronTime):
		print("CRON Config:                " + str(cronTime))
	else:
		print("CRON Config:                " + "None")

	if outputJob > 0:

		timeTotalEnd 	= time.time()
		timeTotal 		= timeTotalEnd - timeTotalStart		

		print("\n------ * ------")

		with open(ALU_FILE_OUT_CSV,'r') as fLog:
			reader 	= csv.reader(fLog)
			routers = list(reader)

		timeLog = [float(row[len(row)-1]) for row in routers]

		print("timeTotal:                  " + fncFormatTime(timeTotal) + "s")
		print("timeMin                     " + fncFormatTime(min(timeLog)) + "s")
		print("timeAvg:                    " + fncFormatTime(sum(timeLog)/len(routers)) + "s")
		print("timeMax:                    " + fncFormatTime(max(timeLog)) + "s")
		print("timeTotal/Routers:          " + fncFormatTime(timeTotal/len(routers)) + "s")
		print("\n------ * ------")

		df = pd.DataFrame(routers,columns=['DateTime','LogInfo','Plugin','IP','HostName','User','Reason','id','port','server','clientType','txLines','rxLines','time'])
		df.to_csv(ALU_FILE_OUT_CSV,index=False)

		dfFailed = df[df['Reason'] != 'SendSuccess']
		print("\nFailed routers:             " + str(len(dfFailed)))
		if len(dfFailed) > 0:
			print(dfFailed)

		dfRun         = pd.read_csv(aluFileCsv, header=None)

		errorRouters  = list(df[df['HostName'].isnull()]['IP'])
		failedRouters = list(df[df['Reason'] != 'SendSuccess']['IP'])
		
		dfError       = dfRun[dfRun[0].isin(errorRouters)]
		dfError.to_csv('dfError_' + aluFileCsv, index=False, header=False)
		dfFailed      = dfRun[dfRun[0].isin(failedRouters)]
		dfFailed.to_csv('dfFailed_' + aluFileCsv, index=False, header=False)

		print("\n------ * ------")
		print(df.groupby(['Reason']).agg({'Reason':['count'],'time':['min','max']}))

	print("------ * ------\n")

def fncFormatTime(timeFloat):

	move = 100

	return str( float(int(timeFloat*move))/move )

def fncPrintConsole(inText, show=1):
	#logging.debug(inText)
	localtime   = time.localtime()
	if show:
		print(str(time.strftime("%H:%M:%S", localtime)) + "| " + inText)

def run_mi_thread(i, CliLine, ip, outputJob, DIRECTORY_LOGS, LogInfo, LOG_TIME, aluConfigFileModule, useSSHTunnel, ALU_TELNET_READ_TIMEOUT, ALU_FILE_OUT_CSV, cronTime, clientType, delayFactor):
	"""[summary]

	Args:
		i ([type]): [description]
		CliLine ([type]): [description]
		ip ([type]): [description]
		outputJob ([type]): [description]
		DIRECTORY_LOGS ([type]): [description]
		LogInfo ([type]): [description]
		LOG_TIME ([type]): [description]
		aluConfigFileModule ([type]): [description]
		useSSHTunnel ([type]): [description]
		ALU_TELNET_READ_TIMEOUT ([type]): [description]
		ALU_FILE_OUT_CSV ([type]): [description]
		cronTime ([type]): [description]
		clientType ([type]): [description]
		delayFactor ([type]): [description]
	"""
	time.sleep(random.random())
	myConnection(i, CliLine, ip, outputJob, DIRECTORY_LOGS, LogInfo, LOG_TIME, aluConfigFileModule, useSSHTunnel, ALU_TELNET_READ_TIMEOUT, ALU_FILE_OUT_CSV, cronTime, clientType, delayFactor).run()

def sort_order(lista):
	"""[List will be ordered and sorted always by the first field which is the system IP of the router]

	Args:
		lista ([list]): [List of IP system]

	Returns:
		[list]: [Ordered List]
	"""

	lista_sorted 	= sorted(lista, key=itemgetter(0))
	lista_grouped 	= groupby(lista_sorted, key=itemgetter(0))
	a = []
	for i,rou in enumerate(lista_grouped):
		a.append(list(rou[1]))
	return a

def verifyCronTime(cronTime):
	"""[We verify cronTime before moving on]

	Args:
		cronTime ([list]): [list of parameters]

	Returns:
		[list]
	"""

	if cronTime in ['',[],None]:
		return []
	elif len(cronTime)!=6:
		print('Wrong cronTime length. Quitting ...')
		quit()
	else:
		cronName   = str(cronTime[0])
		month      = str(cronTime[1])
		weekday    = str(cronTime[2])
		dayOfMonth = int(cronTime[3])
		hour       = int(cronTime[4])
		minute     = int(cronTime[5])

	if cronName[0] in [str(x) for x in range(0,10)]:
		print('Wrong CRON name. First char cannot be a number. Quitting ...')
		quit()		
	elif not re.compile(r'^[0-9A-Za-z]{1,32}$').search(cronName):
		print('Wrong CRON name. Quitting ...')
		quit()
	
	if month not in [calendar.month_name[x].lower() for x in range(1,13)]:
		print('Wrong month name. Quitting ...')
		quit()

	if weekday not in [calendar.day_name[x].lower() for x in range(0,7)]:
		print('Wrong weekDay name. Quitting ...')
		quit()		

	if dayOfMonth not in list(range(1,32)):
		print('Wrong dayOfMonth value. Quitting ...')
		quit()			

	if hour not in list(range(0,24)):
		print('Wrong hour value. Quitting ...')
		quit()

	if minute not in list(range(0,60)):
		print('Wrong minute value. Quitting ...')
		quit()

	return cronTime

def verifyServers(JumpHosts):
	"""We verify the SERVERS dictionary before moving on.

	Args:
		SERVERS ([str]): [Name of the file containing servers information in YML format.]

	Returns:
		[dict]: [Dictionary with servers information]
	"""

	try:
		with open(JumpHosts,'r') as f:
			servers = yaml.load(f, Loader=yaml.FullLoader)
	except:
		print("Missing " + JumpHosts + " file. Quitting..")
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
	newServers = {}
	for k,val in enumerate(servers.values()):
		newServers[k] = val

	return newServers	

def verifyCsv(aluFileCsv):
	"""[Verify CSV file]

	Args:
		aluFileCsv ([str]): [Name of CSV file]

	Returns:
		[list]: [List of Routers]
	"""

	try:
		if aluFileCsv.split(".")[-1] == "csv":
			iFile 		= open(aluFileCsv,"r")
			csvFile 	= csv.reader(iFile, delimiter=",", quotechar="|")
			routers 	= list(csvFile)
			iFile.close()
		else:
			print("Missing CSV file. Verify extension of the file to be '.csv'. Quitting...")
			quit()
	except:
		print("No CSV file found. Quitting ...")
		quit()

	return routers

def verifyPlugin(aluConfigFileModule):
	"""[Verifies the plugin template]

	Args:
		aluConfigFileModule ([str]): [Name of config template]

	Returns:
		[module]: [The module]
	"""

	try:
		if aluConfigFileModule.split(".")[-1] == "py":
			aluConfigFileModule = aluConfigFileModule.split(".")[0]
			#exec ("from " + aluConfigFileModule + " import construir_cliLine")
			mod = importlib.import_module(aluConfigFileModule)
			print(mod)
		else:
			print("Missing config file. Verify extension of the file to be '.py'. Quitting...")
			quit()
	except Exception as e:
		print(e)
		print("----\nError importing configFile. Quitting ...")
		quit()

	return mod

def renderMop(aluCliLineJob0, aluConfigFileModule):
	"""[Generates a MOP based on the CSV and plugin information]

	Args:
		aluCliLineJob0 ([file]): [configLines]
		aluConfigFileModule ([str]):  [The plugin for this MOP]

	Returns:
		None
	"""

	job0FileName = "job0_" + aluConfigFileModule + ".docx"

	#with open(job0_name,'r') as f:
	#	config = f.read()

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

	myDoc.add_heading('MOP for ' + aluConfigFileModule, 0)

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

	print(aluCliLineJob0)

	myDoc.save(job0FileName)

###

class myConnection(threading.Thread):
	"""[Class for connection Object]
	"""

	def __init__(self, thrdNum, config_line, systemIP, outputJob, DIRECTORY_LOGS, LogInfo, LOG_TIME, aluConfigFileModule, useSSHTunnel, ALU_TELNET_READ_TIMEOUT, ALU_FILE_OUT_CSV, cronTime, clientType, delayFactor):

		threading.Thread.__init__(self)
		self.num 			= thrdNum
		self.datos 			= config_line
		self.outputJob 	    = outputJob
		self.DIRECTORY_LOGS = DIRECTORY_LOGS
		self.ALU_TELNET_READ_TIMEOUT = ALU_TELNET_READ_TIMEOUT
		self.ALU_FILE_OUT_CSV = ALU_FILE_OUT_CSV
		self.delayFactor    = delayFactor
		self.LogInfo        = LogInfo
		self.LOG_TIME       = LOG_TIME
		self.plugin         = aluConfigFileModule

		# local generated variables
		self.connInfo = {
			'systemIP':systemIP,
			'useSSHTunnel':useSSHTunnel,
			'clientType':clientType,
			'localPort':-1,
			'remotePort':-1,
			'controlPlaneAccess':-1,
			'aluLogged':-1,
			'aluLogUser':"N/A",
			'aluLogReason':"N/A",
			'hostname':"N/A",
			'timos':"N/A",
			'cronTime':cronTime,
			'sshServer':-1,
			'conn2rtr':-1,
			'delayFactor':delayFactor,
			'telnetTimeout':ALU_TELNET_READ_TIMEOUT,
		}

		if ":" in self.connInfo['systemIP']:
			self.connInfo['remotePort'] = int( self.connInfo['systemIP'].split(":")[1] )			
			self.connInfo['systemIP']   = self.connInfo['systemIP'].split(":")[0]
		else:
			if self.connInfo['clientType'] == 'tel':
				self.connInfo['remotePort'] = ROUTER_TELNET_PORT

			elif self.connInfo['clientType'] == 'ssh':
				self.connInfo['remotePort'] = ROUTER_SSH_PORT

		if self.connInfo['useSSHTunnel'] == 1:
			self.connInfo['serverKey'] = self.num % len(SERVERS)
		else:
			self.connInfo['serverKey'] = -1

		self.tDiff	    = 0
		self.strConn    = "Con-" + str(self.num) + "| "
		self.outRx 	    = ''
		self.fRx        = ''
		self.runStatus  = 1
		self.useCron    = len(self.connInfo['cronTime'])

	def run(self):

		# We update the connection info dictionary, after we've set up the connection towards the router...
		self.connInfo.update(self.fncConnectToRouter(self.connInfo))

		if self.connInfo['conn2rtr'] != -1 and self.connInfo['aluLogged'] == 1:

			self.connInfo['timos']      = self.fncAuxGetVal(self.connInfo['conn2rtr'], self.connInfo['clientType'], 'timos')
			self.connInfo['hostname']   = self.fncAuxGetVal(self.connInfo['conn2rtr'], self.connInfo['clientType'], 'hostname')
			self.connInfo['timosMajor'] = int(self.connInfo['timos'].split("-")[2].split(".")[0])

			if self.outputJob == 2:

				fncPrintConsole(self.strConn + "#### Running routine for " + self.connInfo['systemIP'] +  " ...")

				self.f = self.logFileCreation(self.connInfo['hostname'], self.DIRECTORY_LOGS, self.datos, self.strConn)

				self.fRx		 = self.f[0]
				self.fullPathCmd = self.f[1]
				self.fCmd        = self.f[2]

				if self.useCron > 0:

					self.s = self.fncUploadFile(self.strConn, self.fullPathCmd, self.fCmd, self.connInfo)

					self.sftpStatus   = self.s[0]
					self.aluLogReason = self.s[1]

					if self.sftpStatus == 1:

						self.datos = self.runCron(self.fCmd, self.connInfo)
						self.b     = self.routerRunRoutine(self.datos, self.ALU_TELNET_READ_TIMEOUT, self.connInfo)

						#fncPrintConsole(self.strConn + "Run: " + str(self.b[0]))

						self.connInfo['aluLogReason'] = self.b[0]
						self.tDiff 					  = self.b[1]
						self.runStatus      		  = self.b[2]
						self.outRx          		  = self.b[3]

				else:

					self.b = self.routerRunRoutine(self.datos, self.ALU_TELNET_READ_TIMEOUT, self.connInfo)
	
					self.connInfo['aluLogReason'] = self.b[0]
					self.tDiff 					  = self.b[1]
					self.runStatus      		  = self.b[2]
					self.outRx          		  = self.b[3]

				if self.runStatus == 1:

					self.connInfo.update(self.routerLogout(self.connInfo))
					fncPrintConsole(self.strConn + "Logout: " + str(self.connInfo['aluLogReason']))

				else:

					fncPrintConsole(self.strConn + "TelnetReadTimeOut")

		self.logData(self.connInfo, self.num, self.tDiff, self.ALU_FILE_OUT_CSV, self.outRx, self.fRx, self.strConn, self.datos, self.LogInfo, self.LOG_TIME, self.plugin)

		#######################
		# closing connections #

		print(self.connInfo['conn2rtr'], self.connInfo['aluLogged'], self.connInfo['useSSHTunnel'], self.connInfo['sshServer'].tunnel_is_up, self.connInfo['clientType'])
		#print(self.connInfo)
		
		if self.connInfo['conn2rtr'] != -1 or self.connInfo['aluLogged'] == 1:

			if self.connInfo['clientType'] == 'tel':
				self.connInfo['conn2rtr'].close()

			elif self.connInfo['clientType'] == 'ssh':
				self.connInfo['conn2rtr'].disconnect()

		if self.connInfo['useSSHTunnel'] == 1 or self.connInfo['sshServer']:
			self.connInfo['sshServer'].stop()

		#                     #
		#######################

	def fncWriteToConnection(self, inText, timer, conn2rtr, clientType):

		### Writes to a connection. For telnet connections, stream needs to be encoded before doing it...
		if clientType == 'tel':
			inText = inText + '\n'
			output = conn2rtr.write(inText.encode())
			time.sleep(timer)

		elif clientType == 'ssh':

			if type(inText) == type([]):
				output = conn2rtr.send_config_set(inText, cmd_verify=False)
			elif type(inText) == type(''):
				output = conn2rtr.send_command(inText)

			return output

	def fncAuxGetVal(self, conn2rtr, clientType, what):

		if clientType == 'tel':

			if what == "timos":

				inText = "show version\n"	
				self.fncWriteToConnection(inText, ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
				rx     = conn2rtr.expect(ALU_TIMOS_LOGIN)
				timos  = rx[1].groups()[0].decode()

				return timos

			elif what == "hostname":

				inText = "\n"
				self.fncWriteToConnection(inText, ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
				rx     = conn2rtr.expect(ALU_HOSTNAME)
				hostname = rx[1].groups()[1].decode()

				return hostname	

		elif clientType == 'ssh':

			if what == "timos":

				inText = "show version"
				rx     = self.fncWriteToConnection(inText, ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
				match  = re.compile(ALU_TIMOS_SSH).search(rx)
				timos  = match.groups()[0]

				return timos

			elif what == 'hostname':

				inText = ["show system info | match Name"]
				rx     = self.fncWriteToConnection(inText, ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
				match  = re.compile(ALU_HOSTNAME_SSH).search(rx)
				hostname = match.groups()[1]

				return hostname

	def fncConnectToRouter(self, connInfo):
		"""[We update the connection info dictionary, after we've set up the connection towards the router]

		Args:
			connInfo ([dict]): [Contains all conection related relevant information ]

		Returns:
			[dict]: [Updated connInfo dictionary]
		"""

		### Creates connection to router

		if connInfo['useSSHTunnel'] == 1:

			tunnel = self.fncSshServer(self.strConn, connInfo)

			connInfo['controlPlaneAccess'] 	= tunnel[0]
			connInfo['localPort'] 		   	= tunnel[1]
			connInfo['sshServer']    		= tunnel[2]
			
			fncPrintConsole(self.strConn + "Trying router " + IP_LOCALHOST + ":" + str(connInfo['localPort']) + " -> " + connInfo['systemIP'] + ":" + str(connInfo['remotePort']))

		else:

			fncPrintConsole(self.strConn + "Using direct " + connInfo['clientType'] + " access: ")
			fncPrintConsole(self.strConn + "Trying router " + connInfo['systemIP'] + ":" + str(connInfo['remotePort']) )

			connInfo['controlPlaneAccess'] 	= 1	
			connInfo['localPort'] 			= ROUTER_TELNET_PORT
			connInfo['sshServer']    		= -1

		if connInfo['controlPlaneAccess'] == 1:

			if connInfo['clientType'] == 'tel':

				try:
					if connInfo['useSSHTunnel'] == 1:
						connInfo['conn2rtr'] = telnetlib.Telnet(IP_LOCALHOST, connInfo['localPort'])
					else:
						connInfo['conn2rtr'] = telnetlib.Telnet(connInfo['systemIP'], connInfo['remotePort'])

					connInfo['conn2rtr'].timeout = ALU_TIME_LOGIN
					a = self.routerLoginTelnet(connInfo['conn2rtr'], connInfo['clientType'], connInfo['systemIP'])

					connInfo['aluLogged']    = a[0]
					connInfo['aluLogUser']   = a[1]
					connInfo['aluLogReason'] = a[2]
					connInfo['aluPass']      = a[3]

				except:

					connInfo['conn2rtr'] = -1

			elif connInfo['clientType'] == 'ssh':

				try:
					if connInfo['useSSHTunnel'] == 1:
						a = self.routerLoginSsh(IP_LOCALHOST, connInfo['localPort'], connInfo['systemIP'], connInfo['delayFactor'])
					else:
						a = self.routerLoginSsh(connInfo['systemIP'], connInfo['remotePort'], connInfo['systemIP'], connInfo['delayFactor'])

					connInfo['conn2rtr']     = a[0]
					connInfo['aluLogged']    = a[1]
					connInfo['aluLogUser']   = a[2]
					connInfo['aluLogReason'] = a[3]
					connInfo['aluPass']      = a[4]

				except:
					connInfo['conn2rtr'] = -1

		else:

			connInfo['conn2rtr']     = -1
			connInfo['aluLogged'] 	 = -1
			connInfo['aluLogUser']   = "N/A"
			connInfo['aluLogReason'] = "noControlPlaneAccess"
			connInfo['aluPass']      = "N/A"
			connInfo['sshServer']    = -1

		return connInfo

	def fncUploadFile(self, strConn, fileLocal, fileRemote, connInfo):
		### upload configFile via SFTP

		out = [-1,'sftpError']

		if connInfo['useSSHTunnel'] == 1:

			# We need to rewrite the remotePort because the clientType could be telnet.
			# There is no problem because the connection to the CLI has already been 
			# established and is located in connInfo['conn2rtr'].
			# This is only for the purpose of uploading a file vía SFTP.

			connInfo['remotePort'] = ROUTER_SSH_PORT

			sshSftp = self.fncSshServer(strConn, connInfo)
			sftpAccess    = sshSftp[0]
			sftpPort      = sshSftp[1]
			sshServerSftp = sshSftp[2]

			transport = paramiko.Transport((IP_LOCALHOST,sftpPort))
			transport.connect(None,connInfo['aluLogUser'],connInfo['aluPass'])

			# The routers with timos above 6.X do support SFTP.
			# Otherwise we need to use SCP.

			if connInfo['timosMajor'] > 6:
				fncPrintConsole(strConn + "uploading file: SFTP: " + str(sftpPort))
				sftp = paramiko.SFTPClient.from_transport(transport)
			else:
				fncPrintConsole(strConn + "uploading file: SCP: " + str(sftpPort))
				sftp = SCPClient(transport)

			try:
				sftp.put(fileLocal,'cf3:/' + fileRemote)
				out = [1,'sftpOk']
			except:
				out = [-1,'sftpError']

			sftp.close()
			transport.close()
			sshServerSftp.stop()

		else:

			transport = paramiko.Transport((connInfo['systemIP'],ROUTER_SSH_PORT))
			transport.connect(None,connInfo['aluLogUser'],connInfo['aluPass'])

			if connInfo['timosMajor'] > 6:
				fncPrintConsole(strConn + "uploading file: SFTP: " + str(sftpPort))
				sftp = paramiko.SFTPClient.from_transport(transport)
			else:
				fncPrintConsole(strConn + "uploading file: SCP: " + str(sftpPort))
				sftp = SCPClient(transport)

			try:
				sftp.put(fileLocal,'cf3:/' + fileRemote)
				out = [1,'sftpOk']
			except:
				out = [-1,'sftpError']

			sftp.close()
			transport.close()

		return out

	def fncSshServer(self, strConn, connInfo):

		#serverKey = random.choice(list(SERVERS.keys())) 
		serverKey = connInfo['serverKey']

		tempIp   = SERVERS[serverKey]['ip']
		tempPort = SERVERS[serverKey]['port']
		tempUser = SERVERS[serverKey]['user']
		tempPass = SERVERS[serverKey]['password']

		try:
			server = SSHTunnelForwarder( 	(tempIp, tempPort), 
												ssh_username = tempUser, 
												ssh_password = tempPass, 
												remote_bind_address = (connInfo['systemIP'], connInfo['remotePort']),
											)
			server.start()
			localPort = server.local_bind_port
			controlPlaneAccess = 1
			fncPrintConsole(self.strConn + "sshServerTunnel on port: " + str(localPort))

		except:

			fncPrintConsole(strConn + "Error SSH Tunnel")
			controlPlaneAccess = -1
			localPort 		   = -1

		return controlPlaneAccess, localPort, server

	def routerLoginTelnet(self, conn2rtr, clientType, systemIP):

		#	i[0]	meaning
		#	-1		Timeout
		#	0		Login:
		#	1		Connection closed by foreign host

		# NOTA: tener presente que 'i' debe esperarse al primer intento.
		# Si volvemos, es porque el expect ya nos dio login o timeout

		aluLogged    = -1
		aluLogUser   = "N/A"
		aluPass      = "PassN/A"
		aluLogReason = "N/A"
		index        = 0

		while aluLogged == -1:

			try:
				i = conn2rtr.expect(ALU_PROMPT_LOGIN + ALU_PROMPT_CLOSED + ALU_PROMPT , ALU_TIME_LOGIN)
			except:
				aluLogUser 			= "UserN/A"
				aluLogReason 		= "TelnetError"
				aluLogged 			= -1
				aluPass             = "PassN/A"
				fncPrintConsole(self.strConn + aluLogReason)
				return (aluLogged,aluLogUser,aluLogReason,aluPass)

			# expected: (0, <_sre.SRE_Match object at 0x7f0887a37d98>, 'login:')
			#fncPrintConsole("i: " + str(i))

			if i[0] == -1:
				# timeout
				self.fncWriteToConnection("\003",ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
				aluLogUser 			= "UserN/A"
				aluLogReason 		= "TelnetTimeout"
				aluLogged 			= -1
				fncPrintConsole(self.strConn + aluLogReason)
				break

			elif i[0] == 0:
		
				if index < len(ROUTER_USER):

					tempUser = ROUTER_USER[index][0]
					tempPass = ROUTER_USER[index][1]

					self.fncWriteToConnection(tempUser,ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)

					j = conn2rtr.expect(ALU_PROMPT_PASS + ALU_PROMPT_CLOSED)
					# expected: (0, <_sre.SRE_Match object at 0x7f0887a37e00>, ' Password:')
					#fncPrintConsole("j: " + str(j))

					if j[0] == 0:
						self.fncWriteToConnection(tempPass,ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
						#fncPrintConsole(self.strConn + "User: " + tempUser + ", Pass: " + tempPass + ", index: " + str(index))
						aluLogUser 		= tempUser
						aluLogged		= -1
						index			= index + 1


					elif i[0] == 1:
						# ALU_PROMPT_CLOSED
						# Sometimes loggin into a router is not possible
						# because many users are already logged in into it.
						self.fncWriteToConnection("\003",ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
						aluLogUser 			= "UserN/A"
						aluLogReason	 	= "TelnetFailedConnection"
						aluLogged 			= -1
						aluPass             = "PassN/A"
						fncPrintConsole(self.strConn + aluLogReason + ": " + systemIP)
						break

				else:
					# We've tryed all the user/pass. Quitting.
					self.fncWriteToConnection("\003",ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
					aluLogUser 			= tempUser
					aluLogReason	 	= "MaxLoginReached"
					aluLogged 			= -1
					aluPass             = "PassN/A"
					fncPrintConsole(self.strConn + aluLogReason + ": " + systemIP)
					break

			elif i[0] == 1:
				# ALU_PROMPT_CLOSED
				# Sometimes loggin into a router is not possible
				# because many users are already logged in into it.
				self.fncWriteToConnection("\003",ALU_TELNET_WRITE_TIMEOUT, conn2rtr, clientType)
				aluLogUser 			= "UserN/A"
				aluLogReason 		= "TelnetFailedConnection"
				aluLogged 			= -1
				aluPass             = "PassN/A"
				fncPrintConsole(self.strConn + aluLogReason + ": " + systemIP)
				break

			elif i[0] > 1:
				aluLogReason 	= "LoggedOk"
				aluLogged 		= 1
				
		return (aluLogged,aluLogUser,aluLogReason,tempPass)

	def routerLoginSsh(self, ip, port, systemIP, delayFactor):

		conn2rtr     = -1
		aluLogged    = -1
		aluLogUser   = "N/A"
		aluPass      = "PassN/A"
		aluLogReason = "N/A"
		index        = 0

		while aluLogged == -1:

			if index < len(ROUTER_USER):

				tempUser = ROUTER_USER[index][0]
				tempPass = ROUTER_USER[index][1]

				try:
					#SSHClient.connect(hostname=ip, port=port, username=tempUser, password=tempPass)
					#conn2rtr = ConnectHandler(device_type="nokia_sros", host=ip, port=port, username=tempUser, password=tempPass, timeout=10, banner_timeout=30)
					conn2rtr = ConnectHandler(device_type="nokia_sros", host=ip, port=port, username=tempUser, password=tempPass, global_delay_factor=delayFactor)
					aluLogged    = 1
					aluLogReason = "LoggedOk"
					aluLogUser   = tempUser
					aluPass      = tempPass
				except:
					index 	     = index + 1
					aluLogUser   = tempUser
					aluLogReason = "SSHFailedConnection"
					aluLogged 	 = -1
					aluPass      = "PassN/A"
					fncPrintConsole(self.strConn + aluLogReason + ": " + systemIP)

			else:
				# We've tryed all the user/pass. Quitting.
				aluLogUser 	 = tempUser
				aluLogReason = "MaxLoginReached"
				aluLogged 	 = -1
				aluPass      = "PassN/A"
				fncPrintConsole(self.strConn + aluLogReason + ": " + systemIP)
				break
				
		return (conn2rtr,aluLogged,aluLogUser,aluLogReason,tempPass)

	def logFileCreation(self, hostname, DIRECTORY_LOGS, datos, strConn):

		fncPrintConsole(strConn + "Creating files locally for " + hostname + "...")

		# Verify for logs directory
		if not os.path.exists(DIRECTORY_LOGS):
			os.makedirs(DIRECTORY_LOGS)

		# Filenames
		aluFileCommands = hostname + "_commands.cfg"
		aluFileOutRx	= hostname + "_rx.txt"

		# Complete = Directories + Filenames
		aluCompleteCmd 	= DIRECTORY_LOGS + aluFileCommands
		aluCompleteRx	= DIRECTORY_LOGS + aluFileOutRx

		# Create files
		fCmd = open(aluCompleteCmd, "w")
		fCmd.write(datos)
		fCmd.close()

		fRx	= open(aluCompleteRx, "w")

		return(fRx, aluCompleteCmd, aluFileCommands)

	def routerRunRoutine(self, datos, ALU_TELNET_READ_TIMEOUT, connInfo):

		# Sending script to ALU
		runStatus = 1
		tStart 		 = time.time()
		outRx  		 = ""
		aluLogReason = ""

		if connInfo['cronTime']:
			fncPrintConsole(self.strConn + "Establishing script with CRON...", show=1)
		else:
			# Splitting self.datos into individual lines
			fncPrintConsole(self.strConn + "Running script per line...", show=1)

		if connInfo['clientType'] == 'tel':
			self.fncWriteToConnection(datos, ALU_TELNET_WRITE_TIMEOUT, connInfo['conn2rtr'], connInfo['clientType'])
			outRx = connInfo['conn2rtr'].read_until(ALU_FIN_SCRIPT.encode(), ALU_TELNET_READ_TIMEOUT)
			outRx = outRx.decode()

		elif connInfo['clientType'] == 'ssh':
			datos = datos.split('\n')[1:]
			outRx = self.fncWriteToConnection(datos, ALU_TELNET_WRITE_TIMEOUT, connInfo['conn2rtr'], connInfo['clientType'])
			#conn2rtr.expect(".*"+ALU_FIN_SCRIPT+".*", timeout=ALU_TELNET_READ_TIMEOUT)
			#outRx = conn2rtr.current_output

		## Analizing output
		str_major_error_list = [x.decode() for x in ALU_MAJOR_ERROR_LIST]
		str_minor_error_list = [x.decode() for x in ALU_MINOR_ERROR_LIST]
		
		if any(word in outRx for word in str_major_error_list):
			aluLogReason = "MajorFailed"
		elif any(word in outRx for word in str_minor_error_list):
			aluLogReason = "MinorFailed"
		else:
			aluLogReason = "SendSuccess"

		tEnd  = time.time()
		tDiff = tEnd - tStart

		if abs(tDiff - ALU_TELNET_READ_TIMEOUT) <= ALU_TIME_DIFF:
			aluLogReason = "TelnetReadTimeOut"
			runStatus = -1

		fncPrintConsole(self.strConn + "Time: " + fncFormatTime(tDiff) + ". Result: " + aluLogReason, show=1)

		return(aluLogReason, tDiff, runStatus, outRx)

	def logData(self, connInfo, connId, tDiff, ALU_FILE_OUT_CSV, outRx, fRx, strConn, datos, LogInfo, LOG_TIME, plugin):

		if connInfo['useSSHTunnel'] == 1:
			serverName = SERVERS[connInfo['serverKey']]['name']
		else:
			serverName = '-1'

		aluCsvLine = (
			LOG_TIME + CH_COMA +
			LogInfo + CH_COMA + 
			plugin + CH_COMA + 
			connInfo['systemIP'] + CH_COMA +
			connInfo['hostname'] + CH_COMA +
			connInfo['aluLogUser'] + CH_COMA +
			connInfo['aluLogReason'] + CH_COMA +
			str(connId) + CH_COMA +
			str(connInfo['localPort']) + CH_COMA +
			serverName + CH_COMA +
			connInfo['clientType'] + CH_COMA +
			str(len(datos.split('\n'))) + CH_COMA +
			str(len(outRx.split('\n'))) + CH_COMA +
			fncFormatTime(tDiff)
		)

		fncPrintConsole(strConn + "logData: " + aluCsvLine)

		with open(ALU_FILE_OUT_CSV,'a') as fLog:
			fLog.write(aluCsvLine + "\n")
			
		if connInfo['aluLogged'] == 1:
			fRx.write(outRx)
			fRx.close()

	def routerLogout(self, connInfo):

		if connInfo['aluLogged'] == 1:

			if connInfo['clientType'] == 'tel':

				#
				# aluPrompt = [ "A:.*#" , "A:.*>.*#" , "B:.*#", "B:.*>.*#" ]
				#                 0           1            2         3

				# loggin correct, proceed with logout
				self.fncWriteToConnection(CH_CR, ALU_TELNET_WRITE_TIMEOUT, connInfo['conn2rtr'], connInfo['clientType'])
				i = connInfo['conn2rtr'].expect(ALU_PROMPT, PROMPT_TIMEOUT)
				#fncPrintConsole("i: " + str(i))

				if i[0] in [0,1,2,3]:
					# Logging out
					self.fncWriteToConnection("logout", ALU_TELNET_WRITE_TIMEOUT, connInfo['conn2rtr'], connInfo['clientType'])
					
					try:
						j = connInfo['conn2rtr'].expect(ALU_PROMPT_LOGOUT, PROMPT_TIMEOUT)
						#fncPrintConsole("j: " + str(j))
					
						if j[0] in [0,1,2,3]:
							#connInfo['aluLogged'] = -1
							fncPrintConsole(self.strConn + "Logged out OK from " + connInfo['systemIP'])

					except:
						#connInfo['aluLogged'] = -1
						fncPrintConsole(self.strConn + "Something happended. Not properly logged out from " + connInfo['systemIP'])

			elif connInfo['clientType'] == 'ssh':

				pass

		return connInfo

	def sshStop(self):
		self.sshServer.stop()
		fncPrintConsole(self.strConn + "SSH" + str(self.num) + " stopped ...")

	def runCron(self, script, connInfo):

		def setScript(cronName, script):

			cfg = ""
			cfg = cfg + "script " + cronName + " owner taskAutom\nshutdown\n"
			cfg = cfg + "location cf3:\\" + script + "\n"
			cfg = cfg + "no shutdown\n"
			cfg = cfg + "exit\n"
			return cfg

		def action(cronName):

			cfg = ""
			cfg = cfg + "action " + cronName + " owner taskAutom\nshutdown\n"
			cfg = cfg + "results cf3:\\resultTestCron.txt\n"
			cfg = cfg + "script " + cronName + " owner taskAutom\n"
			cfg = cfg + "no shutdown\n"
			cfg = cfg + "exit\n"
			return cfg

		def policy(cronName):

			cfg = ""
			cfg = cfg + "script-policy " + cronName + " owner taskAutom\nshutdown\n"
			cfg = cfg + "results cf3:\\resultTestCron.txt\n"
			cfg = cfg + "script " + cronName + " owner taskAutom\n"
			cfg = cfg + "no shutdown\n"
			cfg = cfg + "exit\n"			
			return cfg

		def schedule(timos, cronName, month, weekday, dayOfMonth, hour, minute):

			cfg = ""
			cfg = cfg + "schedule " + cronName + " owner taskAutom\nshutdown\n"

			if timos > 7:
				cfg = cfg + "script-policy " + cronName + " owner taskAutom\n"
			else:
				cfg = cfg + "action " + cronName + " owner taskAutom\n"
			
			cfg = cfg + "type oneshot\n"
			cfg = cfg + "day-of-month " + dayOfMonth + "\n"
			cfg = cfg + "hour " + hour + "\n"
			cfg = cfg + "minute " + minute + "\n"
			cfg = cfg + "month " + month + "\n"
			cfg = cfg + "weekday " + weekday + "\n"
			cfg = cfg + "no shutdown \n"
			cfg = cfg + "exit\n"
			cfg = cfg + "exit all\n"
			cfg = cfg + "admin save\n"
			cfg = cfg + "echo " + ALU_FIN_SCRIPT + "\n"
			return cfg

		cronName   = str(connInfo['cronTime'][0])
		month      = str(connInfo['cronTime'][1])
		weekday    = str(connInfo['cronTime'][2])
		dayOfMonth = str(connInfo['cronTime'][3])
		hour       = str(connInfo['cronTime'][4])
		minute     = str(connInfo['cronTime'][5])

		cfg = ""

		if connInfo['timosMajor'] > 7:

			cfg = cfg + "/configure system script-control\n"
			cfg = cfg + setScript(cronName, script)
			cfg = cfg + policy(cronName)
			cfg = cfg + "/configure system cron\n"
			cfg = cfg + schedule(connInfo['timosMajor'], cronName, month, weekday, dayOfMonth, hour, minute)

		else:

			cfg = cfg + "/configure cron\n"
			cfg = cfg + setScript(cronName, script)
			cfg = cfg + action(cronName)
			cfg = cfg + schedule(connInfo['timosMajor'], cronName, month, weekday, dayOfMonth, hour, minute)

		cfg = "/environment no more\necho " + ALU_START_SCRIPT + "\n" + cfg

		return cfg

####################################
# Main Function                    #
####################################

def fncRun(outputJob, aluFileCsv, aluConfigFileModule, progNumThreads=0, VpnUser='', VpnPass='', LogInfo='', useSSHTunnel=1, TelTimOut=90, cronTime=None, clientType='tel', delayFactor=1, JumpHosts='servers.yml'):
	"""[summary]

	Args:
		outputJob ([int]): [Type of Job]
		aluFileCsv ([str]): [data]
		aluConfigFileModule ([str]): [plugin]
		progNumThreads (int, optional): Defaults to 0.
		VpnUser (str, optional): Defaults to ''.
		VpnPass (str, optional): Defaults to ''.
		LogInfo (str, optional): [Name of the task]. Defaults to ''.
		useSSHTunnel (int, optional): Defaults to 1.
		TelTimOut (int, optional): [Seconds for Telnet Read Timeout]. Defaults to 90.
		cronTime ([type], optional): [Parameters for Cron]. Defaults to None.
		clientType (str, optional): [Telnet or SSH]. Defaults to 'tel'.
		delayFactor (int, optional): [DelayFactor for SSH client]. Defaults to 1.
		JumpHosts (str, optional): [File with Servers for JumpHost. Defaults to server.yml]

	Returns:
		[int]: 0
	"""
    
	# CronTime
	cronTime = verifyCronTime(cronTime)

	# Servers
	if useSSHTunnel == 1:
		global SERVERS 
		SERVERS = {}
		SERVERS = verifyServers(JumpHosts)

	# CSV File
	routers = verifyCsv(aluFileCsv)

	# Config File
	mod = verifyPlugin(aluConfigFileModule)

	
	# Running...
	if outputJob == 2:

		# LogInfo
		LOG_TIME           = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
		DIRECTORY_LOGS 	   = os.getcwd() + "/logs_" + LOG_TIME + "_" + LogInfo + "_" + aluConfigFileModule + "/"
		ALU_FILE_OUT_CSV   = DIRECTORY_LOGS + "00_log.csv"

		# Verify if DIRECTORY_LOGS exists. If so, ask for different name ...
		if os.path.exists(DIRECTORY_LOGS):
			print("Folder " + DIRECTORY_LOGS + " already exists.\nUse a different folder name.\nQuitting ...")
			quit()
		else:
			os.makedirs(DIRECTORY_LOGS)
			open(ALU_FILE_OUT_CSV,'w').close()
			#os.mknod(ALU_FILE_OUT_CSV)

		# VPN Access
		ROUTER_USER1[0] = VpnUser
		ROUTER_USER1[1] = VpnPass

		#### --- Generar threads
		#lock 			= threading.Lock()
		threads_list 	= ThreadPool(progNumThreads)

	
	#### --- Parsing Data
	routers 		= sort_order(routers)
	timeTotalStart 	= time.time()
	aluCliLineJob0  = ""
	
	for i, router in enumerate(routers):

		systemIP  = router[0][0]
		aluCliLine = ""

		if outputJob == 2:

			for j,item in enumerate(router):
				aluCliLine = aluCliLine + mod.construir_cliLine(j,item)

			if aluCliLine[-1] == "\n":
				aluCliLine = aluCliLine[:-1]

			if len(cronTime)==0:
				aluCliLine = "\necho " + ALU_START_SCRIPT + "\n/environment no more\n" + aluCliLine + "\nexit all\necho " + ALU_FIN_SCRIPT

			# running routine
			threads_list.apply_async(run_mi_thread, args=(i, aluCliLine, systemIP, outputJob, DIRECTORY_LOGS, LogInfo, LOG_TIME, aluConfigFileModule, useSSHTunnel, TelTimOut, ALU_FILE_OUT_CSV, cronTime, clientType, delayFactor))

		else:

			for j,item in enumerate(router):
				aluCliLineJob0 = aluCliLineJob0 + mod.construir_cliLine(j,item,1)

	if outputJob == 2:
		threads_list.close()
		### The .join() implies that processes/threads need to finish themselves before moving on.
		threads_list.join()
		fncPrintResults(outputJob, TelTimOut, useSSHTunnel, clientType, progNumThreads, aluConfigFileModule, aluFileCsv, routers, timeTotalStart, LogInfo, cronTime, delayFactor, DIRECTORY_LOGS, ALU_FILE_OUT_CSV)

	elif outputJob == 0:

		#job0FileName = "job0_" + aluConfigFileModule

		#with open(job0FileName + ".cfg", "w") as text_file:
		#	text_file.write(aluCliLineJob0)

		renderMop(aluCliLineJob0, aluConfigFileModule)

		fncPrintResults(outputJob, TelTimOut, useSSHTunnel, clientType, progNumThreads, aluConfigFileModule, aluFileCsv, routers, timeTotalStart, LogInfo, cronTime, delayFactor)

	return 0

if __name__ == '__main__':

	parser1 = argparse.ArgumentParser(description='Task Automation Parameters.', prog='PROG', usage='%(prog)s [options]')
	parser1.add_argument('-csv','--csvFile',     type=str, required=True, help='CSV File with parameters',)
	parser1.add_argument('-j'  ,'--jobType',     type=int, required=True, choices=[0,2], default=0, help='Type of job')
	parser1.add_argument('-py' ,'--pyFile' ,     type=str, required=True, help='PY Template File',)

	parser1.add_argument('-log','--logInfo' ,    type=str, help='Description for log folder', )
	parser1.add_argument('-jh' ,'--JumpHosts',   type=str, help='JumpHosts file. Default=servers.yml', default='servers.yml')
	parser1.add_argument('-crt','--cronTime',    type=str, nargs='+' , help='Data for CRON: name(ie: test), month(ie april), weekday(ie monday), day-of-month(ie 28), hour(ie 17), minute(ie 45).', default=[])
	parser1.add_argument('-u'  ,'--username',    type=str, help='Username', )
	parser1.add_argument('-th' ,'--threads' ,    type=int, help='Number of threads. Default=1', default=1,)
	parser1.add_argument('-to' ,'--timeout' ,    type=int, help='Telnet Timeout [sec]. Default=90', default=90,)
	parser1.add_argument('-df' ,'--delayFactor', type=int, help='SSH delay factor. Default=1', default=1,)
	parser1.add_argument('-tun','--sshTunnel',   type=int, help='Use SSH Tunnel to routers. Default=1', default=1, choices=[0,1])
	parser1.add_argument('-ct', '--clientType',  type=str, help='Connection type. Default=tel', default='tel', choices=['tel','ssh'])
	parser1.add_argument('-v'  ,'--version',               help='Version', action='version', version='Lucas Aimaretto - (C)2020 - laimaretto@gmail.com - Version: 7.5' )

	args = parser1.parse_args()

	### reading parameters

	outputJob 			= args.jobType
	aluFileCsv 			= args.csvFile
	aluConfigFileModule = args.pyFile
	VpnUser 			= args.username
	VpnPass 			= None
	progNumThreads		= args.threads
	LogInfo 			= args.logInfo
	useSSHTunnel 		= args.sshTunnel
	TelTimOut 			= args.timeout
	cronTime            = args.cronTime
	clientType          = args.clientType
	delayFactor         = args.delayFactor
	JumpHosts           = args.JumpHosts

	### Rady to go ...

	if outputJob == 0:

		fncRun(outputJob,aluFileCsv,aluConfigFileModule,progNumThreads,VpnUser,VpnPass,LogInfo,useSSHTunnel,TelTimOut,cronTime,clientType,delayFactor,JumpHosts)

	elif outputJob == 2 and VpnUser and progNumThreads and LogInfo and useSSHTunnel in [0,1] and TelTimOut:

		print("\n#######################################")
		print("# About to run. Ctrl+C if not sure... #")
		print("#######################################\n")
		VpnPass = getpass("### -> PASSWORD (" + VpnUser + "): ")

		fncRun(outputJob,aluFileCsv,aluConfigFileModule,progNumThreads,VpnUser,VpnPass,LogInfo,useSSHTunnel,TelTimOut,cronTime,clientType,delayFactor,JumpHosts)

	else:

		print("Not enough paramteres.\nRun: python script_x_y.py -h for help.\nQuitting...")