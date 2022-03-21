To be placed in the directory of the Nagios Core install, typically <code>/usr/local/nagios/</code>.

You <b>MUST</b> update the different files to match your configuration first.

If you are going to use Discord to receive the alerts: update the <code>discord_host_alerts.py</code> and <code>discord_service_alerts.py</code> in <code>libexec</code> with your channel's webhook.
If you will not use it, remove all mentions of Discord in <code>contacts.cfg</code>.<br>

The Discord scripts were shamefully copied and modified from https://github.com/Operator873/Nagios-Discord :)

<br>(Same applies for email alerts, see the Postfix config.)

Note: it is best to set up Nagios for using https. This requires valid certificates (or self signed, doesn't matter except for the browser warnings), and it isn't complicated - plenty of tutorials to achieve this.

