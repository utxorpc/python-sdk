"""Connect to UTxO RPC server and perform some queries.

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)

"""

import asyncio
import os
from utxorpc.cardano import (
    CardanoAddress,
    CardanoPoint,
    CardanoSyncClient,
    CardanoTxOutputPattern,
    CardanoQueryClient,
    CardanoTxoRef,
)
from utxorpc.generics.clients.sync_client import FollowTipResponseAction


async def main() -> None:
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

    async with sync_client.async_connect() as client:
        fetched_block = await client.async_fetch_block(ref=[BLOCK_REF])
        print("FetchBlock: {}", fetched_block)
        dumped_history = await client.async_dump_history(start=BLOCK_REF, max_items=1)
        print("DumpHistory: {}", dumped_history)

        i = 0
        async for followed_tip in client.async_follow_tip(intersect=[BLOCK_REF]):
            i += 1
            if followed_tip.action == FollowTipResponseAction.apply:
                assert followed_tip.block is not None  # Block can't be None when APPLY
                print(f"FollowTip {i}: {followed_tip.block.header}")
            else:
                print(f"FollowTip {i}: {followed_tip.action}")
            if i >= 5:
                break

    query_client: CardanoQueryClient = CardanoQueryClient(
        HOST, metadata={"dmtr-api-key": API_KEY}
    )

    async with query_client.async_connect() as client:
        utxos = await client.async_search_utxos(
            match=CardanoTxOutputPattern(
                address={
                    "exact_address": CardanoAddress.from_base64(
                        "YEm9mD0SNTpI05rRUhIiDr1x3T+JfrKauJ88tY4="
                    ).hash
                }
            )
        )
        print(f"Utxos: {utxos}")

        utxo = await client.async_read_utxos(keys=[TXO_REF])
        print(f"Utxo: {utxo}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
