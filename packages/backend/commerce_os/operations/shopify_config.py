"""Central, reviewable Shopify Admin API contract configuration."""

SHOPIFY_ADMIN_API_VERSION = "2026-07"
SHOPIFY_REQUIRED_SCOPES = ("read_products", "write_products")
SHOPIFY_GRAPHQL_PATH = "/admin/api/{api_version}/graphql.json"
