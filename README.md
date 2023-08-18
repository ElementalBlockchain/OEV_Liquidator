# a Granary Finance liquidator bot for auctions using API3 OEV

This bot for Granary Finance will monitor open loans via the graph and submit OEV bids to update the price and liquidate!

1. Copy the env file to .env and fill out all the necessary information within it
2. Add token values to thegraph.py that have non-standard decimal values (ex. WBTC, USDC, GUSD)
3. Run the deployer.py script to deploy the smart contract, this will add FL_ADDRESS and MULTICALL to the .env
4. Go to the https://oev.api3.org/ frontend and deposit into the OEV Prepayment Depository
5. Run the bot using execution.py

