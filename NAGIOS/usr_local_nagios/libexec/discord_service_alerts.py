#!/usr/bin/python3

import sys
#from discord_webhook import DiscordWebhook, DiscordEmbed
from discord import SyncWebhook #, Embed

HOOK = "https://discord.com/api/webhooks/953992689152577536/qX5TkFZe2HCwPswnBJVjcVTQ5To6ny-mh5MpIicC5C0RhttyBolh8II_lLojiyV4B-sw"

# def codecolor(alerttype):
#     clr_red = 13632027
#     clr_yel = 16098851
#     clr_grn = 8311585
#
#     if alerttype == 'CRITICAL':
#         return clr_red
#     elif alerttype == 'OK':
#         return clr_grn
#     else:
#         return clr_yel


def main(nagios_input):
    nagios_input.pop(0)

    line1 = f"**{nagios_input[0]} -- {nagios_input[1]}**"
    line2 = f"{nagios_input[2]}\n{nagios_input[4]}"

    if nagios_input[3] == 'CRITICAL':
        status = '🚨'
    elif nagios_input[3] == 'OK':
        status = '✅'
    else:
        status = '⚠️'

    webhook = SyncWebhook.from_url(HOOK)

    webhook.send(f"{status}\n{line1}\n{line2}\n\n<@CONTACT_ID1>, <@CONTACT_ID2>")



    # create embed object for webhook
    #embed = Embed(title=line1, description=line2, color=codecolor(nagios_input[3]))
    # webhook.send( embed=embed)  # mind the <> -- the id is in format @45613241654987
    #
    # # add embed object to webhook
    # webhook.add_embed(embed)
    #
    # webhook.execute()

main(sys.argv)

