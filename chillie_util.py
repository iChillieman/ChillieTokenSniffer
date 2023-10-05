from decimal import Decimal
import json
from math import floor
import random
import sys
import time
import asyncio
import traceback
from chillie_db import fetch_abi, insert_abi, insert_allowance_request, db_insert_event, insert_honeypot, insert_sale, insert_zero_balance, is_allowance_already_requested, remove_buy, remove_buy_estimate
from config import BSC_SCAN_API_KEY, WALLET_ADDRESS, WALLET_PRIVATE_KEY, ETHER_SCAN_API_KEY, UNI_ROUTER_ADDRESS, WETH
from web3 import Web3, exceptions
import requests

#WBNB = Web3.to_checksum_address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c')
CHILLIEMAN = Web3.to_checksum_address(WALLET_ADDRESS)
ETHER = 10 ** 18
PRICE_ABI = json.loads('[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"token0","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"token1","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[],"name":"factory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"who","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"totalSupply","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]')
BALANCE_ABI = json.loads('[{"inputs":[{"internalType":"address","name":"who","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner_","type":"address"},{"internalType":"address","name":"spender","type":"address"}],"name":"allowance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"spender","type":"address"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"approve","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"}]')
SNIPER_LOG = "log_chillie_sniper.log"
LOG_BUYER = "log_chillie_buyer.log"
LOG_WATCHER = "log_chillie_watcher.log"
LOG_PLAY = "log_play.log"
LOG_UNICRYPT = "log_unicrypt.log"
LOG_ANON = "log_anoncrypt.log"

time_to_monitor = 60 * 30 # Check Verification Status for 30 minutes before giving up on the token

