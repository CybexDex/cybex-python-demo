WELCOME To CYBEX Python API Demo
============================

This is the python demo for [CYBEX Python API](https://github.com/CybexDex/RomeAPI).


Quick Start
------------

`cybex_demo.py` can be used as a quick start to use [Cybex Python API](https://github.com/CybexDex/RomeAPI).

The CYBEX Python API is able to sign a transactions with the provided private key.
The standalone *Cyb Signer* is __not required__ if you use the [CYBEX Python API](https://github.com/CybexDex/RomeAPI).

Please prepare below information before using `cybex-demo.py`:

1. __Account Name__
1. __Private Key__

__Usage:__
```
python3 cybex-demo.py <account name> <private key>
e.g. python3 cybex-demo.py test_user 5JbxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXd
```

__Note: Please use python3, you may encounter problems if python2 is used.__

Cybex API Connector (required Cyb Signer) - to be deprecated
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

__Note: Currently auto trader is not updated to use latest cybex python api, it still requires cyb signer.__


[Cyb Signer](https://github.com/CybexDex/cyb-signer)
------------

The [Cyb Signer](https://github.com/CybexDex/cyb-signer) is a standalone Java program, it provides a way to sign a transaction through RESTful API.




