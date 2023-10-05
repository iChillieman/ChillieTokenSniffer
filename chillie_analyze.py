# import the following dependencies
import asyncio
from decimal import Decimal
import traceback
from web3 import Web3
from chillie_db import db_fetch_all_buy_estimates, db_fetch_all_buys, fetch_all_watching, fetch_all_zero_balance, fetch_sold_count, insert_estimate, insert_estimate_event, db_insert_event, insert_garbage, db_insert_ready_to_watch, insert_zero_balance, refresh_estimate_tables, remove_buy, remove_buy_estimate
from chillie_util import BALANCE_ABI, CHILLIEMAN, calc_sell, get_contract_abi, sell_tokens
from config import TRANSACTION_AMOUNT


# add your blockchain connection information
rpc_url = 'https://bsc-dataseed.binance.org/'    
#rpc_url = 'https://ethereum.publicnode.com'
web3 = Web3(Web3.HTTPProvider(rpc_url))
if web3.is_connected():
    print('Connected successfully!')
else:
    print('Failed to connect to Smart Chain')
    exit


#pancakeswap router abi 
router_address = '0x10ED43C718714eb63d5aA57B78B54704E256024E'    #Testnet #0xD99D1c33F9fC3444f8101754aBC46c52416550D1
router_abi = get_contract_abi(router_address)
router = web3.eth.contract(address=router_address, abi=router_abi)

async def main():
    total_sell_amount = 0

    print("Starting Analysis..")
    refresh_estimate_tables()

    #First load all Buys out - The amount of token, the hex for the token, and the estimated SALE price calculated when you bought the coin
    #All Purchases and estimates for Token are based on buying TRANSACTION_AMOUNT ETH worth of token

    #watching_list = fetch_all_watching()
    #for buy in db_fetch_all_buys():
    for buy in db_fetch_all_buy_estimates():
        hex = buy[1]
        amount_to_estimate = buy[2]
        # print("Hex: ", hex)


        #Check is this token is already being watched
        # is_watched = False
        # for watching in watching_list:
        #     watched = watching[0]
        #     # print("Watched: ", watched)
        #     if watching[0] == hex:
        #         is_watched = True
        
        # if is_watched:
        #     continue

        #times_sold = fetch_sold_count(hex)
        
        token_to_estimate = web3.to_checksum_address(hex)
        #token_contract = web3.eth.contract(address=token_to_estimate, abi=BALANCE_ABI)
        try:
            #amount_to_estimate = token_contract.functions.balanceOf(CHILLIEMAN).call()
        
            if amount_to_estimate == 0:
                print(token_to_estimate + " Could not get Sale price. - No Balance!")
                #remove_buy(hex)
                #insert_zero_balance(hex)
                continue

            # print("Amount to estimate: " + amount_to_estimate)
            sell_caluculation = calc_sell(router, token_to_estimate, amount_to_estimate)
        except:
            traceback.print_exc()
            continue

        if sell_caluculation == "None":
            print(token_to_estimate + " Could not get Sale price. - Sell Calculation is 0")
            continue

        # print("Amount to Estimate: ", amount_to_estimate)
        # print("Sell Calculation: ", sell_caluculation)

        #New Sale Price / Old Sale Price * 100 = Percentage of Raised
        gain = Decimal(sell_caluculation) / Decimal(TRANSACTION_AMOUNT)
        # insert_estimate(hex, str(sell_caluculation), str(gain))
        # if True:
        if gain > .3:
            print("[" + hex + "] Sale Price: " + str(sell_caluculation))
            print("[" + hex + "] Percentage: " + str(gain))
            #print("[" + hex + "] Sold Count: " + str(times_sold))
            insert_estimate(hex, str(sell_caluculation), str(gain))
            total_sell_amount = total_sell_amount + sell_caluculation
            continue
        else:
            print("This Token is Garbage - {}".format(hex))
            insert_garbage(hex)
            #remove_buy(hex)
            #remove_buy_estimate(hex)
            # Insert tokens in ready_to_watch table to hand off to Seller...
            # db_insert_ready_to_watch(hex)
            
            
            # try:
            #     if await sell_tokens(web3, router, hex, 1):
            #         total_sell_amount = total_sell_amount + sell_caluculation
            #         remove_buy(hex)
            #         print("Running Total: " + str(total_sell_amount))
            #     else:
            #         print("Couldnt Sell Token =[")
            # except:
            #     print("Cant Sell... ERROR - Get Rid of it")
            #     remove_buy(hex)
            #     insert_garbage(hex)

    print("Final Total: " + str(total_sell_amount))

def launch():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
    
launch()