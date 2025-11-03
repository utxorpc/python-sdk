from typing import AsyncGenerator, Any, Generic, Optional
from enum import Enum

from utxorpc_spec.utxorpc.v1alpha.watch.watch_pb2 import (  # type: ignore
    WatchTxRequest,
    TxPredicate,
)
from utxorpc_spec.utxorpc.v1alpha.watch.watch_pb2_grpc import WatchServiceStub  # type: ignore

from utxorpc.generics import BlockType, PointType
from . import Client


class WatchTxResponseAction(Enum):
    apply = "APPLY"
    undo = "UNDO"
    idle = "IDLE"


class WatchTxResponseWrapper(Generic[BlockType, PointType]):
    action: WatchTxResponseAction
    tx: Optional[Any]
    block_ref: Optional[PointType]

    def __init__(
        self,
        action: WatchTxResponseAction,
        tx: Optional[Any] = None,
        block_ref: Optional[PointType] = None,
    ) -> None:
        self.action = action
        self.tx = tx
        self.block_ref = block_ref


class WatchClient(Client[WatchServiceStub], Generic[BlockType, PointType]):
    stub = WatchServiceStub

    async def async_watch_tx(
        self,
        predicate: Optional[TxPredicate] = None,
        field_mask: Optional[Any] = None,
        intersect: Optional[Any] = None,
    ) -> AsyncGenerator[WatchTxResponseWrapper[BlockType, PointType], Any]:
        """Watch for transactions matching the given predicate"""
        stub = self.get_async_stub()

        request = WatchTxRequest()
        if predicate:
            request.predicate.CopyFrom(predicate)
        if field_mask:
            request.field_mask.CopyFrom(field_mask)
        if intersect:
            if hasattr(intersect, "__iter__"):
                # Convert points to block refs if needed
                request.intersect.extend(
                    [self.chain.point_to_block_ref(point) for point in intersect]
                )
            else:
                request.intersect.append(self.chain.point_to_block_ref(intersect))

        async for response in stub.WatchTx(
            request,
            metadata=[(k, v) for k, v in self.metadata.items()],
        ):
            if response.apply.SerializeToString() != b"":
                yield WatchTxResponseWrapper(
                    action=WatchTxResponseAction.apply,
                    tx=response.apply,
                )
            elif response.undo.SerializeToString() != b"":
                yield WatchTxResponseWrapper(
                    action=WatchTxResponseAction.undo,
                    tx=response.undo,
                )
            elif response.idle.SerializeToString() != b"":
                yield WatchTxResponseWrapper(
                    action=WatchTxResponseAction.idle,
                    block_ref=self.chain.block_ref_to_point(response.idle),
                )
