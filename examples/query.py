"""Query UTxO RPC server for blockchain data.

To generate an API key you can do the following:

1. Install and configure dmtr cli. See instructions [here](https://docs.demeter.run/cli)
2. Use `dmtr ports create` to create a free UTxO RPC port.
3. Enjoy :)

"""

import os
import spec_compatibility  # noqa: F401
from utxorpc import CardanoQueryClient
from utxorpc_spec.utxorpc.v1alpha.query.query_pb2 import (  # type: ignore
    UtxoPredicate,
    AnyUtxoPattern,
)
from utxorpc_spec.utxorpc.v1alpha.cardano.cardano_pb2 import (  # type: ignore
    TxOutputPattern,
    AddressPattern,
    AssetPattern,
)


def example_read_params(client):
    """Example: Read blockchain parameters"""
    print("\nExample 1: Reading blockchain parameters")

    params = client.read_params()

    # Assertions
    assert params is not None, "Expected params response, got None"
    assert hasattr(params, "values"), "Expected params to have 'values' field"
    assert params.values is not None, "Expected params.values to not be None"
    assert hasattr(params.values, "cardano"), (
        "Expected params.values to have 'cardano' field"
    )
    assert params.values.cardano is not None, (
        "Expected Cardano parameters to not be None"
    )

    if params.values and params.values.cardano:
        p = params.values.cardano
        print("Blockchain parameters:")

        # Basic assertions for critical parameters
        if hasattr(p, "protocol_version") and p.protocol_version:
            assert p.protocol_version.major > 0, (
                f"Expected protocol major > 0, got {p.protocol_version.major}"
            )
            assert p.protocol_version.minor >= 0, (
                f"Expected protocol minor >= 0, got {p.protocol_version.minor}"
            )

        print("All parameter assertions passed!")

        # Print available fields safely
        if hasattr(p, "protocol_version") and p.protocol_version:
            print(
                f"   - Protocol version: {p.protocol_version.major}.{p.protocol_version.minor}"
            )

        # Numeric fields
        fields = {
            "min_fee_a": "Min fee coefficient",
            "min_fee_b": "Min fee constant",
            "max_block_size": "Max block body size",
            "max_tx_size": "Max transaction size",
            "key_deposit": "Stake key deposit",
            "pool_deposit": "Pool deposit",
            "min_pool_cost": "Min pool cost",
            "max_value_size": "Max value size",
            "collateral_percentage": "Collateral percentage",
            "max_collateral_inputs": "Max collateral inputs",
        }

        for field, label in fields.items():
            if hasattr(p, field):
                value = getattr(p, field)
                if field.endswith("deposit") or field.endswith("cost"):
                    print(f"   - {label}: {value} lovelace")
                elif field.endswith("size"):
                    print(f"   - {label}: {value} bytes")
                elif field.endswith("percentage"):
                    print(f"   - {label}: {value}%")
                else:
                    print(f"   - {label}: {value}")

        # Price memory and steps
        if hasattr(p, "prices") and p.prices:
            if hasattr(p.prices, "memory") and p.prices.memory:
                print(
                    f"   - Price memory: {p.prices.memory.numerator}/{p.prices.memory.denominator}"
                )
            if hasattr(p.prices, "steps") and p.prices.steps:
                print(
                    f"   - Price steps: {p.prices.steps.numerator}/{p.prices.steps.denominator}"
                )

        # Execution units
        if hasattr(p, "max_tx_ex_units") and p.max_tx_ex_units:
            print(
                f"   - Max tx execution units: memory={p.max_tx_ex_units.memory}, steps={p.max_tx_ex_units.steps}"
            )
        if hasattr(p, "max_block_ex_units") and p.max_block_ex_units:
            print(
                f"   - Max block execution units: memory={p.max_block_ex_units.memory}, steps={p.max_block_ex_units.steps}"
            )

        # Cost models
        if hasattr(p, "cost_models") and p.cost_models:
            models = []
            if hasattr(p.cost_models, "plutus_v1") and p.cost_models.plutus_v1:
                models.append(
                    f"PlutusV1 ({len(p.cost_models.plutus_v1.values)} params)"
                )
            if hasattr(p.cost_models, "plutus_v2") and p.cost_models.plutus_v2:
                models.append(
                    f"PlutusV2 ({len(p.cost_models.plutus_v2.values)} params)"
                )
            if hasattr(p.cost_models, "plutus_v3") and p.cost_models.plutus_v3:
                models.append(
                    f"PlutusV3 ({len(p.cost_models.plutus_v3.values)} params)"
                )
            if models:
                print(f"   - Cost models: {', '.join(models)}")


