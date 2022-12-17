from ecdsa import SigningKey, VerifyingKey, NIST384p
import json, requests, os, sys, random, time, hashlib
node = 'http://127.0.0.1:8000'
def create_wallet():
    sk = SigningKey.generate()
    vk = sk.verifying_key
    return [sk.to_string().hex(), vk.to_string().hex()]
wallets = []
for file in os.listdir():
    if file.startswith('wallet') and file.endswith('.json'):
        with open(file) as wallet:
            wallets.append(json.loads(wallet.read()))
            wallet.close()
if len(wallets) == 0:
    if input('We can`t find any wallets, do you want to create a new one? => ') in ['y', 'Y']:
        wallet = create_wallet()
        with open(f'wallet{random.randint(0, 1000)}.json', 'w') as file:
            file.write(json.dumps(wallet))
            file.close()
        print('Wallet created succefectly. Goodbye!')
    else:
        print('Goodbye!')
    sys.exit()
else:
    print(f'We are found {len(wallets)} wallets.')
    i = 0
    for wallet in wallets:
        print(f'{i}. {wallet[1]}')
        i += 1
    print(f'{i}. Create a new wallet.')
    choice = int(input('=> '))
    if choice.isnumeric():
        choice = int(choice)
    else:
        print('You entered the wrong value!')
        input('Press enter to close.')
        sys.exit()
    if choice == i:
        wallet = create_wallet()
        with open(f'wallet{random.randint(0, 1000)}.json', 'w') as file:
            file.write(json.dumps(wallet))
            file.close()
        print('Wallet created succefectly. Goodbye!')
        sys.exit()
    if choice < len(wallets):
        using = wallets[choice][1]
        using_privkey = wallets[choice][0]
    else:
        print('Goodbye!')
        sys.exit()
while True:
    cmd = input('OwlCoinCMD => ')
    if cmd.startswith('exit'):
        print('Goodbye!')
        sys.exit()
    elif cmd.startswith('history'):
        txs = requests.get(f'{node}/txs?addr={using}').json()['txs']
        balance = 0
        for tx in txs:
            tx_type = '-' if tx[0] == using else '+'
            if tx_type == '-':
                balance -= tx[2]
            else:
                balance += tx[2]
            print()
            print(f'{tx_type} | {tx[0]} => {tx[1]} | {tx[2]} OWL | {tx[3]}')
        print(f'Your balance: {balance} OWL')
    elif cmd.startswith('send'):
        from_addr = using
        to_addr = input('TO: => ')
        amount = float(input('AMOUNT: => '))
        message = input('MESSAGE: (leave empty for blank message) =>')
        if input('Is everything correct? (Y, y, Да, да, N, n, Нет, нет) => ') in ['Y', 'y', 'Да', 'да']:
            signature = SigningKey.from_string(bytes.fromhex(using_privkey)).sign(hashlib.sha256(f'{from_addr}{to_addr}{amount}{message}'.encode()).hexdigest().encode()).hex()
            data = requests.post(f'{node}/transaction?amount={amount}&to={to_addr}&from={from_addr}&message={message}&sign={signature}').json()
            if data['ok'] == True:
                print('Transaction was submitted succefetly!')
            else:
                print(data['message'])
    elif cmd.startswith('balance'):
        txs = requests.get(f'{node}/txs?addr={using}').json()['txs']
        balance = 0
        for tx in txs:
            if tx[0] == using:
                balance -= tx[2]
            else:
                balance += tx[2]
        print(f'Your balance: {balance} OWL')
    elif cmd.startswith('help'):
        print('send - send coins.')
        print('balance - get balance.')
        print('history - get balance and transacation history.')
        print('help - print this note.')
        print('exit - quit the wallet.')
