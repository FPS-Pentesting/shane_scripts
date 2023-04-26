#!/usr/bin/python
import os, sys, time, requests, ipaddress
from datetime import datetime

# Insert HackerTarget API key here
apikey=""

def Usage():
	print("Usage: reverse_ip_hackertarget.py <CIDRList> <OutFile>\n")
	print("CIDRList should contain a list of CIDR addresses, one per line.\n Each CIDR range counts as only 1 query, so convert your IPList to CIDR range.")
	print("OutFile will be created and will contain domain IP mappings.")
	exit()

# Function to handle API requests
def ApiRequest(url):
	for attempt in range(10):
		try:
			response=requests.get(url)
		except requests.exceptions.RequestException as e:
			time.sleep(1)
			continue
		else:
			return response
	print("10 HTTP requests failed in a row, exiting")
	exit() 		

#Define some output colors
class color:
	BLU = '\033[94m'
	YLW = '\033[93m'
	GRN = '\033[92m'
	ENDC = '\033[0m'
	

# Check supplied arguments
n = len(sys.argv)
if n != 3:
	Usage()
if not os.path.isfile(sys.argv[1]):
	print("!!! File \""+sys.argv[1]+"\" does NOT exist!!!\n")
	Usage()
#if os.path.isfile(sys.argv[2]):
#	print("!!! File \""+sys.argv[2]+"\" already exists, please choose an output file that does not exist!!!\n")
#	Usage()
	
### Main ###
starttime = datetime.now()
ipFile = open(sys.argv[1], 'r')
outFile = open(sys.argv[2], 'a')
count = 0
limitReached = 0
lines = ipFile.readlines()
numIPs = len(lines)

#Make sure all IPs are in CIDR notation
#Each CIDR counts as 1 query, so using only CIDR helps avoid hitting the API query limit
badFormat = 0
for ip in lines:
	ip = ip.rstrip('\n')
	try:
		ipaddress.ip_network(ip)
	except ValueError:
		print(f"Non-CIDR Address: {ip}")
		badFormat = 1
if badFormat:
	print("Non-CIDR format detected, try running the input file through \"convert_to_cidr\" exiting.")
	exit()

#Process each CIDR	
for ip in lines:
	#strip newline from end of IP address
	ip = ip.rstrip('\n')
	#Check if we hit our Query Limit
	if limitReached == 0:
	
		#set up the request elements
		ipURL = f"https://api.hackertarget.com/reverseiplookup/?q={ip}&apikey={apikey}"
		
		#Execute HTTPS Query for reverse IP info
		reverseIP = ApiRequest(ipURL)

		#Use these later to see if we've hit the limit
		queryCount = reverseIP.headers["X-API-Count"]
		queryLimit = reverseIP.headers["X-API-Quota"]

		#Check if we have hit the query limit
		if(int(queryCount) >= int(queryLimit)):
			print("Your daily API query count of "+queryCount+" has reached or exceeded the limit of "+queryLimit+"!")
			limitReached=1
			endTime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
			if(count < numIPs):
				print("We didn't finish processing all of the IP addresses.")
				print("Creating a new file to store the IP addresses we still need to query.")
				print(f"Name of new file: {color.BLU}hackertarget_remaining_IPList_{endTime}{color.ENDC}")
				newIPList = open(f"hackertarget_remaining_IPList_{endTime}", 'w')
				print("\nContinue the process later by using the following command:")
				print(f"{color.GRN}./reverse_ip_hackertarget.py hackertarget_remaining_IPList_{endTime} {outFile.name}{color.ENDC}")
				newIPList.write(ip+"\n")
			continue
		else:
			print("Percentage Complete: "+str(round(100 * count/numIPs, 2)), end='\r')
			count+=1
			
		#Write results to outfile
		for item in reverseIP.text.split("\n"):
			if("No DNS A records found" in item):
				pass
			elif("," in item):
				outFile.write(item+'\n')
			elif("," not in item):
				outFile.write(item+','+ip+'\n')
			else:
				print("!!! Unexpected result: "+item+"\nThis script needs to be updated to handle this situation.")
				outFile.write("!!! Unexpected result: "+item+"\tThis script needs to be updated to handle this situation.\n")

	else:#Query limit has been reached, add remaining IPs to file to make continuing later easy
		newIPList.write(ip+"\n")

print("Number of queries made: "+str(count))
print(f"Current daily query usage is: {queryCount}/{queryLimit}")
print("Script completion took: "+str(datetime.now()-starttime))
print(f"Results are in CSV format in {color.BLU}{outFile.name}{color.ENDC}")	
if count != numIPs:	
	print(f"\n{color.YLW}WARNING{color.ENDC}: Finished processing {count}/{numIPs} lines from the input file.")
	print(f"Continue tomorrow using: {color.GRN}./reverse_ip_hackertarget.py hackertarget_remaining_IPList_{endTime} {outFile.name}{color.ENDC}")
	

