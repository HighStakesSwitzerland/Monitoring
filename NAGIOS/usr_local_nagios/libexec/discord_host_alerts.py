#!/usr/bin/python3

import sys
from discord_webhook import DiscordWebhook, DiscordEmbed

HOOK = "THE DISCORD WEBHOOK LINK HERE: https://......"

def codecolor(alerttype):
    clr_red = 13632027
    clr_yel = 16098851
    clr_grn = 8311585

    if alerttype == 'DOWN':
        return clr_red
    elif alerttype == 'UP':
        return clr_grn
    else:
        return clr_yel


def main(nagios_input):
    nagios_input.pop(0)

    webhook = DiscordWebhook(url=HOOK)
    # create embed object for webhook
    embed = DiscordEmbed(title=nagios_input[0], description=nagios_input[1], color=codecolor(nagios_input[2]))

    # add embed object to webhook
    webhook.add_embed(embed)

    webhook.execute()

main(sys.argv)
