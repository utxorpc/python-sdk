from typing import AsyncGenerator, Any, Generic, Optional

from utxorpc_spec.utxorpc.v1alpha.submit.submit_pb2 import (  # type: ignore
    SubmitTxRequest,
    WaitForTxRequest,
    WatchMempoolRequest,
    AnyChainTx,
    TxInMempool,
    TxPredicate,
    Stage,
)
from utxorpc_spec.utxorpc.v1alpha.submit.submit_pb2_grpc import SubmitServiceStub  # type: ignore

from utxorpc.generics import BlockType, PointType
from . import Client


class SubmitClient(Client[SubmitServiceStub], Generic[BlockType, PointType]):
    stub = SubmitServiceStub

    async def async_submit_tx(self, tx_bytes: bytes) -> bytes:
        """Submit a transaction to the blockchain asynchronously"""
        stub = self.get_async_stub()
        tx = AnyChainTx(raw=tx_bytes)
        response = await stub.SubmitTx(
            SubmitTxRequest(tx=tx),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return response.ref

    async def async_wait_for_tx(self, tx_ref: bytes) -> AsyncGenerator[Stage, Any]:
        """Wait for a transaction to reach various stages asynchronously"""
        stub = self.get_async_stub()
        async for response in stub.WaitForTx(
            WaitForTxRequest(ref=[tx_ref]),
            metadata=[(k, v) for k, v in self.metadata.items()],
        ):
            yield response.stage

    async def async_watch_mempool(
        self, predicate: Optional[TxPredicate] = None
    ) -> AsyncGenerator[TxInMempool, Any]:
        """Watch mempool for transactions matching predicate asynchronously"""
        stub = self.get_async_stub()
        request = WatchMempoolRequest()
        if predicate:
            request.predicate.CopyFrom(predicate)

        async for response in stub.WatchMempool(
            request,
            metadata=[(k, v) for k, v in self.metadata.items()],
        ):
            yield response.tx

    def submit_tx(self, tx_bytes: bytes) -> bytes:
        """Submit a transaction to the blockchain synchronously"""
        stub = self.get_stub()
        tx = AnyChainTx(raw=tx_bytes)
        response = stub.SubmitTx(
            SubmitTxRequest(tx=tx),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return response.ref
