import io
import json
import urllib.error

import pytest

from factflow.llm_providers import AllProvidersFailed, Provider, ProviderChain, default_providers


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _ok(text):
    return _Resp(json.dumps({"choices": [{"message": {"content": text}}]}).encode())


def test_default_order_and_keyless_ovh_available_without_secrets():
    names = [p.name for p in default_providers({})]
    assert names == ["groq", "ovhcloud"]
    assert [p.available() for p in default_providers({})] == [False, True]
    assert [p.name for p in default_providers({"CLOUDFLARE_ACCOUNT_ID": "a", "CLOUDFLARE_API_TOKEN": "t"})][-1] == "cloudflare"


def test_failover_on_rate_limit_then_success_and_usage_counted():
    calls = []

    def opener(request, timeout):
        calls.append(request.full_url)
        if "groq" in request.full_url:
            raise urllib.error.HTTPError(request.full_url, 429, "limit", {}, None)
        return _ok("hello")

    chain = ProviderChain(default_providers({"GROQ_API_KEY": "k"}), opener=opener)
    assert chain.complete("s", "u") == "hello"
    assert len(calls) == 2 and chain.usage == {"ovhcloud": 1}


def test_provider_without_key_is_skipped_not_called():
    calls = []
    chain = ProviderChain(default_providers({}), opener=lambda r, timeout: calls.append(r.full_url) or _ok("x"))
    chain.complete("s", "u")
    assert all("groq" not in c for c in calls)


def test_all_fail_raises_with_each_reason():
    def opener(request, timeout):
        raise urllib.error.URLError("down")

    chain = ProviderChain([Provider("a", "http://a", "m", "k"), Provider("b", "http://b", "m", requires_key=False)], opener=opener)
    with pytest.raises(AllProvidersFailed) as exc:
        chain.complete("s", "u")
    assert set(exc.value.errors) == {"a", "b"}


def test_json_reply_with_code_fence_and_bad_json_falls_through():
    replies = iter(["no json here", "still no json", "```json\n{\"a\": 1}\n```"])
    chain = ProviderChain([Provider("a", "http://a", "m", "k"), Provider("b", "http://b", "m", "k")],
                          opener=lambda r, timeout: _ok(next(replies)))
    assert chain.complete_json("s", "u") == {"a": 1}
    assert chain.usage == {"b": 1}


def test_chain_records_why_each_provider_was_skipped():
    from factflow.llm_providers import Provider, ProviderChain

    class Boom:
        def __call__(self, *a, **k):
            import urllib.error
            raise urllib.error.HTTPError("u", 429, "rate", {}, None)

    chain = ProviderChain([Provider("a", "http://x", "m1", None), Provider("b", "http://x", "m2", "k")], opener=Boom())
    try:
        chain.complete("s", "u")
    except Exception:
        pass
    assert chain.failures == ["a: no credentials configured", "b (m2) attempt 1: HTTP 429"]


def test_malformed_json_is_retried_once_on_the_same_provider():
    import io, json
    from factflow.llm_providers import Provider, ProviderChain

    replies = iter(["not json", '{"ok": 1}'])

    class Resp(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def opener(request, timeout=0):
        return Resp(json.dumps({"choices": [{"message": {"content": next(replies)}}]}).encode())

    chain = ProviderChain([Provider("a", "http://x", "m", "k")], opener=opener)
    assert chain.complete_json("s", "u") == {"ok": 1}
    assert len(chain.failures) == 1
