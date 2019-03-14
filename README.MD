WELCOME To CYBEX ROME API Demo
============================

This is the python demo for [CYBEX ROME API](https://github.com/CybexDex/RomeAPI).


Quick Start
------------

`cybex_demo.py` can be used as a quick start to use [Cybex ROME API](https://github.com/CybexDex/RomeAPI).

The CYBEX ROME API is able to sign a transactions with the provided private key.
The standalone *Cyb Signer* is __not required__ if you use the [CYBEX ROME API](https://github.com/CybexDex/RomeAPI).

Please prepare below information before using `cybex-demo.py`:

1. __Account Name__
1. __Private Key__

The *Account Name* is the same as the user name you use to logon to the CYBEX exchange at https://dex.cybex.io/.
The *Private Key*, however, is __NOT__ the password you use for the web login.

To find your private key, please go to go to https://olddex.cybex.io (Note that this is the old version):

1. logon with your account name and password
1. on the top left of the web page, go to ACCOUNT, then to the middle left of the page, click 'Permissions'
1. under 'Active Permissions'->ACCOUNT/KEY/ADDRESS, click the public key string, which looks like CYB81SdxxxxxxxxxxxxxxxxxxxxxxxxJW
1. on the pop up box titled 'Private key viewer', click 'SHOW', then the private key string will be shown under 'Private key (WIF - Wallet Import Format)', which looks like '5HyMuxxxxxxxxxxxxxxxxxxxxxxxxxx4ka'
1. copy and save the private key string in a secure place to use with the CYBEX ROME API

__Usage:__
```
python3 cybex-demo.py <account name> <private key>
e.g. python3 cybex-demo.py test_user 5JbxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXd
```

__Note: Please use python3, you may encounter problems if python2 is used.__

Cybex API Connector (Cyb Signer required) - to be deprecated
---------

`cybexapi_connector.py` provides 2 wrappers.

One wraps around the CYBEX Restful API server.

The Cybex API server mainly provides API calls to send transaction, query position, query order, etc

The other one wraps the Transaction Signer.

Transaction Signer provies 3 api calls to provide signature to new order, cancel and cancel all orders.



Auto Trader
------------

`autotrader.py` is a sample (simple) strategy implemented using python. 
It looks at huobi's market data, calculate 1 minute MACD crossing signals.
 
Whenever the MACD cross up, the auto-trader buys.
 
Whenever the MACD corss down,the auto-trader sells.

This auto-trader will require a config.ini to contain API keys for the Huobi market 
data api.

__Note: Currently auto trader is not updated to use the latest CYBEX ROME API, it still requires cyb signer.__


[Cyb Signer](https://github.com/CybexDex/cyb-signer)
------------

The [Cyb Signer](https://github.com/CybexDex/cyb-signer) is a standalone Java program, it provides a way to sign a transaction through RESTful API.




