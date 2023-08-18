from tools import *
Account.enable_unaudited_hdwallet_features()

class OEV:
    def __init__(self, web3):
        self.name = self.__class__.__name__
        self.web3 = web3

        self.endpoint = os.getenv("API")
        self.signature_expiry = 82400

    def oev_configuration(self):
        r = requests.get(self.endpoint + "configuration")
        logging.info(r.text)

    def oev_status(self, account):
        time_stamp = int(time.mktime(datetime.datetime.now().timetuple()) + self.signature_expiry)
        date_time = datetime.datetime.fromtimestamp(time_stamp)
        str_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {"prepaymentDepositoryChainId": int(os.getenv("PREPAYMENT_DEPOSIT_CHAIN")), "requestType":"API3 OEV Relay, status","searcherAddress":account.address,"validUntil": str_date_time,"prepaymentDepositoryAddress":os.getenv("PREPAYMENT_DEPOSIT_ADDRESS")}
        data["signature"] = signature(account, json.dumps(dict(sorted(data.items(), key=lambda x:x[0])), separators=(',', ':'))).signature.hex()
        headers = {'Content-type': 'application/json'}
        r = requests.post(self.endpoint+"status", data=json.dumps(data), headers=headers)
        if r:
            return r.text
        else:
            return {'result' : False}

    def all_bids(self, account):
        data = json.loads(self.oev_status(account))
        return data

    def winning_bids(self, account):
        try:
            data = json.loads(self.oev_status(account))
        except:
            return False
        try:
            if data["executableAuctions"] != []:
                return data["executableAuctions"][0]
            else:
                return False
        except:
            return False

    def place_bid(self, account, flashloanreceiver, asset_value, dAppProxyAddress, dAppProxyChainId, bid_amount=os.getenv("MIN_BID"), condition="LTE"):
        time_stamp = int(time.mktime(datetime.datetime.now().timetuple()) + self.signature_expiry)
        date_time = datetime.datetime.fromtimestamp(time_stamp)
        str_date_time = date_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        data = {
          "searcherAddress": account.address,
          "validUntil": str_date_time,
          "prepaymentDepositoryChainId": int(os.getenv("PREPAYMENT_DEPOSIT_CHAIN")),
          "prepaymentDepositoryAddress": os.getenv("PREPAYMENT_DEPOSIT_ADDRESS"),
          "bidAmount": str(bid_amount),
          "dAppProxyAddress": dAppProxyAddress,
          "dAppProxyChainId": dAppProxyChainId,
          "condition": condition,
          "fulfillmentValue": str(int(asset_value)),
          "requestType": "API3 OEV Relay, place-bid",
          "updateExecutorAddress": flashloanreceiver
        }
        data["signature"] = signature(account, json.dumps(dict(sorted(data.items(), key=lambda x:x[0])), separators=(',', ':'))).signature.hex()
        headers = {'Content-type': 'application/json'}
        r = requests.post(self.endpoint+"place-bid", data=json.dumps(data), headers=headers)
        if r:
            return json.loads(r.text)
        else:
            logging.info(f'\tplace_bid(): bad response from bid relay: {r}')

    def run_all(self, account):
        self.oev_configuration()
        self.oev_status(account)
        output = self.place_bid(account, os.getenv("FL_ADDRESS"), asset_value(), os.getenv("TWAVEoevDatafeedProxy"), dAppProxyChainId=5)
        logging.info(output)

    def update_prices(self, account, contract_obj, update_target):
        wins = self.winning_bids(account)
        encodedUpdateTransaction = wins["encodedUpdateTransaction"]
        nativeCurrencyAmount = int(wins["nativeCurrencyAmount"])
        updatePeriodEnd = wins["updatePeriodEnd"]
        expiry = int(datetime.datetime.strptime(updatePeriodEnd, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
        now = int(datetime.datetime.timestamp(datetime.datetime.now()))
        if now < expiry - 30:
            logging.info(f'updating oev price....')
            function = contract_obj.functions.updatePrice([update_target], [encodedUpdateTransaction], [nativeCurrencyAmount])
            tx_params = get_tx_params(web3=self.web3, account=account, value=nativeCurrencyAmount, gas=1000000)
            tx = build_and_send_and_wait(self.web3, account, function, tx_params)
            return tx

