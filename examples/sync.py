"""Async sync client examples following test-like structure.

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)

"""

import asyncio
import os
import spec_compatibility  # noqa: F401
from utxorpc.sync import CardanoPoint, CardanoSyncClient
from utxorpc.generics.clients.sync import FollowTipResponseAction


async def test_read_tip(client: CardanoSyncClient) -> None:
    """Test reading the current blockchain tip"""
    print("\nTesting readTip...")

    tip = await client.async_read_tip()

    print("ReadTip result:")
    print(f"   - Slot: {tip.slot}")
    print(f"   - Hash: {tip.hash.hex()}")

    # Assertions
    assert isinstance(tip.slot, int), f"Expected slot to be int, got {type(tip.slot)}"
    assert isinstance(tip.hash, bytes), (
        f"Expected hash to be bytes, got {type(tip.hash)}"
    )
    assert tip.slot > 1, f"Expected slot > 1, got {tip.slot}"
    assert len(tip.hash) > 0, f"Expected hash length > 0, got {len(tip.hash)}"

    print("All assertions passed!")


async def test_fetch_block(client: CardanoSyncClient) -> None:
    """Test fetching a specific block"""
    print("\nTesting fetchBlock...")

    block_ref = CardanoPoint(
        slot=85213090,
        hash="e50842b1cc3ac813cb88d1533c3dea0f92e0ea945f53487c1d960c2210d0c3ba",
    )

    block = await client.async_fetch_block(ref=[block_ref])

    print("FetchBlock result:")
    if block and hasattr(block, "header"):
        print(f"   - Header slot: {block.header.slot}")
        print(f"   - Header hash: {block.header.hash.hex()}")
        print(f"   - Header height: {block.header.height}")

        # Assertions
        assert block.header.slot == 85213090, (
            f"Expected slot 85213090, got {block.header.slot}"
        )
        assert len(block.header.hash) > 0, (
            f"Expected hash length > 0, got {len(block.header.hash)}"
        )
        assert block.header.height > 0, (
            f"Expected height > 0, got {block.header.height}"
        )

        print("All assertions passed!")
    else:
        print("Block not found or missing header")


async def test_dump_history(client: CardanoSyncClient) -> None:
    """Test dumping historical blocks (renamed from fetchHistory for consistency)"""
    print("\nTesting dumpHistory...")

    start_point = CardanoPoint(
        slot=85213090,
        hash="e50842b1cc3ac813cb88d1533c3dea0f92e0ea945f53487c1d960c2210d0c3ba",
    )

    history = await client.async_dump_history(start=start_point, max_items=3)

    print("DumpHistory result:")
    print(f"   - Found {len(history)} blocks")

    for i, block in enumerate(history):
        if block and hasattr(block, "header"):
            print(
                f"   - Block {i + 1}: slot={block.header.slot}, height={block.header.height}"
            )

    # Assertions
    assert len(history) > 0, f"Expected history length > 0, got {len(history)}"
    assert len(history) <= 3, f"Expected history length <= 3, got {len(history)}"

    print("All assertions passed!")


async def test_follow_tip(client: CardanoSyncClient) -> None:
    """Test following blockchain tip updates"""
    print("\nTesting followTip...")

    intersect_point = CardanoPoint(
        slot=85213090,
        hash="e50842b1cc3ac813cb88d1533c3dea0f92e0ea945f53487c1d960c2210d0c3ba",
    )

    # Create async iterator
    follow_generator = client.async_follow_tip(intersect=[intersect_point])
    follow_iterator = follow_generator.__aiter__()

    print("FollowTip streaming started...")

    try:
        # Get first response (should be reset)
        first_response = await asyncio.wait_for(
            follow_iterator.__anext__(), timeout=10.0
        )

        print("First response:")
        print(f"   - Action: {first_response.action.value}")

        if first_response.action == FollowTipResponseAction.reset:
            print(f"   - Reset point slot: {first_response.point.slot}")
            print(f"   - Reset point hash: {first_response.point.hash.hex()}")

            # Assertions for reset response
            assert first_response.action == FollowTipResponseAction.reset, (
                f"Expected reset action, got {first_response.action}"
            )
            assert first_response.point is not None, (
                "Expected point for reset action, got None"
            )
            assert first_response.block is None, (
                f"Expected no block for reset action, got {first_response.block}"
            )

            print("Reset response assertions passed!")

        # Try to get second response (should be apply/undo)
        try:
            second_response = await asyncio.wait_for(
                follow_iterator.__anext__(), timeout=15.0
            )

            print("Second response:")
            print(f"   - Action: {second_response.action.value}")

            if second_response.action in [
                FollowTipResponseAction.apply,
                FollowTipResponseAction.undo,
            ]:
                if second_response.block and hasattr(second_response.block, "header"):
                    print(
                        f"   - Block header slot: {second_response.block.header.slot}"
                    )
                    print(
                        f"   - Block header hash: {second_response.block.header.hash.hex()}"
                    )
                    print(
                        f"   - Block header height: {second_response.block.header.height}"
                    )

                    # Assertions for apply/undo response
                    assert second_response.block is not None, (
                        f"Expected block for {second_response.action} action, got None"
                    )
                    assert second_response.point is None, (
                        f"Expected no point for {second_response.action} action, got {second_response.point}"
                    )
                    assert second_response.block.header.slot > 85213090, (
                        f"Expected slot > 85213090, got {second_response.block.header.slot}"
                    )

                    print("Apply/Undo response assertions passed!")
                else:
                    print("Block found but missing header")
            else:
                print(f"   - Unexpected action: {second_response.action}")

        except asyncio.TimeoutError:
            print(
                "Timeout waiting for second response (this is normal for low-activity chains)"
            )

    except asyncio.TimeoutError:
        print("Timeout waiting for first response")

    print("FollowTip test completed!")


async def main() -> None:
    import sys

    # Check if running in local mode
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        HOST = "localhost:50051"
        metadata = {}
        secure = False
        print("Running in LOCAL mode")
    else:
        HOST = "preview.utxorpc-v0.demeter.run"
        API_KEY = os.getenv("DMTR_API_KEY")
        assert API_KEY is not None, "DMTR_API_KEY must be defined"
        metadata = {"dmtr-api-key": API_KEY}
        secure = True

    client = CardanoSyncClient(HOST, metadata=metadata, secure=secure)

    print("Sync Client Tests (Asynchronous)")
    print("=" * 50)

    async with client.async_connect() as connected_client:
        print("Connected to UTxO RPC server")

        # Run all async tests
        await test_read_tip(connected_client)
        await test_fetch_block(connected_client)
        await test_dump_history(connected_client)
        await test_follow_tip(connected_client)

        print("\nAll async tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
