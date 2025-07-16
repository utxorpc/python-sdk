"""Async submit client examples with transaction building.

This example demonstrates:
1. Building and submitting real transactions
2. Watching mempool for transactions (address, payment part, delegation part)
3. Watching mempool for specific assets and policy IDs
4. Waiting for transaction confirmation
"""

import asyncio
import spec_compatibility  # noqa: F401
from utxorpc import CardanoSubmitClient
from tx_builder import (
    TEST_CONFIG,
    create_wallet_from_mnemonic,
    build_simple_transaction,
    tx_to_bytes,
)
from pycardano import BlockFrostChainContext
from utxorpc_spec.utxorpc.v1alpha.submit.submit_pb2 import (
    Stage,
    TxPredicate,
    AnyChainTxPattern,
)
from utxorpc_spec.utxorpc.v1alpha.cardano.cardano_pb2 import (
    TxPattern,
    TxOutputPattern,
    AddressPattern,
    AssetPattern,
)


async def example_submit_tx_with_building(client: CardanoSubmitClient):
    """Example: Build and submit a real transaction"""
    print("\nExample: Building and submitting transaction")

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

        # Assertions
        assert signing_key is not None, "Expected signing key, got None"
        assert from_address is not None, "Expected from_address, got None"
        print(f"Address: {from_address}")

        # Check balance
        utxos = chain_context.utxos(str(from_address))
        assert utxos is not None, "Expected UTxOs, got None"
        assert isinstance(utxos, list), f"Expected UTxOs to be list, got {type(utxos)}"

        balance = sum(utxo.output.amount.coin for utxo in utxos)
        assert isinstance(balance, int), (
            f"Expected balance to be int, got {type(balance)}"
        )
        assert balance >= 0, f"Expected balance >= 0, got {balance}"
        print(f"Balance: {balance} lovelace")

        if balance < TEST_CONFIG["min_balance"]:
            print(f"Insufficient balance: {balance} < {TEST_CONFIG['min_balance']}")
            return None

        # Build transaction
        tx = build_simple_transaction(
            chain_context=chain_context,
            from_address=from_address,
            to_address=str(from_address),  # Send to self
            amount=TEST_CONFIG["send_amount"],
            signing_key=signing_key,
        )

        # Assertions
        assert tx is not None, "Expected transaction, got None"
        assert hasattr(tx, "id"), "Expected transaction to have id"
        assert hasattr(tx.id, "payload"), "Expected transaction id to have payload"

        tx_id = tx.id.payload.hex()
        assert isinstance(tx_id, str), f"Expected tx_id to be string, got {type(tx_id)}"
        assert len(tx_id) > 0, f"Expected tx_id length > 0, got {len(tx_id)}"
        print(f"Transaction built: {tx_id}")

        # Submit via UTxO RPC
        tx_bytes = tx_to_bytes(tx)
        assert isinstance(tx_bytes, bytes), (
            f"Expected tx_bytes to be bytes, got {type(tx_bytes)}"
        )
        assert len(tx_bytes) > 0, f"Expected tx_bytes length > 0, got {len(tx_bytes)}"

        server_ref = await client.async_submit_tx(tx_bytes)
        assert server_ref is not None, "Expected server_ref, got None"
        assert isinstance(server_ref, bytes), (
            f"Expected server_ref to be bytes, got {type(server_ref)}"
        )
        assert len(server_ref) > 0, (
            f"Expected server_ref length > 0, got {len(server_ref)}"
        )

        print(f"Transaction submitted: {server_ref.hex()}")
        print("All transaction assertions passed!")

        return server_ref

    except Exception as e:
        print(f"Error: {e}")
        return None


