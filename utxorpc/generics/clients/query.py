from typing import AsyncGenerator, Any, Generic, List, Optional, Iterable, Union

from utxorpc_spec.utxorpc.v1alpha.query.query_pb2 import (  # type: ignore
    ReadUtxosRequest,
    ReadUtxosResponse,
    SearchUtxosRequest,
    SearchUtxosResponse,
    ReadParamsRequest,
    ReadParamsResponse,
    UtxoPredicate,
    TxoRef,
)
from utxorpc_spec.utxorpc.v1alpha.query.query_pb2_grpc import QueryServiceStub  # type: ignore

from utxorpc.generics import BlockType, PointType
from . import Client


class QueryClient(Client[QueryServiceStub], Generic[BlockType, PointType]):
    stub = QueryServiceStub

    async def async_read_utxos(
        self, keys: Iterable[Union[bytes, TxoRef]]
    ) -> ReadUtxosResponse:
        stub = self.get_async_stub()
        # Convert keys to TxoRef objects if they are bytes
        refs = []
        for key in keys:
            if isinstance(key, bytes):
                # Legacy format: tx_hash (32 bytes) + output_index (4 bytes little-endian)
                if len(key) == 36:
                    tx_hash = key[:32]
                    output_index = int.from_bytes(key[32:36], byteorder="little")
                    refs.append(TxoRef(hash=tx_hash, index=output_index))
                else:
                    raise ValueError(
                        f"Invalid key length: {len(key)}. Expected 36 bytes (32 for hash + 4 for index)"
                    )
            else:
                refs.append(key)

        response = await stub.ReadUtxos(
            ReadUtxosRequest(keys=refs),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return response

    async def async_search_utxos(
        self, predicate: UtxoPredicate, field_mask: Optional[Any] = None
    ) -> AsyncGenerator[SearchUtxosResponse, Any]:
        stub = self.get_async_stub()
        request = SearchUtxosRequest(predicate=predicate)
        if field_mask:
            request.field_mask.CopyFrom(field_mask)

        async for response in stub.SearchUtxos(
            request,
            metadata=[(k, v) for k, v in self.metadata.items()],
        ):
            yield response

    async def async_read_params(
        self, field_mask: Optional[Any] = None
    ) -> ReadParamsResponse:
        stub = self.get_async_stub()
        request = ReadParamsRequest()
        if field_mask:
            request.field_mask.CopyFrom(field_mask)

        response = await stub.ReadParams(
            request,
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return response

    def read_utxos(self, keys: Iterable[Union[bytes, TxoRef]]) -> ReadUtxosResponse:
        stub = self.get_stub()
        # Convert keys to TxoRef objects if they are bytes
        refs = []
        for key in keys:
            if isinstance(key, bytes):
                # Legacy format: tx_hash (32 bytes) + output_index (4 bytes little-endian)
                if len(key) == 36:
                    tx_hash = key[:32]
                    output_index = int.from_bytes(key[32:36], byteorder="little")
                    refs.append(TxoRef(hash=tx_hash, index=output_index))
                else:
                    raise ValueError(
                        f"Invalid key length: {len(key)}. Expected 36 bytes (32 for hash + 4 for index)"
                    )
            else:
                refs.append(key)

        response = stub.ReadUtxos(
            ReadUtxosRequest(keys=refs),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return response

    def search_utxos(
        self, predicate: UtxoPredicate, field_mask: Optional[Any] = None
    ) -> List[SearchUtxosResponse]:
        stub = self.get_stub()
        request = SearchUtxosRequest(predicate=predicate)
        if field_mask:
            request.field_mask.CopyFrom(field_mask)

        responses = []
        try:
            # Try to iterate if it's a stream
            for response in stub.SearchUtxos(
                request,
                metadata=[(k, v) for k, v in self.metadata.items()],
            ):
                responses.append(response)
        except TypeError:
            # If not iterable, it's a single response
            response = stub.SearchUtxos(
                request,
                metadata=[(k, v) for k, v in self.metadata.items()],
            )
            responses.append(response)
        return responses

    def read_params(self, field_mask: Optional[Any] = None) -> ReadParamsResponse:
        stub = self.get_stub()
        request = ReadParamsRequest()
        if field_mask:
            request.field_mask.CopyFrom(field_mask)

        response = stub.ReadParams(
            request,
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return response
