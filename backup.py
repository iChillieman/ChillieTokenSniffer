# async def check_if_honeypot_2(hex, owner_address):
#     #Min numbers of buyers to check, and how many attempts do you want to try
#     minimum_successes = 3
#     minimum_new_entries = 1
#     max_attempts = 15
#     attempt_delay = 10

#     saved_buyer_count = 0

#     new_approval_delay = 2
#     max_monitoring_time = 5 * 60 # 5 minutes

#     print("Checking if " + hex + " for Honeypot...")
#     approved_addresses = {}

#     owner_address = web3.to_checksum_address(owner_address)
#     token_address = web3.to_checksum_address(hex)
#     token_abi = get_contract_abi(hex)
#     token_contract = web3.eth.contract(token_address, abi=token_abi)
#     block_number_to_check = web3.eth.block_number - 1000 #Check 100 blocks for approvals
#     approval_filter = token_contract.events.Approval.create_filter(fromBlock=block_number_to_check) 
#     for approval in approval_filter.get_all_entries():
#         owner = web3.to_checksum_address(approval['args']['owner'])
#         spender = web3.to_checksum_address(approval['args']['spender'])
#         if spender == router_address and owner != owner_address:
#             approved_addresses[str(owner)] = "BOOM"


#     can_trade = 0
#     cannot_trade = 0
#     zero_balance = 0
#     for approved_account in approved_addresses.keys():
#         owner = web3.to_checksum_address(approved_account)
#         try:
#             owner_balance = token_contract.functions.balanceOf(owner).call()
#             if owner_balance == 0:
#                 zero_balance = zero_balance + 1
#                 continue 
#             pancakeswap2_txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
#                     owner_balance,
#                     0, #Minimum amount of BNB to receive
#                     [token_address, wbnb],
#                     owner,
#                     (int(time.time()) + 1000000)

#                     ).build_transaction({
#                     'from': owner,
#                     'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
#                     'nonce': web3.eth.get_transaction_count(owner),
#                     })
#             # print(owner + " can sell")
#             can_trade = can_trade + 1
#         except exceptions.ContractLogicError as contract_error:
#             if str(contract_error).find('TRANSFER_FROM_FAILED') != -1:
#                 # print(owner + " got scammed")
#                 cannot_trade = cannot_trade + 1
                
#             else:
#                 print("UNEXPECTED ERROR: " + str(contract_error))
#         except Exception as err:
#             print("Cannot check " + str(owner) + "\n" + str(err))

#     print(hex + " Can Sell: " + str(can_trade))
#     print(hex + " Can Not:  " + str(cannot_trade))
#     print(hex + " Zero Balances:  " + str(zero_balance))











#     attempts = 0
#     success_count = 0
#     while attempts != max_attempts:
#         attempts = attempts + 1
#         saved_seller_count = starting_sellers
#         saved_buyer_count = starting_buyers

#         #Wait around for a minute or two for approvals
#         new_entry_counter = 0
#         end_time = int(time.time()) + max_monitoring_time
#         while new_entry_counter < minimum_new_entries and int(time.time()) < end_time:
#             for approval in approval_filter.get_new_entries():
#                 from_address = web3.to_checksum_address(approval['args']['from'])
#                 to_address = web3.to_checksum_address(approval['args']['to'])
#                 if to_address == owner_address or from_address == owner_address:
#                     # print("This one doesnt count, its from the owner")
#                     continue
#                 elif to_address == pair_address:
#                     # print(hex + " Seller! " + str(from_address))
#                     sell_addresses[str(from_address)] = "BOOM"
#                 elif from_address == pair_address:
#                     # print(hex + " Buyer ! "+ str(to_address))
#                     buy_addresses[str(to_address)] = "BOOM"
                
#                 current_buyers = len(buy_addresses)
#                 current_sellers = len(sell_addresses)

#                 if current_buyers > saved_buyer_count:
#                     saved_buyer_count = current_buyers
#                     new_entry_counter = new_entry_counter + 1

#                 elif current_sellers > saved_seller_count:
#                     saved_seller_count = current_sellers
#                     new_entry_counter = new_entry_counter + 1

#             if new_entry_counter < minimum_new_entries:
#                 await asyncio.sleep(new_approval_delay)

#         if new_entry_counter < minimum_new_entries:
#             if attempts == max_attempts:
#                 raise Exception("Not enough Buyers to see if this is a scam")

#         # Checking for New Sellers!

#         ending_buyers = len(buy_addresses)
#         ending_sellers = len(sell_addresses)

#         if starting_buyers == 0:
#             starting_buy_ratio = 0
#         else:
#             starting_buy_ratio = Decimal(starting_sellers) / Decimal(starting_buyers)

#         if ending_buyers == 0:
#             ending_buy_ratio = 0
#         else:
#             ending_buy_ratio = Decimal(ending_sellers) / Decimal(ending_buyers)

#         # print(hex + " Starting Buyers : " + str(starting_buyers))
#         # print(hex + " Ending Buyers   : " + str(ending_buyers))

#         # print(hex + " Starting Sellers: " + str(starting_sellers))
#         # print(hex + " Ending Sellers  : " + str(ending_sellers))

#         # print(hex + " Starting Ratio: " + str(starting_buy_ratio))
#         # print(hex + " Ending Ratio  : " + str(ending_buy_ratio))

#         #Once the amount of people who CANT sell stays the same, and people who CAN sell increases, its time to buy!

#         if starting_sellers == 0:
#             starting_sellers = ending_sellers
#             starting_buyers = ending_buyers
#             if attempts == max_attempts:
#                 raise Exception("Not enough Sellers")
#             continue
#         elif ending_sellers > starting_sellers:
#             print(hex + " Nice, more sellers than you started with!")
#             success_count = success_count + 1
#             if success_count >= minimum_successes:
#                 return True
#         elif attempts == max_attempts:
#             return False
        
