from decimal import Decimal
import time
import traceback
from async_timeout import asyncio
from web3 import Web3
from chillie_db import db_fetch_all_buy_estimates, insert_estimate, insert_garbage, insert_rug_pull, insert_zero_balance, refresh_estimate_tables, remove_buy_estimate
from chillie_util import BALANCE_ABI, calc_sell, get_contract_abi, sell_tokens
import config

# add your blockchain connection information
bsc = 'https://bsc-dataseed.binance.org/'    
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.is_connected():
    print('Connected successfully!')
else:
    print('Failed to connect to Smart Chain')
    exit

router = web3.eth.contract(address=UNI_ROUTER_ADDRESS, abi=get_contract_abi(UNI_ROUTER_ADDRESS))

refresh_estimate_tables()

async def sell_all_coins():
    for buy in db_fetch_all_buy_estimates():
        hex = buy[1]
        token_address = Web3.to_checksum_address(hex)

        try:
            token = web3.eth.contract(address=token_address, abi=BALANCE_ABI) # declaring the token contract
            token_balance = token.functions.balanceOf(config.WALLET_ADDRESS).call() # returns int with balance, without decimals

            if token_balance > 0:
                selling_return = calc_sell(router, token_address, token_balance)
            else:
                selling_return = 0
                insert_zero_balance(hex)
                remove_buy_estimate(hex)
                print("Zero Balance Removed")
                continue
            gain = Decimal(selling_return) / Decimal(0.005)

            if gain < 0.01:
                insert_rug_pull(hex)
                remove_buy_estimate(hex)
                print("Rugpull Removed")
            elif gain < 0.4:
                insert_garbage(hex)
                remove_buy_estimate(hex)
                print("Grabage Removed")
            else:
                await sell_tokens(web3, router, hex, 1)
            
        except Exception as err:
            print("Couldnt Sell " + hex)
            traceback.print_exc()

def launch():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(sell_all_coins())
    finally:
        loop.close()
    
launch()