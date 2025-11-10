from utxorpc.sync import CardanoBlock, CardanoPoint, CardanoChain
from utxorpc.generics.clients.watch import WatchClient


class CardanoWatchClient(WatchClient[CardanoBlock, CardanoPoint]):
    """Cardano-specific watch client for UTxO RPC"""

    chain = CardanoChain
