# SPPD_API.py
# Created 12/02/19
# Updated 01/07/20
# Current Version: 0.01
#----------------------

import pytz, datetime
import os, sys
new_path=sys.path
folder=os.getcwd()
if folder not in new_path:
	new_path.append(folder)
try:
	folder=os.path.dirname(os.path.realpath(__file__))
	if os.path.isdir(folder) and folder not in new_path:
		new_path.append(folder)
except:
	pass
try:
	folder=os.path.dirname(sys.executable)
	if os.path.isdir(folder) and folder not in new_path:
		new_path.append(folder)
except:
	pass
sys.path=new_path

from uuid import getnode
import requests
import base64
import sys, os, time
from urllib.parse import urlencode
import gpsoauth
import json
import threading

SPACES_SANDBOX='spaces/99e34ec4-be44-4a31-a0a2-64982ae01744/sandboxes/DRAFI_IP_LNCH_PDC_A'

###INPUT###
USERNAME = ""
PASSWORD = ""

#We only want to make a single call at a time
API_LOCK = threading.Condition()

def setUsernamePassword(user_name,password):
	global USERNAME, PASSWORD
	USERNAME=user_name
	PASSWORD=password
	if "@" not in USERNAME:
		print("Error: You need to type in your username (email address)")
		sys.exit(1)

###AUTHENTICATION###
MASTER_TOKEN_PATH='MASTERTOKEN.txt'
OAUTH_TOKEN_PATH='OAUTHTOKEN.txt'
UBI_TOKEN_PATH='UBITOKEN.txt'

NAME_ON_PLATFORM=None
PROFILE_ID=None

	
#ANDROID_ID=str(getnode())+"0"
ANDROID_ID="39e94ca643b94360"
UBI_TOKEN=None
UBI_EXPIRATION = -1
OAUTH_EXPIRATION = -1

HEADERS = {
	"Ubi-AppId" : "b5f1619b-8612-4966-a083-2fac253e2090",
	"X-Unity-Version" : "5.6.4p4",
	"X-Version" : "420",
	"X-Platform" : "1",
	"X-Device" : "131652800",
	"User-Agent" : "Dalvik/2.1.0 (Linux; U; Android 7.1.1; Pixel XL Build/NOF26V)",
}

def updatePaths():
	for pathx in sys.path:
		folder=os.path.join(pathx,'MASTERTOKEN.txt')
		if os.path.exists(folder):
			global MASTER_TOKEN_PATH
			MASTER_TOKEN_PATH=folder
		folder=os.path.join(pathx,'OAUTHTOKEN.txt')
		if os.path.exists(folder):
			global OAUTH_TOKEN_PATH
			OAUTH_TOKEN_PATH=folder
		folder=os.path.join(pathx,'UBITOKEN.txt')
		if os.path.exists(folder):
			global UBI_TOKEN_PATH
			UBI_TOKEN_PATH=folder

def checkLoggedIn(force_connect=False):
	global UBI_TOKEN
	if UBI_TOKEN==None or UBI_EXPIRATION < time.time():
		UBI_TOKEN=authenticateAll(force_connect=force_connect)
		updateHeaders()
	
def updateHeaders():
	global HEADERS,UBI_TOKEN
	if UBI_TOKEN == None:
		print("Error: You were unable to get a token from Ubisoft!")
		return
	HEADERS["Authorization"] = f"Ubi_v1 t={UBI_TOKEN}"

def parse_auth_response(text):
	response_data = {}
	for line in text.split('\n'):
		if not line:
			continue
		key, _, val = line.partition('=')
		response_data[key] = val
	return response_data

def getMasterToken(email,password,android_id):
	response_body=gpsoauth.perform_master_login(email,password,android_id)
	if "Token" not in response_body:
		print("Unable to get Auth Token")
		print(f"response_body: {response_body}")
		return None
	return response_body["Token"]
	
