<code>sasl_passwd</code> should be placed in /etc/postfix and updated with the gmail credentials.<br>
It's plain text so mind the permissions.<br>

Then run <code>postmap /etc/postfix/sasl_passwd</code>

<code>main.cf</code> should work out of the box, just update the line <code>myhostname = monitoring</code> to whatever your hostname actually is (find it in <code>/etc/hostname</code>)

Pay attention to the line <code>mailbox_command = procmail -a "$EXTENSION"</code>, which requires <code>procmail</code> to be installed.<br>
You can otherwise change this to <code>sendmail</code> or whatever you prefer.