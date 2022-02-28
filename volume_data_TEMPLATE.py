###A simple template that one should update with the appropriate values and cloud services.
#DO. NOT. MAKE. PUBLIC. (your API tokens are in there!)

###DIGITAL OCEAN###

DIGITALOCEAN_1_IP = '0.0.0.0'
DIGITALOCEAN_12_IP = '0.0.0.1'
DIGITALOCEAN_REGION = 'fra1' #droplets and volumes are in Frankfurt
#We start at 2 because the nagios 'Check Disk Space 1' command is for the root partition, which we can't resize
DIGITALOCEAN_1_VOLID_2 = 'the volume id' #to be retrieved through an API call.
DIGITALOCEAN_1_MOUNTPOINT_2 = '/dev/sda' #whatever is right for you
DIGITALOCEAN_2_VOLID_2 = 'another volume id'  # "volume-fra1-05"
DIGITALOCEAN_2_MOUNTPOINT_2 = '/dev/sdb'
do_token='00000000' #your token. Don't disclose it.



###HETZNER###
HETZNER_1_IP = ''
HETZNER_2_IP = ''
HETZNER_1_VOLID_2 = ''   #start numbering at 2
HETZNER_1_MOUNTPOINT_2 = ''
HETZNER_2_VOLID_2 = ''
HETZNER_2_MOUNTPOINT_2 = ''

