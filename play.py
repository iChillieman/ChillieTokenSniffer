from web3 import Web3, exceptions
import json
import traceback


rpc_url = 'https://bsc-dataseed.binance.org/'    
#rpc_url = 'https://ethereum.publicnode.com'
web3 = Web3(Web3.HTTPProvider(rpc_url))
if web3.is_connected():
    print('Welcome Chillieman! - Let me find you some good buys ;]')
else:
    print('Failed to connect to Blockchain!')
    exit()

txn = '0x5565448697c6f65020a4c52bfd5cd386c1297942057bea378bbcc5a1153ae0dc'

try:
    print("Trying to Pull Transaction: {}".format(txn))
    transaction = web3.eth.get_transaction(txn)
    print(transaction)
except exceptions.TransactionNotFound as e:
    print("TNF - Could not Retrieve transaction for tx_stripped. Trying Again")
    traceback.print_exc()
except Exception as e:
    print("EXCEPTION - Could not Retrieve transaction for tx_stripped. Trying Again")
    traceback.print_exc()

            
print("Done")