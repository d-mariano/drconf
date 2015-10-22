#!/usr/bin/env python

'''
   Author:         Dave Mariano
   Date:           April 18, 2015
   Filename:       drconf.py
   
   This is a script to provide password changing automation for Cisco
   routers.  Before reading a file containing the IP addresses of routers,
   the script may either proceed to configure the series of routers, 
   assuming the same username and password of each for remote connection,
   or can allow for changing the passwords separately.  If there are 
   different remote terminal logins for each router or different changed 
   passwords wanted, manual input for each router should be chosen.
'''
# Allows for Python 2.x to use the 3.x print function 
from __future__ import print_function

import getpass
import os
import string
import sys
import signal

try:
    import pexpect
except ImportError:
    sys.stderr.write("You do not have 'pexpect' installed.\n")
    sys.stderr.write("Use `pip install pexpect` to install.\n")
    exit(1)

# For Python 2.x and Python 3.x compatibility
try:
    raw_input
except NameError:
    raw_input = input




## Main Menu
# A choice is provided by the user and passed to the seekRouters function
# to determine what to do when the routers are connected to remotely.
def menu():
    print(  '\n#############  Menu  #####################\n'
            '1.\tCisco Secret Change\n'
            '2.\tHealth Check\n'
            '3.\tSystem Audit\n'
            '4.\tQuit\n')
    choice = raw_input('Enter the number of your task: ')

    print('\n')
    if choice == '1':       # Cisco Secret Change
        print('\n#############  Secret Change  #####################\n')
        seekRouters(choice)
    elif choice == '2':     # Health Check
        print('\n#############  Health Check  #####################\n')
        seekRouters(choice)
    elif choice == '3':     # System Audit
        print('\n#############  System Audit  #####################\n')
        seekRouters(choice)
    elif choice == '4':     # Quit
        return
    else:
        print(choice, 'is not an option.')
        
    print('\n')
    menu()     


## Seek Routers
# Gives the user a choice of changing the secret of each Cisco 
# router manually with different information or all at once 
# with the same information.
def seekRouters(choice):
    automated = raw_input('Which mode would you like to use?  ( default=automated, m=manual )   ')
    
    # Read the first line of the file
    addr = f.readline().decode('utf-8')
    
    # Automated PW change for each router, requires only one PW input
    # and applies it to all IP's in file
    if automated.lower() != 'm':
        print('Entering automated mode.\n')
        print('Enter login informaton to be used for all routers.')
        user, pw, sec = setLoginInfo()
        # New secret must be obtained for password change 
        if choice == '1':
            new = newSecret()
        print ('\n')
    else:
        print('Entering manual mode.\n')
    
        
    while 1:
        if addr == "\n" or addr.startswith('#'):
            addr = f.readline().decode('utf-8')
            if addr == '':
                break
            continue
        # Input must be made each time for manual mode
        if automated.lower() == 'm':   
            print('\nEnter login information for router', addr)
            user, pw, sec = setLoginInfo()
                
        # Make the connection to router at IP addr
        child = connect(addr, user, pw, sec)
        # Verify a successful connection has been made to this router
        if child != -1:  
            # The operation executed after the remote connection to the
            # router has been made is dependent on the users' choice
            if choice == '1':
                # A new secret must be inputted for each router in manual mode
                if automated == 'm':
                    new = newSecret()
                secretChange(new, child)
            elif choice == '2':
                healthCheck(child)    
            elif choice == '3':
                systemAudit(addr, child)

        addr = f.readline().decode('utf-8') # Check for end of file

        if addr == '': # Make sure the next address is not blank
            break
        
        # Manual Skip, Continue, or Cancel
        if automated.lower() == 'm':
            ans = raw_input('Next router is ' + addr + '\nContinue to next router? (default=continue, s=skip, n=cancel)   ')
            if ans.lower() == 's':
                print('\nSkipping router', addr)
                # Must read next line if a skip is to be made
                addr = f.readline().decode('utf-8') # Check for end of file
                if addr == '':
                    break
            elif ans.lower() == 'n':
                break
    
    f.seek(0, 0) # Reset position of pointer to the beginning of the file
    print('\nEnd of routers...')

# Sets and returns login information specified by the user
def setLoginInfo():
    user = raw_input('Username: ')
    pw = getpass.getpass('Password: ')
    sec = getpass.getpass('Existing Secret: ')
    return user, pw, sec, 

