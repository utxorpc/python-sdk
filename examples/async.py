"""Connect to UTxO RPC server and perform some queries.

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)

"""

import asyncio
import os
from utxorpc.cardano import CardanoPoint, CardanoSyncClient
from utxorpc.generics.clients.sync_client import FollowTipResponseAction


async def main() -> None:
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

    async with client.async_connect() as client:
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
            if i >= 50:
                break


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
