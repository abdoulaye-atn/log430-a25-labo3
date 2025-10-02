import graphene
from graphene import ObjectType, String, Int
from stocks.schemas.product import Product
from db import get_redis_conn

class Query(ObjectType):
    product = graphene.Field(Product, id=String(required=True))
    stock_level = Int(product_id=String(required=True))

    def resolve_product(self, info, id):
        r = get_redis_conn()
        raw = r.hgetall(f"stock:{id}")
        if not raw:
            return None

        def _b2s(b):
            return b.decode("utf-8") if isinstance(b, (bytes, bytearray)) else b

        d = { _b2s(k): _b2s(v) for k, v in raw.items() }

        return Product(
            id=id,
            name=d.get("name") or f"Product {id}",
            sku=d.get("sku"),
            price=float(d["price"]) if d.get("price") is not None else None,
            quantity=int(d["quantity"]) if d.get("quantity") is not None else None,
        )

    def resolve_stock_level(self, info, product_id):
        r = get_redis_conn()
        q = r.hget(f"stock:{product_id}", "quantity")
        return int(q) if q else 0
