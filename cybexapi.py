from time import sleep
import requests
import logging
import json

SLEEP_INTERVAL = 5
signer_endpoint_root = "http://127.0.0.1:8090/signer/v1"
api_endpoint_root = "https://apitest.cybex.io/v1"

logging.basicConfig(filename="log.txt")


class CybexRestful:
    """Cybex Restful API sample implementation

    """
    def __init__(self, api_root=api_endpoint_root, clordid_prefix=None, timeout=None):
        self.logger = logging.getLogger('root')
        self.api_root = api_root

        self.timeout = timeout

        # Prepare HTTPS session
        self.session = requests.Session()

        self.session.headers.update({'user-agent': 'cybex-bot'})
        self.session.headers.update({'content-type': 'application/json'})
        self.session.headers.update({'accept': 'application/json'})

    def curl_cybex(self, path, param_data=None, post_data=None, verb=None):
        url = self.api_root + path

        # Default to POST if data is attached, GET otherwise
        if not verb:
            verb = 'POST' if postdict else 'GET'

        # Make the request
        response = None

        try:
            self.logger.info("sending req to %s: %s" % (url, json.dumps(param_data or post_data or '')))
            req = requests.Request(verb, url, json=post_data, params=param_data)
            prepped = self.session.prepare_request(req)
            response = self.session.send(prepped, timeout=self.timeout)
            # Make non-200s throw
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response is None:
                raise e
            if response.status_code == 401:
                pass
            elif response.status_code == 404:
                pass
            elif response.status_code == 429:
                pass
            elif response.status_code == 503:
                pass
            elif response.status_code == 400:
                pass
        except requests.exceptions.Timeout as e:
            pass

        except requests.exceptions.ConnectionError as e:
            pass

        return response.json()

    def get_instruments(self):
        url = "%s/instrument" % self.api_root
        return requests.get(url)

    def get_order_book(self):
        url = "%s/orderBook" % self.api_root
        return requests.get(url)

    def get_position(self, seller_id):
        url = "%s/position" % self.api_root
        params = {'sellerId': seller_id}
        return requests.get(url, params=params)

    def get_orders(self, account):
        url = "%s/order" % self.api_root
        data = {'accountName': account}
        headers = {'Content-type': 'application/json'}
        return requests.get(url, json=data, headers=headers)
        #return requests.get(url, json=data)

    def get_bar_data(self):
        pass

    def get_trades(self, ):
        # Get trades starting from a particular trade ID.
        # Calling this every interval will effectively gets all the trades.
        # User can use these data to calculate other indicator.
        pass

    def place_order(self, data):
        url = "%s/transaction" % self.api_root
        headers = {'Content-type': 'application/json'}
        return requests.post(url, json=data, headers=headers)

    def cancel_order(self, data):
        url = "%s/transaction" % self.api_root
        headers = {'Content-type': 'application/json'}
        return requests.post(url, json=data, headers=headers)

    def cancel_all_orders(self, data):
        url = "%s/transaction" % self.api_root
        headers = {'Content-type': 'application/json'}
        return requests.post(url, json=data, headers=headers)


class SignerConnector:
    def __init__(self, api_root=signer_endpoint_root):
        self.api_root = api_root

    def new_order(self, symbol, price, quantity, side):
        url = "%s/newOrder" % self.api_root
        data = {'assetPair': symbol, 'price': price, 'quantity': quantity, 'side': side}
        headers = {'Content-type': 'application/json'}
        return requests.post(url, json=data, headers=headers)

    def cancel(self, trxid):
        url = "%s/cancelOrder" % self.api_root
        data = {'originalTransactionId': trxid}
        return requests.post(url, json=data)

    def cancel_all(self, symbol):
        url = "%s/cancelAll" % self.api_root
        data = {'assetPair': symbol}
        return requests.post(url, json=data)

