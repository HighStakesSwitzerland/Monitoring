#!/usr/bin/python3

#An event handler for Nagios, that automatically increases a Digital Ocean or Hetzner
#volume size when the remaining space is less than 5G through an API call.


###IMPORTANT###
#"resize_volume.py" and "volume_data.py" must be placed in /usr/local/nagios/libexec/
###############

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
    print(args) #will appear in nagios' log
    self.host = args.host
    service = args.service
    self.service_state = args.service_state #OK, WARNING, UNKNOWN, CRITICAL
    self.service_state_type = args.service_state_type #SOFT OR HARD
    #host and service combination allows to identify the concerned volume.
    #host can be 'DIGITALOCEAN_1', service for example 'Check Disk Space 2'. Take the digit from the service to identify the disk.

    self.ip = eval(f"{self.host}_IP")   #this is ugly.
    self.volume_id = eval(f"{self.host}_VOLID_{service.split()[-1]}")
    self.mount_point = eval(f"{self.host}_MOUNTPOINT_{service.split()[-1]}")


    if 'DIGITALOCEAN' in self.host:
      self.headers = {'Authorization': f'Bearer {do_token}'} #authorization header for the API calls
    elif 'HETZNER' in self.host:
      self.headers = {'Authorization': f'Bearer {hz_token}'}

  def run(self):

    if self.service_state == 'CRITICAL' and self.service_state_type == 'HARD': #Do nothing if different combination.

      print("VALUES: ", self.volume_id, self.mount_point, self.ip )

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
        os_size = round(float(check_output(["ssh", f"{ssh_account}@{self.ip}", f'df | grep {self.mount_point}'], timeout=10).decode(
          'utf-8').split()[1])/1048576) #convert the kb to gb (1024*1024)
      except Exception as e:
        #well I don't know. Do nothing anyway.
        print(e)
        pass

      print("CURRENT SIZE & OS SIZE: ", current_size, os_size)

      if isclose(os_size, current_size, abs_tol=5): #both sizes are close enough, so we can proceed
        #POST request to resize the volume (add 15G)
        data = {'type':'resize','size_gigabytes': current_size + 15, "region": f'{DIGITALOCEAN_REGION}'}
        result = requests.post(f'https://api.digitalocean.com/v2/volumes/{self.volume_id}/actions', headers=self.headers, data=dumps(data), timeout=30).json()

        if result['action']['status'] == 'done':
          self.expand_filesystem(filesystem)
          exit(0)
        #no need for a try/except: script will fail whatever the exception. Someone will need to manually increase the volume size.
        #next run will detect that the disk size at the os and droplet levels are different and abort.
      else: #the only option here is that the disk is larger than the OS thinks - maybe was increased and the filesystem not expanded.
        self.expand_filesystem(filesystem) #let's just try to use the entire available space.
        exit(0)

      exit(1)

  def hetzner(self):

    volume_details = requests.get(f'https://api.hetzner.cloud/v1/volumes/{self.volume_id}', headers=self.headers,
                                  timeout=30).json()

    current_size = int(volume_details['volume']['size'])
    filesystem = volume_details['volume']['format']

    os_size = 0
    try:
      os_size = round(float(check_output(["ssh", f"{ssh_account}@{self.ip}", f'df | grep {self.mount_point}'], timeout=10).decode(
        'utf-8').split()[1])/1048576) #convert the kb to gb (1024*1024)
    except Exception as e:
      print(e)
      pass

    print("CURRENT SIZE & OS SIZE: ", current_size, os_size)

    if isclose(os_size, current_size, abs_tol=5):
      data = {'size': current_size + 15}
      requests.post(f'https://api.hetzner.cloud/v1/volumes/{self.volume_id}/actions/resize', headers=self.headers,
                             data=dumps(data), timeout=30).json()

      #the result isn't sent back immediately. Just check the new size of the volume to make sure it worked.
      sleep(3) #wait a bit to ensure the command is actually passed (although from the timestamps, it's done instantly).
      #new_size = int(requests.get(f'https://api.hetzner.cloud/v1/volumes/{self.volume_id}', headers=self.headers,
       #                           timeout=30).json()['volume']['size'])
      #if new_size > current_size:
      self.expand_filesystem(filesystem)
      exit(0)
    else:
      self.expand_filesystem(filesystem)
      exit(0)

    exit(1)

  def expand_filesystem(self, filesystem):
    if filesystem == 'ext4':
      command = 'resize2fs'
    else:
      command = 'xfs_growfs'
    Popen(["ssh", f"{ssh_account}@{self.ip}", f"{command} {self.mount_point}"])
    return

parser = ArgumentParser()
parser.add_argument('host')
parser.add_argument('service')
parser.add_argument('service_state')
parser.add_argument('service_state_type')
args = parser.parse_args()

ResizeVolume(args).run()

