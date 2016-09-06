#!/usr/bin/python3                                                                                                                                                              

import os                                                                                                                                                                       
import re                                                                                                                                                                       
import sys                                                                                                                                                                      
import argparse                                                                                                                                                                 

parser = argparse.ArgumentParser(description='Clients vpn auto config.')                                                                                                        
parser.add_argument('client', metavar='c', type=str, help='point name for vpn client')                                                                                          
parser.add_argument('--no_changes', dest='no_changes', action='store_true', default=False)                                                                                      
args = parser.parse_args()                                                                                                                                                      

CLIENT = args.client                                                                                                                                                            
NO_CHANGES = args.no_changes                                                                                                                                                    
OPEN_VPN_RSA = '/etc/openvpn/easy-rsa/2.0/'                                                                                                                                     
OPEN_VPN_ROOT = '/etc/openvpn/'                                                                                                                                                 
OPEN_VPN_CLIENT_DIR = '/etc/openvpn/clients/'                                                                                                                                   
CLIENT_FILES = '%skeys/ca.crt %skeys/%s.key %skeys/%s.crt' % (OPEN_VPN_RSA, OPEN_VPN_RSA, CLIENT, OPEN_VPN_RSA,  CLIENT)                                                        

# find all tunnel based on grep open vpn directory configs                                                                                                                      
tuns = []                                                                                                                                                                       
response = os.popen('grep %s /etc/openvpn/*.conf' % '\'dev tun\'')                                                                                                              
for i in response:                                                                                                                                                              
    try:                                                                                                                                                                        
        tuns.append((int(re.search('tun(\d+)', i).group(1)), i))                                                                                                                
    except AttributeError:                                                                                                                                                      
        print('Something wrong here: ===', i.strip(), '===', sep='')                                                                                                            

# find max tun                                                                                                                                                                  
last_config = sorted(tuns)[-1][-1]                                                                                                                                              
# find last user config by max tun                                                                                                                                              
last_user = re.search('openvpn/(.*)\.conf', last_config).group(1)                                                                                                               

if NO_CHANGES:                                                                                                                                                                  
    print('Last user is: {}'.format(last_user))
    print('cd {}'.format(OPEN_VPN_RSA))
    print('. ./vars && ./pkitool {}'.format(CLIENT))
    print('mkdir {}'.format(OPEN_VPN_CLIENT_DIR + CLIENT))
    print('cp -i {} {}'.format(CLIENT_FILES, OPEN_VPN_CLIENT_DIR + CLIENT + '/'))
    print('touch ' + OPEN_VPN_ROOT+CLIENT+'.conf')
    print('touch ' + OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf')
else:
    # run pkitool with client nickname
    os.chdir(OPEN_VPN_RSA)
    os.system('. ./vars && ./pkitool %s' % CLIENT)

    # make a directory for client and move files generated by pkitool to this dir
    os.mkdir(OPEN_VPN_CLIENT_DIR + CLIENT)
    os.system('cp -i %s %s' % (CLIENT_FILES, OPEN_VPN_CLIENT_DIR + CLIENT + '/'))

    # create empty files for further configurations
    os.system('touch ' + OPEN_VPN_ROOT+CLIENT+'.conf')
    os.system('touch ' + OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf')

print('Editing server side conf...')
# Edit server-side conf
# TODO refactor with configparse
with open(OPEN_VPN_ROOT + last_user + '.conf', 'r') as last_conf:
    if NO_CHANGES:
        print(OPEN_VPN_ROOT + last_user + '.conf:')
        new_conf = sys.stdout
    else:
        new_conf = open(OPEN_VPN_ROOT + CLIENT + '.conf', 'a')

    for line in last_conf:
        if line.strip().startswith('port'):
            port = int(re.search('^port (\d+)', line).group(1))
            port += 1
            new_conf.write('port %s\n' % port)
        elif line.strip().startswith('ifconfig'):
            spam, ip1, ip2 = line.split()
            ip1 = ip1.split('.')
            ip2 = ip2.split('.')
            ip1 = ('.'.join(ip1[:-1]) + '.' + str(int(ip1[-1])+2))
            ip2 = ('.'.join(ip2[:-1]) + '.' + str(int(ip2[-1])+2))
            new_conf.write('%s %s %s\n' % (spam, ip1, ip2))
        elif line.strip().startswith('dev'):
            dev = int(re.search('tun(\d+)$', line).group(1))
            dev += 1
            new_conf.write('dev tun%s\n' % dev)
        elif line.strip().startswith('log-append'):
            new_conf.write('log-append /var/log/vpn/%s.log\n' % CLIENT)
        elif line.strip().startswith('status'):
            new_conf.write('status /var/log/vpn/%s-status.log\n' % CLIENT)
        else:
            new_conf.write(line)
    if not NO_CHANGES:
        new_conf.close()

print('Done. Check it by the addr of %s' % OPEN_VPN_ROOT + CLIENT + '.conf')


print('Editing client  side conf...')
# Edit client side conf
# TODO refactor with configparse
with open(OPEN_VPN_CLIENT_DIR + last_user + '/vpn-gfrd.conf', 'r') as last_conf:
    if NO_CHANGES:
        print(OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf:')
        new_conf = sys.stdout
    else:
        new_conf = open(OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf', 'a')
    for line in last_conf:
        if line.strip().startswith('port'):
            port = int(re.search('^port (\d+)', line).group(1))
            port += 1
            new_conf.write('port %s\n' % port)
        elif line.strip().startswith('ifconfig'):
            spam, ip1, ip2 = line.split()
            ip1 = ip1.split('.')
            ip2 = ip2.split('.')
            ip1 = ('.'.join(ip1[:-1]) + '.' + str(int(ip1[-1])+2))
            ip2 = ('.'.join(ip2[:-1]) + '.' + str(int(ip2[-1])+2))
            new_conf.write('%s %s %s\n' % (spam, ip1, ip2))
        elif line.strip().startswith('cert'):
            new_conf.write('cert %s.crt\n' % CLIENT)
        elif line.strip().startswith('key'):
            new_conf.write('key %s.key\n' % CLIENT)
        else:
            new_conf.write(line)
    if not NO_CHANGES:
        new_conf.close()

print('Done. Check it by the addr of %s' % OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf')
print('Archiving client configurations...')

if NO_CHANGES:
    print('tar -zcvf ' + OPEN_VPN_CLIENT_DIR + CLIENT + '/' + CLIENT + '.tar.gz ' + OPEN_VPN_CLIENT_DIR + CLIENT)
    print('/etc/init.d/openvpn start {}\n'.format(CLIENT))
    print('!!!NOTICE THIS SCRIPT WAS USED IN DEBUG MODE AND HAS NOT DONE ANYTHING!!!')
else:
    os.system('/etc/init.d/openvpn start {}\n'.format(CLIENT))
    os.system('tar -zcvf ' + OPEN_VPN_CLIENT_DIR + CLIENT + '/' + CLIENT + '.tar.gz ' + OPEN_VPN_CLIENT_DIR + CLIENT)

print('Thank you for flying with vpn network lines\n Good luck ! :)')
