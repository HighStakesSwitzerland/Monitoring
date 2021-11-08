# Nagios-Config-Scripts
Nagios server configuration files along with the remote server setup and scripts (API, NRPE)
The remote hosts are monitored by querying a custom API (Python3/FastAPI) and getting some key parameters about the validator.

Clone the repo, update <code>automated_install.sh</code> (disk info) and <code>systemd_service</code> (path and validator details), then run <code>automated_install.sh</code>.

<b>INSTRUCTIONS</b>

- A couple Python modules are needed : <code>uvicorn</code> and <code>fastapi</code>. <br>
Install with <code>python3 -m pip install uvicorn fastapi</code>.
- You need to install Nagios on a Linux host, along with the webserver (Apache by default, probably possible to use another if you're feeling adventurous).<br>
This tutorial is pretty straightforward: https://support.nagios.com/kb/article/nagios-core-installing-nagios-core-from-source-96.html
<br><br>
- You also need to configure Postfix or sendmail on the Nagios server so that you get the email alerts (note that you can also configure Nagios to send Discord/Telegram/SMS alerts).<br>
If you don't have a properly configured mail server with a certificate and everything, all the messages Nagios sends out may be flagged as spam.<br>
One (lazy and ugly) option is to configure Postfix to send emails using a Gmail account as described here: https://www.linode.com/docs/guides/configure-postfix-to-send-mail-using-gmail-and-google-workspace-on-debian-or-ubuntu/<br>
This requires enabling the "Access for less secure apps" on this account, so better create a new account just for this.
<br><br>
- Once Nagios is installed, you can copy the Nagios_config/etc folder, keeping the structure, to <code>/usr/local/nagios/</code>.<br>
  - You <b>must</b> update different files however:<br>
  <code>htpasswd.users</code><br>
  <code>cgi.cfg</code><br>
  All the files in <code>/etc/objects/</code> except <code>commands.cfg</code> which should work as is.<br>
  Verify that the config is correct with <code>/usr/local/nagios/bin/nagios -v /usr/local/nagios/etc/nagios.cfg</code> then restart Nagios.<br>
  You <b>must</b> obviously ensure that the network configuration is fine (NRPE port open on the remote hosts in particular)<br>
- The remote hosts can be easily configured by cloning the repo and running the <code>automated_install.sh</code> script, <b>after having updated the relevant parameters</b>.
- Quick note though: this deployment requires updating the firewall. We're using cloud services so the firewalls are updated manually from the provider's GUI, but otherwise you should update iptables/ufw.
 
- Don't hesitate to ping us on Discord: <code>Thomas | Terran Stakers#0885</code> or <code>Joe | Terran Stakers#0880
</code>