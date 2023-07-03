#!/bin/bash

###RUN THIS SCRIPT IF YOU ARE GOING TO USE PROMETHEUS (e.g. with Grafana)###

#you will need to update /etc/prometheus/prometheus.yml afterwards, adding localhost:PORT at the end (the port set in config.toml)#
source config.sh

curl -s https://api.github.com/repos/prometheus/prometheus/releases/latest | grep browser_download_url | grep linux-amd64 | cut -d '"' -f 4 | wget -qi -
tar xf prometheus*.tar.gz
cd prometheus*/

#listen on the node_exporter's port. Need to also add the Prometheus ports of the validator(s) if enabled.
sed -i s/localhost:9090/localhost:9100/g prometheus.yml

groupadd --system prometheus
useradd -s /sbin/nologin --system -g prometheus prometheus

mkdir /var/lib/prometheus
for i in rules rules.d files_sd; do sudo mkdir -p /etc/prometheus/${i}; done

mv prometheus promtool /usr/local/bin/
mv prometheus.yml /etc/prometheus/prometheus.yml
mv consoles/ console_libraries/ /etc/prometheus/

tee /etc/systemd/system/prometheus.service<<EOF
[Unit]
Description=Prometheus
Documentation=https://prometheus.io/docs/introduction/overview/
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecReload=/bin/kill -HUP \$MAINPID
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.external-url=

SyslogIdentifier=prometheus
Restart=always

[Install]
WantedBy=multi-user.target
EOF

for i in rules rules.d files_sd; do sudo chown -R prometheus:prometheus /etc/prometheus/${i}; done
for i in rules rules.d files_sd; do sudo chmod -R 775 /etc/prometheus/${i}; done
chown -R prometheus:prometheus /var/lib/prometheus/

#install node_exporter to get the server's metrics
curl -s https://api.github.com/repos/prometheus/node_exporter/releases/latest | grep browser_download_url | grep linux-amd64 | cut -d '"' -f 4 | wget -qi -
tar xf node_exporter*.tar.gz
mv node_exporter*/node_exporter /etc/prometheus

tee /etc/systemd/system/node_exporter.service<<EOF
[Unit]
Description=Prometheus - Node Exporter
Documentation=https://prometheus.io/docs/introduction/overview/
Wants=network-online.target
After=network-online.target
Before=prometheus.service

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecReload=/bin/kill -HUP $MAINPID
ExecStart=/etc/prometheus/node_exporter

SyslogIdentifier=prometheus
Restart=always

[Install]
WantedBy=multi-user.target
EOF

line=$(sed -n '/- targets: \["localhost:9100"\]/p' "/etc/prometheus/prometheus.yml")


for i in "${PROMETHEUS_PORTS[@]}"; do
  line="${line/]/, \"localhost:$i\"]}"
done

sed -i "s|- targets: \[\"localhost:9100\"\]|$line|" /etc/prometheus/prometheus.yml


systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus
systemctl enable node_exporter
systemctl start node_exporter

cd .. 
rm -r prometheus-* 
