"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    # 1) Créer un article (POST /products)
    product_payload = {"name": "Some Item", "sku": "12345", "price": 1299.99}
    r = client.post("/products", data=json.dumps(product_payload), content_type="application/json")
    assert r.status_code == 201
    p = r.get_json()
    assert isinstance(p, dict) and "product_id" in p and isinstance(p["product_id"], int) and p["product_id"] > 0
    product_id = p["product_id"]

    # 1.1) Essayer de créer un user (POST /users) ; si 4xx/5xx → fallback user_id=2 (seed)
    user_id = None
    user_payload = {"name": "Abdou Niane", "email": "abdou@ets.ca"}
    r = client.post("/users", data=json.dumps(user_payload), content_type="application/json")
    if r.status_code in (200, 201):
        ub = r.get_json() or {}
        user_id = ub.get("user_id") or ub.get("id")
    if not user_id:
        # Fallback basé sur ta collection Postman (exemples avec user_id = 2)
        user_id = 2

    # 2) Ajouter 5 unités au stock (POST /stocks)
    add_stock_payload = {"product_id": product_id, "quantity": 5}
    r = client.post("/stocks", data=json.dumps(add_stock_payload), content_type="application/json")
    assert r.status_code in (200, 201), f"POST /stocks a échoué: {r.status_code} {r.get_data(as_text=True)}"

    # 3) Vérifier le stock = 5 (GET /stocks/:id)
    r = client.get(f"/stocks/{product_id}")
    assert r.status_code in (200, 201), f"GET /stocks/{product_id} status={r.status_code} body={r.get_data(as_text=True)}"
    stock1 = r.get_json() or {}
    qty1 = stock1.get("quantity") or (stock1.get("stock") or {}).get("quantity")
    assert qty1 == 5, f"Attendu 5, obtenu {qty1} pour /stocks/{product_id}"

    # 4) Passer une commande de 2 unités (POST /orders)
    order_payload = {"user_id": user_id, "items": [{"product_id": product_id, "quantity": 2}]}
    r = client.post("/orders", data=json.dumps(order_payload), content_type="application/json")
    assert r.status_code in (200, 201), f"POST /orders a échoué: {r.status_code} {r.get_data(as_text=True)}"
    ob = r.get_json() or {}
    assert "order_id" in ob and isinstance(ob["order_id"], int) and ob["order_id"] > 0
    order_id = ob["order_id"]

    # 5) Vérifier le stock = 3 (GET /stocks/:id)
    r = client.get(f"/stocks/{product_id}")
    assert r.status_code in (200, 201)
    stock2 = r.get_json() or {}
    qty2 = stock2.get("quantity") or (stock2.get("stock") or {}).get("quantity")
    assert qty2 == 3, f"Attendu 3 après commande, obtenu {qty2}"

    # 6) Extra: supprimer la commande puis vérifier stock = 5
    r = client.delete(f"/orders/{order_id}")
    assert r.status_code in (200, 204), f"DELETE /orders/{order_id} a échoué: {r.status_code} {r.get_data(as_text=True)}"

    r = client.get(f"/stocks/{product_id}")
    assert r.status_code in (200, 201)
    stock3 = r.get_json() or {}
    qty3 = stock3.get("quantity") or (stock3.get("stock") or {}).get("quantity")
    assert qty3 == 5, f"Attendu 5 après suppression de commande, obtenu {qty3}"
