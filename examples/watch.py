"""Watch client examples following the same pattern as submit examples.

This example demonstrates:
1. Building and submitting a transaction with assets
2. Watching for transactions by address patterns (exact, payment, delegation)
3. Watching for transactions by asset patterns (specific asset, policy ID)
4. Real-time transaction monitoring

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)
"""

import asyncio
import spec_compatibility  # noqa: F401
from utxorpc import CardanoWatchClient, CardanoSubmitClient
from tx_builder import (
    TEST_CONFIG,
    create_wallet_from_mnemonic,
    build_simple_transaction,
    tx_to_bytes,
)
from pycardano import BlockFrostChainContext
from utxorpc_spec.utxorpc.v1alpha.watch.watch_pb2 import (  # type: ignore
    TxPredicate,
    AnyChainTxPattern,
)
from utxorpc_spec.utxorpc.v1alpha.cardano.cardano_pb2 import (  # type: ignore
    TxPattern,
    TxOutputPattern,
    AddressPattern,
    AssetPattern,
)


async def example_submit_tx_with_assets(client: CardanoSubmitClient):
    """Example: Build and submit a transaction with assets"""
    print("\nExample: Building and submitting transaction with assets")

    try:
        # Create chain context
        chain_context = BlockFrostChainContext(
            project_id=TEST_CONFIG["blockfrost_api_key"],
            network=TEST_CONFIG["network"],
            base_url="https://cardano-preview.blockfrost.io/api",
        )

        # Create wallet from mnemonic
        signing_key, from_address = create_wallet_from_mnemonic(
            TEST_CONFIG["mnemonic"], TEST_CONFIG["network"]
        )

        print(f"Address: {from_address}")

        # Check balance
        utxos = chain_context.utxos(str(from_address))
        balance = sum(utxo.output.amount.coin for utxo in utxos)
        print(f"Balance: {balance} lovelace")

        if balance < TEST_CONFIG["min_balance"]:
            print(f"Insufficient balance: {balance} < {TEST_CONFIG['min_balance']}")
            return None

        # Build transaction with assets (includes asset with policy ID 8b05e87a...)
        tx = build_simple_transaction(
            chain_context=chain_context,
            from_address=from_address,
            to_address=str(from_address),  # Send to self
            amount=TEST_CONFIG["send_amount"],
            signing_key=signing_key,
        )

        tx_id = tx.id.payload.hex()
        print(f"Transaction built: {tx_id}")

        # Submit via UTxO RPC
        tx_bytes = tx_to_bytes(tx)
        await client.async_submit_tx(tx_bytes)

        print(f"Transaction submitted: {tx_id}")
        return bytes.fromhex(tx_id), from_address

    except Exception as e:
        print(f"Error: {e}")
        return None, None


