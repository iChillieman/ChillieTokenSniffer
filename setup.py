from web3 import Web3
from chillie_db import create_tables, db_insert_ready_to_watch, remove_watching, temp

create_tables()
# temp()
# token = Web3.to_checksum_address('0XE70601CEBEBBF78A5DC658E659DDAE29CEC6AECF')
# db_insert_ready_to_watch(token)

# remove_watching('0x5D10780da28E5B225A0C6a1BeD230a04cF96ece3')
# remove_watching('0XE70601CEBEBBF78A5DC658E659DDAE29CEC6AECF')
# remove_watching('0xe70601cEBEBbF78a5dC658E659Ddae29cEc6AeCf')