#['Expiry'] 1574408077
def authenticateGoogle(username,androidId,masterToken, user_agent='Dalvik/2.1.0 (Linux; U; Android 5.1.1; SM-N950N Build/LYZ28N)'):
	HOST="https://android.googleapis.com/auth"
	payload={
		"androidId": androidId,
		"lang":"en_US",
		"google_play_services_version":"15090023",
		"sdk_version":"23",
		"device_country":"us",
		"client_sig":"e3d6da236ed1df2c0d46476c7e90f2007a9a411e",
		"oauth2_prompt":"auto",
		"callerSig":"38918a453d07199354f8b19af05ec6562ced5788",
		"Email":username,
		"oauth2_include_profile":"0",
		"has_permission":"1",
		"service":"oauth2:server:client_id:265464518803-3jnqov9h917mdj5c3kg0u39790tj9k7s.apps.googleusercontent.com:api_scope:https://www.googleapis.com/auth/games_lite",
		"app":"com.ubisoft.dragonfire",
		"check_email":"1",
		"token_request_options":"CAAgASgCOAFQAw==",
		"callerPkg":"com.google.android.gms",
		"Token":masterToken
	}
	payload_str = urlencode(payload)
	HEADERS={
		"device": androidId,
		"app": "com.ubisoft.dragonfire",
		"Accept-Encoding": "gzip",
		'User-Agent': user_agent,
		"content-type": "application/x-www-form-urlencoded",
		"Host": "android.googleapis.com",
		"Connection": "Keep-Alive"
	}
	r = requests.post(HOST, data=payload_str, headers=HEADERS)
	response_body=r.text
	split_dict=parse_auth_response(response_body)
	if "Auth" not in split_dict.keys():
		print("Unable to get Google oAuth Token")
		print(f"response_body: {response_body}")
		return None,time.time()
	if "Expiry" not in split_dict.keys():
		print("Unable to get Google oAuth 'Expiry' attribute")
		print(f"response_body: {response_body}")
		return split_dict["Auth"],time.time()+2*60*60
	expiration_time=int(split_dict["Expiry"])# - 3600 #One hour buffer?
	return split_dict["Auth"], expiration_time

#"expiration":"2019-11-23T09:18:04.0671070Z"
def authenticateUbisoft(authToken):
	HOST='https://public-ubiservices.ubi.com/v3/profiles/sessions'
	payload_str="{}"
	
	HEADERS={
		"Ubi-AppId": "b5f1619b-8612-4966-a083-2fac253e2090",
		"Content-Type": "application/json",
		"X-Unity-Version": "5.6.4p4",
		"Authorization": f"googlegames t={authToken}",
		"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 6.0.1; VirtualBox Build/MOB31T)",
		"Host": "public-ubiservices.ubi.com",
		"Connection": "Keep-Alive",
		"Accept-Encoding": "gzip"
	}
	r = requests.post(HOST, data=payload_str, headers=HEADERS)
	response_body=r.text
	result=dict()
	try:
		result = json.loads(response_body)
	except Exception as e:
		print(str(e))
	#print(f"response_body: {response_body}")
	if "ticket" not in result or "nameOnPlatform" not in result or "profileId" not in result:
		print("Unable to get Ubi Token")
		print(f"response_body: {response_body}")
		return None,int(time.time()),None
	if "expiration" not in result.keys():
		print("Unable to get Ubi Token 'expiration' attribute")
		print(f"response_body: {response_body}")
		return result["ticket"],time.time()+2*60*60, result["nameOnPlatform"]
	expiration_str=result["expiration"][:-2] #skip the last 2 characters
	struct_time=time.strptime(expiration_str, "%Y-%m-%dT%H:%M:%S.%f")
	expiration_time_local=int(time.mktime(struct_time))-1800 #One hour buffer?	
	local = pytz.utc
	naive=datetime.datetime.fromtimestamp(expiration_time_local)
	local_dt = local.localize(naive, is_dst=None)
	utc_dt = local_dt.astimezone(pytz.utc)
	expiration_time_utc=int(utc_dt.timestamp())
	utc_string_time = utc_dt.strftime("%Y-%m-%d %H:%M%z")
	#print(f"UbiToken Expiration Time (UTC): {utc_string_time}")
	return result["ticket"], expiration_time_utc, result["nameOnPlatform"], result["profileId"]

