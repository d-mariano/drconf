#!/usr/bin/env python

'''
   Author:         Dave Mariano
   Date:           April 18, 2015
   Filename:       drconf.py
   
   This is a script to provide password changing automation for Cisco
   routers.  Before reading a file containing the IP addresses of routers,
   the script may either proceed to configure the series of routers 
   assuming the same username and password for remote login of each 
   or can allow for changing the passwords separately.  If there are 
   different remote terminal logins for each router or different changed 
   passwords wanted, manual input for each router should be chosen.

   Passwords will be entirely visible when entering them, which means they 
   will be visible to anyone observing the terminal during and possibly 
   after the process.  Use this with caution.
'''

from __future__ import print_function
import sys
import signal

try:
    import pexpect
except ImportError:
    sys.stderr.write("You do not have 'pexpect' installed.\n")
    sys.stderr.write("Use `pip install pexpect` to install.\n")
    exit(1)

# For Python 2.7 and Python 3.3 compatibility
try:
    raw_input
except NameError:
    raw_input = input

    
# Sets the login information and desired new password/secret
def setLoginInfo():
    user = raw_input('Telnet Username: ')
    pw = raw_input('Telnet Password: ')
    sec = raw_input('Existing Secret: ')
    new = raw_input('New Secret: ')
    return user, pw, sec, new

#  Connect and Change :
#   This method connects to addr via telnet, applying the appropriate
#   password and username.  The existing secret is then used to enter
#   privelaged  mode in order to change the secret to the new one.
def candc(addr, user, pw, sec, new):
    print('\nAttempting password change on router', line)
    # Make a telnet process using the current router address
    child = pexpect.spawnu('telnet %s' % (addr))
    child.timeout = 4
    child.expect(unicode('Username: '))
    child.sendline(user)
    try:
        child.expect(unicode('Password: '))
        child.sendline(pw)
    except:
        print
        # If things get to here, a blank username may have been inputted
        # or the user does not require a password.  The next check will
        # determine the appropriate action
    try:
        child.expect(unicode('>'))
    except:
        print('Incorrect Telnet login.\n\n')
        return
    child.sendline('enable')
    child.expect(unicode('Password: '))
    child.sendline(sec)
    try:
        child.expect(unicode('#'))
    except:
        print('Incorrect enable password\n\n')
        return
    child.sendline('conf t')
    child.expect(unicode('#'))
    child.sendline(unicode('enable secret %s' % new))
    child.expect(unicode('#'))
    print('Password changed successfully.\n\n')
    # Close the child
    if child.isalive():
        child.close()

# Menu for user selection
def menu():
    print('1.\tCisco Secret Change'
            '2.\tHealth Check'
            '3.\tQuit'

# Handler for keyboard interrupt
def sigintHandler(signum, frame):
    print('\n')
    f.close()
    sys.exit(1)


# Initialize CTRL+C interrupt handler
signal.signal(signal.SIGINT, sigintHandler)

# Open file of routers for reading
f = open('routers', 'rb') 
automated = raw_input('Which mode would you like to use? ( default=automated, m=manual )   ')

# Automated PW change for each router, requires only one PW input
# and applies it to all IP's in file
if(automated.lower() != 'm'):
    print('Enter login informaton to be used for all routers.')
    user, pw, sec, new = setLoginInfo()
    print ('\n')
    line = f.readline()
    while( line  != "" ):
        line = f.readline()    
else:
    print('Entering manual mode.\n')
    line = f.readline()
    while( line != "" ):
        # Manual input required for each IP address in file
        print('Enter information for router', line)
        user, pw, sec, new = setLoginInfo()
        candc(line, user, pw, sec, new)
        line = f.readline()

f.close()
    