def example_read_utxos_by_ref(client):
    """Example: Read specific UTxOs by output reference"""
    from utxorpc_spec.utxorpc.v1alpha.query.query_pb2 import TxoRef  # type: ignore

    print("\nExample 2: Reading UTxOs by output reference")

    # Example UTXO reference (transaction hash + output index)
    tx_hash = bytes.fromhex(
        "9874bdf4ad47b2d30a2146fc4ba1f94859e58e772683e75001aca6e85de7690d"
    )
    output_index = 0

    # Create TxoRef message
    txo_ref = TxoRef(hash=tx_hash, index=output_index)

    try:
        response = client.read_utxos([txo_ref])

        # Assertions
        assert response is not None, "Expected response, got None"
        assert hasattr(response, "items"), "Expected response to have 'items' field"

        if response.items:
            print(f"Found {len(response.items)} UTXO(s)")
            assert len(response.items) > 0, "Expected at least one UTXO item"

            for i, item in enumerate(response.items):
                assert item is not None, f"Expected item {i} to not be None"
                if hasattr(item, "cardano") and item.cardano:
                    if hasattr(item.cardano, "txo") and item.cardano.txo:
                        txo = item.cardano.txo
                        print(f"   UTXO {i + 1}:")

                        # Assertions for UTXO structure
                        if hasattr(txo, "coin") and txo.coin:
                            assert isinstance(txo.coin, int), (
                                f"Expected coin to be int, got {type(txo.coin)}"
                            )
                            assert txo.coin > 0, f"Expected coin > 0, got {txo.coin}"
                            print(f"     - Value: {txo.coin} lovelace")

                        if hasattr(txo, "address") and txo.address:
                            assert isinstance(txo.address, bytes), (
                                f"Expected address to be bytes, got {type(txo.address)}"
                            )
                            assert len(txo.address) > 0, (
                                f"Expected address length > 0, got {len(txo.address)}"
                            )
                            print(f"     - Address: {txo.address.hex()[:40]}...")

                        if hasattr(txo, "assets") and txo.assets:
                            assert len(txo.assets) >= 0, (
                                f"Expected assets length >= 0, got {len(txo.assets)}"
                            )
                            print(f"     - Assets: {len(txo.assets)} group(s)")

            print("All UTXO assertions passed!")
        else:
            print("No UTxOs found for this reference")
    except Exception as e:
        print(f"Error: {e}")


def example_search_utxos_by_address(client):
    """Example: Search UTxOs by address"""
    print("\nExample 3: Searching UTxOs by address")

    # Test address (preview network)
    # addr_test1qpefcf7srnr0u0q2ljugw7rhd7cvkthevwpaznl0e532sqa00wm4wxec8q7wmf6yyn05j30svdxevyg0n6ytv25qtaqnm9h4j

    # Address components
    payment_part = bytes.fromhex(
        "79b7c890294b7e3b16bd1df5f71f14c0122a598d56701f705405ea9a"
    )
    delegation_part = bytes.fromhex(
        "acaea823b1510c83335a9781a0be679994f76e5609998de5144dd82f"
    )
    # Full address bytes (network byte 0x00 + payment + delegation)
    full_address = bytes.fromhex(
        "0079b7c890294b7e3b16bd1df5f71f14c0122a598d56701f705405ea9aacaea823b1510c83335a9781a0be679994f76e5609998de5144dd82f"
    )

    # Test 1: Search by full address
    print("\n   Searching by full address...")
    pattern = AnyUtxoPattern()
    pattern.cardano.CopyFrom(
        TxOutputPattern(address=AddressPattern(exact_address=full_address))
    )

    predicate = UtxoPredicate(match=pattern)

    try:
        results = client.search_utxos(predicate=predicate)

        # Assertions
        assert results is not None, "Expected search results, got None"
        assert hasattr(results, "__iter__"), "Expected results to be iterable"

        total_utxos = sum(len(batch.items) for batch in results if batch.items)
        assert total_utxos >= 0, f"Expected total_utxos >= 0, got {total_utxos}"
        print(f"   Found {total_utxos} UTXO(s) matching full address")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Search by payment part
    print("\n   Searching by payment part...")
    pattern = AnyUtxoPattern()
    pattern.cardano.CopyFrom(
        TxOutputPattern(address=AddressPattern(payment_part=payment_part))
    )

    predicate = UtxoPredicate(match=pattern)

    try:
        results = client.search_utxos(predicate=predicate)
        total_utxos = sum(len(batch.items) for batch in results if batch.items)
        print(f"   Found {total_utxos} UTXO(s) matching payment part")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Search by delegation part
    print("\n   Searching by delegation part...")
    pattern = AnyUtxoPattern()
    pattern.cardano.CopyFrom(
        TxOutputPattern(address=AddressPattern(delegation_part=delegation_part))
    )

    predicate = UtxoPredicate(match=pattern)

    try:
        results = client.search_utxos(predicate=predicate)
        total_utxos = sum(len(batch.items) for batch in results if batch.items)
        print(f"   Found {total_utxos} UTXO(s) matching delegation part")

        # Show first UTXO as example if found
        if total_utxos > 0:
            for batch in results:
                if batch.items and len(batch.items) > 0:
                    item = batch.items[0]
                    if hasattr(item, "cardano") and item.cardano:
                        if hasattr(item.cardano, "txo") and item.cardano.txo:
                            txo = item.cardano.txo
                            print("\n   Example UTXO:")
                            if hasattr(txo, "coin"):
                                print(f"     - Value: {txo.coin} lovelace")
                            if hasattr(txo, "address") and txo.address:
                                print(f"     - Address: {txo.address.hex()[:60]}...")
                            break
    except Exception as e:
        print(f"   Error: {e}")