def authenticateAll(oauth_token_only=False,force_connect=False):
	updatePaths()
	if not oauth_token_only and not os.path.isfile(MASTER_TOKEN_PATH) and PASSWORD == "":
		print("Error: You need to type in a password")
		sys.exit(1)
	masterToken=None
	if os.path.isfile(MASTER_TOKEN_PATH):
		fh=open(MASTER_TOKEN_PATH, 'r')
		for line in fh:
			split_line=line.strip("\n").split(",")
			masterName=split_line[0]
			if masterName == USERNAME:
				masterToken=split_line[1]
				break
		fh.close()
	if masterToken==None:
		masterToken=getMasterToken(USERNAME,PASSWORD,ANDROID_ID)
		if masterToken == None: return None
		fh=open(MASTER_TOKEN_PATH, 'a')
		fh.write(f'{USERNAME},{masterToken}\n')
		fh.close()
	#print(f"masterToken: {masterToken}")
	print(f"Found masterToken: You don't need a password to login anymore.")
	
	global OAUTH_EXPIRATION
	authToken=None
	if os.path.isfile(OAUTH_TOKEN_PATH) and OAUTH_EXPIRATION == -1:
		fh=open(OAUTH_TOKEN_PATH, 'r')
		result=fh.read()
		fh.close()
		split_result=result.split(",")
		if len(split_result)==3:
			masterName=split_result[0]
			if masterName == USERNAME:
				OAUTH_EXPIRATION=int(split_result[1])
				authToken=split_result[2]
	if OAUTH_EXPIRATION < time.time() or force_connect:
		authToken,OAUTH_EXPIRATION=authenticateGoogle(USERNAME,ANDROID_ID,masterToken)
		fh=open(OAUTH_TOKEN_PATH, 'w')
		fh.write(f'{USERNAME},{OAUTH_EXPIRATION},{authToken}')
		fh.close()
	if OAUTH_EXPIRATION > 0:
		last_refresh_pretty=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(OAUTH_EXPIRATION))
		print(f"OAUTH_EXPIRATION: {last_refresh_pretty}")
		#print(f"authToken: {authToken}, OAUTH_EXPIRATION: {OAUTH_EXPIRATION}")
	if authToken == None: return None
	
	global UBI_EXPIRATION
	ubiToken=None
	if os.path.isfile(UBI_TOKEN_PATH) and UBI_EXPIRATION == -1:
		fh=open(UBI_TOKEN_PATH, 'r')
		result=fh.read()
		fh.close()
		split_result=result.split(",")
		if len(split_result)==3:
			masterName=split_result[0]
			if masterName == USERNAME:
				UBI_EXPIRATION=int(split_result[1])
				ubiToken=split_result[2]
	if UBI_EXPIRATION < time.time() or force_connect:
		result="code=" + authToken
		result=base64.b64encode(result.encode('utf-8'))
		result=result.decode("utf-8")
		if oauth_token_only: return result
		global NAME_ON_PLATFORM,PROFILE_ID
		ubiToken,UBI_EXPIRATION,NAME_ON_PLATFORM,PROFILE_ID=authenticateUbisoft(result)
		if ubiToken == None: return None
		fh=open(UBI_TOKEN_PATH, 'w')
		fh.write(f'{USERNAME},{UBI_EXPIRATION},{ubiToken}')
		fh.close()
	if UBI_EXPIRATION > 0:
		last_refresh_pretty=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(UBI_EXPIRATION))
		print(f"UBI_EXPIRATION: {last_refresh_pretty} USERNAME: {USERNAME}")
	return ubiToken
	
	
###RESTFUL API###

