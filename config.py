from web3 import Web3

# TODO - CHILLIEMAN - MAKE THIS ETH!!!!! (check_if_sellable)


WALLET_PRIVATE_KEY = 'WALLET_PRIVATE_KEY'
WALLET_ADDRESS = 'WALLET_ADDRESS'
BSC_SCAN_API_KEY= 'BSC_SCAN_API'
ETHER_SCAN_API_KEY = 'ETH_SCAN_API'

#What Router will be used? (This is UniSwaps V2 router)
UNI_ROUTER_ADDRESS = Web3.to_checksum_address('0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D')
#WETH = Web3.to_checksum_address('0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2') # This is WETH (Ethereum)
WETH = Web3.to_checksum_address('0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c') # This is WBNB (Binance)
#How much ETH do you want to spend on each Token?
TRANSACTION_AMOUNT = 0.01

# Do you want to actually trigger a buy, or just Sniffing the blockchain??
IS_BUYING_ENABLED = False

# What gas price would you like to estimate with? (Check https://etherscan.io/gastracker [High])
ESTIMATE_GAS_PRICE = '50'

#If you only want to buy a certain token Symbol: (TODO - Chillieman - Implement this)
IS_ONLY_BUY_SYMBOLS = False
ONLY_BUY_SYMBOLS = ['PEPE', "WOJAK"]
