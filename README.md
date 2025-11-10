# python-sdk
Python SDK for the UTxO RPC interface

## Features

- Sync and Query service clients for Cardano blockchain
- Support for both synchronous and asynchronous operations
- Type-safe implementation with Protocol Buffers
- Easy-to-use API with connection management


# Important Note

Due to import path issues in utxorpc-spec 0.16.0, you must import `spec_compatibility` before using this SDK:

```python
import spec_compatibility
from utxorpc import CardanoSyncClient, CardanoQueryClient
```

# Setup

`utxorpc` requires `Python3.9>,<4.0`. To setup a local environment you can run:

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
