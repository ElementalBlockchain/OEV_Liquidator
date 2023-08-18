from tools import *

### configure tokens without 18 decimals here:
nonstandard_decimal_tokens = {"WBTC": 8, "fBTC": 18, "USDC": 6, "fUSDC": 18}
### fUSDC https://goerli.etherscan.io/token/0x45ad9d110a687b68ab06cb5bd6be2f9f72e101b5
def markets():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=20&page=1&sparkline=false&locale=en"
    response = requests.get(url).text
    data = json.loads(response)
    ids = {"WETH": 'ethereum', "fUSDC": "usd-coin", "fBTC": "bitcoin"}
    for item in data:
        ids[(item['symbol']).upper()] = item['id']
    return ids
market_data = markets()

def fetchV2UnhealthyLoans(theGraphURL="https://api.thegraph.com/subgraphs/name/0xfantommenace/goerli"):
    headers = {"Content-Type": "application/json"}

    query = """
    query {
      users(
        first: 1000
        skip: 0
        orderBy: id
        orderDirection: desc
        where: {borrowedReservesCount_gt: 0}
      ) {
        id
        borrowedReservesCount
        collateralReserve: reserves(where: {currentATokenBalance_gt: 0}) {
          currentATokenBalance
          reserve {
            usageAsCollateralEnabled
            reserveLiquidationThreshold
            reserveLiquidationBonus
            borrowingEnabled
            utilizationRate
            symbol
            underlyingAsset
            price {
              priceInEth
              oracle {
                usdPriceEth
              }
            }
            decimals
          }
        }
        borrowReserve: reserves(where: {currentTotalDebt_gt: 0}) {
          currentTotalDebt
          reserve {
            usageAsCollateralEnabled
            reserveLiquidationThreshold
            borrowingEnabled
            utilizationRate
            symbol
            underlyingAsset
            price {
              priceInEth
              oracle {
                usdPriceEth
              }
            }
            decimals
          }
        }
      }
    }
    """

    response = requests.post(theGraphURL, headers=headers, json={"query": query})
    loansJson = response.json()

    loans = []
    local_price_storage = {}
    for user in loansJson["data"]["users"]:
        collateralReserve = []
        for reserve in user["collateralReserve"]:
            token = reserve["reserve"]["underlyingAsset"]
            amount = reserve["currentATokenBalance"]
            if reserve["reserve"]["symbol"] in local_price_storage.keys():
                amountInUSD = getStoredPriceValue(amount, local_price_storage[reserve["reserve"]["symbol"]])
            else:
                amountInUSD = getLivePriceValue(reserve["reserve"]["symbol"],
                                                amount)  # Implement getAssetPrice function
                local_price_storage[reserve["reserve"]["symbol"]] = amountInUSD / int(amount)
            collateralReserve.append((reserve["reserve"]["symbol"], token, amount, amountInUSD))

        borrowReserve = []
        for reserve in user["borrowReserve"]:
            token = reserve["reserve"]["underlyingAsset"]
            amount = reserve["currentTotalDebt"]
            if reserve["reserve"]["symbol"] in local_price_storage.keys():
                amountInUSD = getStoredPriceValue(amount, local_price_storage[reserve["reserve"]["symbol"]])
            else:
                amountInUSD = getLivePriceValue(reserve["reserve"]["symbol"],
                                                amount)  # Implement getAssetPrice function
                local_price_storage[reserve["reserve"]["symbol"]] = amountInUSD / int(amount)
            borrowReserve.append((reserve["reserve"]["symbol"], token, amount, amountInUSD))

        try:
            totalCollateralInUSD = sum(amountInUSD for _, _, _, amountInUSD in collateralReserve)
            totalBorrowInUSD = sum(amountInUSD for _, _, _, amountInUSD in borrowReserve)
            # TODO this isn't an accurate way of doing this, needs updated to actual asset liquidation threshold
            healthFactor = (totalCollateralInUSD * 85 * (10 ** 18)) / (totalBorrowInUSD * 100)

            loans.append(
                Loan(
                    user=user["id"],
                    collateralReserve=collateralReserve,
                    borrowReserve=borrowReserve,
                    totalCollateralInUSD=totalCollateralInUSD,
                    totalBorrowInUSD=totalBorrowInUSD,
                    healthFactor=healthFactor,
                    borrowToken=None,
                    collateralToken=None,
                    liquidationPrice=None
                )
            )
        except:
            pass

    unhealthyLoans = [loan for loan in loans if loan.healthFactor < (10 ** 18) * 12 / 10]
    unhealthyLoansFiltered = [loan for loan in unhealthyLoans if len(loan.collateralReserve) == 1 and len(loan.borrowReserve) == 1]
    logging.info(f'found {len(loans)} loans, {len(unhealthyLoansFiltered)} of which under health factor of 1.2')

    liquidationPrices = []
    for loan in unhealthyLoansFiltered:
        collateralToken = loan.collateralReserve[0][1]
        borrowToken = loan.borrowReserve[0][1]
        liquidationPrice = (loan.totalBorrowInUSD * (10 ** 18) * 100) / (
                    85 * int(loan.collateralReserve[0][2]))  # this needs checked, might be inaccurate or rounding badly
        hf = ('{:.0f}'.format(loan.healthFactor))
        liquidationPrices.append(
            Loan(
                user=loan.user,
                collateralToken=collateralToken,
                borrowToken=borrowToken,
                collateralReserve=loan.collateralReserve,
                borrowReserve=loan.borrowReserve,
                liquidationPrice=liquidationPrice,
                totalCollateralInUSD=loan.totalCollateralInUSD,
                totalBorrowInUSD=loan.totalBorrowInUSD,
                healthFactor=float(hf),
            )
        )
    if liquidationPrices:
        return liquidationPrices


def getStoredPriceValue(amount: Decimal, price) -> Decimal:
    return price * (int(amount))


def getLivePriceValue(symbol: str, amount: Decimal) -> Decimal:
    if symbol == "TWAVE":
        decimal = 18
        value = asset_value()
        return value * (int(amount) / 10 ** decimal)

    name, decimal = getTokenValues(symbol)
    url = "https://api.coingecko.com/api/v3/coins/" + name
    response = requests.get(url).text
    data = json.loads(response)
    time.sleep(1)

    try:
        return data['market_data']['current_price']['usd'] * (int(amount) / 10 ** decimal)
    except KeyError:
        time.sleep(60)
        response = requests.get(url).text
        data = json.loads(response)
        logging.info(f"2nd try price: {data['market_data']['current_price']['usd']}")
        return data['market_data']['current_price']['usd'] * (int(amount) / 10 ** decimal)


def getTokenValues(symbol: str):
    decimal = 18
    if symbol in nonstandard_decimal_tokens.keys():
        decimal = nonstandard_decimal_tokens[symbol]
    return market_data[symbol], decimal


if __name__ == "__main__":
    loans = fetchV2UnhealthyLoans()
    for loan in loans:
        logging.info(f"User: {loan.user}:")
        logging.info(f" \t Collateral Token: {loan.collateralToken}, Borrow Token: {loan.borrowToken}")
        logging.info(
            f" \t Liquidation Price: {loan.liquidationPrice:.4f}, Total Collateral In USD: {loan.totalCollateralInUSD:.4f}")
        logging.info(f" \t Total Borrow In USD: {loan.totalBorrowInUSD:.4f}, Health Factor: {loan.healthFactor / 10 ** 18}")
