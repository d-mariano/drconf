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
import sys
import signal

# Check for pexepct
try:
    import pexpect
    import pxssh
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
    print(  '#############  Menu  #####################\n'
            '1.\tCisco Secret Change\n'
            '2.\tHealth Check\n'
            '3.\tSystem Audit\n'
            '4.\tQuit\n')
    choice = raw_input('Enter the number of your task: ')
    print('\n')
    if choice == '1':       # Cisco Secret Change
        seekRouters(choice) 
    elif choice == '2':     # Health Check
        seekRouters(choice)
    elif choice == '3':     # System Audit
        seekRouters(choice)
    elif choice == '4':     # Quit
        return
    else:
        print(choice, 'is not an option.')
    print('\n')
    menu() # Run the menu again after operation


## Cisco Secret Change
# Gives the user a choice of changing the secret of each Cisco 
# router manually with different information or all at once 
# with the same information.
def seekRouters(choice):
    automated = raw_input('Which mode would you like to use?  ( default=automated, m=manual )   ')
    
    # Read the first line of the file
    addr = f.readline()
    
    # Automated PW change for each router, requires only one PW input
    # and applies it to all IP's in file
    if(automated.lower() != 'm'):
        print('Enter login informaton to be used for all routers.')
        user, pw, sec= setLoginInfo()
        # New secret must be obtained for password change 
        if(choice == '1'):
            new = newSecret()
        print ('\n')
        
        while( addr  != "" ):
            # Make the connection to router at IP addr
            child = connect(addr, user, pw, sec)
            # Verify a successful connection has been made to this router
            if child != -1:  
                # The operation executed after the remote connection to the
                # router has been made is dependent on the users' choice
                if choice == '1':
                    secretChange(new, child)
                elif choice == '2':
                    healthCheck(child)    
                elif choice == '3':
                    systemAudit(child)
            addr = f.readline()    
    else:
        print('Entering manual mode.\n')
        while( addr != "" ):
            # Manual input required for each IP address in file
            print('Enter login information for router', line)
            user, pw, sec= setLoginInfo()
    
            # Make the connection
            child = connect(addr, user, pw, sec)
            # Verify a successful connection
            if child == -1:  
                if choice == '1':
                    # New secret must inputted for secret change
                    new = newSecret()
                    secretChange(new, child)
                elif choice == '2':
                    healthCheck(child)    
                elif choice == '3':
                    systemAudit(child)
            addr = f.readline()
    
    f.seek(0, 0) # Reset position of pointer to the beginning of the file


# Sets and returns login information specified by the user
def setLoginInfo():
    user = raw_input('Username: ')
    pw = getpass.getpass('Password: ')
    sec = getpass.getpass('Existing Secret: ')
    return user, pw, sec, 

# Sets and returns the new secret desired by the user
def newSecret():
    while 1:
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
    print('\nAttempting to connect to router', addr)
    # Make ssh process using the current router address
    try:
        child = pexpect.spawnu('ssh %s@%s -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null' % (user,addr))
        child.timeout = 4
    except:
        print('Could not reach host', addr)
    
    # Password entry attempt
    try:
        child.expect(unicode('password: '))
        child.sendline(pw)
    except:
        print('Could not connect to host', addr)
        if child.isalive():
            child.close()
        return -1
    try:
        child.expect(unicode('>'))
    except:
        print('Incorrect login.\n\n')
        if child.isalive():
            child.close()
        return -1
    
    # Enable secret attempt
    child.sendline('enable')
    child.expect(unicode('Password: '))
    child.sendline(sec)
    try:
        child.expect(unicode('#'))
    except:
        print('Incorrect enable password\n\n')
        if child.isalive():
            child.close()
        return -1
    # Return the remote login process
    return child


## Cisco Secret Change
# This method connects to addr via telnet, applying the appropriate
# password and username.  The existing secret is then used to enter
# privelaged  mode in order to change the secret to the new one.
def secretChange(new, child):
    child.sendline('conf t')
    child.expect(unicode('#'))
    child.sendline(unicode('enable secret %s' % new))
    child.expect(unicode('#'))
    print('Password changed successfully.\n\n')
    # Work is done, close the child
    if child.isalive():
        child.close()


## Health Check
# Checks the health of the cisco network using ping, connectivity of
# neighbors, and the interface status. 
def healthCheck(child):
    
    if child.isalive():
        child.close()


## System Audit
# Checks the version information of the router's software.
def systemAudit(child):
    if child.isalive():
        child.close()


# Handler for keyboard interrupt
def sigintHandler(signum, frame):
    print('\n')
    f.close()
    sys.exit(1)



# Initialize CTRL+C interrupt handler
signal.signal(signal.SIGINT, sigintHandler)

f = open('routers', 'rb') # Open file of routers for reading

menu() # Begin menu loop

f.close() 
    
