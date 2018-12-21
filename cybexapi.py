from time import sleep
import requests
import logging
import json

SLEEP_INTERVAL = 5
signer_endpoint_root = "http://127.0.0.1:8090/signer/v1"
api_endpoint_root = "https://api.cybex.io/v1"

logging.basicConfig(filename="log.txt")


class CybexAPIException(Exception):
    def __init__(self, response):
        self.code = 0
        try:
            json_res = response.json()
        except ValueError:
            self.message = 'Invalid JSON error message from Cybex: {}'.format(response.text)
        else:
            self.code = json_res['code']
            self.message = json_res['msg']
        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        return 'API error (code=%s): %s' % (self.code, self.message)


class CybexRequestException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'CybexRequestException: %s' % self.message


class CybexSignerException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'CybexSignerException: %s' % self.message


class CybexException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'CybexException: %s' % self.message


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

    def get_instruments(self):
        url = "%s/instrument" % self.api_root
        return self._handle_response(requests.get(url))

    def get_order_book(self):
        url = "%s/orderBook" % self.api_root
        return self._handle_response(requests.get(url))

    def get_position(self, seller_id):
        url = "%s/position" % self.api_root
        params = {'sellerId': seller_id}
        return self._handle_response(requests.get(url, params=params))

    def get_orders(self, account):
        url = "%s/order" % self.api_root
        data = {'accountName': account}
        headers = {'Content-type': 'application/json'}
        return self._handle_response(requests.get(url, json=data, headers=headers))

    def get_bar_data(self):
        pass

    def get_trades(self, ):
        # Get trades starting from a particular trade ID.
        # Calling this every interval will effectively gets all the trades.
        # User can use these data to calculate other indicator.
        pass

    def send_transaction(self, data):
        url = "%s/transaction" % self.api_root
        headers = {'Content-type': 'application/json'}
        return self._handle_response(requests.post(url, json=data, headers=headers))

    def _handle_response(self, response):
        # Return the json object if there is no error
        if not str(response.status_code).startswith('2'):
            raise CybexAPIException(response)
        try:
            data = response.json()
            if 'Status' in data and data['Status'] == 'Failed':
                msg = 'Unknown error.'
                if 'rejectReason' in data:
                    msg = data['rejectReason']
                raise CybexRequestException(msg)
            return data
        except ValueError:
            raise CybexRequestException('Invalid Response: %s' % response.text)


class SignerConnector:
    def __init__(self, api_root=signer_endpoint_root):
        self.api_root = api_root

    def prepare_order_message(self, symbol, price, quantity, side):
        url = "%s/newOrder" % self.api_root
        data = {'assetPair': symbol, 'price': price, 'quantity': quantity, 'side': side}
        headers = {'Content-type': 'application/json'}
        return self._handle_response(requests.post(url, json=data, headers=headers))

    def prepare_cancel_message(self, trxid):
        url = "%s/cancelOrder" % self.api_root
        data = {'originalTransactionId': trxid}
        return self._handle_response(requests.post(url, json=data))

    def prepare_cancel_all_message(self, symbol):
        url = "%s/cancelAll" % self.api_root
        data = {'assetPair': symbol}
        return self._handle_response(requests.post(url, json=data))

    def _handle_response(self, response):
        # Return the json object if there is no error
        if not str(response.status_code).startswith('2'):
            raise CybexAPIException(response)
        try:
            data = response.json()
            if 'Status' in data and data['Status'] == 'Failed':
                msg = 'Unknown error'
                if 'Message' in data:
                    msg = data['Message']
                raise CybexSignerException(data[msg])
            return data
        except ValueError:
            raise CybexSignerException('Invalid Response: %s' % response.text)

