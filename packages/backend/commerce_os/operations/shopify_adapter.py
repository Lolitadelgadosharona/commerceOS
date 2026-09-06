from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from commerce_os.ai_runtime.adapters import EnvironmentCredentialResolver
from commerce_os.operations.shopify_config import SHOPIFY_GRAPHQL_PATH


class ShopifyAdapterError(RuntimeError):
    def __init__(self, category: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.category = category
        self.retryable = retryable


def connector_owned_fields(projection: dict[str, object]) -> dict[str, object]:
    """Return only fields that the current productSet contract writes and reconciles."""
    return {
        "title": projection.get("title"),
        "description_html": projection.get("description_html"),
        "vendor": projection.get("vendor"),
        "product_type": projection.get("product_type"),
        "handle": projection.get("handle"),
        "seo": projection.get("seo"),
        "options": projection.get("options", []),
        "variants": projection.get("variants", []),
        "external_status": "draft",
    }


@dataclass(frozen=True)
class ShopifyConnectionResult:
    store_domain: str
    granted_scopes: list[str]
    shop_gid: str | None = None
    merchant_name: str | None = None
    partner_development: bool | None = None
    plan_display_name: str | None = None


@dataclass(frozen=True)
class ShopifyResourceResult:
    external_product_id: str
    external_variant_ids: list[str]
    status: str
    owned_fields: dict[str, object]


class ShopifyAdapter(Protocol):
    def validate_connection(self) -> ShopifyConnectionResult: ...

    def create_product(self, projection: dict[str, object]) -> ShopifyResourceResult: ...

    def update_product(
        self, external_product_id: str, projection: dict[str, object]
    ) -> ShopifyResourceResult: ...

    def fetch_product(self, external_product_id: str) -> ShopifyResourceResult | None: ...


class DeterministicShopifyAdapter:
    """Stateful test transport; it never performs network I/O."""

    def __init__(self, store_domain: str = "mock-store.myshopify.com") -> None:
        self.store_domain = store_domain
        self.resources: dict[str, ShopifyResourceResult] = {}
        self.create_calls = 0
        self.update_calls = 0
        self.failure: ShopifyAdapterError | None = None

    def validate_connection(self) -> ShopifyConnectionResult:
        self._fail()
        return ShopifyConnectionResult(
            self.store_domain,
            ["read_products", "write_products"],
            "gid://shopify/Shop/1",
            "Deterministic Development Store",
            True,
            "Development",
        )

    def create_product(self, projection: dict[str, object]) -> ShopifyResourceResult:
        self._fail()
        self.create_calls += 1
        external_id = f"gid://shopify/Product/{1000 + self.create_calls}"
        result = ShopifyResourceResult(
            external_id,
            [f"gid://shopify/ProductVariant/{2000 + self.create_calls}"],
            "draft",
            connector_owned_fields(projection),
        )
        self.resources[external_id] = result
        return result

    def update_product(
        self, external_product_id: str, projection: dict[str, object]
    ) -> ShopifyResourceResult:
        self._fail()
        if external_product_id not in self.resources:
            raise ShopifyAdapterError("external_resource_missing", "External Product is missing.")
        self.update_calls += 1
        current = self.resources[external_product_id]
        result = ShopifyResourceResult(
            external_product_id,
            current.external_variant_ids,
            "draft",
            connector_owned_fields(projection),
        )
        self.resources[external_product_id] = result
        return result

    def fetch_product(self, external_product_id: str) -> ShopifyResourceResult | None:
        self._fail()
        return self.resources.get(external_product_id)

    def simulate_drift(self, external_product_id: str, field: str, value: object) -> None:
        current = self.resources[external_product_id]
        fields = dict(current.owned_fields)
        fields[field] = value
        self.resources[external_product_id] = ShopifyResourceResult(
            current.external_product_id, current.external_variant_ids, current.status, fields
        )

    def _fail(self) -> None:
        if self.failure:
            raise self.failure


class ShopifyGraphQLAdapter:
    """Transport-only GraphQL adapter. Domain authorization remains outside this class."""

    def __init__(
        self,
        *,
        store_domain: str,
        api_version: str,
        credential_reference: str,
        timeout_seconds: int = 15,
    ) -> None:
        self.store_domain = store_domain
        self.api_version = api_version
        self.credential_reference = credential_reference
        self.timeout_seconds = timeout_seconds
        self.resolver = EnvironmentCredentialResolver()

    def validate_connection(self) -> ShopifyConnectionResult:
        data, headers = self._graphql(
            "query ConnectionCheck { shop { id name myshopifyDomain "
            "plan { partnerDevelopment publicDisplayName } } }"
        )
        domain = str(data["shop"]["myshopifyDomain"])
        scopes = [
            x.strip()
            for x in headers.get("X-Shopify-API-Access-Scopes", "").split(",")
            if x.strip()
        ]
        shop = data["shop"]
        plan = shop.get("plan") or {}
        return ShopifyConnectionResult(
            domain,
            scopes,
            str(shop.get("id")) if shop.get("id") else None,
            str(shop.get("name")) if shop.get("name") else None,
            plan.get("partnerDevelopment"),
            str(plan.get("publicDisplayName")) if plan.get("publicDisplayName") else None,
        )

    def create_product(self, projection: dict[str, object]) -> ShopifyResourceResult:
        return self._set_product(None, projection)

    def update_product(
        self, external_product_id: str, projection: dict[str, object]
    ) -> ShopifyResourceResult:
        return self._set_product(external_product_id, projection)

    def fetch_product(self, external_product_id: str) -> ShopifyResourceResult | None:
        query = (
            "query Product($id: ID!) { product(id: $id) { "
            "id title descriptionHtml vendor productType handle status "
            "seo { title description } options { name optionValues { name } } "
            "variants(first: 250) { nodes { id sku price selectedOptions { name value } } } } }"
        )
        data, _ = self._graphql(query, {"id": external_product_id})
        product = data.get("product")
        if product is None:
            return None
        variants = [
            {
                "sku": item.get("sku"),
                "price": str(item.get("price")),
                "optionValues": [
                    {"optionName": option.get("name"), "name": option.get("value")}
                    for option in item.get("selectedOptions", [])
                ],
            }
            for item in product.get("variants", {}).get("nodes", [])
        ]
        options = [
            {
                "name": item.get("name"),
                "values": [{"name": value.get("name")} for value in item.get("optionValues", [])],
            }
            for item in product.get("options", [])
        ]
        owned_fields = {
            "title": product.get("title"),
            "description_html": product.get("descriptionHtml"),
            "vendor": product.get("vendor"),
            "product_type": product.get("productType"),
            "handle": product.get("handle"),
            "seo": product.get("seo"),
            "options": options,
            "variants": variants,
            "external_status": str(product.get("status", "DRAFT")).lower(),
        }
        return ShopifyResourceResult(
            str(product["id"]),
            [str(item["id"]) for item in product.get("variants", {}).get("nodes", [])],
            str(product.get("status", "DRAFT")).lower(),
            owned_fields,
        )

    def _set_product(
        self, external_product_id: str | None, projection: dict[str, object]
    ) -> ShopifyResourceResult:
        product_input = self.product_set_input(projection)
        variables: dict[str, object] = {"input": product_input, "synchronous": True}
        identifier = ""
        if external_product_id:
            variables["identifier"] = {"id": external_product_id}
            identifier = ", identifier: $identifier"
        query = (
            "mutation ProductSet($input: ProductSetInput!, $synchronous: Boolean!"
            + (", $identifier: ProductSetIdentifiers" if external_product_id else "")
            + ") { productSet(input: $input, synchronous: $synchronous"
            + identifier
            + ") { product { id status variants(first: 250) { nodes { id } } } "
            "userErrors { message } } }"
        )
        data, _ = self._graphql(query, variables)
        payload = data["productSet"]
        if payload.get("userErrors"):
            raise ShopifyAdapterError("validation", "Shopify rejected the governed projection.")
        product = payload["product"]
        return ShopifyResourceResult(
            str(product["id"]),
            [str(x["id"]) for x in product["variants"]["nodes"]],
            str(product["status"]).lower(),
            connector_owned_fields(projection),
        )

    @staticmethod
    def product_set_input(projection: dict[str, object]) -> dict[str, object]:
        """Map only Commerce OS-owned product fields; inventory is intentionally absent."""
        return {
            "title": projection["title"],
            "descriptionHtml": projection["description_html"],
            "vendor": projection.get("vendor"),
            "productType": projection.get("product_type"),
            "handle": projection.get("handle"),
            "status": "DRAFT",
            "seo": projection.get("seo"),
            "productOptions": projection.get("options", []),
            "variants": projection.get("variants", []),
        }

    def _graphql(
        self, query: str, variables: dict[str, object] | None = None
    ) -> tuple[dict[str, Any], dict[str, str]]:
        secret = self.resolver.resolve(self.credential_reference)
        request = urllib.request.Request(
            "https://"
            + self.store_domain
            + SHOPIFY_GRAPHQL_PATH.format(api_version=self.api_version),
            data=json.dumps({"query": query, "variables": variables or {}}).encode(),
            headers={"Content-Type": "application/json", "X-Shopify-Access-Token": secret},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read())
                response_headers = dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            category = {401: "authentication", 403: "authorization_scope", 429: "rate_limit"}.get(
                exc.code, "shopify_api" if exc.code < 500 else "network"
            )
            raise ShopifyAdapterError(
                category,
                f"Shopify request failed with HTTP {exc.code}.",
                category in {"rate_limit", "network"},
            ) from None
        except (TimeoutError, urllib.error.URLError):
            raise ShopifyAdapterError("network", "Shopify connection failed.", True) from None
        if body.get("errors"):
            raise ShopifyAdapterError("shopify_api", "Shopify GraphQL returned an error.")
        return body["data"], response_headers
