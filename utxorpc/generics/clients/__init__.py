from contextlib import asynccontextmanager, contextmanager
from functools import partial
from typing import (
    Any,
    Dict,
    Generic,
    Iterable,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import grpc

from utxorpc.generics import Chain


class StubType(Protocol):
    def __init__(self, channel: Union[grpc.Channel, grpc.aio.Channel]): ...


Stub = TypeVar("Stub", bound=StubType)


class Client(Generic[Stub]):
    uri: str
    metadata: Dict[str, str]
    secure: bool
    ssl_context: Optional[grpc.ChannelCredentials]
    channel: Optional[grpc.Channel]
    async_channel: Optional[grpc.aio.Channel]
    options: Optional[Iterable[Tuple[str, str]]]
    compression: Optional[grpc.Compression]

    chain: Type[Chain]
    stub: Type[Stub]

    def __init__(
        self,
        uri: str,
        metadata: Optional[Dict[str, str]] = None,
        secure: bool = True,
        options: Optional[Sequence[Tuple[str, Any]]] = None,
        compression: Optional[grpc.Compression] = None,
        ssl_context: Optional[grpc.ChannelCredentials] = None,
    ) -> None:
        self.uri = uri
        self.metadata = metadata or {}
        self.secure = secure
        self.ssl_context = ssl_context
        self.options = options
        self.compression = compression

    def get_stub(self) -> Stub:
        if self.channel is None:
            raise Exception(
                "Missing connect. Meant to be used in connect context manager"
            )

        return self.stub(self.channel)

    def get_async_stub(self) -> Stub:
        if self.async_channel is None:
            raise Exception(
                "Missing async_connect. Meant to be used in async connect context manager"
            )

        return self.stub(self.async_channel)

    @contextmanager
    def connect(self):
        """Perform connection to UTxO RPC endpoint.

        Usage
        -----

        ```python
        with client.connect() as client:
            block = client.fetch_block(ref=CardanoPoint(slot=123, hash="hash"))
            print(block)
        ```

        """
        get_channel = partial(
            grpc.insecure_channel,
            self.uri,
            options=self.options,
            compression=self.compression,
        )
        if self.secure:
            get_channel = partial(
                grpc.secure_channel,
                self.uri,
                self.ssl_context or grpc.ssl_channel_credentials(),
                options=self.options,
                compression=self.compression,
            )
        with get_channel() as channel:
            self.channel = channel
            try:
                yield self
            finally:
                pass

    @asynccontextmanager
    async def async_connect(self):
        """Perform async connection to UTxO RPC endpoint.

        Usage
        -----

        ```python
        async with client.connect() as async_client:
            block = await async_client.fetch_block(
                ref=CardanoPoint(slot=123, hash="hash")
            )
            print(block)
        ```

        """
        get_channel = partial(
            grpc.aio.insecure_channel,
            self.uri,
            # Typing bug on grpc lib (https://github.com/grpc/grpc/issues/37025)
            options=self.options,  # type: ignore
            compression=self.compression,
        )
        if self.secure:
            get_channel = partial(
                grpc.aio.secure_channel,
                self.uri,
                self.ssl_context or grpc.ssl_channel_credentials(),
                # Typing bug on grpc lib (https://github.com/grpc/grpc/issues/37025)
                options=self.options,  # type: ignore
                compression=self.compression,
            )
        async with get_channel() as async_channel:
            self.async_channel = async_channel
            try:
                yield self
            finally:
                pass
