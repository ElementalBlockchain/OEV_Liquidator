from tools import *
from oev import OEV
from thegraph import fetchV2UnhealthyLoans, getLivePriceValue

# https://goerli.etherscan.io/address/0x4152465e8a592a8b4d2c74141d8a0013895a15fc

class Execution:
    def __init__(self, web3, account, fl_address, minimum_bid, wrapped_token):
        self.name = self.__class__.__name__
        self.web3 = web3
        self.account = account
        self.unhealthy_loans = fetchV2UnhealthyLoans()

        self.auctions = {}
        self.user_bids = {}
        self.completed = {}

        self.wrapped_token = wrapped_token
        self.native_price = getLivePriceValue(wrapped_token, 1*10 ** 18)
        print(f"Native Network Token Price: {self.native_price}")
        self.minimum_bid = int(minimum_bid)

        fl_abi = json.loads(open('./contracts/storage/flashLoanReceiver_abi.json').read())
        self.flashloanreciver = load_contract(self.web3, fl_address, fl_abi)
        self.oev = OEV(web3)
        self.multicall = load_contract(web3, os.getenv("MULTICALL"), open("./contracts/storage/OevSearcherMulticallV1_abi.json").read())

        self.ofile = open("log.txt", "a")
        self.ofile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Starting Execution.py " + '\n')

    def update_loans(self):
        print(f'(updating loan data)')
        try:
            self.unhealthy_loans = fetchV2UnhealthyLoans()
        except:
            print(f'an error occurred, most likely an HTTP call to the subgraph. loop will continue without updated loans')
        try:
            native_price = getLivePriceValue(self.wrapped_token, 1*10 ** 18) # update execution's native network token price each loop
            if native_price != self.native_price:
                self.native_price = native_price
                print(f'(native network token price updated: {self.native_price:.4f})')
                time.sleep(15)
        except:
            print(f'an error occurred, most likely an HTTP call to the pricing source. loop will continue without updating native token price')
        temp = self.completed.items()
        for user, timestamp in temp:
            if int(time.mktime(datetime.datetime.now().timetuple())) - timestamp > 600:
                del self.completed[user]
                print(f'user {user} was liquidated {int(time.mktime(datetime.datetime.now().timetuple())) - timestamp} ago, flushing from completion queue.')

    def profit_potential(self, loan):
        if loan.totalCollateralInUSD > loan.totalBorrowInUSD: # use this when live to ensure profitability
            # if oracle_value() > loan.liquidationPrice: # this ensures you  aren't bidding on loans with a health factor less than 1
                return ((float(loan.collateralReserve[0][2])/10**18)*loan.liquidationPrice) - loan.totalBorrowInUSD
        else:
            return 0

    def place_bids(self):
        print(f'(checking loans)')
        for loan in self.unhealthy_loans:
            if loan.user in self.user_bids.keys():
                print(f'bid for {self.auctions[self.user_bids[loan.user]].liquidationPrice} already placed for user: {loan.user}, TWAVE: {oracle_value()}')
                continue
            # TODO this is here because there is no WETH/USDC pool on goerli  :::::::::::
            if loan.collateralReserve[0][0] == "WETH":
                break
            # TODO this is here because there is no WETH/USDC pool on goerli   ^^^^^^^^^
            if loan.totalCollateralInUSD > loan.totalBorrowInUSD:
                profit_potential = self.profit_potential(loan)
                if profit_potential > 0:
                    bid_amount = ((profit_potential * 0.05) / self.native_price ) * 10**18 # bidding half of the potential profit in native tokens for the update
                    if bid_amount < self.minimum_bid: # if that ends up being lower than the minimum bid then set to minimum bid
                        bid_amount = self.minimum_bid
                        profit_potential = profit_potential - ((self.minimum_bid/10**18)*self.native_price) # if using min bid, factor it into profit potential
                    if profit_potential > 0 and loan.liquidationPrice > 1:
                        print("")
                        print(f'User {loan.user} liquidation information:')
                        bid = self.oev.place_bid(self.account, self.flashloanreciver.address, bid_amount=int(bid_amount), oracle_value=int(loan.liquidationPrice * 10 ** 18), dAppProxyAddress=dapp_proxy_address(loan.collateralReserve[0][0]), dAppProxyChainId=web3.eth.chain_id)
                        if bid:
                            print(f"\tCollateral Token: {loan.collateralToken}, Borrow Token: {loan.borrowToken}")
                            print(f"\tLiquidation Price: {loan.liquidationPrice:.4f}, Total Collateral In USD: {loan.totalCollateralInUSD:.4f}")
                            print(f"\tTotal Borrow In USD: {loan.totalBorrowInUSD:.4f}, Health Factor: {loan.healthFactor / 10 ** 18}")
                            print(f'\tprofit potential: {profit_potential}, bid amount: {int(bid_amount)/10**18}')
                            print(f'\tbid {bid} on ${loan.liquidationPrice} {loan.collateralReserve[0][0]}, TWAVE current price: {oracle_value()}')
                            self.auctions[bid["id"]] = loan
                            self.user_bids[loan.user] = bid["id"]
                            self.ofile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} placed bid: {bid['id']}" + '\n')
                        else:
                            continue
                else:
                    print(f'\tthe profit potential is {profit_potential} USD, no bid placed: {loan}')

    def check_winners(self):
        print(f'(checking oev endpoint for auctions won)')
        wins = self.oev.winning_bids(self.account)
        if wins:
            print(f'(found won auctions: {wins["winningBidIds"]})')
            for auction in [x for x in wins['winningBidIds'] if x in self.auctions.keys()]:
                try:
                    loan = self.auctions[auction]
                    if loan.user in self.completed.keys():
                        print(f'user: {loan.user} was liquidated {int(time.mktime(datetime.datetime.now().timetuple())) - self.completed[loan.user]} seconds ago, skipping...')
                        continue
                    print(f'liquidating user: {loan.user}')
                    loan_amount = None
                    for item in loan.borrowReserve:
                        if item[1] == loan.borrowToken:
                            loan_amount = int(item[2])
                    encodedUpdateTransaction = wins["encodedUpdateTransaction"]
                    nativeCurrencyAmount = int(wins["nativeCurrencyAmount"])

                    # USING FL RECEIVER MULTICALL
                    updatePrice_function = self.flashloanreciver.functions.updatePrice([os.getenv("Api3ServerV1")], [encodedUpdateTransaction], [nativeCurrencyAmount])
                    tx_params = get_tx_params(web3=self.web3, account=account, value=nativeCurrencyAmount, gas=1000000)
                    function = updatePrice_function.buildTransaction(tx_params)
                    if replay_tx(web3, function) is True:
                        args = ([os.getenv("Api3ServerV1")], [encodedUpdateTransaction], [nativeCurrencyAmount], [Web3.toChecksumAddress(loan.borrowToken)], [loan_amount], [0], Web3.toChecksumAddress(loan.collateralToken) + Web3.toChecksumAddress(loan.user).replace("0x", ""))
                        doLiquidation_function = self.flashloanreciver.functions.doLiquidation(*args)
                        tx_params = get_tx_params(web3=web3, account=self.account, value=nativeCurrencyAmount, gas=1000000)
                        function = doLiquidation_function.buildTransaction(tx_params)
                        if replay_tx(web3, function) is True:
                            tx = build_and_send_and_wait(web3, self.account, doLiquidation_function, tx_params)
                            if tx:
                                print(f'LIQUIDATION: price update and liquidation multicall submitted: {tx}')
                                del self.auctions[auction]
                                del self.user_bids[loan.user]
                                self.completed[loan.user] = int(time.mktime(datetime.datetime.now().timetuple()))
                                self.ofile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} multicall submitted: {tx}" + '\n')
                            else:
                                print(f'price update and liquidation multicall submitted and failed: {tx}')
                        else:
                            self.auction_failure("multicall simulation", replay_tx(web3, function))
                    else:
                        self.auction_failure("price update simulation", replay_tx(web3, function))
                except KeyError:
                    self.auction_failure("liquidation", KeyError)
                except Exception as e:
                    self.auction_failure("liquidation", e)

    def auction_failure(self, location, function):
        self.ofile.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {location} fail: {function}" + '\n')
        print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {location} fail: {function}" + '\n')


