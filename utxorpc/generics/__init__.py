from typing import Optional, Protocol, TypeVar

from utxorpc_spec.utxorpc.v1alpha.sync.sync_pb2 import (  # type: ignore
    AnyChainBlock,
    BlockRef,
)

BlockType = TypeVar("BlockType", covariant=True)
PointType = TypeVar("PointType")


class Chain(Protocol[BlockType, PointType]):
    @staticmethod
    def any_chain_to_block(message: AnyChainBlock) -> Optional[BlockType]: ...

    @staticmethod
    def point_to_block_ref(point: PointType) -> BlockRef: ...

    @staticmethod
    def block_ref_to_point(block_ref: BlockRef) -> PointType: ...
