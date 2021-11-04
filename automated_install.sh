#!/bin/bash

###You must cd into the cloned repo (Nagios-Config-Scripts) before running this script.###

###UPDATE THE FILE systemd_service PRIOR TO RUNNING THIS SCRIPT !!###
###UPDATE THE DISK CONFIG BELOW###

if [ $EUID != 0 ]; then
    echo "Please run this script as root"
    exit
fi

apt update && apt install -y autoconf gcc libc6 libmcrypt-dev make libssl-dev wget bc gawk dc build-essential snmp libnet-snmp-perl gettext xinetd python3-pip

wget --no-check-certificate -O nagios-plugins.tar.gz https://github.com/nagios-plugins/nagios-plugins/archive/release-2.3.3.tar.gz
wget https://github.com/NagiosEnterprises/nrpe/releases/download/nrpe-4.0.2/nrpe-4.0.2.tar.gz

tar xzf nagios-plugins.tar.gz && tar xzf nrpe-4.0.2.tar.gz

useradd nagios && groupadd nagios && usermod -a -G nagios nagios

cd nagios-plugins-release-2.3.3 && ./tools/setup && ./configure && make install

cd ../nrpe-4.0.2 && ./configure --with-nrpe-port=58888 --enable-command-args

make all && make install && make install-config && make install-inetd && make install-init

sed -i 's/5666/58888/g' /etc/services

cp ../check_api /usr/local/nagios/libexec/

sed -i 's/127.0.0.1 ::1/127.0.0.1 ::1 78.213.99.50/g' /etc/xinetd.d/nrpe
systemctl restart xinetd.service

### UPDATE THE DISK CONFIG HERE (/dev/DISK_NAME)
echo 'command[check_disk_1]=/usr/local/nagios/libexec/check_disk -w 20% -c 10% -p /dev/vda1' >> /usr/local/nagios/etc/nrpe.cfg
##ADD OTHER DISKS AS REQUIRED
echo 'command[check_icmp]=/usr/local/nagios/libexec/check_icmp localhost' >> /usr/local/nagios/etc/nrpe.cfg
echo 'command[check_api]=/usr/local/nagios/libexec/check_api $ARG1$' >> /usr/local/nagios/etc/nrpe.cfg
sed -i 's/dont_blame_nrpe=0/dont_blame_nrpe=1/g' /usr/local/nagios/etc/nrpe.cfg
sed -i 's/allowed_hosts=127.0.0.1,::1/allowed_hosts=127.0.0.1,::1,78.213.99.50/g' /usr/local/nagios/etc/nrpe.cfg

cp ../systemd_service /etc/systemd/system/monitoring_api.service
systemctl daemon-reload && systemctl enable monitoring_api.service && systemctl start monitoring_api.service

systemctl enable nrpe.service && systemctl start nrpe.service

pip install fastapi uvicorn

###remove obsolete files and folders
cd ..
rm -r nagios-plugins* nrpe-4.0.2*
