from time import sleep
from requests import get
from subprocess import call

previous_height = 0

RPC_port = 26657
upgrade_height = 1292226

node = 'aura'
binary = 'aurad'
build_path = f'/home/aura/{node}/build/{binary}'
prod_path = f'/home/{node}/go/bin/'
extra_command = "" #"['rm', '-r', '/home/aura/.aura/wasm/wasm/cache/']

while True:
    try:
        current_height = int(get(f'http://localhost:{RPC_port}/status').json()['result']['sync_info']['latest_block_height'])
        print(current_height)
        if current_height == upgrade_height:
            print("Upgrading")
            break  # break the loop and move forward
        else:
            previous_height = current_height
            sleep(3)
    except Exception as e:
        if previous_height == upgrade_height -1:  # sometimes a node just crashes upon reaching the upgrade height, so if the previous block was
            # right before the upgrade height, let's assume it was reached...
            break
        else:
            print(e)
            exit(1)

# stop the node
call(['systemctl', 'stop', f'{node}.service'])
sleep(2)
call(['cp', '-p', build_path, prod_path])

if extra_command:
    call(extra_command)

sleep(1)

call(['systemctl', 'start', f'{node}.service'])

exit(0)

