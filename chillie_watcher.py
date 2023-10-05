# import the following dependencies
from decimal import Decimal
import random
import traceback
from web3 import Web3, exceptions
import asyncio
from chillie_db import fetch_all_ready_to_watch, fetch_all_watching, fetch_sold_count, fetch_starting_balance, insert_checkpoint, db_insert_event, insert_garbage, insert_reserves, insert_rug_pull, insert_sell_estimate, insert_unsellable, insert_watching, insert_zero_balance, remove_buy, remove_buy_estimate, remove_ready_to_watch, remove_watching, update_starting_balance
from chillie_util import BALANCE_ABI, CHILLIEMAN, LOG_WATCHER, PRICE_ABI, calc_buy, calc_sell, get_contract_abi, sell_tokens, setLogger
import time

from config import TRANSACTION_AMOUNT

setLogger(LOG_WATCHER)

amount_of_active_tasks = 0
tax_allowance=.20 #Allowing tax up to 20%

# add your blockchain connection information
bsc = 'https://bsc-dataseed.binance.org/'    
web3 = Web3(Web3.HTTPProvider(bsc))
if web3.is_connected():
    print('Welcome Chillieman! - Time to make you some money ;]')
else:
    print('Failed to connect to Smart Chain')
    exit()

# PancakeSwap factory (Emits the PairCreated event)
factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'  #Testnet  #0x6725F303b657a9451d8BA641348b6761A6CC7a17
factory_abi = get_contract_abi(factory_address)
factory = web3.eth.contract(address=factory_address, abi=factory_abi)

#pancakeswap router 
router_address = '0x10ED43C718714eb63d5aA57B78B54704E256024E'    #Testnet #0xD99D1c33F9fC3444f8101754aBC46c52416550D1
router_abi = get_contract_abi(router_address)
router = web3.eth.contract(address=router_address, abi=router_abi)

