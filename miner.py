import requests, hashlib, time
node = 'http://sovenok-hacker.ml:8888/'
miner_address = 'aee1e56a137546a6f7335df38e8648a8bb28627a642cbee00737d939c0aae422351b26223349177e10d2f45b3456d937'
while True:
    task = requests.get(f'{node}/task?addr={miner_address}').json()
    i = 0
    print(f'TASK: ID={task[2]} DIFF={task[1]} Y={task[0]}')
    start_time = time.time()
    while not hashlib.sha256(f'{task[0] * i}'.encode()).hexdigest().endswith('0' * task[1]):
        i += 1
    solved_time = time.time()
    print(f'Solution found, hashrate is {i / (solved_time - start_time)} H/S.')
    response = requests.get(f'{node}/check?task_id={task[2]}&x={i}').json()
    if not response['ok']:
        print(response['message'])
        input()