async def example_watch_mempool_patterns(client: CardanoSubmitClient, test_address):
    """Example: Watch mempool for address, payment part, and delegation part patterns"""
    print("\nExample: Watching mempool for address patterns")

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

        # Assertions
        assert test_address is not None, "Expected test_address, got None"
        assert isinstance(address_bytes, bytes), (
            f"Expected address_bytes to be bytes, got {type(address_bytes)}"
        )
        assert len(address_bytes) > 0, (
            f"Expected address_bytes length > 0, got {len(address_bytes)}"
        )

        if payment_bytes:
            assert isinstance(payment_bytes, bytes), (
                f"Expected payment_bytes to be bytes, got {type(payment_bytes)}"
            )
            assert len(payment_bytes) > 0, (
                f"Expected payment_bytes length > 0, got {len(payment_bytes)}"
            )

        if delegation_bytes:
            assert isinstance(delegation_bytes, bytes), (
                f"Expected delegation_bytes to be bytes, got {type(delegation_bytes)}"
            )
            assert len(delegation_bytes) > 0, (
                f"Expected delegation_bytes length > 0, got {len(delegation_bytes)}"
            )

        print(f"Address: {test_address}")

        watchers = {}
        detected_txs = {"address": [], "payment": [], "delegation": []}

        # 1. Watch for address
        async def watch_address():
            predicate = TxPredicate()
            pattern = AnyChainTxPattern()
            tx_pattern = TxPattern()

            address_pattern = AddressPattern()
            address_pattern.exact_address = address_bytes
            tx_pattern.has_address.CopyFrom(address_pattern)

            pattern.cardano.CopyFrom(tx_pattern)
            predicate.match.CopyFrom(pattern)

            async for tx in client.async_watch_mempool(predicate):
                tx_id = tx.ref.hex()
                if tx_id not in detected_txs["address"]:
                    detected_txs["address"].append(tx_id)
                    print(f"Address watcher detected: {tx_id[:16]}...")
                if len(detected_txs["address"]) >= 2:
                    return "address"

        watchers["address"] = asyncio.create_task(watch_address())

        # 2. Watch for payment part
        if payment_bytes:

            async def watch_payment():
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

                async for tx in client.async_watch_mempool(predicate):
                    tx_id = tx.ref.hex()
                    if tx_id not in detected_txs["payment"]:
                        detected_txs["payment"].append(tx_id)
                        print(f"Payment watcher detected: {tx_id[:16]}...")
                    if len(detected_txs["payment"]) >= 2:
                        return "payment"

            watchers["payment"] = asyncio.create_task(watch_payment())

        # 3. Watch for delegation part
        if delegation_bytes:

            async def watch_delegation():
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

                async for tx in client.async_watch_mempool(predicate):
                    tx_id = tx.ref.hex()
                    if tx_id not in detected_txs["delegation"]:
                        detected_txs["delegation"].append(tx_id)
                        print(f"Delegation watcher detected: {tx_id[:16]}...")
                    if len(detected_txs["delegation"]) >= 2:
                        return "delegation"

            watchers["delegation"] = asyncio.create_task(watch_delegation())

        # Wait for watchers
        try:
            done, pending = await asyncio.wait(
                list(watchers.values()),
                timeout=10.0,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

        except asyncio.TimeoutError:
            pass

        # Results
        print(f"Address watcher: {len(detected_txs['address'])} transactions")
        if payment_bytes:
            print(f"Payment watcher: {len(detected_txs['payment'])} transactions")
        if delegation_bytes:
            print(f"Delegation watcher: {len(detected_txs['delegation'])} transactions")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


async def example_watch_mempool_for_asset(client: CardanoSubmitClient):
    """Example: Watch mempool for specific asset by submitting a transaction"""
    print("\nExample: Watching mempool for specific asset")

    try:
        # Specific asset to watch for
        asset_subject = bytes.fromhex(
            "8b05e87a51c1d4a0fa888d2bb14dbc25e8c343ea379a171b63aa84a0434e4354"
        )

        # Build predicate for asset watching
        predicate = TxPredicate()
        pattern = AnyChainTxPattern()
        tx_pattern = TxPattern()

        asset_pattern = AssetPattern()
        asset_pattern.asset_name = asset_subject
        tx_pattern.moves_asset.CopyFrom(asset_pattern)

        pattern.cardano.CopyFrom(tx_pattern)
        predicate.match.CopyFrom(pattern)

        # Start watching in background
        async def watch_for_asset_tx():
            async for tx in client.async_watch_mempool(predicate):
                print(f"Detected transaction with asset: {tx.ref.hex()[:16]}")
                return tx
            return None

        watcher_task = asyncio.create_task(watch_for_asset_tx())
        await asyncio.sleep(0.5)

        # Submit a transaction with the asset
        signing_key, test_address = create_wallet_from_mnemonic(
            TEST_CONFIG["mnemonic"], TEST_CONFIG["network"]
        )

        chain_context = BlockFrostChainContext(
            project_id=TEST_CONFIG["blockfrost_api_key"],
            network=TEST_CONFIG["network"],
            base_url="https://cardano-preview.blockfrost.io/api",
        )

        tx = build_simple_transaction(
            chain_context=chain_context,
            from_address=test_address,
            to_address=str(test_address),
            amount=TEST_CONFIG["send_amount"],
            signing_key=signing_key,
        )

        tx_id = tx.id.payload.hex()
        tx_bytes = tx_to_bytes(tx)

        tx_ref = await client.async_submit_tx(tx_bytes)
        print(f"Submitted transaction: {tx_id}")

        # Wait for watcher to detect the transaction
        try:
            result = await asyncio.wait_for(watcher_task, timeout=10.0)
            if result:
                print("Asset watcher detected the transaction")
        except asyncio.TimeoutError:
            print("Timeout waiting for asset detection")
            watcher_task.cancel()

        return tx_ref

    except Exception as e:
        print(f"Error: {e}")
        return None


async def example_watch_mempool_for_policy_id(client: CardanoSubmitClient):
    """Example: Watch mempool for policy ID by submitting a transaction"""
    print("\nExample: Watching mempool for policy ID")

    try:
        # Policy ID to watch for
        policy_id = bytes.fromhex(
            "8b05e87a51c1d4a0fa888d2bb14dbc25e8c343ea379a171b63aa84a0"
        )

        # Build predicate for policy ID watching
        predicate = TxPredicate()
        pattern = AnyChainTxPattern()
        tx_pattern = TxPattern()

        asset_pattern = AssetPattern()
        asset_pattern.policy_id = policy_id
        tx_pattern.moves_asset.CopyFrom(asset_pattern)

        pattern.cardano.CopyFrom(tx_pattern)
        predicate.match.CopyFrom(pattern)

        # Start watching in background
        async def watch_for_policy_tx():
            async for tx in client.async_watch_mempool(predicate):
                print(f"Detected transaction with policy ID: {tx.ref.hex()[:16]}")
                return tx
            return None

        watcher_task = asyncio.create_task(watch_for_policy_tx())
        await asyncio.sleep(0.5)

        # Submit a transaction with the asset
        signing_key, test_address = create_wallet_from_mnemonic(
            TEST_CONFIG["mnemonic"], TEST_CONFIG["network"]
        )

        chain_context = BlockFrostChainContext(
            project_id=TEST_CONFIG["blockfrost_api_key"],
            network=TEST_CONFIG["network"],
            base_url="https://cardano-preview.blockfrost.io/api",
        )

        tx = build_simple_transaction(
            chain_context=chain_context,
            from_address=test_address,
            to_address=str(test_address),
            amount=TEST_CONFIG["send_amount"],
            signing_key=signing_key,
        )

        tx_id = tx.id.payload.hex()
        tx_bytes = tx_to_bytes(tx)

        tx_ref = await client.async_submit_tx(tx_bytes)
        print(f"Submitted transaction: {tx_id}")

        # Wait for watcher to detect the transaction
        try:
            result = await asyncio.wait_for(watcher_task, timeout=10.0)
            if result:
                print("Policy ID watcher detected the transaction")
        except asyncio.TimeoutError:
            print("Timeout waiting for policy ID detection")
            watcher_task.cancel()

        return tx_ref

    except Exception as e:
        print(f"Error: {e}")
        return None


async def example_wait_for_tx_confirmation(client: CardanoSubmitClient, tx_ref: bytes):
    """Example: Wait for transaction confirmation"""
    if not tx_ref:
        print("\nSkipping waitForTx test (no transaction reference)")
        return

    print("\nTesting waitForTx for confirmation")

    try:
        print(f"Waiting for transaction {tx_ref.hex()[:16]}")

        stage_count = 0
        async for stage in client.async_wait_for_tx(tx_ref):
            stage_count += 1
            print(f"Stage {stage_count}: {Stage.Name(stage)}")

            if stage_count >= 1:
                break

        if stage_count >= 1:
            print("Transaction confirmed")
        else:
            print("Transaction not yet confirmed")

    except Exception as e:
        print(f"Error waiting for transaction: {e}")


async def main():
    """Run all submit client tests."""
    client = CardanoSubmitClient(
        TEST_CONFIG["uri"], metadata=TEST_CONFIG["headers"], secure=False
    )

    print("UTxO RPC Async Submit Examples")
    print("=" * 50)
    print(f"Connecting to: {TEST_CONFIG['uri']}")

    async with client.async_connect() as connected_client:
        print("Connected successfully")

        _, test_address = create_wallet_from_mnemonic(
            TEST_CONFIG["mnemonic"], TEST_CONFIG["network"]
        )

        await example_watch_mempool_for_asset(connected_client)
        await example_watch_mempool_for_policy_id(connected_client)
        tx_ref = await example_submit_tx_with_building(connected_client)
        await example_watch_mempool_patterns(connected_client, test_address)

        if tx_ref:
            await example_wait_for_tx_confirmation(connected_client, tx_ref)

        print("\nAll async submit examples completed")


if __name__ == "__main__":
    asyncio.run(main())
