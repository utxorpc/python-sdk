from utxorpc.sync import CardanoBlock, CardanoPoint, CardanoChain
from utxorpc.generics.clients.query import QueryClient


class CardanoQueryClient(QueryClient[CardanoBlock, CardanoPoint]):
    chain = CardanoChain
