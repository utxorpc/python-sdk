"""Decodes the Cardano vectors with the spec's generated types."""

import csv
from pathlib import Path

import pytest
from utxorpc_spec.utxorpc.v1alpha.cardano import cardano_pb2 as v1alpha
from utxorpc_spec.utxorpc.v1beta.cardano import cardano_pb2 as v1beta

VECTORS = Path(__file__).parent / "vectors" / "cardano"

with open(VECTORS / "vectors.tsv", newline="") as index:
    ROWS = list(csv.DictReader(index, delimiter="\t"))


@pytest.mark.parametrize("row", ROWS, ids=[row["name"] for row in ROWS])
@pytest.mark.parametrize("version,module", [("v1alpha", v1alpha), ("v1beta", v1beta)])
def test_decodes_vector(version, module, row):
    raw = (VECTORS / version / f"{row['name']}.pb").read_bytes()

    block = module.Block()
    block.ParseFromString(raw)

    assert block.header.slot == int(row["slot"])
    assert block.header.hash.hex() == row["hash"]
    assert len(block.body.tx) == int(row["tx_count"])
    if row["first_tx_hash"] != "-":
        assert block.body.tx[0].hash.hex() == row["first_tx_hash"]
    assert block.SerializeToString(deterministic=True) == raw