async def update_loans(executor):
    print(f'(starting loop to keep loan database updated)')
    time.sleep(180)
    while True:
        executor.update_loans()
        time.sleep(180)

async def bidder_loop(executor):
    print(f'(starting loop to place bids if an opportunity is found)')
    while True:
        executor.place_bids()
        time.sleep(60)

async def settlement_loop(executor):
    print(f'(starting loop to settle any possible liquidations)')
    while True:
        executor.check_winners()
        time.sleep(60)

if __name__ == "__main__":
    web3 = Web3(HTTPProvider(endpoint_uri=os.getenv("RPC"), request_kwargs={'timeout': 100}))
    account = web3.eth.account.from_key(os.getenv("PRIV_KEY"))
    secondary_account = from_mnemonic()
    executor = Execution(web3, account, os.getenv("FL_ADDRESS"), os.getenv("MIN_BID"), os.getenv("WRAPPED_NETWORK_TOKEN"))

    def first_thread_tasks():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(update_loans(executor))
        loop.run_forever()
    t1 = Thread(target=first_thread_tasks)
    t1.start()

    def second_thread_tasks():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(bidder_loop(executor))
        loop.run_forever()
    t2 = Thread(target=second_thread_tasks)
    t2.start()

    def third_thread_tasks():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(settlement_loop(executor))
        loop.run_forever()
    t2 = Thread(target=third_thread_tasks)
    t2.start()
