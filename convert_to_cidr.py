#!/usr/bin/python
import os, sys, ipaddress, subprocess

def Usage():
	print("Usage: convert_to_cidr.py <IPList>\n")
	print("IPList should contain a list of single IP, IP dash ranges, or CIDR addresses, one per line.")
	print("OutFile will be created and will contain only CIDR notation.")
	exit()

# Check supplied arguments
n = len(sys.argv)
if n != 2:
	Usage()
if not os.path.isfile(sys.argv[1]):
	print("!!! File \""+sys.argv[1]+"\" does NOT exist!!!\n")
	
### Main ###
ipFile = open(sys.argv[1], 'r')
outFile = open(f"{os.path.splitext(ipFile.name)[0]}_CIDR.txt", 'w')

#Use Nmap to generate a list of individual IP addresses
nmapCommand = subprocess.run(["nmap", "-n", "-sL", "-iL", f"{ipFile.name}"], capture_output=True, text=True)
#Exit if Nmap reports errors with the input File
if(len(nmapCommand.stderr)>0):
	print(nmapCommand.stderr)
	print("Please correct the above issues in the input File and try again.")
	exit()

#Create list of single IPs from Nmap output
singleIPlist=[]
for line in nmapCommand.stdout.split("\n"):
	if "Nmap scan report for" in line:
		singleIPlist.append(line.split(" ")[4])
		
#Convert individual IPs to list of condensed CIDR addresses using ipaddress library
nets = [ipaddress.ip_network(ip) for ip in singleIPlist]
cidrs = list(ipaddress.collapse_addresses(nets))

for cidr in cidrs:
	outFile.write(str(cidr)+"\n")
print(f"Wrote consolidated CIDRs to: {outFile.name}")


	

