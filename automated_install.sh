#!/bin/bash

###UPDATE THE FILE config.sh PRIOR TO RUNNING THIS SCRIPT !!###
#Nothing to update here.

#THIS SCRIPT SETS UP THE CLIENT, = A NODE THAT IS MONITORED BY NAGIOS.
#Nagios' config should be updated with the node's information (in services.cfg and hosts.cfg).

###You must cd into the cloned repo (Monitoring) before running this script.###



#load all the variables from config.sh

source config.sh

if [ -z ${NAGIOS_SERVER_IP} ]; then
  echo "Missing server IP. Please update config.sh"
  exit
fi

if [ $EUID != 0 ]; then
    echo "Please run this script as root"
    exit
fi

apt update && apt install -y autoconf gcc libc6 libmcrypt-dev make libssl-dev wget bc gawk dc build-essential snmp libnet-snmp-perl gettext xinetd python3-pip #python3-fastapi python3-uvicorn

pip install fastapi==0.75.0 starlette==0.17.1 uvicorn==0.17.6

wget --no-check-certificate -O nagios-plugins.tar.gz https://github.com/nagios-plugins/nagios-plugins/archive/release-2.3.3.tar.gz
wget https://github.com/NagiosEnterprises/nrpe/releases/download/nrpe-4.0.3/nrpe-4.0.3.tar.gz

tar xzf nagios-plugins.tar.gz && tar xzf nrpe-4.0.3.tar.gz

useradd nagios && groupadd nagios && usermod -a -G nagios nagios

cd nagios-plugins-release-2.3.3 && ./tools/setup && ./configure && make install

cd ../nrpe-4.0.3 && ./configure --with-nrpe-port=58888 --enable-command-args --with-need-dh=no  #last argument necessary with ssl 3

make all && make install && make install-config && make install-inetd && make install-init

if [[ -v NRPE_PORT ]] && [[ "$NRPE_PORT" != "5666" ]]; then
  sed -i "s/5666/$NRPE_PORT/g" /etc/services
fi

cp ../check_api /usr/local/nagios/libexec/

sed -i "s/127.0.0.1 ::1/127.0.0.1 ::1 $NAGIOS_SERVER_IP/g" /etc/xinetd.d/nrpe
systemctl restart xinetd.service


### DISK CONFIG ###

for i in "${DISK_LIST[@]}"; do
  echo $i >> /usr/local/nagios/etc/nrpe.cfg
done

echo 'command[check_icmp]=/usr/local/nagios/libexec/check_icmp localhost' >> /usr/local/nagios/etc/nrpe.cfg
echo 'command[check_api]=/usr/local/nagios/libexec/check_api $ARG1$' >> /usr/local/nagios/etc/nrpe.cfg
sed -i 's/dont_blame_nrpe=0/dont_blame_nrpe=1/g' /usr/local/nagios/etc/nrpe.cfg
sed -i "s/allowed_hosts=127.0.0.1,::1/allowed_hosts=127.0.0.1,::1,$NAGIOS_SERVER_IP/g" /usr/local/nagios/etc/nrpe.cfg

sed -i "s/-i validator_name1 PORT1 -i validator_name2 PORT2 etc./$VALIDATORS/g" ../systemd_service
cp ../systemd_service /etc/systemd/system/monitoring_api.service
systemctl daemon-reload && systemctl enable monitoring_api.service && systemctl start monitoring_api.service

systemctl enable nrpe.service && systemctl start nrpe.service

###remove obsolete files and folders
cd ..
rm -r nagios-plugins* nrpe-4.0.3*
