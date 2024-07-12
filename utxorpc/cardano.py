from typing import (
    Optional,
    Union,
)

from typing_extensions import TypeAlias
from utxorpc_spec.utxorpc.v1alpha.cardano.cardano_pb2 import Block  # type: ignore
from utxorpc_spec.utxorpc.v1alpha.sync.sync_pb2 import (  # type: ignore
    AnyChainBlock,
    BlockRef,
)

from utxorpc.generics import Chain
from utxorpc.generics.clients.sync_client import SyncClient


CardanoBlock: TypeAlias = Block


class CardanoPoint:
    slot: int
    hash: bytes

    def __init__(self, slot: int, hash: Union[bytes, str]):
        self.slot = slot
        if isinstance(hash, str):
            self.hash = bytes.fromhex(hash)
        else:
            self.hash = hash


class CardanoChain(Chain[CardanoBlock, CardanoPoint]):
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


class CardanoSyncClient(SyncClient[CardanoBlock, CardanoPoint]):
    chain = CardanoChain
