import requests, hashlib, time
from colorama import init
from colorama import Fore, Back, Style
from multiprocessing import Process
init()
node = 'http://127.0.0.1:8000'
miner_address = '09e761510d1fd850054b15aeb24fd62de256528f8481daa059904b844fdce42f86375b3ec80c5f7b77135dd5e5abaf98'

def check_work(task):
    task2 = get_work()
    if task[3] == task2[3]:
        return True
    else:
        return False

def get_work():
    task = requests.post(f'{node}/task?addr={miner_address}').json()
    return task

def hash_calc(speed):
    if speed >= 10000000000:
        value = "%.0f%s" % (speed/1000000000.00, 'G')
    elif speed >= 10000000:
        value = "%.0f%s" % (speed/1000000.00, 'M')
    else:
        if speed >= 10000:
            value = "%.0f%s" % (speed/1000.0, 'k')
    return value

def mining(core):
    global speeds
    while True:
        task = get_work()
        i = 0
        print(Style.RESET_ALL + Back.BLUE +  f'CORE {core}', end='')
        print(Style.RESET_ALL + Fore.YELLOW  + f' TASK: BLOCK={task[3]} ID={task[2]} DIFF={task[1]} Y={task[0]}')
        start_time = time.time()
        while not hashlib.blake2s(f'{task[0] * i}'.encode()).hexdigest().endswith('0' * task[1]):
            if (time.time() - start_time) > 30:
                if not check_work(task):
                    print(Style.RESET_ALL + Back.BLUE +  f'CORE {core}', end='')
                    print(Style.RESET_ALL + Back.GREEN + ' New work!')
                    task = get_work()
                    print(Style.RESET_ALL + Back.BLUE +  f'CORE {core}', end='')
                    print(Style.RESET_ALL + Fore.YELLOW  + f' TASK: BLOCK={task[3]} ID={task[2]} DIFF={task[1]} Y={task[0]}')
                else:
                    speed = round(i / (time.time() - start_time))
                    speed = hash_calc(speed)
                    print(Style.RESET_ALL + Back.BLUE +  f'CORE {core}', end='')
                    print(Style.RESET_ALL + Fore.YELLOW  + f'Hashrate: {speed} H/S.')
                    i = 0
                start_time = time.time()
            else:
                pass
            i += 1
        print(Style.RESET_ALL + Back.BLUE +  f'CORE {core}', end='')
        print(Style.RESET_ALL + Back.GREEN + f' Block found! Number: {task[3]}')
        response = requests.post(f'{node}/check?task_id={task[2]}&x={i}').json()
        if response['ok']:
            print(Style.RESET_ALL + Back.GREEN + 'Accepted!')
        else:
            print(Style.RESET_ALL + Back.RED + 'Rejected. Reason: ' + response['message'])
if __name__ == '__main__':
    for i in range(multiprocessing.cpu_count()):
        time.sleep(0.25)
        i = Process(target=mining, args=(i,))
        i.start()
