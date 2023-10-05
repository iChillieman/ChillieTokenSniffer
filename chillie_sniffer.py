from decimal import Decimal
import json
from web3 import Web3, exceptions
import asyncio
from chillie_db import db_insert_buy, db_insert_buy_estimate, db_insert_event, db_insert_ready_to_watch
from chillie_util import CHILLIEMAN, LOG_BUYER, calc_buy, calc_sell, check_verification_with_delay, get_contract_abi, get_contract_abi_bnb, is_worth_buying, setLogger
import time
import traceback

from config import TRANSACTION_AMOUNT, WALLET_PRIVATE_KEY, IS_BUYING_ENABLED, ESTIMATE_GAS_PRICE, WETH

setLogger(LOG_BUYER)

amount_of_active_tasks = 0
tax_allowance=.12 #Allowing tax up to 12%

# add your blockchain connection information
rpc_url = 'https://bsc-dataseed.binance.org/'    
#rpc_url = 'https://ethereum.publicnode.com'
web3 = Web3(Web3.HTTPProvider(rpc_url))
if web3.is_connected():
    print('Welcome Chillieman! - Let me find you some good buys ;]')
else:
    print('Failed to connect to Blockchain!')
    exit()

# PancakeSwap factory (Emits the PairCreated event)
factory_address = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'  #Testnet  #0x6725F303b657a9451d8BA641348b6761A6CC7a17
#pancakeswap router 
router_address = '0x10ED43C718714eb63d5aA57B78B54704E256024E'    #Testnet #0xD99D1c33F9fC3444f8101754aBC46c52416550D1

#UniSwap Factory 
#factory_address = '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
#factory_abi = get_contract_abi(factory_address)
factory_abi = get_contract_abi_bnb(factory_address)
factory = web3.eth.contract(address=factory_address, abi=factory_abi)

#UniSwap Router
#router_address = '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
#router_abi = get_contract_abi(router_address)
router_abi = get_contract_abi_bnb(router_address)
router = web3.eth.contract(address=router_address, abi=router_abi)
    

#If conditions are met we buy the token
async def buy(token_to_buy_string, pair_address, owner_address):
    try:
        start_time = time.time()
        minimum_wait = start_time + 15
        #Delayed Verification Checking!
        print("Checking if " + token_to_buy_string + " verified...")
        if not await check_verification_with_delay(token_to_buy_string):
            print("Giving up on " + token_to_buy_string)
            return

        should_buy = await is_worth_buying(web3, router_address, token_to_buy_string, pair_address, owner_address)
        if not should_buy:
            print("Decided Not to buy " + token_to_buy_string)
            # TODO - Add this event in DB
            return

        # Contract is verified! Majority is not blocked from trading (HoneyPot)!

        if time.time() < minimum_wait:
            print("Slow Down Botty!")
            await asyncio.sleep(minimum_wait - time.time())

        print("Potential Token: " + token_to_buy_string)

        token_to_buy = web3.to_checksum_address(token_to_buy_string)

        
        success = False
        attempt_delay = 2 # CONFIG - Wait 2 Seconds between Buy Attempts
        attempts = 0
        max_attempts = 3 # CONFIG - Try 3 times to buy it
        while attempts < max_attempts:
            attempts = attempts + 1
            try:
                buy_output = calc_buy(router, token_to_buy, TRANSACTION_AMOUNT)
                buy_output_string = str(buy_output)

                estimated_sale = calc_sell(router, token_to_buy, buy_output)
                estimated_sale_string = str(estimated_sale)

                #If you couldnt fetch the amount of Tokens to receive, then dont buy this token
                if buy_output_string == "None" or estimated_sale_string == "None":
                    print("Could not get Buy or Sell Prices. Try Again or Dont Buy")
                    await asyncio.sleep(attempt_delay)
                    continue

                #Check how much you would get back if you sold right now. If you get back 
                percentage_after_tax = Decimal(estimated_sale) / Decimal(TRANSACTION_AMOUNT)
                if percentage_after_tax < 1 - tax_allowance:
                    print("Tax seems too high, or maybe too late. Not buying: " + str(token_to_buy_string))
                    return
                

                #This is the Token(BNB) amount you want to Swap
                amount_to_pay = web3.to_wei(TRANSACTION_AMOUNT,'ether')
                nonce = web3.eth.get_transaction_count(CHILLIEMAN)

                txn = router.functions.swapExactETHForTokens(
                    0, # set to 0, or specify minimum amount of token you want to receive - consider decimals!!!
                    [WETH,token_to_buy],
                    CHILLIEMAN,
                    (int(time.time()) + 10000)
                ).build_transaction({
                    'from': CHILLIEMAN,
                    'value': amount_to_pay,
                    'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
                    'nonce': nonce,
                })

                test_gas_estimation = web3.eth.estimate_gas(txn)
                gas_string = Web3.to_json(test_gas_estimation)
                
                if Decimal(test_gas_estimation) > 300000:
                    db_insert_event("EXPENSIVE_GAS")
                    print(token_to_buy_string  + " gas is too expensive: " + gas_string)
                    return
                else:
                    #Todo - Figure out the gas price for this estimate (Probably not going to be 5 gwei)
                    estimate = test_gas_estimation * int(ESTIMATE_GAS_PRICE)
                    estimation_in_eth = web3.from_wei(estimate, 'gwei')
                    db_insert_buy_estimate(token_to_buy_string, buy_output_string, str(estimation_in_eth))
                    print("Estimated gas: [" + token_to_buy_string  + "]: " + str(estimation_in_eth))
                
                if IS_BUYING_ENABLED:
                    print(token_to_buy + " Buying Token...")
                    signed_txn = web3.eth.account.sign_transaction(txn, private_key=WALLET_PRIVATE_KEY)
                    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                else:
                    print("Sniff Sniff!!")
                    return
                success = True
                break
                
            except Exception as err:
                print(token_to_buy_string + " Error during Purchasing:\n" + str(err))
                traceback.print_exc()
                await asyncio.sleep(attempt_delay)
        if not success:
            print(token_to_buy_string + " Could not successfully Buy token.")
            return
        
        # Now that you have sent your transaction, lets retrieve it and see if it was a success!

        monitory_delay = 2 # Check for transaction success every 2 seconds
        monitor_time = 2 * 60 # Monitor for 2 minutes
        right_now = time.time()
        end_time = right_now + monitor_time
        success = False
        while time.time() < end_time:
            try:
                receipt = web3.eth.get_transaction_receipt(tx_token)
                receipt_string = web3.to_json(receipt)
                receipt_json = json.loads(receipt_string)
                if int(receipt_json['status']) == 0:
                    break
                else:
                    success = True
                    break
            except exceptions.TransactionNotFound as err:
                0 #Do nothing - The transaction just is pending... Hasnt even been indexed

            await asyncio.sleep(monitory_delay)

        if success:
            print(token_to_buy_string + ": Bought token successfully!! =D")
            # TODO - CHILLIEMAN -> This takes in the gas estimation, not the actual gas used!!
            amount_invested = Decimal(TRANSACTION_AMOUNT) + Decimal(estimation_in_eth)
            db_insert_buy(token_to_buy, str(amount_invested))

            #Send to the Watcher...
            db_insert_ready_to_watch(token_to_buy)
        else:
            print("We did not buy the token succesffully....")
            # TODO - Retry from the top??

    except Exception as err:
        print(token_to_buy_string + " Could not buy Token ...")
        traceback.print_exc()


