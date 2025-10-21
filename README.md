# Monitoring Deployment Scripts and Configuration Files (Nagios & Grafana) for Cosmos-Based Blockchains.
This repository contains configuration files for a Nagios 4 deployment, that would monitor one to multiple Cosmos/Tendermint-based validators:
- Nagios server configuration files, which <b>must be updated to match one's actual setup</b>, 
- Remote server(s) setup and scripts (API, NRPE),
- The remote hosts are monitored by querying a custom API (Python3/FastAPI) through Nagios' NRPE and getting some key parameters about the validator.

- <code>resize_volume.py</code> is a script allowing to automatically increase the disk space for Hetzner and Digital Ocean, using their respective API.<br>
The relevant data (disk ids, API tokens, disk mount points) must be defined in another file named <code>volume_data.py</code> and both should be placed in <code>/usr/local/nagios/libexec/</code>
- This works with Nagios and the different values such as the host and service names should match the hostnames from Nagios (in our case, host may be <code>HETZNER-1</code>, service may be <code>Check Disk Space 2</code>, and so on).

- The <code>prometheus_install.sh</code> script is meant to install Prometheus and its systemd service to plug into Grafana for example.


<b>WHY?</b>

- We intend to provide a means for the community to monitor their validators, accessible even to those without much technical knowledge. As such, the code is voluntarily kept as simple as it can possibly be -- it may be subject to changes, improvements and complexification, but we'll try to keep it easily readable and deployable.
- The monitoring tool allows one to be alerted almost instantly whenever a problem arises, thus being able to quickly resolve an issue and in turn, improve the overall stability of the network.<br>
Avoiding being slashed is also a nice perk.
- Why Nagios? This is clearly not the most modern of the monitoring solutions, however it is one of the easiest to understand and set up. It is also very low on resources: our initial deployment tests were on a Raspberry Pi 3, which handled the task without any problem. This can be installed on pretty much any Linux machine.

<b>MONITORED METRICS</b>

- <code>Disk space</code>: WARNING at 6 Go left, CRITICAL at 3 Go. (by default, alerts are sent on CRITICAL state only)
- The Python script creates API endpoints allowing to monitor the following items:
  - <code>Validator Status</code>: whether the node is running (OK) or not (CRITICAL). 
  - <code>Block Delay</code>: delta between the node's block timestamp and the official timestamp. WARNING if above 2s (and usually it's about 0.1s max).
  - <code>Missed Block</code>: WARNING if the node missed a block. Displays the missed block number, 'N/A' otherwise. This metric also monitors that the block height is properly incrementing. Status become CRITICAL if the height does not increment for about 15 seconds.
  - <code>Bonding Status</code>: OK if the validator is bonded (= part of the active set), CRITICAL otherwise.

Other metrics and endpoints can easily be added in the script, and the corresponding services defined in Nagios.

<b>INSTRUCTIONS - CLIENT SIDE</b>

- Update the items in <code>config.sh</code> then just run <code>automated_install.sh</code>.
- You can also run <code>prometheus_install.sh</code> if you intend to use Prometheus (with Grafana for example).
- A Grafana template dashboard is provided in the GRAFANA folder.
- <b>TERRA & INJECTIVE specific</b>: if running an Oracle for Terra and a Peggo Orchestrator, these can be monitored as well. Update the addresses in lines 38 and 49 of <code>cosmos_validators_monitoring.py</code>.

<b>INSTRUCTIONS - NAGIOS INSTALLATION AND CONFIGURATION</b>

- You need to install Nagios on a Linux host, along with the webserver (Apache by default, probably possible to use another if you're feeling adventurous).<br>
This tutorial is pretty straightforward: https://support.nagios.com/kb/article/nagios-core-installing-nagios-core-from-source-96.html<br>
- Once Nagios is installed, you can configure it using the templates provided in the <code>etc</code> and <code>libexec</code> directories. The default target location is <code>/usr/local/nagios/</code>.<br>
- IF YOU WISH TO RECEIVE ALERTS BY EMAIL: you also need to configure Postfix or sendmail on the Nagios server (note that you can also configure Nagios to send Discord/Telegram/SMS alerts).<br>
If you don't have a properly configured mail server with a certificate and everything, all the messages Nagios sends out may be flagged as spam.<br>
One (kind of lazy and ugly, yet quick and easy) option is to configure Postfix to send emails using a Gmail account as described here: https://www.linode.com/docs/guides/configure-postfix-to-send-mail-using-gmail-and-google-workspace-on-debian-or-ubuntu/<br>
This requires enabling the "Access for less secure apps" on this account, so better create a new account just for this.<br>
- IF YOU WISH TO RECEIVE DISCORD ALERTS:
  - In <code>libexec</code> with the NAGIOS folder:
    - The <code>discord_XXX_alerts.py</code> files are exacty what their names suggest. Update with your Discord webhook if you wish to receive such alerts. Otherwise, don't copy them and delete the user 'discord' and all mention of it in Nagios' <code>/objects/*.cfg</code> files.
- <b>IMPORTANT</b>: by default, Nagios alerts are sent to Discord primarily. If a service/host is still in CRITICAL state after 2 notifications, then an escalation is triggered and alerts are sent by email.<br>
Do NOT overlook the email alerts. :) 
- You <b>must</b> update the provided files to match your local setup:<br>
  --><code>htpasswd.users</code><br>
  --><code>cgi.cfg</code><br>
  -->All the files in <code>/etc/objects/</code> except <code>commands.cfg</code> which should work as is.<br>
  Verify that the config is correct with <code>/usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg</code> then restart Nagios.<br>
- You <b>must</b> obviously ensure that the network configuration is fine (NRPE port open on the remote hosts in particular)<br>

<b>THE DISK RESIZE SCRIPT</b>

- An event_handler in Nagios allows to automatically resize Cloud volumes when they are close to be full. The disk space being the main cost when it comes to cloud, it's best not to buy storage that will remain unused for a long time.
- The python script will use the Cloud service API to add 5G to a volume when it has only 3G left (just in case it fails, to give enough time to resolve manually).
- Then it connects to the server in SSH and passes the command to expand the filesystem.
- This is most definitely a security problem, although the SSH account that is used is a very limited one that can only execute this command (using <code>rbash</code> and <code>sudoers</code>) ; working on a more secure solution.
- run manually with <code>/usr/local/nagios/libexec/resize_volume.py 'DIGITALOCEAN_1' 'Check Disk Space VOLUME' CRITICAL HARD</code>


- Don't hesitate to ping us on Discord: <code>Thomas | High Stakes#0885</code> or <code>Joe | High Stakes#0880</code>
