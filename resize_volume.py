#An event handler for Nagios, that automatically increases a Digital Ocean
#volume size when the remaining space is less than 5G through an API call.
from time import sleep

import requests
from json import dumps
from subprocess import Popen, check_output
from math import isclose
from argparse import ArgumentParser
from volume_data import * #API token, droplet IPs and region, volume ids and mount points

class ResizeVolume:
  def __init__(self, args):
    super().__init__()
    self.host = args.host
    service = args.service
    self.service_state = args.service_state #OK, WARNING, UNKNOWN, CRITICAL
    self.service_state_type = args.service_state_type #SOFT OR HARD
    #host and service combination allows to identify the concerned volume. Currently there is only one volume per host.
    if self.host == 'DIGITALOCEAN-1':
      if service == 'Check Disk Space 2':
        self.volume_id = do_volume_id_1
        self.mount_point = do_volume_1_mount_point
        self.ip = do_ip_1
    elif self.host == 'DIGITALOCEAN-2':
      if service == 'Check Disk Space 2':   #code could be more condensed but perhaps later on we'll have multiple volumes per host.
        self.volume_id = do_volume_id_2
        self.mount_point = do_volume_2_mount_point
        self.ip = do_ip_2

    elif self.host == 'HETZNER-1':
      if service == 'Check Disk Space 2':   #code could be more condensed but perhaps later on we'll have multiple volumes per host.
        self.volume_id = hz_volume_id_1
        self.mount_point = hz_volume_1_mount_point
        self.ip = hz_ip_1

    elif self.host == 'HETZNER-2':
      if service == 'Check Disk Space 2':   #code could be more condensed but perhaps later on we'll have multiple volumes per host.
        self.volume_id = hz_volume_id_2
        self.mount_point = hz_volume_2_mount_point
        self.ip = hz_ip_2

    if 'DIGITALOCEAN' in self.host:
      self.headers = {'Authorization': f'Bearer {do_token}'} #authorization header for the API calls
    elif 'HETZNER' in self.host:
      self.headers = {'Authorization': f'Bearer {hz_token}'}

  def run(self):

    if self.service_state == 'CRITICAL' and self.service_state_type == 'HARD': #Do nothing if different combination.

      if 'DIGITALOCEAN' in self.host:
        self.digital_ocean()
      elif 'HETZNER' in self.host:
        self.hetzner()

  def digital_ocean(self):

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
        data = {'type':'resize','size_gigabytes': current_size+15, "region": f'{do_region}'}
        result = requests.post(f'https://api.digitalocean.com/v2/volumes/{self.volume_id}', headers=self.headers, data=dumps(data), timeout=30).json()

        if result['action']['status'] == 'done':
          if filesystem == 'ext4':
            command = 'resize2fs'
          else:
            command = 'xfs_grows'
          Popen(["ssh", f"root@{self.ip}", f"{command} {self.mount_point}"])

          exit(0)
        #no need for a try/except: script will fail whatever the exception. Someone will need to manually increase the volume size.
        #next run will detect that the disk size at the os and droplet levels are different and abort.
      exit(1)

  def hetzner(self):

    volume_details = requests.get(f'https://api.hetnzer.cloud/v1/volumes/{self.volume_id}', headers=self.headers,
                                  timeout=30).json()

    current_size = int(volume_details['volume']['size'])
    filesystem = volume_details['volume']['format']

    os_size = 0
    try:
      os_size = int(check_output(["ssh", f"root@{self.ip}", f'df -h | grep {self.mount_point}'], timeout=10).decode(
        'utf-8').split()[1][:-1])
    except:
      pass

    if isclose(os_size, current_size, abs_tol=5):
      data = {'size': current_size + 15}
      requests.post(f'https://api.digitalocean.com/v2/volumes/{self.volume_id}/actions/resize', headers=self.headers,
                             data=dumps(data), timeout=30).json()

      #the result isn't sent back immediately. Just check the new size of the volume to make sure it worked.
      sleep(3) #wait a bit to ensure the command is actually passed (although from the timestamps, it's done instantly).
      new_size = int(requests.get(f'https://api.hetnzer.cloud/v1/volumes/{self.volume_id}', headers=self.headers,
                                  timeout=30).json()['volume']['size'])
      if new_size > current_size:
        if filesystem == 'ext4':
          command = 'resize2fs'
        else:
          command = 'xfs_grows'
        Popen(["ssh", f"root@{self.ip}", f"{command} {self.mount_point}"])

        exit(0)
    exit(1)

parser = ArgumentParser()
parser.add_argument('host')
parser.add_argument('service')
parser.add_argument('service_state')
parser.add_argument('service_state_type')
args = parser.parse_args()

ResizeVolume(args).run()

