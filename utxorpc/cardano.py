import base64
from typing import Optional, Union

from typing_extensions import TypeAlias
from utxorpc_spec.utxorpc.v1alpha.cardano.cardano_pb2 import (  # type: ignore
    Block,
    TxOutput,
    TxOutputPattern,
)
from utxorpc_spec.utxorpc.v1alpha.query.query_pb2 import (  # type: ignore
    AnyUtxoPattern,
    AnyUtxoData,
    TxoRef,
)
from utxorpc_spec.utxorpc.v1alpha.sync.sync_pb2 import (  # type: ignore
    AnyChainBlock,
    BlockRef,
)

from utxorpc.generics import Chain
from utxorpc.generics.clients.query_client import QueryClient
from utxorpc.generics.clients.sync_client import SyncClient


CardanoBlock: TypeAlias = Block
CardanoTxOutputPattern: TypeAlias = TxOutputPattern
CardanoTxOutput: TypeAlias = TxOutput


class CardanoAddress:
    hash: bytes

    def __init__(self, hash: bytes):
        self.hash = hash

    @classmethod
    def from_hex(cls, string: str) -> "CardanoAddress":
        return CardanoAddress(bytes.fromhex(string))

    @classmethod
    def from_base64(cls, string: str) -> "CardanoAddress":
        return CardanoAddress(base64.b64decode(string))


class CardanoPoint:
    slot: int
    hash: bytes

    def __init__(self, slot: int, hash: Union[bytes, str]):
        self.slot = slot
        if isinstance(hash, str):
            self.hash = bytes.fromhex(hash)
        else:
            self.hash = hash


class CardanoTxoRef:
    index: int
    hash: bytes

    def __init__(self, index: int, hash: bytes):
        self.index = index
        self.hash = hash

    @classmethod
    def from_hex(cls, index: int, hash: str) -> "CardanoTxoRef":
        return cls(index=index, hash=bytes.fromhex(hash))

    @classmethod
    def from_base64(cls, index: int, hash: str) -> "CardanoTxoRef":
        return cls(index=index, hash=base64.b64decode(hash))


class CardanoChain(
    Chain[
        CardanoBlock,
        CardanoPoint,
        CardanoTxOutputPattern,
        CardanoTxOutput,
        CardanoTxoRef,
    ]
):
    @staticmethod
    def any_chain_to_block(message: AnyChainBlock) -> Optional[CardanoBlock]:
        try:
            return message.cardano
        except (IndexError, AttributeError):
            return None

    @staticmethod
    def point_to_block_ref(point: CardanoPoint) -> BlockRef:
        return BlockRef(index=point.slot, hash=point.hash)

    @staticmethod
    def block_ref_to_point(block_ref: BlockRef) -> CardanoPoint:
        return CardanoPoint(slot=block_ref.index, hash=block_ref.hash)

    @staticmethod
    def any_utxo_data_to_tx_output(any_utxo_data: AnyUtxoData) -> CardanoTxOutput:
        return any_utxo_data.cardano

    @staticmethod
    def tx_output_pattern_to_any_utxo_pattern(
        tx_output_pattern: CardanoTxOutputPattern,
    ) -> AnyUtxoPattern:
        return AnyUtxoPattern(cardano=tx_output_pattern)

    @staticmethod
    def chain_txo_ref_to_txo_ref(txo_ref: CardanoTxoRef) -> TxoRef:
        return TxoRef(index=txo_ref.index, hash=txo_ref.hash)


class CardanoQueryClient(
    QueryClient[CardanoTxOutputPattern, CardanoTxOutput, CardanoTxoRef]
):
    chain = CardanoChain


class CardanoSyncClient(SyncClient[CardanoBlock, CardanoPoint]):
    chain = CardanoChain
