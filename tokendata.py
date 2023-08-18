import os

# these long names need mappings to symbols for coingecko price checks
def getTokenValues(token: str):
    name = None
    decimal = None
    if token == os.getenv("WBTC"):
        name = 'bitcoin'
        decimal = 18
    if token == os.getenv("WETH"):
        name = 'ethereum'
        decimal = 18
    if token == os.getenv("USDC"):
        name = 'usd-coin'
        decimal = 18
    return name, decimal


