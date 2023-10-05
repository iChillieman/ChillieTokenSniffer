chillie_Sniffer.py

chillie_buyer.py
- Responsible for finding New Tokens to Snipe

chillie_seller.py
- Responsible for observing Bought Tokens (Keep checking the price) - And wait for an optimal time to sell

chillie_analyze.py
- Responsible for Checking OLD tokens that might not be worth buying - It checks DBz for Tokens that have been previously been bought, and probably need to be reconsidered for Sale.

chillie_garbage.py
- Responsible for Checking OLD tokens that have previously been deemed as Garbage - and probably need to be reconsidered for Sale. (These Tokens were previously regarded as HoneyPots, but already purchased)
