"""Tests for LockedStore / sync worker helper."""

from __future__ import annotations

import threading
import time

from code_graph_service.locked_store import LockedStore, sync_max_file_workers


def test_sync_max_file_workers_auto_from_cpu_and_rpm(monkeypatch):
    monkeypatch.delenv("AGENTCORE_SYNC_MAX_FILE_WORKERS", raising=False)
    monkeypatch.setenv("AGENTCORE_LITELLM_RPM", "30")
    monkeypatch.setattr("code_graph_service.locked_store.os.cpu_count", lambda: 8)
    assert sync_max_file_workers() == 8

    monkeypatch.setattr("code_graph_service.locked_store.os.cpu_count", lambda: 64)
    assert sync_max_file_workers({"AGENTCORE_LITELLM_RPM": "10"}) == 10

    # High RPM: limited by CPU only (no fixed 32 ceiling)
    monkeypatch.setattr("code_graph_service.locked_store.os.cpu_count", lambda: 64)
    assert sync_max_file_workers({"AGENTCORE_LITELLM_RPM": "100"}) == 64


def test_sync_max_file_workers_explicit_override(monkeypatch):
    monkeypatch.setattr("code_graph_service.locked_store.os.cpu_count", lambda: 8)
    assert sync_max_file_workers({"AGENTCORE_SYNC_MAX_FILE_WORKERS": "3", "AGENTCORE_LITELLM_RPM": "30"}) == 3
    assert sync_max_file_workers({"AGENTCORE_SYNC_MAX_FILE_WORKERS": "auto", "AGENTCORE_LITELLM_RPM": "5"}) == 5
    assert sync_max_file_workers({"AGENTCORE_SYNC_MAX_FILE_WORKERS": "nope", "AGENTCORE_LITELLM_RPM": "2"}) == 2
    assert sync_max_file_workers({"AGENTCORE_SYNC_MAX_FILE_WORKERS": "0", "AGENTCORE_LITELLM_RPM": "7"}) == 7


def test_locked_store_serializes_mutations():
    class Counter:
        def __init__(self) -> None:
            self.value = 0

        def bump(self) -> int:
            current = self.value
            self.value = current + 1
            return self.value

    locked = LockedStore(Counter())
    errors: list[BaseException] = []

    def worker() -> None:
        try:
            for _ in range(200):
                locked.bump()
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert locked.value == 1600


def test_build_service_does_not_serialize_remote_embeddings(monkeypatch):
    import code_graph_service.bootstrap as bootstrap
    import code_graph_service.llm_wiring as llm_wiring
    from code_graph_service.testing import InMemoryStore
    from llm_gateway import FakeLlmGateway

    class RemoteEmbeddings:
        local = None
        model = "remote/model"

        def __init__(self) -> None:
            self.barrier = threading.Barrier(2)

        def embed(self, text: str):
            self.barrier.wait(timeout=1.0)
            return text

    remote = RemoteEmbeddings()
    gateway = FakeLlmGateway()
    monkeypatch.setattr(bootstrap, "build_store", lambda _settings: InMemoryStore())
    monkeypatch.setattr(bootstrap, "build_llm_gateway", lambda: gateway)
    monkeypatch.setattr(
        bootstrap,
        "build_embeddings",
        lambda _gateway, settings=None: remote,
    )
    monkeypatch.setattr(bootstrap, "build_embedding_index", lambda _settings: None)
    monkeypatch.setattr(llm_wiring, "maybe_preload_embeddings", lambda _embeddings: False)
    service = bootstrap.build_service(object())

    errors: list[BaseException] = []

    def worker(value: str) -> None:
        try:
            service.embeddings.embed(value)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(value,)) for value in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2.0)

    assert errors == []
    assert all(not thread.is_alive() for thread in threads)


def test_build_service_does_not_serialize_loaded_local_embeddings(monkeypatch):
    import code_graph_service.bootstrap as bootstrap
    import code_graph_service.llm_wiring as llm_wiring
    from code_graph_service.testing import InMemoryStore
    from llm_gateway import FakeLlmGateway

    class LocalEmbeddings:
        model = "local/model"

        def __init__(self) -> None:
            self.barrier = threading.Barrier(2)

        def embed(self, text: str, *, is_query: bool = False):
            self.barrier.wait(timeout=1.0)
            return text

    class HybridEmbeddings:
        def __init__(self) -> None:
            self.local = LocalEmbeddings()

        def embed(self, text: str):
            return self.local.embed(text)

    embeddings = HybridEmbeddings()
    gateway = FakeLlmGateway()
    monkeypatch.setattr(bootstrap, "build_store", lambda _settings: InMemoryStore())
    monkeypatch.setattr(bootstrap, "build_llm_gateway", lambda: gateway)
    monkeypatch.setattr(bootstrap, "build_embeddings", lambda _gateway, settings=None: embeddings)
    monkeypatch.setattr(bootstrap, "build_embedding_index", lambda _settings: None)
    monkeypatch.setattr(llm_wiring, "maybe_preload_embeddings", lambda _embeddings: False)
    service = bootstrap.build_service(object())
    errors: list[BaseException] = []

    def worker(value: str) -> None:
        try:
            service.embeddings.embed(value)
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(value,)) for value in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2.0)

    assert errors == []
    assert all(not thread.is_alive() for thread in threads)


def test_local_embedding_limit_is_shared_across_service_instances(monkeypatch):
    import code_graph_service.local_embeddings as local_embeddings

    class Encoder:
        def __init__(self) -> None:
            self.active = 0
            self.peak = 0
            self.lock = threading.Lock()

        def encode(self, _payload, **_kwargs):
            with self.lock:
                self.active += 1
                self.peak = max(self.peak, self.active)
            time.sleep(0.1)
            with self.lock:
                self.active -= 1
            return [0.0, 0.0]

    encoder = Encoder()
    monkeypatch.setattr(local_embeddings, "_load_sentence_transformer", lambda *_args: encoder)
    left = local_embeddings.LocalBgeEmbeddings(model_name="same", cache_dir="same", dims=2)
    right = local_embeddings.LocalBgeEmbeddings(model_name="same", cache_dir="same", dims=2)
    start = threading.Barrier(8)
    errors: list[BaseException] = []

    def worker(instance) -> None:
        try:
            start.wait(timeout=1.0)
            instance.embed("value")
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(left if index < 4 else right,))
        for index in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2.0)

    assert errors == []
    assert encoder.peak <= 4


def test_local_model_loads_are_process_serialized(monkeypatch):
    import code_graph_service.local_embeddings as local_embeddings

    active = 0
    peak = 0
    lock = threading.Lock()

    class Encoder:
        def encode(self, _payload, **_kwargs):
            return [0.0, 0.0]

    def load_model(*_args):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.1)
        with lock:
            active -= 1
        return Encoder()

    monkeypatch.setattr(local_embeddings, "_load_sentence_transformer", load_model)
    left = local_embeddings.LocalBgeEmbeddings(model_name="left", cache_dir="same", dims=2)
    right = local_embeddings.LocalBgeEmbeddings(model_name="right", cache_dir="same", dims=2)
    start = threading.Barrier(2)

    def worker(instance) -> None:
        start.wait(timeout=1.0)
        instance.embed("value")

    threads = [threading.Thread(target=worker, args=(instance,)) for instance in (left, right)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2.0)

    assert all(not thread.is_alive() for thread in threads)
    assert peak == 1
