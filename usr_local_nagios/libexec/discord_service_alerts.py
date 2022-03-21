#!/usr/bin/python3

import sys
from discord_webhook import DiscordWebhook, DiscordEmbed

HOOK = "THE DISCORD WEBHOOK LINK HERE: https://......"

def codecolor(alerttype):
    clr_red = 13632027
    clr_yel = 16098851
    clr_grn = 8311585

    if alerttype == 'CRITICAL':
        return clr_red
    elif alerttype == 'OK':
        return clr_grn
    else:
        return clr_yel


def main(nagios_input):
    nagios_input.pop(0)
    line1 = f"{nagios_input[0]} -- {nagios_input[1]}"
    line2 = f"{nagios_input[2]}\n{nagios_input[4]}"


    webhook = DiscordWebhook(url=HOOK)
    # create embed object for webhook
    embed = DiscordEmbed(title=line1, description=line2, color=codecolor(nagios_input[3]))

    # add embed object to webhook
    webhook.add_embed(embed)

    webhook.execute()

main(sys.argv)

