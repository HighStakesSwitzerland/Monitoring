import logging
from math import isclose
from threading import Thread
from time import sleep
from requests import get
from datetime import datetime

import uvicorn
from fastapi import FastAPI

from argparse import ArgumentParser

logging.basicConfig(filename='/var/log/monitoring.log', filemode='w+',
                    format='%(asctime)s %(levelname)s %(message)s', datefmt='%d/%m/%Y %H:%M:%S :', level=logging.WARNING)


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

        ##TERRA SPECIFIC : ORACLE API##
        self.terravaloper = ''
        if self.VALIDATOR == 'terra':
            self.oracle_url = f"http://localhost:1317/oracle/voters/{self.terravaloper}/miss"
            self.oracle_status = ""
            try:
                self.missed_votes = int(get(self.oracle_url).json()['result'])
            except:
                self.missed_votes = 0
            self.timeout = 0

        ##INJECTIVE SPECIFIC : INJECTIVE-PEGGO ORCHESTRATOR
        self.injective_address = ''
        if self.VALIDATOR == 'injective':
            self.timeout = 0
            self.peggo_status = ''
            self.peggo_lastbatch_url = f"https://lcd.injective.network/peggy/v1/batch/last?address={self.injective_address}"
            self.peggo_valsets_url = f"https://lcd.injective.network/peggy/v1/valset/last?address={self.injective_address}"
            self.peggo_last_observed_nonce_url = 'https://lcd.injective.network/peggy/v1/module_state'
            self.peggo_last_claimed_event_url = f'https://lcd.injective.network/peggy/v1/oracle/event/{self.injective_address}'
            self.injective_peggo()

        ##UMEE SPECIFIC : PEGGO ORCHESTRATOR
        self.umee_address = ''
        if self.VALIDATOR == 'umee':
            self.timeout = 0
            self.peggo_status = 0
            self.missed_url = f"http://localhost:1317/umee/oracle/v1/validators/{self.umee_address}/miss"
            self.window_url = f"http://localhost:1317/umee/oracle/v1/slash_window"
            missed = int(get(self.missed_url).json()['miss_counter'])
            window = int(get(self.window_url).json()['window_progress'])
            self.peggo_ratio = missed/window


        ##BAND SPECIFIC : YODA
        self.band_address = ''
        if self.VALIDATOR == 'bandprotocol':
            self.yoda_status = ''
            self.yoda_status_url = f"http://localhost:1318/oracle/v1/validators/{self.band_address}"

        ###define the urls to get the json data
        self.status_url = f"http://localhost:{self.PORT}/status"
        self.signatures_url = f"http://localhost:{self.PORT}/block?{self.block_height}"
        ###
        ###TERRA ENDPOINTS###
        ###setup FastAPI
        if app is None:
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

        @self.app.get(f"/{self.VALIDATOR}/oracle_status")
        def oracle_status():
            return self.oracle_status

        @self.app.get(f"/{self.VALIDATOR}/peggo")
        def peggo():
            return self.peggo_status

        @self.app.get(f"/{self.VALIDATOR}/yoda")
        def yoda():
            return self.yoda_status

    def run(self):

        while True:
            #Get the validator address
            try: #if the node is down, or self.PORT is wrong, will trigger an exception.
                self.status_data = get(self.status_url).json()
                self.validator_address = self.status_data['result']['validator_info']['address']
                self.validator_is_up = True
            except:
                self.validator_is_up = False
                logging.critical(f"{self.VALIDATOR} is down")

            #need to refresh self.status_data below, as the above block won't be executed anymore...
            #add a sleep here to prevent making the request again instantly.
            sleep(1)
            while self.validator_is_up:
                try:
                    self.status_data = get(self.status_url).json()
                except:
                    self.validator_is_up = False
                    logging.critical(f"{self.VALIDATOR} is down")
                    sleep(7)

                if self.validator_is_up:
                    try:
                        self.block_height = self.status_data['result']['sync_info']['latest_block_height']
                        signatures_data = self.get_signatures_data() #get the signatures data matching the block height
                        if signatures_data:
                            official_block_timestamp = datetime.strptime(signatures_data['result']['block']['header']['time'][:-4:] + 'Z', '%Y-%m-%dT%H:%M:%S.%fZ')
                            # timestamps have nanoseconds, so need to strip the last 3 digits (drop the last 4 characters then restore the 'Z', actually)

                            self.check_blocks_incrementing() #verify that block number is increasing.

                            status_block_timestamp = self.check_missed_block(signatures_data)
                            if self.missed_block_height == 0:  # no block was missed, we can check the time delta.
                                self.bonding_status = True  # validator is bonded otherwise the above would be none
                                self.check_time_delta(status_block_timestamp, official_block_timestamp)
                            else:  # if a block was missed, must verify bonding status.
                                self.get_bonding_info()
                    except Exception as e:
                        logging.critical(f"{self.VALIDATOR}: {str(e)}")

                    #monitor the Terra oracle
                    # Need to check that roughly every 1:30 rather than every 7s, otherwise it may be missed by Nagios.
                    if self.VALIDATOR == 'terra':
                        if self.timeout == 15:
                            self.check_oracle_votes()
                            self.timeout = 0
                        else:
                            self.timeout += 1

                    #verify the injective Peggo orchestrator status
                    #probably not much point checking at each loop.
                    if self.VALIDATOR == 'injective':
                        if self.timeout == 10:
                            self.injective_peggo()
                            self.timeout = 0
                        else:
                            self.timeout += 1

                    #verify the umee Peggo orchestrator status
                    if self.VALIDATOR == 'umee':
                        if self.timeout == 10:
                            self.umee_peggo()
                            self.timeout = 0
                        else:
                            self.timeout += 1

                    # verify Band'd yoda
                    if self.VALIDATOR == 'bandprotocol':
                        #if self.timeout == 10:
                        self.band_yoda()

                    sleep(7)

            sleep(6) #if the validator is down, 7s overall between checks.

    def get_signatures_data(self):
        """return the details of the block signature by all the bonded validators"""
        try:
            return get(self.signatures_url).json()
        except:
            self.validator_is_up = False
            logging.critical(f"{self.VALIDATOR}: no signatures data. Validator is down.")
            return None

    def get_bonding_info(self):
        """look for the validator address in the list of bonded validators. If not present, problem."""
        page_number = 1
        while True:
            try:
                bonding_data = get(
                f"http://localhost:{self.PORT}/validators?status=BOND_STATUS_BONDED&per_page=100&page={page_number}").json()

                if [i for i in bonding_data['result']['validators'] if i['address'] == self.validator_address]:
                    self.bonding_status = True
                    return
                else:
                    page_number += 1
            except KeyError: #no more data to retrieve, hence the json result has no such keys. Validator no longer bonded
                #if 'error' in bonding_data.keys():
                logging.critical(f"{self.VALIDATOR}: unbonded")
                self.bonding_status = False
                return
            except Exception as e:
                logging.critical(f"{self.VALIDATOR}: get_bonding_info: unexpected error: {str(e)}")
                self.bonding_status = False
                return

    def check_missed_block(self, signatures_data):
        """check if the signature details of our node are present in the data"""
        #If the node missed the block, it will trigger an exception, which is used to update the variable.

        try:
            signature = [j for j in signatures_data['result']['block']['last_commit']['signatures'] \
                    if j['validator_address'] == self.validator_address][0]  # a dict within a list, hence the [0] to get the dict only
            if not self.missed_block_height == -1:
                self.missed_block_height = 0
            return datetime.strptime(signature['timestamp'][:-4:] + 'Z', '%Y-%m-%dT%H:%M:%S.%fZ')
        except IndexError:
            # if no signature data while the node is bonded, it means that a block was missed.
            if not self.missed_block_height == -1:
                self.missed_block_height = int(self.block_height)
                logging.critical(f"{self.VALIDATOR}: Missed block {int(self.block_height)}")
            return None
        except Exception as e:
            logging.critical(f"{self.VALIDATOR}: check_missed_block: unexpected error: {str(e)}")
            self.missed_block_height = int(self.block_height)
            return

    def check_blocks_incrementing(self):
        """Need to verify that the block height is incrementing. Sometimes the node is actually down but all\
        other metrics are fine, just this height is stuck"""
        if (self.previous_block_height == 0) or (self.block_height > self.previous_block_height):  # first start or normal behavior
            self.previous_block_height = self.block_height
            self.blocks_not_incrementing_counter = 0
            self.missed_block_height = 0
            #logging.warning(f"Blocks are incrementing: {self.block_height}. Counter: {self.blocks_not_incrementing_counter}")
        elif (self.block_height == self.previous_block_height) and not self.blocks_not_incrementing_counter > 3:  # this isn't normal, but let's wait a few loops
            self.blocks_not_incrementing_counter += 1
            logging.warning(f"{self.VALIDATOR}: Blocks aren't incrementing: {self.block_height}. Counter: {self.blocks_not_incrementing_counter}")
        elif (self.block_height == self.previous_block_height) and self.blocks_not_incrementing_counter > 3:  # still not incrementing: issue!
            self.missed_block_height = -1  # this will set the metric to Critical in Nagios.
            logging.critical(f"{self.VALIDATOR}: Height is stuck: {self.block_height}. Counter: {self.blocks_not_incrementing_counter}")


    def check_time_delta(self, status_block_timestamp, official_block_timestamp):
        """check the delta between block timestamp and signature timestamp. If above 2, warning"""
        #print(status_block_timestamp, official_block_timestamp)
        try:
            self.block_delay = round((official_block_timestamp - status_block_timestamp).total_seconds(), 1)
        except Exception as e:
            logging.critical(f"{self.VALIDATOR}: check_time_delta : unexpected error: {str(e)}")


    def check_oracle_votes(self):
        try:
            new_missed_votes = int(get(self.oracle_url).json()['result'])
        except:
            new_missed_votes = 0
        try:
            oracle_height = int(get(self.oracle_url).json()['height'])
        except:
            oracle_height = 0

        missed = new_missed_votes - self.missed_votes
        if missed > 0:
            logging.warning(f"{self.VALIDATOR}: {missed} MISSED ORACLE VOTE(S)")
            self.oracle_status = f"{missed} MISSED ORACLE VOTE(S)"
        elif not isclose(oracle_height, int(self.block_height), abs_tol=1):
            logging.critical(f"{self.VALIDATOR}: ORACLE IS STUCK: {oracle_height}")
            self.oracle_status = f"ORACLE IS STUCK: {oracle_height}"
        else:
            self.oracle_status =  f"Total missed votes: {self.missed_votes} "

        self.missed_votes = new_missed_votes

    def injective_peggo(self):
        try:
            batch = get(self.peggo_lastbatch_url).json()['batch']
            if batch: #should be None is working fine
                self.peggo_status = f"Batch pending: {batch}"
                return
            valsets = get(self.peggo_valsets_url).json()['valsets']
            if valsets:
                self.peggo_status = f"Valsets pending: {valsets}"
                return

            lon = int(get(self.peggo_last_observed_nonce_url).json()['state']['last_observed_nonce'])
            lce = int(get(self.peggo_last_claimed_event_url).json()['last_claim_event']['ethereum_event_nonce'])
            if lon < lce == 1:
                self.peggo_status = f"Peggo is 1 nonce late: LON={lon}, LCE={lce}"
                return
            elif lon < lce > 1:
                self.peggo_status = f"Peggo is f'{lon-lce}' nonces late"
                return

            self.peggo_status = "OK"

        except:
            self.peggo_status = 'No data'

        return

    def umee_peggo(self):
        try:
            missed = int(get(self.missed_url).json()['miss_counter'])
            window = int(get(self.window_url).json()['window_progress'])
            # misses = self.missed/self.window
            new_ratio = missed / window
            self.peggo_status = 0 if new_ratio == 0 else (new_ratio - self.peggo_ratio) / new_ratio * 100  # round(self.peggo_ratio - new_ratio, 6) #f'{self.peggo_ratio - new_ratio:.5f}'
            self.peggo_ratio = new_ratio
            # self.peggo_status = -1 if misses > 0.20 else (misses if misses > 0.05 else "OK")
            return
            # THE BELOW IS NOT IMPLEMENTED CURRENTLY.
            # lon = int(get(self.peggo_last_observed_nonce_url).json()['state']['last_observed_nonce'])
            # lce = int(get(self.peggo_last_claimed_event_url).json()['last_claim_event']['ethereum_event_nonce'])
            # if not lon - lce == 0:
            #     self.peggo_status = f"Peggo is late: LON={lon}, LCE={lce}"
            #     return


        except:
            self.peggo_status = -2  # 'No data'
            return

    def band_yoda(self):
        
        try:
            if get(self.yoda_status_url).json()['status']['is_active']: #if true
                self.yoda_status = 'Active'
            else:
                self.yoda_status = 'Inactive'
        except:
            self.yoda_status = 'No data'

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