class Logger(object):
    def __init__(self, file_name):
        self.terminal = sys.stdout
        self.log = open(file_name, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        #this flush method is needed for python 3 compatibility.
        #this handles the flush command by doing nothing.
        #you might want to specify some extra behavior here.
        pass    

def setLogger(file_name):
    sys.stdout = Logger(file_name)

def format_number_four_places(number):
    return "{:.4f}".format(number)

#{
#   "status":"1",
#   "message":"OK",
#   "result":{
#      "LastBlock":"13053741",
#      "SafeGasPrice":"20",
#      "ProposeGasPrice":"22",
#      "FastGasPrice":"24",
#      "suggestBaseFee":"19.230609716",
#      "gasUsedRatio":"0.370119078777807,0.8954731,0.550911766666667,0.212457033333333,0.552463633333333"
#   }
#}

# TODO - CHILLIEMAN - USE THIS
def get_gas_price_gwei():
    url = "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey={}".format(contract_address, ETHER_SCAN_API_KEY)
    response = requests.get(url).json()
    status = response['status']
    result = response['result']
    proposed_tax = result['ProposeGasPrice']
    fast_tax = result['FastGasPrice']
    if int(status) == 0:
        if not result == 'Contract source code not verified':
            print("Could not check source code... Getting ABI")
            traceback.print_exc()
        abi = None
    else:
        insert_abi(contract_address, result)
        abi = result

    return abi
   
def get_contract_abi(contract_address):
    contract_address = Web3.to_checksum_address(contract_address)
    from_db = fetch_abi(contract_address)
    if from_db == None:
        url = "https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}".format(contract_address, ETHER_SCAN_API_KEY)
        response = requests.get(url).json()
        is_verified = response['status']
        result = response['result']
        if int(is_verified) == 0:
            if not result == 'Contract source code not verified':
                print("Could not check source code... Getting ABI")
                traceback.print_exc()
            abi = None
        else:
            insert_abi(contract_address, result)
            abi = result
    else:
        abi = from_db[0]

    return abi
    
def get_contract_abi_bnb(contract_address):
    contract_address = Web3.to_checksum_address(contract_address)
    from_db = fetch_abi(contract_address)
    if from_db == None:
        url = "https://api.bscscan.com/api?module=contract&action=getabi&address=" + contract_address + "&apikey=" + BSC_SCAN_API_KEY
        response = requests.get(url).json()
        print(response)
        is_verified = response['status']
        result = response['result']
        if int(is_verified) == 0:
            if not result == 'Contract source code not verified':
                print("Could not check source code... Getting ABI")
                traceback.print_exc()
            abi = None
        else:
            print("Contract is Verified! {}".format(contract_address))
            insert_abi(contract_address, result)
            abi = result
    else:
        abi = from_db[0]
    
    
    return abi

def check_if_verified_eth(contract_address):
    try:
        contract_address = Web3.to_checksum_address(contract_address)
        url = "https://api.etherscan.io/api?module=contract&action=getabi&address={}&apikey={}".format(contract_address, ETHER_SCAN_API_KEY)
        response = requests.get(url).json()
        print("ETH [{}] - {}".format(contract_address, response))
        is_verified = response['status']
        result = response['result']
        if int(is_verified) == 0:
            if not result == 'Contract source code not verified':
                print("Could not check source code... Checking if verified! " + str(result))
            return False
        else:
            insert_abi(contract_address, result)
            return True
    except:
        return False

def check_if_verified_bnb(contract_address):
    try:
        contract_address = Web3.to_checksum_address(contract_address)
        url = "https://api.bscscan.com/api?module=contract&action=getabi&address=" + contract_address + "&apikey=" + BSC_SCAN_API_KEY
        response = requests.get(url).json()
        print("BNB [{}] - {}".format(contract_address, response))
        is_verified = response['status']
        result = response['result']
        if int(is_verified) == 0:
            if not result == 'Contract source code not verified':
                print("Could not check source code... Checking if verified! " + str(result))
            return False
        else:
            insert_abi(contract_address, result)
            return True
    except:
        return False

def calc_sell(router, token, sell_amount):

    token_address = Web3.to_checksum_address(token)
    sell_amount = floor(sell_amount)
    try:
        price = router.functions.getAmountsOut(sell_amount, [token_address, WETH]).call()
        normalizedPrice = Web3.from_wei(price[1], 'Ether')
        return normalizedPrice
    except Exception as err:
        print("Could not get " + str(token_address) + " Sell Amount...\n" + str(err))
        traceback.print_exc()

def calc_buy(router, token, bnb_to_spend):
    token_address = Web3.to_checksum_address(token)
    amountIn = Web3.to_wei(bnb_to_spend,'ether')
    try:
        output = router.functions.getAmountsOut(amountIn, [WETH, token_address]).call()
        return output[1]
    except Exception as err:
        print("Could not get " + str(token_address) + " Amount...")
        if str(err).find("INSUFFICIENT_LIQUIDITY") != -1:
            print("Insufficient Liquidity")
        else:
            traceback.print_exc()
            



def get_real_price_in_bnb(decimals, pair_contract, is_reversed):
    peg_reserve = 0
    token_reserve = 0
    (reserve0, reserve1, blockTimestampLast) = pair_contract.functions.getReserves().call()
    
    if is_reversed:
        peg_reserve = reserve0
        token_reserve = reserve1
    else:
        peg_reserve = reserve1
        token_reserve = reserve0
    
    if token_reserve and peg_reserve:
        # CALCULATE PRICE BY TOKEN PER PEG
        price = (Decimal(token_reserve) / 10 ** decimals) / (Decimal(peg_reserve) / ETHER)
        return price
        
    return Decimal('0')


def calc_real_sell(web3, factory, token_string, amount_to_sell):
    print("Chillieman! Real Sell!")
    token = Web3.to_checksum_address(token_string)
    pair = factory.functions.getPair(token, WETH).call()
    pair_contract = web3.eth.contract(address=pair, abi=PRICE_ABI)
    is_reversed = pair_contract.functions.token0().call() == WETH
    decimals = web3.eth.contract(address=token, abi=PRICE_ABI).functions.decimals().call()
    price = get_real_price_in_bnb(decimals, pair_contract, is_reversed)
    
    actual_tokens = Decimal(amount_to_sell) / 10 ** decimals
    final = Decimal(price) * Decimal(amount_to_sell)
    return final

async def check_verification_with_delay(token):
    delays = [31.21, 56.47, 40.62, 40.11, 20.29]
    starting_time = int(time.time())
    ending_time = starting_time + time_to_monitor

    try:
        #Delayed Verification Checking!
        verification_attempts = 0
        verified = False

        while not verified and time.time() < ending_time:
            verification_attempts = verification_attempts + 1
            verified = check_if_verified_bnb(token)
            if not verified:
                await asyncio.sleep(random.choice(delays))
            elif verification_attempts > 1:
                print(token + " Delayed Contract verification - Time ellapsed: " + str(int(time.time()) - starting_time))
                time_taken = int((time.time() - starting_time) / 60)
                db_insert_event("DELAYED [" + str(time_taken) + " m] Verification: " + token)
                
        return verified
    except Exception as err:
        print("Could not check verification status on "+ token)
        traceback.print_exc()

async def check_if_sellable(web3, router_address, hex, pair, owner):
    #Min numbers of buyers to check, and how many attempts do you want to try
    minimum_successes = 3 #Minimum of 3 unique Sellers
    minimum_new_entries = 1
    max_attempts = 10
    attempt_delay = 5

    saved_buyer_count = 0
    saved_seller_count = 0

    new_transfer_delay = 5
    max_monitoring_time = 10 * 60 # 10 minutes

    buy_addresses = {}
    sell_addresses = {}

    owner_address = web3.to_checksum_address(owner)
    pair_address = web3.to_checksum_address(pair)
    token_address = web3.to_checksum_address(hex)
    token_abi = get_contract_abi_bnb(hex) # TODO - CHILLIEMAN - MAKE THIS ETH!!!!!
    token_contract = web3.eth.contract(token_address, abi=token_abi)
    block_number_to_check = web3.eth.block_number - 500 #Check 500 blocks for existing transfers
    transfer_filter = token_contract.events.Transfer.create_filter(fromBlock=block_number_to_check) 
    for transfer in transfer_filter.get_all_entries():
        from_address = web3.to_checksum_address(transfer['args']['from'])
        to_address = web3.to_checksum_address(transfer['args']['to'])
        if to_address == owner_address or from_address == owner_address:
            print(hex + " Owner Activity detected. Doesnt Count!")
            continue
        elif to_address == router_address or from_address == router_address:
            print(hex + " Router Activity detected. Doesnt Count!")
            continue
        elif to_address == pair_address:
            print("Seller! " + str(from_address))
            sell_addresses[str(from_address)] = "BOOM"
        elif from_address == pair_address:
            print("Buyer!"+ str(to_address))
            buy_addresses[str(to_address)] = "BOOM"

    starting_buyers = len(buy_addresses)
    starting_sellers = len(sell_addresses)
    print("[{}] Starting Buyers: {}".format(token_address, starting_buyers))
    print("[{}] Starting Sellers: {}".format(token_address, starting_sellers))

    attempts = 0
    success_count = 0
    while attempts != max_attempts:
        attempts = attempts + 1
        saved_seller_count = starting_sellers
        saved_buyer_count = starting_buyers

        #Wait around for a minute or two for approvals
        new_entry_counter = 0
        new_entry_delay = 2
        end_time = time.time() + max_monitoring_time
        while new_entry_counter < minimum_new_entries:
            if time.time() > end_time:
                print(hex + " Nothing is going on this going on after awhile... Giving up")
                return False
            
            try:
                for transfer in transfer_filter.get_new_entries():
                    from_address = web3.to_checksum_address(transfer['args']['from'])
                    to_address = web3.to_checksum_address(transfer['args']['to'])
                    if to_address == owner_address or from_address == owner_address:
                        print(hex + "This one doesnt count, its from the owner")
                        continue
                    elif to_address == router_address or from_address == router_address:
                        print(hex + "New Router Activity detected. Doesnt Count!")
                        continue
                    elif to_address == pair_address:
                        print(hex + " Seller! " + str(from_address))
                        sell_addresses[str(from_address)] = "BOOM"
                    elif from_address == pair_address:
                        print(hex + " Buyer ! "+ str(to_address))
                        buy_addresses[str(to_address)] = "BOOM"
                    
                    current_buyers = len(buy_addresses)
                    current_sellers = len(sell_addresses)

                    if current_buyers > saved_buyer_count:
                        saved_buyer_count = current_buyers
                        new_entry_counter = new_entry_counter + 1

                    elif current_sellers > saved_seller_count:
                        saved_seller_count = current_sellers
                        new_entry_counter = new_entry_counter + 1
            except:
                traceback.print_exc()
                transfer_filter = token_contract.events.Transfer.create_filter(fromBlock='latest')
            await asyncio.sleep(new_entry_delay)

        if new_entry_counter < minimum_new_entries:
            if attempts == max_attempts:
                raise Exception("Not enough Buyers to see if this is a scam")

        # Checking for New Sellers!

        
        ending_buyers = len(buy_addresses)
        ending_sellers = len(sell_addresses)
        print("[{}] Buyers: {} - Sellers: {}".format(token_address, ending_buyers, ending_sellers))

        if attempts == 1:
            if starting_sellers >= minimum_successes:
                print(hex + " Awesome! There are already " + str(minimum_successes) + " unique sellers! -BUYY")
                return True
            
            if starting_sellers > 0:
                print(hex + " Starting with " + str(starting_sellers) + " sellers!")
            else:
                print(hex + " No Sellers Found yet!")
            success_count = starting_sellers
        elif ending_sellers > starting_sellers:
            print(hex + " Nice, more sellers than you started with!")
            success_count = success_count + ending_sellers
            if success_count >= minimum_successes:
                return True
        elif attempts == max_attempts:
            return False
        
        starting_sellers = ending_sellers
        starting_buyers = ending_buyers
        await asyncio.sleep(attempt_delay)


async def is_worth_buying(web3, router_address, token, pair_address, owner_address):
    print("Token " + str(token) + " ... Pair: " + str(pair_address))
    print("Token " + str(token) + " ... Owner: " + str(owner_address))
    # TODO: Add a check of holdings. Make sure UniSwap holds most tokens 
    # - Owner should NOT have a huge amount (above 10%)
    # - Check the Common Burn Addresses for percentages (0x0, 0xdead, 0x1)

    # TODO: specific HoneyPots: Check for function() in Token contract
    try:
        
        if await check_if_sellable(web3, router_address, token, pair_address, owner_address):
            #Its Sellable!
            return True
        # TODO - Check if its Symbol is correct?
        
        return False
    except Exception as e:
        print("Cant say this is worth buying!\n")
        # TODO - Add to not wor
        traceback.print_exc()
        return False

#TODO: Make this function faster and use less checks
async def estimate_sell_tax(web3, router, token, token_sell_amount, estimated_sale):
    print(token + " Checking Sales Tax...")
    print(token + " Tokens to sell: " + str(token_sell_amount))

    #TODO: Make this function faster and use less checks
    tax_increment = 5
    current_tax = 0
    found_limit = False
    sell_tax_delay = .1

    while True:
        try:
            min = Decimal(estimated_sale) * Decimal(1 - (current_tax / 100))
            min_receive_amount = web3.to_wei(min,'ether')
            pancakeswap2_txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                token_sell_amount,
                min_receive_amount, #Minimum amount of BNB to receive
                [token, WETH],
                CHILLIEMAN,
                (int(time.time()) + 1000000)
                ).build_transaction({
                'from': CHILLIEMAN,
                'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
                'nonce': web3.eth.get_transaction_count(CHILLIEMAN),
                })

            found_limit = True
            if current_tax == 0:
                return 0
            else:
                current_tax = current_tax - 1
        except exceptions.ContractLogicError as contract_error:
            if str(contract_error).find('TRANSFER_FROM_FAILED') != -1:
                print(token + "Cannot Estimate! - TRANSFER_FROM_FAILED... FK")
                return -1
            elif str(contract_error).find('INSUFFICIENT_OUTPUT_AMOUNT') != -1:
                if not found_limit:
                    current_tax = current_tax + tax_increment
                else:
                    return current_tax + 1
            elif str(contract_error).find('INSUFFICIENT_INPUT_AMOUNT') != -1:
                print(token + "Cannot Estimate! - INSUFFICIENT_INPUT_AMOUNT... FK")
                return -2
            else:
                traceback.print_exc()
        except Exception as e:
            print(token + " Unexpected problem trying to Estimate Taxes.")
            traceback.print_exc()
        
        await asyncio.sleep(sell_tax_delay)


