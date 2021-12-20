#An event handler for Nagios, that automatically increases a Digital Ocean
#volume size when the remaining space is less than 5G through an API call.

import requests
from json import dumps
from subprocess import Popen, check_output
from math import isclose
from argparse import ArgumentParser
from digital_ocean_data import * #API token, droplet IPs and region, volume ids and mount points

class ResizeVolume:
  def __init__(self, args):
    super().__init__()
    host = args[0]
    service = args[1]
    self.service_state = args[2] #OK, WARNING, UNKNOWN, CRITICAL
    self.service_state_type = args[3] #SOFT OR HARD
    #host and service combination allows to identify the concerned volume. Currently there is only one volume per host.
    if host == 'DIGITALOCEAN-1':
      if service == 'Check Disk Space 2':
        self.volume_id = volume_id_1
        self.mount_point = volume_1_mount_point
        self.ip = droplet_ip_1
    elif host == 'DIGITALOCEAN-2':
      if service == 'Check Disk Space 2':   #code could be more condensed but perhaps later on we'll have multiple volumes per host.
        self.volume_id = volume_id_2
        self.mount_point = volume_2_mount_point
        self.ip = droplet_ip_2

    self.headers = {'Authorization': f'Bearer {token}'} #authorization header for the API calls

  def run(self):

    if self.service_state == 'CRITICAL' and self.service_state_type == 'HARD': #Do nothing if different combination.
      volume_details = requests.get(f'https://api.digitalocean.com/v2/volumes/{self.volume_id}', headers=self.headers, timeout=30).json()

      current_size = int(volume_details['volume']['size_gigabytes'])
      filesystem = volume_details['volume']['filesystem_type'] #xfs or ext4, necessary to pass the appropriate resize command

      #let's check that the disk size in the OS matches the volume size, otherwise it may mean that the last run failed to expand the filesystem.
      #no need to keep buying additional space if it's not actually used.
      os_size = 0
      try:
        os_size = int(check_output(["ssh", f"root@{self.ip}", f'df -h | grep {self.mount_point}'], timeout=10).decode('utf-8').split()[1][:-1])
      except:
        #well I don't know. Do nothing anyway.
        pass

      if isclose(os_size, current_size, abs_tol=5): #both sizes are close enough, so we can proceed
        #POST request to resize the volume (add 15G)
        data = {'type':'resize','size_gigabytes': current_size+15, "region": f'{droplet_region}'}
        result = requests.post(f'https://api.digitalocean.com/v2/volumes/{self.volume_id}', headers=self.headers, data=dumps(data), timeout=30).json()

        try:
          if result['action']['status'] == 'done':
            if filesystem == 'ext4':
              command = 'resize2fs'
            else:
              command = 'xfs_grows'
            Popen(["ssh", f"root@{self.ip}", f"{command} {self.mount_point}"])

            exit(0)
        except: #whatever the exception, the command failed, so, do nothing. Someone will need to manually increase the volume size.
          pass #next run will detect that the disk size at the os and droplet levels are different and abort.

    exit(1)

parser = ArgumentParser()
parser.add_argument('host')
parser.add_argument('service')
parser.add_argument('service_state')
parser.add_argument('service_state_type')
args = parser.parse_args()

ResizeVolume(args).run()