async def example_watch_all_patterns_simultaneously(
    watch_client: CardanoWatchClient, test_address, expected_tx_ref: bytes
):
    """Example: Watch for transactions using multiple patterns simultaneously"""
    print("\nExample: Watching for transactions with multiple patterns")

    try:
        # Prepare address components
        address_bytes = bytes(test_address.to_primitive())
        payment_bytes = (
            test_address.payment_part.to_primitive()
            if test_address.payment_part
            else None
        )
        delegation_bytes = (
            test_address.staking_part.to_primitive()
            if test_address.staking_part
            else None
        )

        # Asset patterns
        asset_subject = bytes.fromhex(
            "8b05e87a51c1d4a0fa888d2bb14dbc25e8c343ea379a171b63aa84a0434e4354"
        )  # Policy ID + Asset name concatenated
        policy_id = bytes.fromhex(
            "8b05e87a51c1d4a0fa888d2bb14dbc25e8c343ea379a171b63aa84a0"
        )  # Policy ID only

        # Create all watchers
        watchers = {}
        results = {}

        # 1. Exact address watcher
        async def watch_exact_address():
            predicate = TxPredicate()
            pattern = AnyChainTxPattern()
            tx_pattern = TxPattern()
            address_pattern = AddressPattern()
            address_pattern.exact_address = address_bytes
            tx_pattern.has_address.CopyFrom(address_pattern)
            pattern.cardano.CopyFrom(tx_pattern)
            predicate.match.CopyFrom(pattern)

            async for response in watch_client.async_watch_tx(predicate):
                if (
                    response.tx
                    and hasattr(response.tx, "cardano")
                    and response.tx.cardano
                ):
                    if hasattr(response.tx.cardano, "hash"):
                        tx_hash = response.tx.cardano.hash
                        if tx_hash == expected_tx_ref:
                            print(
                                f"Exact address watcher detected: {tx_hash.hex()[:16]}..."
                            )
                            results["exact_address"] = True
                            return "exact_address"

        watchers["exact_address"] = asyncio.create_task(watch_exact_address())

        # 2. Payment part watcher
        if payment_bytes:

            async def watch_payment_part():
                predicate = TxPredicate()
                pattern = AnyChainTxPattern()
                tx_pattern = TxPattern()
                output_pattern = TxOutputPattern()
                address_pattern = AddressPattern()
                address_pattern.payment_part = payment_bytes
                output_pattern.address.CopyFrom(address_pattern)
                tx_pattern.produces.CopyFrom(output_pattern)
                pattern.cardano.CopyFrom(tx_pattern)
                predicate.match.CopyFrom(pattern)

                async for response in watch_client.async_watch_tx(predicate):
                    if (
                        response.tx
                        and hasattr(response.tx, "cardano")
                        and response.tx.cardano
                    ):
                        if hasattr(response.tx.cardano, "hash"):
                            tx_hash = response.tx.cardano.hash
                            if tx_hash == expected_tx_ref:
                                print(
                                    f"Payment part watcher detected: {tx_hash.hex()[:16]}..."
                                )
                                results["payment_part"] = True
                                return "payment_part"

            watchers["payment_part"] = asyncio.create_task(watch_payment_part())

        # 3. Delegation part watcher
        if delegation_bytes:

            async def watch_delegation_part():
                predicate = TxPredicate()
                pattern = AnyChainTxPattern()
                tx_pattern = TxPattern()
                output_pattern = TxOutputPattern()
                address_pattern = AddressPattern()
                address_pattern.delegation_part = delegation_bytes
                output_pattern.address.CopyFrom(address_pattern)
                tx_pattern.produces.CopyFrom(output_pattern)
                pattern.cardano.CopyFrom(tx_pattern)
                predicate.match.CopyFrom(pattern)

                async for response in watch_client.async_watch_tx(predicate):
                    if (
                        response.tx
                        and hasattr(response.tx, "cardano")
                        and response.tx.cardano
                    ):
                        if hasattr(response.tx.cardano, "hash"):
                            tx_hash = response.tx.cardano.hash
                            if tx_hash == expected_tx_ref:
                                print(
                                    f"Delegation part watcher detected: {tx_hash.hex()[:16]}..."
                                )
                                results["delegation_part"] = True
                                return "delegation_part"

            watchers["delegation_part"] = asyncio.create_task(watch_delegation_part())

        # 4. Specific asset watcher
        async def watch_specific_asset():
            predicate = TxPredicate()
            pattern = AnyChainTxPattern()
            tx_pattern = TxPattern()
            asset_pattern = AssetPattern()
            asset_pattern.asset_name = asset_subject
            tx_pattern.moves_asset.CopyFrom(asset_pattern)
            pattern.cardano.CopyFrom(tx_pattern)
            predicate.match.CopyFrom(pattern)

            async for response in watch_client.async_watch_tx(predicate):
                if (
                    response.tx
                    and hasattr(response.tx, "cardano")
                    and response.tx.cardano
                ):
                    if hasattr(response.tx.cardano, "hash"):
                        tx_hash = response.tx.cardano.hash
                        if tx_hash == expected_tx_ref:
                            print(
                                f"Specific asset watcher detected: {tx_hash.hex()[:16]}..."
                            )
                            results["specific_asset"] = True
                            return "specific_asset"

        watchers["specific_asset"] = asyncio.create_task(watch_specific_asset())

        # 5. Policy ID watcher
        async def watch_policy_id():
            predicate = TxPredicate()
            pattern = AnyChainTxPattern()
            tx_pattern = TxPattern()
            asset_pattern = AssetPattern()
            asset_pattern.policy_id = policy_id
            tx_pattern.moves_asset.CopyFrom(asset_pattern)
            pattern.cardano.CopyFrom(tx_pattern)
            predicate.match.CopyFrom(pattern)

            async for response in watch_client.async_watch_tx(predicate):
                if (
                    response.tx
                    and hasattr(response.tx, "cardano")
                    and response.tx.cardano
                ):
                    if hasattr(response.tx.cardano, "hash"):
                        tx_hash = response.tx.cardano.hash
                        if tx_hash == expected_tx_ref:
                            print(
                                f"Policy ID watcher detected: {tx_hash.hex()[:16]}..."
                            )
                            results["policy_id"] = True
                            return "policy_id"

        watchers["policy_id"] = asyncio.create_task(watch_policy_id())

        print(f"Watching for transaction: {expected_tx_ref.hex()[:16]}...")
        print(f"Active watchers: {len(watchers)}")

        # Wait for all watchers to complete or timeout
        try:
            done, pending = await asyncio.wait(
                list(watchers.values()),
                timeout=240.0,  # 4 minute maximum timeout
                return_when=asyncio.ALL_COMPLETED,
            )

            # Cancel any remaining watchers
            for task in pending:
                task.cancel()

        except asyncio.TimeoutError:
            print("Watch timeout reached")

        # Results summary
        print("\nWatch results:")
        print(
            f"Exact address: {'Detected' if results.get('exact_address') else 'Not detected'}"
        )
        if payment_bytes:
            print(
                f"Payment part: {'Detected' if results.get('payment_part') else 'Not detected'}"
            )
        if delegation_bytes:
            print(
                f"Delegation part: {'Detected' if results.get('delegation_part') else 'Not detected'}"
            )
        print(
            f"Specific asset: {'Detected' if results.get('specific_asset') else 'Not detected'}"
        )
        print(
            f"Policy ID: {'Detected' if results.get('policy_id') else 'Not detected'}"
        )

        detected_count = len(results)
        total_count = len(watchers)
        print(f"\nDetected by {detected_count}/{total_count} watchers")

        return detected_count == total_count

    except Exception as e:
        print(f"Error in simultaneous watching: {e}")
        return False


async def main():
    """Run watch client examples."""
    # Use local configuration
    watch_client = CardanoWatchClient(
        TEST_CONFIG["uri"], metadata=TEST_CONFIG["headers"], secure=False
    )
    submit_client = CardanoSubmitClient(
        TEST_CONFIG["uri"], metadata=TEST_CONFIG["headers"], secure=False
    )

    print("UTxO RPC Watch Examples")
    print("=" * 50)
    print(f"Connecting to: {watch_client.uri}")

    try:
        async with watch_client.async_connect() as connected_watch_client:
            async with submit_client.async_connect() as connected_submit_client:
                print("Connected successfully")

                # Submit transaction
                tx_ref, test_address = await example_submit_tx_with_assets(
                    connected_submit_client
                )

                if not tx_ref or not test_address:
                    print(
                        "Failed to submit transaction. Check your balance and configuration."
                    )
                    return

                # Watch for transaction
                await example_watch_all_patterns_simultaneously(
                    connected_watch_client, test_address, tx_ref
                )

                print("\nWatch examples completed")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
