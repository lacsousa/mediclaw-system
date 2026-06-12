"""Cliente de telemetria ChromaDB que não envia eventos (evita incompatibilidade posthog 7.x)."""

from chromadb.config import System
from chromadb.telemetry.product import ProductTelemetryClient, ProductTelemetryEvent
from overrides import override


class NoopProductTelemetry(ProductTelemetryClient):
    def __init__(self, system: System):
        super().__init__(system)

    @override
    def capture(self, event: ProductTelemetryEvent) -> None:
        return
