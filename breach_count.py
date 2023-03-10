#!/usr/bin/python
import os, sys, time, requests
from datetime import datetime

# Insert HaveIBeenPwned API key here
apikey=""
# Set this to the number of seconds we need to wait in between each request
# Currently we get 10 requests/min, so we can send 1 request/6 seconds
ratelimit = 6

def Usage():
	print("Usage: breach_count.py <EmailFile> <OutFile>\n")
	print("EmailFile should contain a list of user Email addresses, one per line.")
	print("OutFile will be created and will contain breach information.")
	exit()

# Check supplied arguments
n = len(sys.argv)
if n != 3:
	Usage()
if not os.path.isfile(sys.argv[1]):
	print("!!! File \""+sys.argv[1]+"\" does NOT exist!!!\n")
	Usage()
if os.path.isfile(sys.argv[2]):
	print("!!! File \""+sys.argv[2]+"\" already exists, please choose an output file that does not exist!!!\n")
	Usage()
	
### Main ###
starttime = datetime.now()
emailFile = open(sys.argv[1], 'r')
outFile = open(sys.argv[2], 'w')
outFile.write("Emails,Breaches,BreachNames,Pastes,PasteLinks\n")

count = 0
for email in emailFile:
	#strip newline from end of email address
	email = email.rstrip('\n')
	
	#set up the request elements
	breachUrl = f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=true'
	pasteUrl = f'https://haveibeenpwned.com/api/v3/pasteaccount/{email}'
	headers = {
		'user-agent': 'Flexential Pentesters',
		'hibp-api-key': f'{apikey}'
	}
	
	#send request and get response
	breaches=requests.get(breachUrl, headers=headers)
	#If rate limit hit sleep and try again
	while(breaches.status_code == 429):
		#sleep for recommended time then retry
		sleeptime=int(breaches.headers["Retry-After"])+0.1
		print("Rate limit hit, sleeping for "+str(sleeptime)+" seconds.")
		print("Make sure no one else is using the API!!! :)\n")
		time.sleep(sleeptime)
		breaches=requests.get(breachUrl, headers=headers)
	time.sleep(ratelimit)
	
	#send request and get response
	pastes=requests.get(pasteUrl, headers=headers)
	#If rate limit hit sleep and try again
	while(pastes.status_code == 429):
		#sleep for recommended time then retry
		sleeptime=int(pastes.headers["Retry-After"])+0.1
		print("Rate limit hit, sleeping for "+str(sleeptime)+" seconds.")
		print("Make sure no one else is using the API!!! :)\n")
		time.sleep(sleeptime)
		pastes=requests.get(pasteUrl, headers=headers)
	time.sleep(ratelimit)
	
	#Process the breaches
	breachNum = 0
	breachNames = ""
	if(breaches.status_code == 404):
		breachNum = 0
		breachNames = ""
	elif(breaches.status_code == 200):
		tempList = breaches.json()
		breachNum = len(tempList)
		tempNames = []
		for dictionary in tempList:
			tempNames.append(dictionary['Name'])
		breachNames = ('|'.join(tempNames))
	else:
		breachNum = -1
		breachNames = "There was an unexpected error"
		print("!!!An unexpected HTTP response code was received while processing breaches for this email: "+email)
		print("HTTP status code was: "+str(breaches.status_code))
	#Process the pastes
	pasteNum = 0
	pasteLinks = ""
	if(pastes.status_code == 404):
		pasteNum = 0
		pasteLinks = ""
	elif(pastes.status_code == 200):
		tempList = pastes.json()
		pasteNum = len(tempList)
		tempLinks = []
		for dictionary in tempList:
			tempLinks.append(dictionary['Title'])
		pasteLinks = ('|'.join(tempNames))
	else:
		pasteNum = -1
		print("!!!An unexpected HTTP response code was received while processing pastes for this email: "+email)
		print("HTTP status code was: "+str(pastes.status_code))
	
	print(str(datetime.now()-starttime).split(".")[0]+": "+email+" "+str(breachNum)+" "+breachNames+" "+str(pasteNum)+" "+pasteLinks)
	outFile.write(email+","+str(breachNum)+","+breachNames+","+str(pasteNum)+","+pasteLinks+"\n")
	count += 1
	
print("\nFinished!")
print("Number of emails processed: "+str(count))
print("Script started at: "+str(starttime))
print("Script finished at: "+str(datetime.now()))
print("Completion took: "+str(datetime.now()-starttime))
print("Results are in CSV format in "+sys.argv[2])