# define function to handle events and print to the console
async def handle_event(event):
    token0 = str(Web3.to_json(event['args']['token1']))
    token1 = str(Web3.to_json(event['args']['token0']))
    pair = str(Web3.to_json(event['args']['pair']))
    pair_stripped = pair.upper().strip('"')

    #Get the owner from the TX that triggerd this event
    tx = str(web3.to_json(event['transactionHash']))
    tx_stripped = tx.strip('"')
    
    attempts = 0
    max_attempts = 3
    attempt_delay = 60 
    while attempts != max_attempts:
        attempts = attempts + 1
        try:
            print("Trying to Pull Transaction: {}".format(tx_stripped))
            transaction = web3.eth.get_transaction(tx_stripped)
            break
        except exceptions.TransactionNotFound as e:
            print("NOT FOUND - Could not Retrieve transaction for tx_stripped. Trying Again")
            traceback.print_exc()
            await asyncio.sleep(attempt_delay)
        except Exception as e:
            print("EXCEPTION - Could not Retrieve transaction for tx_stripped. Trying Again")
            traceback.print_exc()
            await asyncio.sleep(attempt_delay)
            
    else:
        print("Attempts: {} Max Attempts: {}".format(attempts, max_attempts))
        print("Could not Retrieve transaction for tx_stripped. Giving Up.")
        return
        
    owner = str(web3.to_json(transaction['from']))
    owner_stripped = owner.upper().strip('"')
    weth_upper = WETH.upper()
    if token0.upper().strip('"') == weth_upper:
        token_to_buy = token1.upper().strip('"')
    elif token1.upper().strip('"') == weth_upper:
        token_to_buy = token0.upper().strip('"')
    else:
        print("Doesnt Use WETH")
        return 
        
    await buy(token_to_buy, pair_stripped, owner_stripped)


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the "PairCreated" event
# this loop runs on a poll interval
async def log_loop(event_filter, poll_interval):
    print("Streaming Events!")
    while True:
        for PairCreated in event_filter.get_new_entries():
            print(PairCreated)
            globals()['amount_of_active_tasks'] = globals()['amount_of_active_tasks'] + 1
            print("New Task for PairCreated!")
            asyncio.create_task(handle_event(PairCreated))
            # await handle_event(PairCreated) # Use this line if you want to process one token at a time and be slow!
            globals()['amount_of_active_tasks'] = globals()['amount_of_active_tasks'] + 1
        await asyncio.sleep(poll_interval)


# when main is called
# create a filter for the latest block and look for the "PairCreated" event for the uniswap factory contract
# run an async loop
# try to run the log_loop function above every 2 seconds
def main():
    event_filter = factory.events.PairCreated.create_filter(fromBlock='latest')
    while True:

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(
                asyncio.gather(
                    log_loop(event_filter, 2)
                )
            )
        except ValueError as err:
            print(err)
            args = err.args[0]
            error = args['code']
            if int(error) == -32000:
                #Error Code -32000 happens when Connection was lost
                print("Restarting... " + args['message'])
                event_filter = factory.events.PairCreated.create_filter(fromBlock='latest')
            else:
                break
        except:
            break

    loop.close()


main()