import asyncio
from enum import Enum
from typing import AsyncGenerator, Any, Generic, List, Optional, Iterable

from utxorpc_spec.utxorpc.v1alpha.sync.sync_pb2 import (  # type: ignore
    DumpHistoryRequest,
    FetchBlockRequest,
    FollowTipRequest,
)
from utxorpc_spec.utxorpc.v1alpha.sync.sync_pb2_grpc import ChainSyncServiceStub  # type: ignore

from utxorpc.generics import BlockType, PointType
from utxorpc.generics.clients import Client


class FollowTipResponseAction(Enum):
    apply = "APPLY"
    undo = "UNDO"
    reset = "RESET"


class FollowTipResponse(Generic[BlockType, PointType]):
    action: FollowTipResponseAction
    block: Optional[BlockType]
    point: Optional[PointType]

    def __init__(
        self,
        action: FollowTipResponseAction,
        block: Optional[BlockType],
        point: Optional[PointType],
    ) -> None:
        self.action = action
        if self.action in (FollowTipResponseAction.apply, FollowTipResponseAction.undo):
            assert block is not None, "block cannot be None if action is APPLY or UNDO"
            self.block = block
            self.point = None
        else:
            assert point is not None, "point cannot be None if action is RESET"
            self.block = None
            self.point = point


class SyncClient(Client[ChainSyncServiceStub], Generic[BlockType, PointType]):
    stub = ChainSyncServiceStub

    async def async_fetch_block(self, ref: Iterable[PointType]) -> Optional[BlockType]:
        stub = self.get_async_stub()
        response = await stub.FetchBlock(
            FetchBlockRequest(
                ref=[self.chain.point_to_block_ref(point) for point in ref]
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return self.chain.any_chain_to_block(response.block[0])

    async def async_dump_history(
        self, start: Optional[PointType], max_items: Optional[int]
    ) -> List[Optional[BlockType]]:
        stub = self.get_async_stub()
        response = await stub.DumpHistory(
            DumpHistoryRequest(
                start_token=self.chain.point_to_block_ref(start), max_items=max_items
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return [self.chain.any_chain_to_block(block) for block in response.block]

    async def async_follow_tip(
        self, intersect: Iterable[PointType], poke: int = 1
    ) -> AsyncGenerator[FollowTipResponse[BlockType, PointType], Any]:
        stub = self.get_async_stub()
        async for response in stub.FollowTip(
            FollowTipRequest(
                intersect=[self.chain.point_to_block_ref(point) for point in intersect]
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        ):
            if response.apply.SerializeToString() != b"":
                yield FollowTipResponse(
                    action=FollowTipResponseAction.apply,
                    block=self.chain.any_chain_to_block(response.apply),
                    point=None,
                )
            elif response.undo.SerializeToString() != b"":
                yield FollowTipResponse(
                    action=FollowTipResponseAction.undo,
                    block=self.chain.any_chain_to_block(response.undo),
                    point=None,
                )
            elif response.reset.SerializeToString() != b"":
                yield FollowTipResponse(
                    action=FollowTipResponseAction.reset,
                    block=None,
                    point=self.chain.block_ref_to_point(response.reset),
                )
            else:
                await asyncio.sleep(poke)

    def fetch_block(self, ref: Iterable[PointType]) -> Optional[BlockType]:
        stub = self.get_stub()
        response = stub.FetchBlock(
            FetchBlockRequest(
                ref=[self.chain.point_to_block_ref(point) for point in ref]
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return self.chain.any_chain_to_block(response.block[0])

    def dump_history(
        self, start: Optional[PointType], max_items: Optional[int]
    ) -> List[Optional[BlockType]]:
        stub = self.get_stub()
        response = stub.DumpHistory(
            DumpHistoryRequest(
                start_token=self.chain.point_to_block_ref(start), max_items=max_items
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return [self.chain.any_chain_to_block(block) for block in response.block]
