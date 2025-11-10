"""
Fix import paths for utxorpc-spec package.
This must be imported before any utxorpc usage.
"""

import sys

# Only set up the mapping if not already done
if "utxorpc.v1alpha" not in sys.modules:
    import utxorpc_spec.utxorpc
    import utxorpc_spec.utxorpc.v1alpha
    import utxorpc_spec.utxorpc.v1alpha.cardano
    import utxorpc_spec.utxorpc.v1alpha.sync
    import utxorpc_spec.utxorpc.v1alpha.query
    import utxorpc_spec.utxorpc.v1alpha.submit
    import utxorpc_spec.utxorpc.v1alpha.watch

    # Map the modules to fix incorrect import paths in protobuf files
    sys.modules["utxorpc.v1alpha"] = utxorpc_spec.utxorpc.v1alpha
    sys.modules["utxorpc.v1alpha.cardano"] = utxorpc_spec.utxorpc.v1alpha.cardano
    sys.modules["utxorpc.v1alpha.sync"] = utxorpc_spec.utxorpc.v1alpha.sync
    sys.modules["utxorpc.v1alpha.query"] = utxorpc_spec.utxorpc.v1alpha.query
    sys.modules["utxorpc.v1alpha.submit"] = utxorpc_spec.utxorpc.v1alpha.submit
    sys.modules["utxorpc.v1alpha.watch"] = utxorpc_spec.utxorpc.v1alpha.watch
