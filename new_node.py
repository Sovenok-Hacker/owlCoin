import json, time, hashlib, random, requests, plyvel
from waitress import serve
from flask import Flask, request
from ecdsa import SigningKey, VerifyingKey, NIST384p, BadSignatureError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
app = Flask('owlCoin')
limiter = Limiter(app, key_func=get_remote_address)
db = plyvel.DB('db', create_if_missing=True)
def get_block(index=1):
    return json.loads(db.get(str(index).encode()))
def get_length():
    i = 0
    for k, v in db:
        i += 1
    return i
if not get_length():
    db.put(b'1', b'[[], 0, null, null, [null, null, null]]')
class systemData():
    def __init__(self):
        self.tasks = {}
        self.pending_transactions = []
        self.friends = []
sysData = systemData()
def validate(chain):
    thash = chain[1]
    for block in chain:
        for txion in block:
            try:
                VerifyingKey.from_string(bytes.fromhex(txion[0])).verify(bytes.fromhex(txion[4]), hashlib.blake2s(
                    f'{txion[0]}{txion[1]}{txion[2]}{txion[3]}'.encode()).hexdigest().encode())
            except BadSignatureError:
                return False
        if not block[3]:
            return False
        thash = block[2]
    return True
@app.route('/announce_nb', methods=['POST'])
@limiter.limit("20/minute")
def consesnus():
    try:
        block = request.get_json()['block']
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the block json.'})
    if not validate([get_block(get_length()), block]): # if our chain with this block is invalid
        return json.dumps({'ok': False, 'message': 'Block is invalid.'})
    blockchain.append(block)
    return {'ok': True}
@app.route('/meet',methods=['GET','POST']) # add friend
@limiter.limit("5/minute")
def meet():
    try:
        url = request.args['url']
    except KeyError:
        return {'ok': False, 'message': 'You must specify the url of your node (e.g. http://mynode.io, or http://184.353.353.74) (I need it is running!).'}
    try:
        if requests.get(f'{url}/blocks').status_code == 200:
            if not url in sysData.friends:
                sysData.friends.append(url)
                return {'ok': True}
            else:
                return {'ok': False, 'message': 'This node is already registered.'}
        else:
            return {'ok': False, 'message': 'Your node didn`t answer ok.'}
    except:
        return {'ok': 'Error in requesting node.'}
@app.route('/txs',methods=['GET','POST']) # get balance
@limiter.limit("20/minute")
def gtxs():
    try:
        addr = request.args['addr']
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the address.'})
    result = 0
    transactions = []
    for i in range(1, get_length()):
        block = get_block(i)
        for txion in block[0]:
            if txion[0] == addr or txion[1] == addr:
                transactions.append(txion)
    return json.dumps({'ok': True, 'txs': transactions})
@app.route('/blocks', methods=['GET','POST'])
@limiter.limit("5/minute")
def get_blocks():
    answer = []
    for i in range(1, get_length()):
        data = get_block(i)
        answer.append([data[0], data[1], i, data[2]])
    return json.dumps(answer), 200, {'Content-Type': 'application/json; charset=utf-8'}
@app.route('/block', methods=['GET', 'POST'])
@limiter.limit("60/minute")
def gb():
    try:
        index = int(request.args['index'])
    except (KeyError, ValueError):
        return json.dumps({'ok': False, 'message': 'Please, specify the index.'})
    if index > get_length():
        return json.dumps({'ok': False, 'message': 'Can`t find this block.'})
    return json.dumps(get_block(index))
@app.route('/transaction',methods=['POST']) # send coins
@limiter.limit("10/minute")
def transfer():
    try:
        sign = request.args['sign']
        sender = request.args['from']
        receiver = request.args['to']
        amount = float(request.args['amount'])
    except (KeyError, ValueError):
        return json.dumps({'ok': False, 'message': 'You must specify the sign, sender address, receiver address, timestamp and amount.'})
    message = request.args.get('message')
    result = 0
    transactions = []
    for i in range(1, get_length()):
        for txion in get_block(i)[0]:
            if txion[0] == sender:
                result -= txion[2]
            elif txion[1] == sender:
                result += txion[2]
    if result < amount:
        return json.dumps({'ok': False, 'message': 'You haven`t enougth coins to send.'})
    try:
        VerifyingKey.from_string(bytes.fromhex(sender)).verify(bytes.fromhex(sign), hashlib.blake2s(f'{sender}{receiver}{amount}{message}'.encode()).hexdigest().encode())
    except BadSignatureError:
        return json.dumps({'ok': False, 'message': 'Invalid signature.'})
    sysData.pending_transactions.append([sender, receiver, amount, message, sign])
    return json.dumps({'ok': True})
@app.route('/task',methods=['POST'])
# @limiter.limit("20/minute")
def create_task():
    try:
        addr = request.args['addr']
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify your address (to get a reward).'})
    task_id = int(random.randint(0, get_length() ** 2))
    l = get_length()
    diff = l // 1000 if l > 1000 else 1
    sysData.tasks.update({task_id: [diff, time.time(), addr]})
    index = get_length() + 1
    print(index)
    return json.dumps([get_length(), diff, task_id, index])
@app.route('/check',methods=['POST'])
# @limiter.limit("20/minute")
def check():
    try:
        tid = int(request.args['task_id'])
        solution = int(request.args['x'])
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the task ID and solution.'})
    if not sysData.tasks.get(tid):
        return json.dumps({'ok': False, 'message': 'Task ID is invalid or task already solved.'})
    if hashlib.blake2s(str(get_length() * solution).encode()).hexdigest().endswith('0' * sysData.tasks[tid][0]):
        solved_in = time.time() - sysData.tasks[tid][1]
        lb = get_block(get_length())
        nb = json.dumps([sysData.pending_transactions,
        round(time.time()),
        hashlib.blake2s(json.dumps(sysData.pending_transactions + [solution, sysData.tasks[tid][0], sysData.tasks[tid][2]] + [lb[1], lb[2]], ensure_ascii=False).encode()).hexdigest(),
        lb[2],
        [solution, sysData.tasks[tid][0], sysData.tasks[tid][2]]], ensure_ascii=False)
        db.put(str(get_length() + 1).encode(), nb.encode())
        sysData.pending_transactions = []
        sysData.pending_transactions.append(['Blockchain', sysData.tasks[tid][2], 1.0, 'Thanks for mining!', 'Blockchain'])
        for node in sysData.friends:
            try:
                requests.post(f'{node}/announce_nb', json=lb)
            except:
                pass
        sysData.tasks.pop(tid)
        return json.dumps({'ok': True})
    return json.dumps({'ok': False, 'message': f'Solution is incorrect.'})
serve(app, host='0.0.0.0', port=8000)
