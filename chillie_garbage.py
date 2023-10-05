from decimal import Decimal
import time
import traceback
from web3 import Web3
from chillie_db import  db_fetch_all_garbage, db_fetch_all_rug_pulls, db_insert_buy, db_insert_buy_estimate, insert_estimate, insert_zero_balance, remove_garbage, remove_rug_pull
from chillie_util import CHILLIEMAN, get_contract_abi, calc_sell
import config

# add your blockchain connection information
bsc = 'https://bsc-dataseed.binance.org/'    
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.is_connected():
    print('Connected successfully!')
else:
    print('Failed to connect to Smart Chain')
    exit

#pancakeswap router abi 
panRouterContractAddress = '0x10ED43C718714eb63d5aA57B78B54704E256024E'    #Testnet #0xD99D1c33F9fC3444f8101754aBC46c52416550D1
panabi = get_contract_abi(panRouterContractAddress)
router = web3.eth.contract(address=panRouterContractAddress, abi=panabi)

wbnb = web3.to_checksum_address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c')   #WBNB


print("Checking garbage ---------")

for buy in db_fetch_all_garbage():
    hex = buy[0]
    token_address = Web3.to_checksum_address(hex)

    try:
        token_abi = get_contract_abi(token_address)
        token = web3.eth.contract(address=token_address, abi=token_abi) # declaring the token contract
        token_balance = token.functions.balanceOf(CHILLIEMAN).call() # returns int with balance, without decimals

        if token_balance > 0:
            selling_return = calc_sell(router, token_address, token_balance)
        else:
            selling_return = 0
            print("Zero Balance")
            insert_zero_balance(hex)
            remove_garbage(hex)
            continue
        gain = Decimal(selling_return) / Decimal(0.005)

        if gain > 0.4:
            db_insert_buy_estimate(hex, str(token_balance), '0.005')
            db_insert_buy(hex, '0.005')
            insert_estimate(hex, str(selling_return), str(gain))
            remove_garbage(token_address)
            print("Taken out of garbage")
            

        print("[" + hex + "] Balance: " + str(token_balance))
        print("[" + hex + "] Sale: " + str(selling_return))
        print("[" + hex + "] Gain: " + str(gain))
        
    except Exception as err:
        print("Couldnt analyze " + hex)
        traceback.print_exc()
