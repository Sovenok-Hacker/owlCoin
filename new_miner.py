import requests, hashlib, time, math, argparse
from colorama import init
from colorama import Fore, Back, Style
import multiprocessing
init()
parser = argparse.ArgumentParser(description='LittleOwlCoin Offical Miner')
parser.add_argument('--node', type=str, help='Node URL')
parser.add_argument('--address', type=str, help='Wallet address', default='Blockchain')
node = parser.parse_args().node
miner_address = parser.parse_args().address

def hash_calc(speed):
    if speed >= 1000000000:
        return '{round(speed/1000000000, 3)} Gh/s'
    elif speed >= 1000000:
        return f'{round(speed/1000000, 3)} Mh/s'
    elif speed >= 1000:
        return f'{round(speed/1000, 3)} Kh/s'
    else:
        return f'{round(speed, 3)} H/s'

def mining(core):
    global speeds
    while True:
        task = requests.post(f'{node}/task?addr={miner_address}').json()
        i = 0
        print(Fore.YELLOW  + f'THREAD #{core} | TASK: BLOCK={task[3]} ID={task[2]} DIFF={task[1]}' + Style.RESET_ALL)
        start_time = time.time()
        while not hashlib.blake2s(f'{task[0] * i}'.encode()).hexdigest().endswith('0' * task[1]):
            i += 1
        print(Fore.YELLOW + f'THREAD #{core} | Block #{task[3]} found! | Hashrate: {hash_calc(i / (time.time() - start_time))}' + Style.RESET_ALL)
        response = requests.post(f'{node}/check?task_id={task[2]}&x={i}').json()
        if response['ok']:
            print(Fore.GREEN + 'Accepted!' + Style.RESET_ALL)
        else:
            print(Fore.RED + f'Rejected. Reason: {response["message"]}' + Style.RESET_ALL)

if __name__ == '__main__':
    for i in range(multiprocessing.cpu_count()):
        p = multiprocessing.Process(target=mining, args=(i,))
        p.start()
