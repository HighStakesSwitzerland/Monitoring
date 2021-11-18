from threading import Thread
from time import sleep
import requests
from datetime import datetime

import uvicorn
from fastapi import FastAPI

from argparse import ArgumentParser

class GetData(Thread):
    def __init__(self, data, app=None):
        super().__init__()

        # Define the validator name and port
        self.VALIDATOR = data[0]
        self.PORT = data[1]

        self.validator_address = ''
        self.status_data = []

        ###Define variables###
        self.validator_is_up = False
        self.block_height = 0
        self.previous_block_height = 0
        self.blocks_not_incrementing_counter = 0
        self.bonding_status = False
        self.missed_block_height = 0
        self.block_delay = 0

        ###define the urls to get the json data
        self.status_url = f"http://localhost:{self.PORT}/status"
        self.signatures_url = f"http://localhost:{self.PORT}/block?{self.block_height}"
        ###
        ###TERRA ENDPOINTS###
        ###setup FastAPI
        if app == None:
            self.app = FastAPI()
            self.app.type = "00"
        else:
            self.app = app

        @self.app.get(f"/{self.VALIDATOR}/validator_status")
        def validator_status():
            return self.validator_is_up

        @self.app.get(f"/{self.VALIDATOR}/block_delay")
        def block_delay():
            return self.block_delay

        @self.app.get(f"/{self.VALIDATOR}/bonding_status")
        def bonding_status():
            return self.bonding_status

        @self.app.get(f"/{self.VALIDATOR}/missed_block_height")
        def missed_block_height():
            return self.missed_block_height

    def run(self):

        while True:
            #Get the validator address
            try: #if the node is down, or self.PORT is wrong, will trigger an exception.
                self.status_data = requests.get(self.status_url).json()
                self.validator_address = self.status_data['result']['validator_info']['address']
                self.validator_is_up = True
            except:
                self.validator_is_up = False
            #need to refresh self.status_data below, as the above block won't be executed anymore...
            #add a sleep here to prevent making the request again instantly.
            sleep(1)
            while self.validator_is_up:
                self.status_data = requests.get(self.status_url).json()
                self.block_height = self.status_data['result']['sync_info']['latest_block_height']
                signatures_data = self.get_signatures_data() #get the signatures data matching the block height
                if signatures_data:
                    official_block_timestamp = datetime.strptime(signatures_data['result']['block']['header']['time'][:-4:] + 'Z', '%Y-%m-%dT%H:%M:%S.%fZ')

                    # Need to verify that the block height is incrementing. Sometimes the node is actually down but all
                    # other metrics are fine, just this height is stuck
                    if (self.previous_block_height == 0) or (self.block_height > self.previous_block_height):  # first start or normal behavior
                        self.previous_block_height = self.block_height
                        self.blocks_not_incrementing_counter = 0
                        self.missed_block_height = 0
                    elif (self.block_height == self.previous_block_height) and not self.blocks_not_incrementing_counter > 2:  # this isn't normal, but let's wait a couple loops
                        self.blocks_not_incrementing_counter += 1
                    elif (self.block_height == self.previous_block_height) and self.blocks_not_incrementing_counter > 2:  # still not incrementing: issue!
                        self.missed_block_height = -1  # this will set the metric to Critical in Nagios.

                    status_block_timestamp = self.check_missed_block(signatures_data)
                    if self.missed_block_height == 0:  # no block was missed, we can check the time delta.
                        self.bonding_status = True  # validator is bonded otherwise the above would be none
                        self.check_time_delta(status_block_timestamp, official_block_timestamp)
                    else:  # if a block was missed, must verify bonding status.
                        self.get_bonding_info()

                sleep(5)

    def get_signatures_data(self):
        """return the details of the block signature by all the bonded validators"""
        try:
            return requests.get(self.signatures_url).json()
        except:
            self.validator_is_up = False
            return None

    def get_bonding_info(self):
        """look for the validator address in the list of bonded validators. If not present, problem."""
        page_number = 1
        while True:
            bonding_data = requests.get(
                f"http://localhost:{self.PORT}/validators?status=BOND_STATUS_BONDED&per_page=100&page={page_number}").json()
            try:
                if [i for i in bonding_data['result']['validators'] if i['address'] == self.validator_address]:
                    self.bonding_status = True
                    return
                else:
                    page_number += 1
            except:
                if 'error' in bonding_data.keys():  # no more data. Validator no longer bonded
                    self.bonding_status = False
                    return

    def check_missed_block(self, signatures_data):
        """check if the signature details of our node are present in the data"""
        #If the node missed the block, it will trigger an exception, which is used to update the variable.

        try:
            if [j for j in signatures_data['result']['block']['last_commit']['signatures'] \
                    if j['validator_address'] == self.validator_address][0]:  # a dict within a list, hence the [0] to get the dict only
                if not self.missed_block_height == -1:
                    self.missed_block_height = 0
                return datetime.strptime(signatures_data['timestamp'][:-4:] + 'Z', '%Y-%m-%dT%H:%M:%S.%fZ')
        except IndexError:
            # if no signature data while the node is bonded, it means that a block was missed.
            if not self.missed_block_height == -1:
                self.missed_block_height = int(self.block_height)
            return None

    def check_time_delta(self, status_block_timestamp, official_block_timestamp):
        """check the delta between block timestamp and signature timestamp. If above 8, warning"""
        # timestamps have nanoseconds, so need to strip the last 3 digits (drop the last 4 characters then restore the 'Z', actually)
        #print(status_block_timestamp, official_block_timestamp)
        self.block_delay = round((official_block_timestamp - status_block_timestamp).total_seconds(), 1)


#if __name__ == "__main__":
parser = ArgumentParser()
parser.add_argument('-i', nargs='+', action='append', help='Usage: python3 getData.py -i VALIDATOR1 PORT1 -i VALIDATOR2 PORT2 etc.')
args = parser.parse_args()
#args will be a list of lists

app = None

for i in args.i:
    getData = GetData(i, app)
    getData.daemon = True
    if app is None:
        app = getData.app
    getData.start()


uvicorn.run(app, host='0.0.0.0', port=5005)