# Sets and returns the new secret desired by the user
def newSecret():
    while 1:
        # Enter new secret and confirm it
        new = getpass.getpass('New Secret: ')
        confirm = getpass.getpass('Confirm New Secret: ')
        if new != confirm:
            print('Passwords do not match.  Please re-enter.')
            continue;
        break;
    return new


## Connect to Router Address 
# Connects to a router specified by addr using the passed login 
# information.  Returns child, being the remote login process 
# opened by pexpect.
def connect(addr, user, pw, sec):
    print("\nAttempting to connect to router" ,addr)
    
    # Make ssh process using the current router address
    try:
        child = pexpect.spawn('ssh %s@%s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null' % (user,addr))
        child.timeout = 4
    except:
        print('Could not reach host', addr)
        return -1
    
    # Password entry attempt
    try:
        child.expect('password: ')
        child.sendline(pw)
    except:
        print('Could not connect to host', addr)
        if child.isalive():
            child.close()
        return -1
    try:
        child.expect('>')
    except:
        print('Incorrect login.\n\n')
        if child.isalive():
            child.close()
        return -1
    
    # Enable secret attempt
    child.sendline('enable')
    child.expect('Password: ')
    child.sendline(sec)
    try:
        child.expect('#')
    except:
        print('Incorrect enable password\n\n')
        if child.isalive():
            child.close()
        return -1
    
    # Return login process for router operation
    return child


## Cisco Secret Change
# This method connects to addr via telnet, applying the appropriate
# password and username.  The existing secret is then used to enter
# privelaged  mode in order to change the secret to the new one.
def secretChange(new, child):
    child.sendline('conf t')
    child.expect('#')
    child.sendline('enable secret %s' % new)
    child.expect('#')
    print('Password changed successfully.\n\n')
    # Work is done, child no longer needed
    if child.isalive():
        child.close()


## Health Check
# Checks the health of the cisco network using ping, connectivity of
# neighbors, and the interface status. 
def healthCheck(child):
    # Layer 1 Validation, show only connected interface status
    child.sendline('show interfaces status | exclude notconnect')
    child.readline() # Read through command
    child.readline() # Read through newline
    results = child.readline() # Read first line
    while 1:
        try:
            results += child.readline() # Append the next line
        except:
            break # Read until prompt
    # Print results
    print(('Interface Status:\n' + results.decode('utf-8')))
    # Layer 2 Validation
    child.sendline('show arp')
    child.readline() # Read through the command 
    results = child.readline()
    while 1:
        try:
            results += child.readline()
        except:
            break
    print(('ARP Table:\n' + results.decode('utf-8')))
    
    # Layer 3 Validation
    

    if child.isalive():
        child.close()


## System Audit
# Checks the version information of the router's software.
def systemAudit(addr, child):
    
    # Get hostname
    child.sendline('show run | include hostname')
    child.expect('hostname ')
    hostname = child.readline()
    child.expect('#')
    
    # Show Version, first line
    child.sendline('show version | include (version|Version)')
    child.expect('\n')
    child.expect('\w+#')
    ver = child.before


    print('Host:\t  {0}Hostname: {1}\n{2}'.format(addr, hostname.decode('utf-8'), ver.decode('utf-8')))
    print('\n')

    # Show Inventory
    child.sendline('show inventory')  
    child.expect('\n')  
    child.expect('\w+#')
    inv = child.before
     
    print('Inventory:\n{0}'.format(inv.decode('utf-8')))

    print('\n') # Newline to separate from next router
    if child.isalive():
        child.close()


def sigintHandler(signum, frame):
    print('\n')
    f.close()
    sys.exit(1)


if __name__ == "__main__":
    # Initialize CTRL+C interrupt handler
    signal.signal(signal.SIGINT, sigintHandler)

    # File 'routers' must exist for the program to work
    if os.access('routers', os.F_OK) is False:
        print('\nThe file \'routers\' does not exist, but will be created.\n')
        f = open('routers', 'w')
        print('\nIt must now be populated with router IP addresses.\n')
        print('Each router IP must be separated with a new line.\n')
        print('Now exiting.\n\n')
        f.close()
        exit()

    # There is no point to run if no routers are specified, so
    # file size must be tested
    finfo = os.stat('routers')
    if finfo.st_size == 0:
        print('\nThe file\'routers\' is 0 bytes long.\n')
        print('The file must be populated with IP addresses of routers.\n')
        print('Each router IP must be separted with a new line.\n')
        print('Now exiting.\n\n')
        exit()

    f = open('routers', 'rb') 

    menu() 

    f.close() 

    exit()

