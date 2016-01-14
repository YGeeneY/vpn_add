#!/usr/bin/python
import os
import re
import sys

try:
    CLIENT = sys.argv[1]
except IndexError:
    CLIENT = input('Enter a client nickname: ')

OPEN_VPN_RSA = '/etc/openvpn/easy-rsa/2.0/'
OPEN_VPN_ROOT = '/etc/openvpn/'
OPEN_VPN_CLIENT_DIR = '/etc/openvpn/clients/'
CLIENT_FILES = '%skeys/ca.crt %skeys/%s.key %skeys/%s.crt' % (OPEN_VPN_RSA,OPEN_VPN_RSA, CLIENT, OPEN_VPN_RSA,  CLIENT)


os.chdir(OPEN_VPN_RSA)
os.system('. ./vars && ./pkitool %s' % CLIENT)

os.mkdir(OPEN_VPN_CLIENT_DIR + CLIENT)
os.system ('cp -i %s %s' % (CLIENT_FILES, OPEN_VPN_CLIENT_DIR + CLIENT + '/'))

tuns = []
response = os.popen('grep %s /etc/openvpn/*.conf' % '\'dev tun\'')
for i in response:
    tuns.append((int(re.search('tun(\d+)', i).group(1)), i))

last_config = sorted(tuns)[-1][-1]
last_user = re.search('openvpn/(.*)\.conf', last_config).group(1)


os.system('touch ' + OPEN_VPN_ROOT+CLIENT + '.conf')
os.system('touch ' + OPEN_VPN_CLIENT_DIR + CLIENT+ '/vpn-gfrd.conf')

print('Editing server side conf...')

# Edit server-side conf
with open(OPEN_VPN_ROOT+ last_user +'.conf', 'r') as last_conf:
    with open(OPEN_VPN_ROOT+ CLIENT +'.conf', 'a') as new_conf:
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

            elif line.strip().startswith('route'):
                spam, ip1, ip2 = line.split()
                ip1 = ip1.split('.')
                ip1 = ('.'.join(ip1[:-1]) + '.' + str(int(ip1[-1])+4))
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

print('Done. Check it by the addr of %s' % OPEN_VPN_ROOT+ CLIENT +'.conf')


print('Editing client  side conf...')

# Edit client side conf
with open(OPEN_VPN_CLIENT_DIR + last_user + '/vpn-gfrd.conf', 'r') as last_conf:
    with open(OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf', 'a') as new_conf:
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

print('Done. Check it by the addr of %s' % OPEN_VPN_CLIENT_DIR + CLIENT + '/vpn-gfrd.conf')

os.system('/etc/init.d/openvpn start %s' % CLIENT)

print('Thank you for flying with vpn network lines\n Good luck ! :)')
