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
    elif cmd.startswith('balance'):
        balance = requests.get(f'{node}/balance?addr={using}').json()['balance']
        print(f'Your balance: {balance} OWL')
    elif cmd.startswith('send'):
        from_addr = using
        to_addr = input('TO: => ')
        amount = float(input('AMOUNT: => '))
        message = input('MESSAGE: (leave empty for blank message) =>')
        if input('Is everything correct? (Y, y, N, n) => ') in ['Y', 'y']:
            signature = SigningKey.from_string(bytes.fromhex(using_privkey)).sign(hashlib.sha256(f'{from_addr}{to_addr}{amount}{message}'.encode()).hexdigest().encode()).hex()
            data = requests.post(f'{node}/transaction?amount={amount}&to={to_addr}&from={from_addr}&message={message}&sign={signature}').json()
            if data['ok'] == True:
                print('Transaction was submitted succefetly!')
            else:
                print(data['message'])