def getTVTLeaderboardAtOffset(offset=1,limit=50):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/playerstats2/leaderboards/team_wars_leaderboard/infinite+c_name+c_banner+c_league+c_members?offset={offset}&limit={limit}'
	response_body=""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTVTLeaderboardAtOffset failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getTeamWarInit():
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/teamwar/init'
	PAYLOAD='{}'
	response_body=""
	try:
		r = requests.post(HOST, data=PAYLOAD, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamWarInit failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getTeamWarUpdate():
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/teamwar/update'
	PAYLOAD='{}'
	response_body=""
	try:
		r = requests.post(HOST, data=PAYLOAD, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamWarUpdate failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getTeamInit():
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/team/init'
	PAYLOAD='{}'
	response_body=""
	try:
		r = requests.post(HOST, data=PAYLOAD, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamInit failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getCardRequests():
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/team/requests'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getCardRequests failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getTeamDetails(team_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/team/teams/{team_id}'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamDetails failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getTeamID(team_name):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/team/search?limit=50&offset=0&name={team_name}'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamID failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getTeamApplications(ingame_team_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/clansservice/clans/default/{ingame_team_id}/applications'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamApplications failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body

def getTeamApplications(ingame_team_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/clansservice/clans/default/{ingame_team_id}/applications'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getTeamApplications failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def acceptApplication(ingame_team_id,user_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/clansservice/clans/default/{ingame_team_id}/applications/profiles/{user_id}'
	PAYLOAD='{}'
	response_body = ""
	try:
		r = requests.put(HOST, data=PAYLOAD, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.acceptApplication failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def rejectApplication(ingame_team_id,user_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/clansservice/clans/default/{ingame_team_id}/applications/profiles/{user_id}'
	response_body = ""
	try:
		r = requests.delete(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.rejectApplication failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def setTeamRole(ingame_team_id,user_id,role='regular'): #regular, elder, co_leader, leader
	API_LOCK.acquire()
	global HEADERS
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/clansservice/clans/default/{ingame_team_id}/members/profiles/{user_id}'
	PAYLOAD='{"role":%s}' % role
	response_body = ""
	#HEADERS["Ubi-AppId"] = "f64d70a5-e962-445e-998c-9f4df6fb1156"
	#HEADERS["X-Unity-Version"] = "2018.4.3f1"
	#HEADERS["X-Version"] = "442"
	#HEADERS["X-Platform"] = "0"
	#HEADERS["X-Device"] = "934806656"
	#HEADERS["User-Agent"] = "southpark/711398 CFNetwork/1120 Darwin/19.0.0"
	#HEADERS["Accept"] = "*/*"
	#HEADERS["Accept-Encoding"] = "gzip, deflate, br"
	#HEADERS["Accept-Language"] = "en-us"
	#HEADERS["Content-Type"] = "application/json"
	try:
		r = requests.put(HOST, data=PAYLOAD, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.setTeamRole failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body

#Seasons (since Stars to MMR Switch)
#https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}
#/playerstats2/leaderboards/pvp_ladder_leaderboard/8/global/infinite+player_name+team_name+highlight?offset={offset}&limit={limit}
#/playerstats2/leaderboards/pvp_ladder_leaderboard/9/global/infinite+player_name+team_name+highlight?offset={offset}&limit={limit}
#/playerstats2/leaderboards/pvp_ladder_leaderboard/10/global/infinite+player_name+team_name+highlight?offset={offset}&limit={limit}
def getGlobalLeaderboardAtOffset(offset=1,limit=50):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/playerstats2/leaderboards/pvp_ladder_leaderboard/10/global/infinite+player_name+team_name+highlight?offset={offset}&limit={limit}'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getGlobalLeaderboardAtOffset failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getUserDetails(user_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://pdc-public-ubiservices.ubi.com/v1/{SPACES_SANDBOX}/team/members/{user_id}'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getUserDetails failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
def getUserName(user_id):
	API_LOCK.acquire()
	checkLoggedIn()
	HOST=f'https://public-ubiservices.ubi.com/v1/profiles?profileId={user_id}'
	response_body = ""
	try:
		r = requests.get(HOST, headers=HEADERS)
		response_body=r.text
	except:
		print("SPPD_API.getUserName failed")
	API_LOCK.notify_all()
	API_LOCK.release()
	return response_body
	
"""
#Note: You can't log in with just any google account, it must be one that is already registered with the game or you get this error message:

"message":
"The server has thrown exception because it cannot fulfill the request: Google Error / Web api. Google Error / Web api. An unexpected web api error code was received. Details: The requested player with ID me was not found..
Stace Trace:    at Ubisoft.Common.Http.SingletonProtectedHttp.<GetContentAsync>d__17.MoveNext()
--- End of stack trace from previous location where exception was thrown ---
   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)
   at Ubisoft.Common.Http.SingletonProtectedHttp.<>c__DisplayClass12_0.<<HttpSendAsync>b__0>d.MoveNext()
   --- End of stack trace from previous location where exception was thrown ---
   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)
   at Ubisoft.Common.CircuitBreaker.Deprecated.AsyncCircuitBreaker.<ExecuteAsync>d__19`1.MoveNext()
   --- End of stack trace from previous location where exception was thrown ---
   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)
   at Ubisoft.Common.Http.SingletonProtectedHttp.<CallWithCircuitBreakerAsync>d__16.MoveNext()
   --- End of stack trace from previous location where exception was thrown ---
   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)
   at Ubisoft.Common.Http.SingletonProtectedHttp.<HttpSendAsync>d__12.MoveNext()
   --- End of stack trace from previous location where exception was thrown ---
   at System.Runtime.ExceptionServices.ExceptionDispatchInfo.Throw()
   at System.Runtime.CompilerServices.TaskAwaiter.HandleNonSuccessAndDebuggerNotification(Task task)
   at Ubisoft.Common.Google.GoogleHandler.<GetPlayerInfoAsync>d__10.MoveNext()",
"errorCode":6,"httpCode":504,"errorContext":"Profiles Client",
"moreInfo":"",
"transactionTime":"2019-11-21T07:06:33.2246609Z",
"transactionId":"d324006f-cee0-4563-9f16-ea7194aba964",
"environment":"PROD"
"""

if __name__ == '__main__':
	#Run something
	#getGlobalLeaderboardAtOffset()
	#print(getTeamID('F2P Whales'))
	setUsernamePassword("email@gmail.com", "password")
	#print(getTeamWarInit())
	pass
	