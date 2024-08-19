from typing import Generic, List, Optional

from utxorpc_spec.utxorpc.v1alpha.query.query_pb2 import (  # type: ignore
    ReadUtxosRequest,
    SearchUtxosRequest,
    UtxoPredicate,
)
from utxorpc_spec.utxorpc.v1alpha.query.query_pb2_grpc import QueryServiceStub  # type: ignore

from utxorpc.generics import TxOutputPatternType, TxOutputType, TxoRefType
from utxorpc.generics.clients import Client


class QueryClient(
    Client[QueryServiceStub], Generic[TxOutputPatternType, TxOutputType, TxoRefType]
):
    stub = QueryServiceStub

    async def async_search_utxos(
        self, match: TxOutputPatternType
    ) -> List[TxOutputType]:
        stub = self.get_async_stub()
        response = await stub.SearchUtxos(
            SearchUtxosRequest(
                predicate=UtxoPredicate(
                    match=self.chain.tx_output_pattern_to_any_utxo_pattern(match)
                )
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )

        return [self.chain.any_utxo_data_to_tx_output(item) for item in response.items]

    def search_utxos(self, match: TxOutputPatternType) -> List[TxOutputType]:
        stub = self.get_stub()
        response = stub.SearchUtxos(
            SearchUtxosRequest(
                predicate=UtxoPredicate(
                    match=self.chain.tx_output_pattern_to_any_utxo_pattern(match)
                )
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )

        return [self.chain.any_utxo_data_to_tx_output(item) for item in response.items]

    def read_utxos(self, keys: List[TxoRefType]) -> List[Optional[TxOutputType]]:
        stub = self.get_stub()
        response = stub.ReadUtxos(
            ReadUtxosRequest(
                keys=[self.chain.chain_txo_ref_to_txo_ref(key) for key in keys]
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return [self.chain.any_utxo_data_to_tx_output(item) for item in response.items]

    async def async_read_utxos(
        self, keys: List[TxoRefType]
    ) -> List[Optional[TxOutputType]]:
        stub = self.get_async_stub()
        response = await stub.ReadUtxos(
            ReadUtxosRequest(
                keys=[self.chain.chain_txo_ref_to_txo_ref(key) for key in keys]
            ),
            metadata=[(k, v) for k, v in self.metadata.items()],
        )
        return [self.chain.any_utxo_data_to_tx_output(item) for item in response.items]