def example_search_utxos_by_policy_id(client):
    """Example: Search UTxOs by policy ID"""
    print("\nExample 4: Searching UTxOs by policy ID")

    # Example policy ID (hex)
    policy_id = bytes.fromhex(
        "047e0f912c4260fe66ae271e5ae494dcd5f79635bbbb1386be195f4e"
    )

    # Create pattern for Cardano
    pattern = AnyUtxoPattern()
    pattern.cardano.CopyFrom(TxOutputPattern(asset=AssetPattern(policy_id=policy_id)))

    predicate = UtxoPredicate(match=pattern)

    try:
        results = client.search_utxos(predicate=predicate)
        total_utxos = 0
        for batch in results:
            if batch.items:
                total_utxos += len(batch.items)
                # Show details of first UTXO as example
                if (
                    total_utxos == len(batch.items)
                    and hasattr(batch.items[0], "cardano")
                    and batch.items[0].cardano
                ):
                    if (
                        hasattr(batch.items[0].cardano, "txo")
                        and batch.items[0].cardano.txo
                    ):
                        txo = batch.items[0].cardano.txo
                        if hasattr(txo, "assets") and txo.assets:
                            for asset_group in txo.assets:
                                if (
                                    hasattr(asset_group, "policy_id")
                                    and asset_group.policy_id == policy_id
                                ):
                                    print(
                                        f"Found UTxOs with policy ID: {policy_id.hex()[:16]}..."
                                    )
                                    if (
                                        hasattr(asset_group, "assets")
                                        and asset_group.assets
                                    ):
                                        print(
                                            f"   - Contains {len(asset_group.assets)} asset(s)"
                                        )
                                    break

        print(f"Total UTxOs found: {total_utxos}")
    except Exception as e:
        print(f"Error: {e}")


def example_search_utxos_by_asset(client):
    """Example: Search UTxOs by specific asset (policy ID + asset name)"""
    print("\nExample 5: Searching UTxOs by specific asset")

    # Example: Search for a specific token
    policy_id = bytes.fromhex(
        "047e0f912c4260fe66ae271e5ae494dcd5f79635bbbb1386be195f4e"
    )
    asset_name = bytes.fromhex(
        "414c4c45594b41545a3030303630"
    )  # "ALLEYKATZ00060" in hex

    # Note: Some servers may not support searching by both policy_id and asset_name
    # Try with just policy_id first
    pattern = AnyUtxoPattern()
    pattern.cardano.CopyFrom(
        TxOutputPattern(
            asset=AssetPattern(
                policy_id=policy_id
                # Removed asset_name to avoid "conflicting asset criteria" error
            )
        )
    )

    predicate = UtxoPredicate(match=pattern)

    try:
        results = client.search_utxos(predicate=predicate)
        total_utxos = 0
        matching_with_name = 0

        for batch in results:
            if batch.items:
                total_utxos += len(batch.items)
                # Check for specific asset name in results
                for item in batch.items:
                    if hasattr(item, "cardano") and item.cardano:
                        if hasattr(item.cardano, "txo") and item.cardano.txo:
                            txo = item.cardano.txo
                            if hasattr(txo, "assets") and txo.assets:
                                for asset_group in txo.assets:
                                    if (
                                        hasattr(asset_group, "policy_id")
                                        and asset_group.policy_id == policy_id
                                    ):
                                        if (
                                            hasattr(asset_group, "assets")
                                            and asset_group.assets
                                        ):
                                            for asset in asset_group.assets:
                                                if (
                                                    hasattr(asset, "name")
                                                    and asset.name == asset_name
                                                ):
                                                    matching_with_name += 1

        print(f"Found {total_utxos} UTXO(s) with policy ID: {policy_id.hex()[:16]}...")
        if matching_with_name > 0:
            print(
                f"   - {matching_with_name} UTXO(s) contain the specific asset: {asset_name.hex()}"
            )
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
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
        if not API_KEY:
            print("Warning: DMTR_API_KEY environment variable not set!")
            print("   Some examples may fail without a valid API key.")
            print("   Get your API key from: https://demeter.run")
            print("\nTip: Run with --local to test against localhost:50051")
            return
        metadata = {"dmtr-api-key": API_KEY}
        secure = True

    print("UTxO RPC Query Examples")
    print("=" * 50)
    print(f"Connecting to: {HOST}")

    client = CardanoQueryClient(HOST, metadata=metadata, secure=secure)

    try:
        with client.connect() as connected_client:
            print("Connected successfully")

            # Run all examples
            example_read_params(connected_client)
            example_read_utxos_by_ref(connected_client)
            example_search_utxos_by_address(connected_client)
            example_search_utxos_by_policy_id(connected_client)
            example_search_utxos_by_asset(connected_client)

            print("\nAll examples completed")

    except Exception as e:
        print(f"\nConnection error: {e}")
        print("   Please check your API key and network connection.")


if __name__ == "__main__":
    main()
