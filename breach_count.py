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

# Function to handle API requests
def ApiRequest(url, headers):
	for attempt in range(10):
		try:
			response=requests.get(url, headers=headers)
		except requests.exceptions.RequestException as e:
			time.sleep(1)
			continue
		else:
			#If rate limit hit sleep and goto next attempt
			if response.status_code == 429:
				#sleep for recommended time then retry
				sleeptime=int(response.headers["Retry-After"])+0.1
				print("Rate limit hit, sleeping for "+str(sleeptime)+" seconds.")
				print("Make sure no one else is using the API!!! :)\n")
				time.sleep(sleeptime)
			else:
				break    		
	time.sleep(ratelimit)
	return response

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
outFile.write("Emails,Breaches,MostRecentBreachDate,BreachNames,Pastes,PasteSources\n")

count = 0
for email in emailFile:
	#strip newline from end of email address
	email = email.rstrip('\n')
	
	#set up the request elements
	breachUrl = f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false'
	pasteUrl = f'https://haveibeenpwned.com/api/v3/pasteaccount/{email}'
	headers = {
		'user-agent': 'Flexential Pentesters',
		'hibp-api-key': f'{apikey}'
	}
	
	#Get breaches
	breaches = ApiRequest(breachUrl, headers)
	#Get pastes
	pastes = ApiRequest(pasteUrl, headers)
	
	#Process the breaches
	breachNum = 0
	mostRecentBreachDate = "N/A"
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
		tempDates = []
		for dictionary in tempList:
			tempDates.append(datetime.strptime(dictionary['BreachDate'], '%Y-%m-%d').date())
		mostRecentBreachDate = max(tempDates)
	else:
		breachNum = -1
		breachNames = "There was an unexpected error"
		print("!!!An unexpected HTTP response code was received while processing breaches for this email: "+email)
		print("HTTP status code was: "+str(breaches.status_code))
		
	#Process the pastes
	pasteNum = 0
	pasteSources = ""
	if(pastes.status_code == 404):
		pasteNum = 0
		pasteSources = ""
	elif(pastes.status_code == 200):
		tempList = pastes.json()
		pasteNum = len(tempList)
		tempLinks = []
		for dictionary in tempList:
			tempLinks.append(dictionary['Source'])
		pasteSources = ('|'.join(tempLinks))
	else:
		pasteNum = -1
		print("!!!An unexpected HTTP response code was received while processing pastes for this email: "+email)
		print("HTTP status code was: "+str(pastes.status_code))
	
	print(str(datetime.now()-starttime).split(".")[0]+": "+email+" "+str(breachNum)+" "+str(mostRecentBreachDate)+" "+breachNames+" "+str(pasteNum)+" "+pasteSources)
	outFile.write(email+","+str(breachNum)+","+str(mostRecentBreachDate)+","+breachNames+","+str(pasteNum)+","+pasteSources+"\n")
	count += 1
	
print("\nFinished!")
print("Number of emails processed: "+str(count))
print("Script started at: "+str(starttime))
print("Script finished at: "+str(datetime.now()))
print("Completion took: "+str(datetime.now()-starttime))
print("Results are in CSV format in "+sys.argv[2])
