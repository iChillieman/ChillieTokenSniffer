import asyncio
from decimal import Decimal
import json
from math import floor
import traceback
from web3 import Web3, exceptions
from web3.middleware import geth_poa_middleware
from chillie_db import insert_allowance_request, is_allowance_already_requested
from chillie_util import PRICE_ABI, calc_sell, get_contract_abi
import config
import time

bsc = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(bsc))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

print(web3.is_connected())


#pancakeswap router
router_address = '0x10ED43C718714eb63d5aA57B78B54704E256024E'
panabi = get_contract_abi(router_address)
router = web3.eth.contract(address=router_address, abi=panabi)

me = web3.to_checksum_address(config.WALLET_ADDRESS)


#Get BNB Balance
balance = web3.eth.get_balance(me) 
balance_readable = web3.from_wei(balance,'ether')
print("Balance: " + str(balance_readable))
 






def check_past_approvals(hex):
    approved_addresses = {}
    token_address = web3.to_checksum_address(hex)
    token_abi = get_contract_abi(hex)
    token_contract = web3.eth.contract(token_address, abi=token_abi)
    block_number_to_check =  web3.eth.block_number - 4900 #Check 100 blocks for approvals
    event_filter = token_contract.events.Approval.create_filter(fromBlock=block_number_to_check)
    for approval in event_filter.get_all_entries():
        owner = web3.to_checksum_address(approval['args']['owner'])
        spender = web3.to_checksum_address(approval['args']['spender'])
        if spender == router_address:
            approved_addresses[str(owner)] = "BOOM"
            # print(owner)
            # print('-------')
    list_to_return = []

    for key in approved_addresses.keys():
        list_to_return.append(key)
        print(key)

    return list_to_return
    

def test_sell(hex):
    token_address = web3.to_checksum_address(hex)
    token_abi = get_contract_abi(hex)
    token_contract = web3.eth.contract(token_address, abi=token_abi)

    current_approved_holders = []
    approved_attempts = 0

    while approved_attempts != 5:
        current_approved_holders = check_past_approvals(hex)
        if len(current_approved_holders) > 3:
            print("Time to test!")
            break
        else:
            print("Cant Test Sell [" + hex + "] Not enough approved wallets: Only " + str(len(current_approved_holders)))
            time.sleep(10)
        approved_attempts = approved_attempts + 1


    can_trade = 0
    cannot_trade = 0
    for approved_account in current_approved_holders:
        print("Checking " + approved_account)
        owner = web3.to_checksum_address(approved_account)
        try:
            owner_balance = token_contract.functions.balanceOf(owner).call()
            if owner_balance == 0:
                print("Zero Balance")
                continue 
            pancakeswap2_txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                        owner_balance,
                        0, #Minimum amount of BNB to receive
                        [token_address, wbnb],
                        owner,
                        (int(time.time()) + 1000000)

                        ).build_transaction({
                        'from': owner,
                        'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
                        'nonce': web3.eth.get_transaction_count(owner),
                        })
            print(owner + " can sell")
            can_trade = can_trade + 1
        except exceptions.ContractLogicError as contract_error:
            if str(contract_error).find('TRANSFER_FROM_FAILED') != -1:
                print(owner + " got scammed")
                cannot_trade = cannot_trade + 1
            else:
                print(contract_error)

    print("Can Sell: " + str(can_trade))
    print("Can Not:  " + str(cannot_trade))
    if can_trade > cannot_trade:
        print("You should buy this")
        return True
    else:
        print("Doesnt look good!")
        return False

            
            




unowned_hex = '0x655c37f3cd32fada9aa67b8e92791a5a7da35ad8'
# sell_tokens(unowned_hex)

blocked_hex = '0x83ed641efe5bc4703c1b96a6ee39a569e97ed5d9'
# sell_tokens(bad_hex)

valid_hex = '0X9F82AFF7F13BB2DFED444539C7C76FC5030B1EF1'
# sell_tokens(valid_hex)


# test_sell(valid_hex)
# test_sell(unowned_hex)
# test_sell(unowned_hex)

sell_tokens(valid_hex)
