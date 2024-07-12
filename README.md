# python-sdk
Python SDK for the UTxO RPC interface


# Setup

`utxorpc` requires `Python3.8>,<4.0`. To setup a local environment you can run:

```sh
just init
```

This will use your system's `python3`, whichever it may be. If you wish to setup a particular Python executable (for example, `python3.12`) you should do:

```sh
just init python3.12
```

To run the examples, you require an Demeter API Key for the UtxoRPC service. To get your API key, you can check the documentation at (https://docs.demeter.run/cli)[https://docs.demeter.run/cli]:

```sh
just run-examples YOUR_DMTR_API_KEY
```

# Contributing

Before commiting, make sure to run the following to format and lint the code.

```sh
just format
just lint
```
