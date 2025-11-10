"""Simple transaction builder helper for UTxO RPC using PyCardano."""

from pycardano import (
    PaymentSigningKey,
    PaymentVerificationKey,
    HDWallet,
    Address,
    Network,
    TransactionBuilder,
    TransactionOutput,
    Value,
)


TEST_CONFIG = {
    "uri": "localhost:50051",
    "headers": {},
    "network": Network.TESTNET,  # Preview testnet
    "blockfrost_api_key": "previewajMhMPYerz9Pd3GsqjayLwP5mgnNnZCC",
    "mnemonic": "february next piano since banana hurdle tide soda reward hood luggage bronze polar veteran fold doctor melt usual rose coral mask interest army clump",
    "min_balance": 6_000_000,
    "send_amount": 5_000_000,
}


def create_wallet_from_mnemonic(mnemonic: str, network: Network = Network.TESTNET):
    """Create wallet from mnemonic phrase.

    Note: This uses PyCardano's standard derivation which may differ from other wallets like Blaze.
    For compatibility with Blaze-generated addresses, you may need to use the address directly.
    """
    print(f"\n🔑 Address Derivation Process:")
    print(f"   Network: {network}")
    print(f"   Mnemonic (first 6 words): {' '.join(mnemonic.split()[:6])}...")
    
    # Create HD wallet from mnemonic
    hdwallet = HDWallet.from_mnemonic(mnemonic)
    print(f"   ✓ HD Wallet created from mnemonic")

    # Derive payment key using standard Cardano derivation path
    # m/1852'/1815'/0'/0/0
    print(f"   📍 Deriving payment key path: m/1852'/1815'/0'/0/0")
    hdwallet_payment = (
        hdwallet.derive(1852, hardened=True)  # Purpose (CIP-1852)
        .derive(1815, hardened=True)  # Cardano coin type
        .derive(0, hardened=True)  # Account 0
        .derive(0)  # External chain
        .derive(0)  # First address
    )
    payment_signing_key = PaymentSigningKey.from_primitive(
        hdwallet_payment.xprivate_key[:32]
    )
    payment_verification_key = PaymentVerificationKey.from_signing_key(
        payment_signing_key
    )
    print(f"   ✓ Payment key derived")
    print(f"     Payment key hash: {payment_verification_key.hash().to_primitive().hex()}")

    # Derive staking key using standard path
    # m/1852'/1815'/0'/2/0
    print(f"   📍 Deriving staking key path: m/1852'/1815'/0'/2/0")
    hdwallet_stake = (
        hdwallet.derive(1852, hardened=True)  # Purpose (CIP-1852)
        .derive(1815, hardened=True)  # Cardano coin type
        .derive(0, hardened=True)  # Account 0
        .derive(2)  # Staking key
        .derive(0)  # First staking key
    )
    from pycardano import StakeSigningKey, StakeVerificationKey

    stake_signing_key = StakeSigningKey.from_primitive(hdwallet_stake.xprivate_key[:32])
    stake_verification_key = StakeVerificationKey.from_signing_key(stake_signing_key)
    print(f"   ✓ Staking key derived")
    print(f"     Staking key hash: {stake_verification_key.hash().to_primitive().hex()}")

    # Create base address (with staking)
    address = Address(
        payment_verification_key.hash(), stake_verification_key.hash(), network=network
    )
    
    print(f"\n🏠 Final Address Details:")
    print(f"   Address: {address}")
    print(f"   Address bytes: {address.to_primitive().hex()}")
    print(f"   Payment part: {address.payment_part.to_primitive().hex() if address.payment_part else 'None'}")
    print(f"   Staking part: {address.staking_part.to_primitive().hex() if address.staking_part else 'None'}")

    return payment_signing_key, address


def build_simple_transaction(
    chain_context,
    from_address: Address,
    to_address: str,
    amount: int,
    signing_key: PaymentSigningKey,
):
    """Build a simple payment transaction with existing assets."""
    from pycardano import MultiAsset, Asset

    # Create transaction builder
    builder = TransactionBuilder(chain_context)

    # Add inputs from address
    builder.add_input_address(from_address)

    # Check if we have assets in UTxOs and include them
    utxos = chain_context.utxos(str(from_address))
    total_assets = MultiAsset()

    # Collect all assets from UTxOs
    for utxo in utxos:
        if utxo.output.amount.multi_asset:
            for policy_id, assets in utxo.output.amount.multi_asset.items():
                if policy_id not in total_assets:
                    total_assets[policy_id] = Asset()
                for asset_name, asset_amount in assets.items():
                    if asset_name in total_assets[policy_id]:
                        total_assets[policy_id][asset_name] += asset_amount
                    else:
                        total_assets[policy_id][asset_name] = asset_amount

    # If we have assets, send a small amount (1 unit) of the first asset found
    output_value = Value(amount)
    if total_assets:
        # Find the first asset and send 1 unit of it
        for policy_id, assets in total_assets.items():
            if (
                policy_id.to_primitive().hex()
                == "8b05e87a51c1d4a0fa888d2bb14dbc25e8c343ea379a171b63aa84a0"
            ):
                # Send 1 unit of the first asset with this policy ID
                first_asset_name = next(iter(assets.keys()))
                send_assets = MultiAsset()
                send_assets[policy_id] = Asset({first_asset_name: 1})
                output_value = Value(amount, send_assets)
                break

    # Add output
    builder.add_output(
        TransactionOutput(Address.from_primitive(to_address), output_value)
    )

    # Build and sign transaction
    signed_tx = builder.build_and_sign(
        signing_keys=[signing_key], change_address=from_address
    )

    return signed_tx


def tx_to_bytes(tx) -> bytes:
    """Convert transaction to bytes for submission."""
    return bytes.fromhex(tx.to_cbor_hex())
