from utxorpc.sync import CardanoBlock, CardanoPoint, CardanoChain
from utxorpc.generics.clients.submit import SubmitClient


class CardanoSubmitClient(SubmitClient[CardanoBlock, CardanoPoint]):
    """Cardano-specific submit client for UTxO RPC"""

    chain = CardanoChain
