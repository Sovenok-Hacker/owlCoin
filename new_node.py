import json, time, hashlib, random, requests
from flask import Flask, request
from ecdsa import SigningKey, VerifyingKey, NIST384p, BadSignatureError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
app = Flask('owlCoin')
limiter = Limiter(app, key_func=get_remote_address)
blockchain = []
class systemData():
    def __init__(self):
        self.mspeed = 0
        self.diff = {}
        self.tasks = {}
        self.pending_transactions = []
        self.friends = []
sysData = systemData()
class Block():
    def __init__(self, data, timestamp, index, phash, pow):
        self.data = data
        self.timestamp = timestamp
        self.index = index
        self.phash = phash
        self.pow = pow
        self.hash = hashlib.sha256(f'{self.data}{self.timestamp}{self.index}{self.phash}{self.pow}'.encode()).hexdigest()
        def check_pow():
            if pow: # if block is not genesis
                return hashlib.sha256(f'{pow[0] * pow[1]}'.encode()).hexdigest().endswith('0' * pow[2])
        self.check_pow = check_pow
blockchain.append(Block({'transactions': [], 'user_data': []}, None, len(blockchain) + 1, None, None)) # create genesis block
def validate(chain):
    thash = chain[0].hash
    for block in chain[1:]:
        for txion in block.data['transactions']:
            try:
                VerifyingKey.from_string(bytes.fromhex(txion[0])).verify(bytes.fromhex(txion[4]), hashlib.sha256(
                    f'{txion[0]}{txion[1]}{txion[2]}{txion[3]}'.encode()).hexdigest().encode())
            except BadSignatureError:
                return False
        if not block.phash == thash or not block.check_pow():
            return False
        thash = block.hash
    return True
@app.route('/announce_nb', methods=['POST'])
@limiter.limit("20/minute")
def consesnus():
    try:
        block = request.get_json()['block']
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the block json.'})
    if not validate(blockchain + [Block(*block)]): # if our chain with this block is invalid
        return json.dumps({'ok': False, 'message': 'Block is invalid.'})
    blockchain.append(Block(*block))
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
@app.route('/balance',methods=['GET','POST']) # get balance
@limiter.limit("20/minute")
def balance():
    try:
        addr = request.args['addr']
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the address.'})
    result = 0
    transactions = []
    for block in blockchain:
        for txion in block.data['transactions']:
            transactions.append(txion)
    for txion in transactions:
        if txion[0] == addr:
            result -= txion[2]
        elif txion[1] == addr:
            result += txion[2]
    return json.dumps({'ok': True, 'balance': result})
@app.route('/blocks',methods=['GET','POST'])
@limiter.limit("50/minute")
def get_blocks():
    answer = []
    for block in blockchain:
        answer.append([block.data, block.timestamp, block.index, block.hash, block.phash, block.pow])
    return json.dumps(answer)
@app.route('/transaction',methods=['POST']) # send coins
@limiter.limit("10/minute")
def transfer():
    try:
        sign = request.args['sign']
        sender = request.args['from']
        receiver = request.args['to']
        amount = float(request.args['amount'])
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the sign, sender address, receiver address, timestamp and amount.'})
    message = request.args.get('message')
    result = 0
    transactions = []
    for block in blockchain:
        for txion in block.data['transactions']:
            transactions.append(txion)
    for txion in transactions:
        if txion[0] == sender:
            result -= txion[2]
        elif txion[1] == sender:
            result += txion[2]
    if result < amount:
        return json.dumps({'ok': False, 'message': 'You haven`t enougth coins to send.'})
    try:
        VerifyingKey.from_string(bytes.fromhex(sender)).verify(bytes.fromhex(sign), hashlib.sha256(f'{sender}{receiver}{amount}{message}'.encode()).hexdigest().encode())
    except BadSignatureError:
        return json.dumps({'ok': False, 'message': 'Invalid signature.'})
    sysData.pending_transactions.append([sender, receiver, amount, message, sign])
    return json.dumps({'ok': True})
@app.route('/task',methods=['POST'])
@limiter.limit("20/minute")
def create_task():
    try:
        addr = request.args['addr']
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify your address (to get a reward).'})
    if sysData.diff.get(addr) == None:
        sysData.diff.update({addr: 5})
    y = random.randint(0, 1000000)
    task_id = int(random.randint(0, y * y))
    sysData.tasks.update({task_id: [y, sysData.diff[addr], time.time(), addr]})
    for block in blockchain:
        index = block.index
    print(index)
    return json.dumps([y, sysData.diff[addr], task_id, index])
@app.route('/check',methods=['POST'])
@limiter.limit("20/minute")
def check():
    try:
        tid = int(request.args['task_id'])
        solution = int(request.args['x'])
    except KeyError:
        return json.dumps({'ok': False, 'message': 'You must specify the task ID and solution.'})
    if not sysData.tasks.get(tid):
        return json.dumps({'ok': False, 'message': 'Task ID is invalid or task already solved.'})
    if hashlib.sha256(f'{sysData.tasks[tid][0] * solution}'.encode()).hexdigest().endswith('0' * sysData.tasks[tid][1]):
        solved_in = time.time() - sysData.tasks[tid][2]
        sysData.pending_transactions.append(['Blockchain', sysData.tasks[tid][3], 1.0, 'Thanks for mining!', 'Blockchain'])
        blockchain.append(Block({'transactions': sysData.pending_transactions, 'user_data': []}, time.time(), len(blockchain) + 1, blockchain[-1].hash, [sysData.tasks[tid][0], solution, sysData.tasks[tid][1], sysData.tasks[tid][3]]))
        for node in sysData.friends:
            try:
                requests.post(f'{node}/announce_nb', json={'block': [blockchain[-1].data, blockchain[-1].timestamp, blockchain[-1].index, blockchain[-1].phash, blockchain[-1].pow]})
            except:
                pass
        sysData.pending_transactions = []
        if solved_in < 10:
            sysData.diff[sysData.tasks[tid][3]] += 1
        elif solved_in > 60:
            sysData.diff[sysData.tasks[tid][3]] -= 1
        sysData.tasks.pop(tid)
        return json.dumps({'ok': True})
    return json.dumps({'ok': False, 'message': f'Solution is incorrect.'})
app.run(host='0.0.0.0', port=8000, threaded=True)
