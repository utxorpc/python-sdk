from typing import Optional, Protocol, TypeVar

from utxorpc_spec.utxorpc.v1alpha.query.query_pb2 import (  # type: ignore
    AnyUtxoPattern,
    AnyUtxoData,
    TxoRef,
)
from utxorpc_spec.utxorpc.v1alpha.sync.sync_pb2 import (  # type: ignore
    AnyChainBlock,
    BlockRef,
)


BlockType = TypeVar("BlockType", covariant=True)
PointType = TypeVar("PointType")
TxOutputPatternType = TypeVar("TxOutputPatternType")
TxOutputType = TypeVar("TxOutputType", covariant=True)
TxoRefType = TypeVar("TxoRefType", contravariant=True)


class Chain(
    Protocol[BlockType, PointType, TxOutputPatternType, TxOutputType, TxoRefType]
):
    @staticmethod
    def any_chain_to_block(message: AnyChainBlock) -> Optional[BlockType]: ...

    @staticmethod
    def point_to_block_ref(point: PointType) -> BlockRef: ...

    @staticmethod
    def block_ref_to_point(block_ref: BlockRef) -> PointType: ...

    @staticmethod
    def tx_output_pattern_to_any_utxo_pattern(
        tx_output_pattern: TxOutputPatternType,
    ) -> AnyUtxoPattern: ...

    @staticmethod
    def any_utxo_pattern_to_tx_output_pattern(
        any_utxo_pattern: AnyUtxoPattern,
    ) -> TxOutputPatternType: ...

    @staticmethod
    def any_utxo_data_to_tx_output(any_utxo_data: AnyUtxoData) -> TxOutputType: ...

    @staticmethod
    def chain_txo_ref_to_txo_ref(txo_ref: TxoRefType) -> TxoRef: ...
