"""Ordered chain of free OpenAI-compatible LLM providers with automatic failover.

Order: Groq, OVHcloud AI Endpoints (anonymous, no key), Cloudflare Workers AI.
A provider that is missing its credentials, rate limited, down or returns an
unusable reply is skipped and the next one is tried. Free-tier quotas and model
names change, so models and endpoints are overridable through environment
variables. Only public source text is ever sent to these services.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

DEFAULT_TIMEOUT = 90


class ProviderError(RuntimeError):
    """One provider could not produce a reply."""


class AllProvidersFailed(RuntimeError):
    """Every configured provider failed; carries each provider's error."""

    def __init__(self, errors: dict[str, str]) -> None:
        self.errors = errors
        super().__init__("All LLM providers failed: " + "; ".join(f"{k}: {v}" for k, v in errors.items()))


@dataclass
class Provider:
    name: str
    url: str
    model: str
    api_key: str | None = None
    requires_key: bool = True
    extra_headers: dict[str, str] = field(default_factory=dict)

    def available(self) -> bool:
        return bool(self.api_key) or not self.requires_key

    def complete(self, system: str, user: str, *, max_tokens: int, temperature: float,
                 opener: Callable[..., Any] = urllib.request.urlopen) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json", "User-Agent": "QuantaTale/0.1", **self.extra_headers}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(self.url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with opener(request, timeout=DEFAULT_TIMEOUT) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:  # 429 quota, 5xx outage, 4xx bad model
            raise ProviderError(f"HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise ProviderError(f"{type(exc).__name__}: {exc}") from exc
        try:
            text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("unexpected response shape: " + json.dumps(body)[:200]) from exc
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("empty reply")
        return text


def default_providers(env: dict[str, str] | None = None) -> list[Provider]:
    env = dict(os.environ) if env is None else env
    providers = [
        Provider("groq", env.get("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions"),
                 env.get("GROQ_MODEL", "llama-3.3-70b-versatile"), env.get("GROQ_API_KEY")),
        Provider("ovhcloud", env.get("OVH_URL", "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions"),
                 env.get("OVH_MODEL", "gpt-oss-120b"), env.get("OVH_API_KEY"), requires_key=False),
    ]
    account = env.get("CLOUDFLARE_ACCOUNT_ID")
    if account:
        providers.append(Provider(
            "cloudflare",
            env.get("CLOUDFLARE_URL", f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions"),
            env.get("CLOUDFLARE_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
            env.get("CLOUDFLARE_API_TOKEN")))
    return providers


class ProviderChain:
    """Try providers in order; skip unavailable ones and report why each failed."""

    def __init__(self, providers: list[Provider] | None = None,
                 opener: Callable[..., Any] = urllib.request.urlopen) -> None:
        self.providers = providers if providers is not None else default_providers()
        self.opener = opener
        self.usage: dict[str, int] = {}
        self.failures: list[str] = []  # every skipped provider and why, for the run log

    def complete(self, system: str, user: str, *, max_tokens: int = 1500, temperature: float = 0.3,
                 validate: Callable[[str], Any] | None = None) -> Any:
        """Return the first reply that passes ``validate`` (default: the raw text)."""
        errors: dict[str, str] = {}
        for provider in self.providers:
            if not provider.available():
                errors[provider.name] = "no credentials configured"
                self.failures.append(f"{provider.name}: no credentials configured")
                continue
            result, failed = None, False
            for attempt in (1, 2):  # a malformed JSON reply is retried once on the same provider
                try:
                    text = provider.complete(system, user, max_tokens=max_tokens, temperature=temperature, opener=self.opener)
                    result = validate(text) if validate else text
                    failed = False
                    break
                except (ProviderError, ValueError) as exc:
                    failed = True
                    errors[provider.name] = str(exc)
                    self.failures.append(f"{provider.name} ({provider.model}) attempt {attempt}: {exc}")
                    if isinstance(exc, ProviderError):
                        break
            if failed:
                continue
            self.usage[provider.name] = self.usage.get(provider.name, 0) + 1
            return result
        raise AllProvidersFailed(errors)

    def complete_json(self, system: str, user: str, **kwargs: Any) -> Any:
        """Ask for JSON and tolerate code fences or surrounding prose."""
        def parse(text: str) -> Any:
            start, end = text.find("{"), text.rfind("}")
            if start == -1 or end <= start:
                raise ValueError("no JSON object in reply")
            return json.loads(text[start:end + 1])
        return self.complete(system, user, validate=parse, **kwargs)
