"""Connect to UTxO RPC server and perform some queries.

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)

"""

import os
from utxorpc import CardanoPoint, CardanoSyncClient


def main() -> None:
    HOST = "preview.utxorpc-v0.demeter.run"

    API_KEY = os.getenv("DMTR_API_KEY")
    assert API_KEY is not None, "DMTR_API_KEY must be defined"

    BLOCK_REF = CardanoPoint(
        slot=52375021,
        hash="b5db7950eebf33a0dd9de9ab1f2b25187d5ca0c74018b101842ee6797a3e9c65",
    )

    client: CardanoSyncClient = CardanoSyncClient(
        HOST, metadata={"dmtr-api-key": API_KEY}
    )

    with client.connect() as client:
        fetched_block = client.fetch_block(ref=[BLOCK_REF])
        print("FetchBlock: {}", fetched_block)
        dumped_history = client.dump_history(start=BLOCK_REF, max_items=1)
        print("DumpHistory: {}", dumped_history)


if __name__ == "__main__":
    main()