async def watch_and_sell(token, start_time, sell_time):
    print("Watching " + token)
    token_address = web3.to_checksum_address(token)
    token_contract = web3.eth.contract(token_address, abi=BALANCE_ABI)

    time_limit = 30 * 60 * 60 # Watch each coin for four Hours
    price_check_delay = 10 # Check each tokens price every 20 seconds
    end_time = start_time + time_limit
    gain = Decimal(0)
    top_gain = Decimal(0)
    starting_balance = fetch_starting_balance(token)

    times_to_attempt_balance_fetch = 5
    attempt = 0
    balance_fetch_delay = 5
    while attempt < times_to_attempt_balance_fetch:
        attempt = attempt + 1
        try:
            current_balance = token_contract.functions.balanceOf(CHILLIEMAN).call()
            if current_balance != 0:
                if starting_balance == 0:
                    update_starting_balance(token, str(current_balance))
                    starting_balance = current_balance
                break

            if attempt == times_to_attempt_balance_fetch - 1:
                print(token_address + " Cannot Fetch balance, trying to load Contract ABI ")
                token_contract = web3.eth.contract(address=token_address, abi=get_contract_abi(token_address))
            if attempt == times_to_attempt_balance_fetch:
                print(token + " Could not fetch balance after " + str(times_to_attempt_balance_fetch) + " attempts")
                insert_zero_balance(token_address)
                remove_watching(token)
                return
            
        except exceptions.ABIFunctionNotFound:
            print(token + " balanceOf function not found - Cannot montior this token - why was this even bought?")
            insert_garbage(token)
            remove_watching(token)
            return
        await asyncio.sleep(balance_fetch_delay)

    checkpoint_increment = 1
    current_checkpoint = 1
    check_point_counter = time.time() + (checkpoint_increment * 60)

    errors = 0 
    while time.time() < end_time and errors < 10:
        the_time = int(time.time())
        try:
            sell_amount = token_contract.functions.balanceOf(CHILLIEMAN).call()
            if sell_amount == 0:
                print(token + " No Tokens to work with... Had tokens before!")
                insert_zero_balance(token_address)
                break

            global_output = calc_sell(router, token_address, starting_balance)
            if global_output == 0:
                errors = errors + 1
                await asyncio.sleep(10)
                continue

            # Calculate Gain from original purchase - Including the buying Tax
            gain = Decimal(global_output) / Decimal(TRANSACTION_AMOUNT)
            # global_gain = Decimal(sell_global_output) / Decimal(TRANSACTION_AMOUNT)
            if gain < 0.01:
                print("You lost your money: " + token + " Top Gain... " + str(top_gain))
                insert_rug_pull(token)
                break
            elif gain < .1:
                print("Garbage...." + token + " Top Gain... " + str(top_gain))
                insert_garbage(token)
                break



            if the_time > check_point_counter:
                insert_checkpoint(token, str(current_checkpoint), str(gain))
                current_checkpoint = current_checkpoint + checkpoint_increment
                check_point_counter = the_time + (checkpoint_increment * 60)


            if gain - top_gain > 100:
                print(token + " This just shot up x100 within a minute - Probably a bug while calculating price!")
                
                attempt = 0
                sell_attempt_delay = 1
                max_sell_attempts = 2 # Send the transaction twice if it fails the first time
                success = False
                while attempt < max_sell_attempts:
                    attempt = attempt + 1
                    try:
                        if await sell_tokens(web3, router, token, 1):
                            success = True
                            break
                    except Exception as e:
                        if attempt != max_sell_attempts:
                            print(token + "Could not Sell, trying again!")
                        print(str(e))

                    await asyncio.sleep(sell_attempt_delay)

                if not success:
                    insert_unsellable(token)
                break
            elif the_time > sell_time:
                if gain < .4:
                    print("Garbage...." + token + " Top Gain... " + str(top_gain))
                    insert_garbage(token)
                    break

                print(token + " Time to the Sell!")

                attempt = 0
                sell_attempt_delay = 1
                max_sell_attempts = 2 # Send the transaction twice if it fails the first time
                success = False
                while attempt < max_sell_attempts:
                    attempt = attempt + 1
                    try:
                        if await sell_tokens(web3, router, token, 1):
                            success = True
                            break
                    except Exception as e:
                        if attempt != max_sell_attempts:
                            print(token + "Could not Sell, trying again!")
                        print(str(e))
                        

                    await asyncio.sleep(sell_attempt_delay)

                if not success:
                    insert_unsellable(token)
                break

            is_new_gain = gain != top_gain
            if gain > top_gain:
                print(token + " New Top gain: " + str(gain))
                top_gain = gain


            # Log the data if its new data
            if is_new_gain:
                insert_sell_estimate(token, str(global_output), str(gain), str(the_time))

        except Exception as err:
            errors = errors + 1
            if str(err).find('Selling this token would lose money') != 1:
                insert_garbage(token)
                break
            else:
                print("Problem with Watching Token..\n" + str(err))
                traceback.print_exc()

        await asyncio.sleep(price_check_delay)
    print("Done with " + token + " ... Gain: " + str(gain))
    remove_watching(token)

async def start_up():
    check_db_delay = 2
    print("LETS FUCKING GO!!!") 
    checkpoints = [4, 5, 6]
    delays = [0.9, 1, 0.3, 0.4, 0.6, 0.8]
    for watching in fetch_all_watching():
        token = watching[0]
        start_time = watching[1]
        end_time = (random.choice(checkpoints) * 60) + start_time
        asyncio.create_task(watch_and_sell(token, start_time, end_time))
        await asyncio.sleep(random.choice(delays))

    while True:
        for token in fetch_all_ready_to_watch():
            token_address = token[0]
            insert_watching(token_address, str(time.time()))
            remove_ready_to_watch(token_address)
            start_time = time.time()
            end_time = (random.choice(checkpoints) * 60) + start_time
            asyncio.create_task(watch_and_sell(token_address, start_time, end_time))
        await asyncio.sleep(check_db_delay)

def main():
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start_up())
    finally:
        loop.close()


main()