#         starting_sellers = ending_sellers
#         starting_buyers = ending_buyers
#         await asyncio.sleep(attempt_delay)



# # Returns True if this is a honeypot
# # Checks for TRANSFER_FROM_FAILED Scam
# async def check_if_honeypot(hex, owner_address):
#     #Min numbers of wallets to check, and how many attempts do you want to try
#     token_owner = web3.to_checksum_address(owner_address)
#     minimum_number_wallets_default = 5
#     minimum_number_wallets = minimum_number_wallets_default
#     max_approval_attempts = 3
#     attempt_delay = 30 # 30 seconds to try again

#     new_approval_delay = 10
#     max_monitoring_time = 5 * 60

#     print("Checking if " + hex + " is a honeypot...")
#     approved_addresses = {}
#     token_address = web3.to_checksum_address(hex)
#     token_abi = get_contract_abi(hex)
#     token_contract = web3.eth.contract(token_address, abi=token_abi)
#     block_number_to_check = web3.eth.block_number - 2000 #Check 100 blocks for approvals
#     approval_filter = token_contract.events.Approval.create_filter(fromBlock=block_number_to_check) 
#     for approval in approval_filter.get_all_entries():
#         owner = web3.to_checksum_address(approval['args']['owner'])
#         spender = web3.to_checksum_address(approval['args']['spender'])
#         if spender == router_address and owner != token_owner:
#             approved_addresses[str(owner)] = "BOOM"
#             # print(owner)
#             # print('-------')
#     approval_list = []

#     for key in approved_addresses.keys():
#         approval_list.append(key)

#     if len(approval_list) < minimum_number_wallets:
#         print("[" + str(len(approval_list)) + "] Have to watch for approval list on " + hex)

#     approval_attempts = 0
#     while approval_attempts != max_approval_attempts:
#         approval_attempts = approval_attempts + 1
#         #Wait around for a minute or two for approvals
#         end_time = int(time.time()) + max_monitoring_time
#         while len(approval_list) < minimum_number_wallets and int(time.time()) < end_time:
#             for approval in approval_filter.get_new_entries():
#                 # print("New Approval!!")
#                 owner = web3.to_checksum_address(approval['args']['owner'])
#                 spender = web3.to_checksum_address(approval['args']['spender'])
#                 if spender == router_address and owner != token_owner:
#                     already_included = False
#                     for key in approved_addresses.keys():
#                         if key == str(owner):
#                             already_included = True
                    
#                     if not already_included:
#                         approved_addresses[str(owner)] = "BOOM"
#                         approval_list.append(str(owner))
#                         if len(approval_list) >= minimum_number_wallets:
#                             break
#             #Get new approvals every 5 seconds to check if its a honeypot
#             await asyncio.sleep(new_approval_delay)

#         if len(approval_list) < minimum_number_wallets:
#             if approval_attempts == max_approval_attempts:
#                 # print(hex + " Cannot Check if this is a honeypot, not enough approvals size: " + str(len(approval_list)))
#                 raise Exception("Not enought Wallets approved to check for honey pots after 3 attempts")
#             else:
#                 await asyncio.sleep(attempt_delay)
#                 continue
#         # else:
#         #     print("Got enough to check honeypot! " + hex)
#         # Minumum reached! Checking for honeypot!

#         can_trade = 0
#         cannot_trade = 0
#         zero_balance = 0
#         for approved_account in approval_list:
#             owner = web3.to_checksum_address(approved_account)
#             try:
#                 owner_balance = token_contract.functions.balanceOf(owner).call()
#                 if owner_balance == 0:
#                     zero_balance = zero_balance + 1
#                     continue 
#                 pancakeswap2_txn = router.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
#                         owner_balance,
#                         0, #Minimum amount of BNB to receive
#                         [token_address, wbnb],
#                         owner,
#                         (int(time.time()) + 1000000)

#                         ).build_transaction({
#                         'from': owner,
#                         'gasPrice': web3.to_wei(ESTIMATE_GAS_PRICE,'gwei'),
#                         'nonce': web3.eth.get_transaction_count(owner),
#                         })
#                 # print(owner + " can sell")
#                 can_trade = can_trade + 1
#             except exceptions.ContractLogicError as contract_error:
#                 if str(contract_error).find('TRANSFER_FROM_FAILED') != -1:
#                     # print(owner + " got scammed")
#                     cannot_trade = cannot_trade + 1
#                 else:
#                     print("UNEXPECTED ERROR: " + str(contract_error))
#             except Exception as err:
#                 print("Cannot check " + str(owner) + "\n" + str(err))

#         print(hex + " Can Sell: " + str(can_trade))
#         print(hex + " Can Not:  " + str(cannot_trade))
#         print(hex + " Zero Balances:  " + str(zero_balance))

#         if can_trade > cannot_trade and can_trade > 1:
#             if zero_balance >= can_trade:
#                 minimum_number_wallets = minimum_number_wallets + 1
#                 if approval_attempts == max_approval_attempts:
#                     raise Exception("Too many Zero Balances")
#             else:
#                 # print("You should buy this")
#                 return False
#         elif approval_attempts == max_approval_attempts:
#             # print("Doesnt look good, dont buy this...")
#             return True
#         elif approval_attempts == max_approval_attempts - 1:
#             #Last Chance... Clear the list for a fresh list - In for the endgame
#             approval_list = []
#             minimum_number_wallets = minimum_number_wallets_default - 1

#         minimum_number_wallets = minimum_number_wallets + 1
#         await asyncio.sleep(attempt_delay)
