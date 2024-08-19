"""Connect to UTxO RPC server and perform some queries.

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)

"""

import os
from utxorpc import (
    CardanoPoint,
    CardanoSyncClient,
    CardanoTxOutputPattern,
    CardanoAddress,
    CardanoQueryClient,
    CardanoTxoRef,
)


def main() -> None:
    HOST = "cardano-preprod.utxorpc.cloud"

    API_KEY = os.getenv("DMTR_API_KEY")
    assert API_KEY is not None, "DMTR_API_KEY must be defined"

    # Preprod
    BLOCK_REF = CardanoPoint(
        slot=68149593,
        hash="403986182453766f3843fc6843fdf8f17587cd2ec10cece313b28c2ac88d39e5",
    )
    TXO_REF = CardanoTxoRef.from_base64(
        index=2, hash="87M9mQb5CDSzemAcO3XyDxYupGVdTeVCuaL/qPF3C/c="
    )

    sync_client: CardanoSyncClient = CardanoSyncClient(
        HOST, metadata={"dmtr-api-key": API_KEY}
    )

    with sync_client.connect() as client:
        fetched_block = client.fetch_block(ref=[BLOCK_REF])
        print("FetchBlock: {}", fetched_block)
        dumped_history = client.dump_history(start=BLOCK_REF, max_items=1)
        print("DumpHistory: {}", dumped_history)

    query_client: CardanoQueryClient = CardanoQueryClient(
        HOST, metadata={"dmtr-api-key": API_KEY}
    )

    with query_client.connect() as client:
        utxos = client.search_utxos(
            match=CardanoTxOutputPattern(
                address={
                    "exact_address": CardanoAddress.from_base64(
                        "YEm9mD0SNTpI05rRUhIiDr1x3T+JfrKauJ88tY4="
                    ).hash
                }
            )
        )
        print("Utxos: {}", utxos)

        utxo = client.read_utxos(keys=[TXO_REF])
        print(f"Utxo: {utxo}")


if __name__ == "__main__":
    main()
