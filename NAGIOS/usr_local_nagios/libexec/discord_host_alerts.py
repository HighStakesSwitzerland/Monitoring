#!/usr/bin/python3

import sys
#from discord_webhook import DiscordWebhook, DiscordEmbed
from discord import SyncWebhook, Embed

HOOK = "THE DISCORD WEBHOOK LINK HERE: https://......"

# def codecolor(alerttype):
#     clr_red = 13632027
#     clr_yel = 16098851
#     clr_grn = 8311585
#
#     if alerttype == 'DOWN':
#         return clr_red
#     elif alerttype == 'UP':
#         return clr_grn
#     else:
#         return clr_yel


def main(nagios_input):
    nagios_input.pop(0)

    if nagios_input[2] == 'DOWN':
        status = '🚨'
    elif nagios_input[2] == 'UP':
        status = '✅'
    else:
        status = '⚠️'

        # $HOSTNAME$ $HOSTADDRESS$ "$SERVICEDESC$" $SERVICESTATE$ $SERVICEOUTPUT$

    webhook = SyncWebhook.from_url(HOOK)

    webhook.send(f"{status}\n**{nagios_input[0]}**\n{nagios_input[1]}\n\n<@CONTACT_ID1")


main(sys.argv)
