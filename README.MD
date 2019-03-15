WELCOME To CYBEX ROME API Demo
============================

This is the python demo for [CYBEX ROME API](https://github.com/CybexDex/RomeAPI).


Quick Start
-----------

The demo application`cybex_demo.py` can be used as a quick start to the [CYBEX ROME API](https://github.com/CybexDex/RomeAPI).

### Use Password for Authentication

Please prepare the below information before using `cybex-demo.py`:

1. __Account Name__
1. __Password__
 
The *Account Name* and *Password* are the cloud wallet account name and password you use to logon to the CYBEX exchange at https://dex.cybex.io/.

__Usage:__
```
python3 cybex-demo.py -n <account name> -p <password>
e.g. python3 cybex-demo.py -n test_user -p xxxxxxxx
```
__NOTE: Please use python3, you may encounter problems if python2 is used.__

Auto Trader
-----------

`autotrader.py` is a sample (simple) strategy implemented using python. 
It looks at huobi's market data, calculate 1 minute MACD crossing signals.
 
Whenever the MACD cross up, the auto-trader buys.
 
Whenever the MACD corss down,the auto-trader sells.

This auto-trader will require a config.ini to contain API keys for the Huobi market 
data api.

__NOTE: Currently auto trader is not updated to use the latest CYBEX ROME API, it still requires *cyb signer* (see below).__


---------------

## Optional Usage

### Use Private Key for Authentication

The *Private Key* can also be used for authentication to use the ROME API.
The *Private Key*, however, is __NOT__ the password you use for the web logon.

To find your private key, go to https://olddex.cybex.io (NOTE that this is the old version):

1. logon with your account name and password
1. on the top left of the web page, go to ACCOUNT, then to the middle left of the page, click 'Permissions'
1. under 'Active Permissions'->ACCOUNT/KEY/ADDRESS, click the public key string, which looks like CYB81SdxxxxxxxxxxxxxxxxxxxxxxxxJW
1. on the pop up box titled 'Private key viewer', click 'SHOW', then the private key string will be shown under 'Private key (WIF - Wallet Import Format)', which looks like '5HyMuxxxxxxxxxxxxxxxxxxxxxxxxxx4ka'
1. copy and save the private key string in a secure place to use with the CYBEX ROME API

__Usage:__
```
python3 cybex-demo.py -n <account name> -k <private key>
e.g. python3 cybex-demo.py -n test_user -k 5JbxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxXd
```

### Cybex API Connector (Cyb Signer Required)


`cybexapi_connector.py` provides two wrappers.

One wraps around the CYBEX Restful API server.

The Cybex API server mainly provides API calls to send transaction, query position, query order, etc

The other one wraps the Transaction Signer.

Transaction Signer provies 3 api calls to provide signature to new order, cancel and cancel all orders.



### [Cyb Signer](https://github.com/CybexDex/cyb-signer)

The [Cyb Signer](https://github.com/CybexDex/cyb-signer) is a standalone Java program, it provides a way to sign a transaction through RESTful API.




