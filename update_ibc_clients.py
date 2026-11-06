#!/usr/bin/python3

from subprocess import run
from discord_webhook import DiscordWebhook, DiscordEmbed

class updateClients:

    def __init__(self):
        super().__init__()
        self.clients = [
            ["fetchhub-4", "07-tendermint-81"],
            ["fetchhub-4","07-tendermint-90"],
            ["injective-1","07-tendermint-266"]
            ]

    def run(self):

        for client in self.clients:
            result = run(['sudo', '-u', 'hermes', '/home/hermes/bin/hermes', 'update', 'client', '--host-chain', client[0], '--client', client[1]], capture_output=True, text=True, timeout=30)
            #print(result)
            if not 'SUCCESS' in result.stdout:
                result = run(['sudo', '-u', 'hermes', '/home/hermes/bin/hermes', '--config', '/home/hermes/.hermes/public_rpcs_config.toml', 'update', 'client', '--host-chain', client[0], '--client', client[1]], capture_output=True, text=True, timeout=30)
                if not 'SUCCESS' in result.stdout:
                    self.discord_message(result.stdout)


    def discord_message(self, message):
        webhook = DiscordWebhook(url="https://discord.com/api/webhooks/xxx")
        embed = DiscordEmbed(title=f"IBC Client Update Failure", description=message, color=16776960)
        webhook.add_embed(embed)
        webhook.execute()

updateClients().run()