#Returns success status of whether tokens were able to be sold
async def sell_tokens(web3, router, token, percentage_to_sell):
    if percentage_to_sell < 0 or percentage_to_sell > 1:
        raise Exception("[sell_tokens] - You must enter a percentage between 0 and 1")

    token_address = web3.to_checksum_address(token)
    token_contract = web3.eth.contract(token_address, abi=BALANCE_ABI)
    total_gas_used = 0 # If the first transaction fails, or you needed to approve, then keep track of the gas spent.

    #Get Token Balance
    balance = token_contract.functions.balanceOf(CHILLIEMAN).call()
    print(token_address + " Balance: " + str(balance))

    if balance == 0:
        print(token_address + " has a 0 balance =[")
        raise Exception("No Balance")

    #Amount of token to sell
    amount_of_tokens_to_sell = floor(Decimal(balance) * Decimal(percentage_to_sell))
    print(token_address + " Selling: " + str(amount_of_tokens_to_sell))

    initial_allowance_amount = token_contract.functions.allowance(CHILLIEMAN, UNI_ROUTER_ADDRESS).call()
    if initial_allowance_amount == 0:
        #No Allowance! - Check the database to see if you have ever requested to unlock allowance for UniSwap.
        if is_allowance_already_requested(token_address):
            print("No allowance, and the Database claims you have already requested it... Check again in a minute?")
            raise Exception("No allowance, but already requested it.")
        max_amount = web3.to_wei(2**64-1,'ether')

        attempts = 0
        success = False
        allowance_delay = 0.5
        while attempts < 10:
            attempts = attempts + 1

            try:
                #Approve Token so we can Sell
                approval_tx = token_contract.functions.approve(UNI_ROUTER_ADDRESS, max_amount).build_transaction({
                    'from': CHILLIEMAN,
                    'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
                    'nonce': web3.eth.get_transaction_count(CHILLIEMAN),
                    })

                gas_estimation = web3.eth.estimate_gas(approval_tx)
                estimate = gas_estimation * 5 
                total_gas_used = web3.from_wei(estimate, 'gwei')
                approval_signed_txn = web3.eth.account.sign_transaction(approval_tx, private_key=WALLET_PRIVATE_KEY)
                approval_tx_token = web3.eth.send_raw_transaction(approval_signed_txn.rawTransaction)
                success = True
                break
            except ValueError as err:
                args = err.args[0]
                error = args['code']
                message = args['message']
                if int(error) == -32000 and str(message).find('nonce too low') != 1:
                    print("Approval: nonce too low.")
                else:
                    traceback.print_exc()
            except:
                traceback.print_exc()
            await asyncio.sleep(allowance_delay)
        
        if not success:
            raise Exception(token_address + " Could not send approval after many attempts....")

        monitory_delay = 1 # Check for transaction success every second
        monitor_time = 3 * 60 # Monitor for 2 minutes
        right_now = time.time()
        end_time = right_now + monitor_time
        success = False
        while time.time() < end_time:
            try:
                receipt = web3.eth.get_transaction_receipt(approval_tx_token)
                receipt_string = web3.to_json(receipt)
                print(receipt_string)
                receipt_json = json.loads(receipt_string)
                if int(receipt_json['status']) == 0:
                    break
                else:
                    success = True
                    insert_allowance_request(token_address)
                    break
            except exceptions.TransactionNotFound as err:
                0 # Could not find Transaction. This is normal... DO nothing
            except Exception as err:
                print("Unexpected Error!")
                traceback.print_exc()

            await asyncio.sleep(monitory_delay)

        if not success:
            raise Exception(token_address + " We could not approve selling the token....")


    print("UniSwap can trade token for you!")
    estimated_sale = calc_sell(router, token_address, amount_of_tokens_to_sell)
    if estimated_sale == 0:
        raise Exception(token_address + " Cannot estimate Sale... Gr")

    estimated_tax = await estimate_sell_tax(web3, router, token_address, amount_of_tokens_to_sell, estimated_sale)

    if estimated_tax == -1:
        #Cannot Sell Token.... TRANSFER_FROM_FAILED
        insert_honeypot(token_address)
        raise Exception("Fucking Honeypot...")
    elif estimated_tax == -2:
        #Cannot Sell Token.... TRANSFER_FROM_FAILED
        insert_zero_balance(token_address)
        raise Exception("Not enough to sell, but not zero balance...")
        
    print("Time to sell!!")

    success = False
    sell_sleep = 1.25
    attempts = 0
    max_attempts = 10
    while attempts < max_attempts and not success:
        attempts = attempts + 1
        try:
            txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                amount_of_tokens_to_sell,
                0, #Minimum amount of BNB to receive
                [token_address, WETH],
                CHILLIEMAN,
                (int(time.time()) + 1000000)
                ).build_transaction({
                'from': CHILLIEMAN,
                'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
                'nonce': web3.eth.get_transaction_count(CHILLIEMAN),
                })

            gas_estimation = web3.eth.estimate_gas(txn)
            estimate = gas_estimation * 5 
            gas_estimation_in_bnb = web3.from_wei(estimate, 'gwei')
            total_gas_used = total_gas_used + gas_estimation_in_bnb
            total_estimation = estimated_sale * (1 - Decimal(estimated_tax) / 100) - total_gas_used
            tax_estimation = estimated_sale * (Decimal(estimated_tax) / 100)
            print(token + " Estimated Sale : " + str(estimated_sale))
            print(token + " Estimated Tax  : " + str(tax_estimation))
            print(token + " Sale After Tax : " + str(estimated_sale * (1 - Decimal(estimated_tax) / 100)))
            print(token + " Estimated Gas  : " + str(total_gas_used))
            print(token + " Estimated Total: " + str(total_estimation))

            if total_estimation <= 0:
                raise Exception("Selling this token would lose money...")

            signed_txn = web3.eth.account.sign_transaction(pancakeswap2_txn, private_key=WALLET_PRIVATE_KEY)
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

            print("Sent the Sell order! Time to wait for the response!")
            #Wait for the Response... Did it go through?
            monitory_delay = 2 # Check for transaction success every couple of seconds
            monitor_time = 3 * 60 # Monitor for 3 minutes
            right_now = time.time()
            end_time = right_now + monitor_time
            while time.time() < end_time:
                try:
                    receipt = web3.eth.get_transaction_receipt(tx_token)
                    receipt_string = web3.to_json(receipt)
                    # print(receipt_string)
                    receipt_json = json.loads(receipt_string)
                    if int(receipt_json['status']) == 0:
                        print("Not Successful Selling ;[" + token_address)
                        return False
                    else:
                        #TODO: Fetch actual Gas used
                        # receipt_json['gasUsed']
                        print("Sold Successfully!!" + token_address)
                        insert_sale(str(token_address), str(estimated_sale), str(total_gas_used), str(tax_estimation))
                        return True
                except exceptions.TransactionNotFound as err:
                    0 # Could not find Transaction. This is normal... DO nothing
                except Exception as err:
                    print("Unexpected Error!")
                    traceback.print_exc()
                    break

                await asyncio.sleep(monitory_delay)

        except exceptions.ContractLogicError as contract_error:
            if str(contract_error).find('TRANSFER_FROM_FAILED') != -1:
                print(token + "Cannot Sell =[ - TRANSFER_FROM_FAILED")
            elif str(contract_error).find('INSUFFICIENT_OUTPUT_AMOUNT') != -1:
                print(token + " Cannot Sell =[ - INSUFFICIENT_OUTPUT_AMOUNT")
            else:
                print("Unexpected error!")
                traceback.print_exc()
        except ValueError as err:
            args = err.args[0]
            error = args['code']
            message = args['message']
            if int(error) == -32000 and str(message).find('nonce too low') != 1:
                print("Selling: nonce too low.")
                total_gas_used = total_gas_used - gas_estimation_in_bnb
            else:
                traceback.print_exc()
        except Exception as e:
            if str(e).find('Selling this token would lose money') != 1:
                raise e
            else:
                print("Problem trying to Sell Tokens.")
                traceback.print_exc()

        await asyncio.sleep(sell_sleep)

    raise Exception(token_address + "Reached end of sell_tokens, but never sold")
