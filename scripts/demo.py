"""Two-step local demonstration. Writes require --allow-writes; approval is separate."""

import argparse
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4

from app.core.config import settings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--allow-writes", action="store_true")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--approve", type=str, metavar="RUN_ID")
    mode.add_argument("--reject", type=str, metavar="RUN_ID")
    args = parser.parse_args()
    if not args.allow_writes:
        parser.error("Explicit --allow-writes required for demo records or decisions")
    target = urlparse(args.url)
    if target.scheme != "http" or target.hostname not in {"localhost", "127.0.0.1"}:
        parser.error("Demo writes are restricted to a local API")
    if args.prepare and settings.ai_provider != "demo":
        parser.error("Set AI_PROVIDER=demo to avoid real OpenAI requests")

    def request(path: str, payload: dict, *, reviewer: bool = False):
        key = settings.reviewer_api_key if reviewer else settings.operator_api_key
        if not key:
            parser.error("Configure operator and reviewer credentials")
        req = Request(
            args.url.rstrip("/") + path,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key.get_secret_value()}",
            },
            method="POST",
        )
        with urlopen(req, timeout=30) as response:
            return json.load(response)

    if args.approve or args.reject:
        run_id = args.approve or args.reject
        # Validate before interpolating an identifier into the URL.
        from uuid import UUID

        run_id = str(UUID(run_id))
        result = request(
            f"/api/v1/assistant/runs/{run_id}/decision",
            {"approve": bool(args.approve)},
            reviewer=True,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    for title, content in (
        (
            "Devoluciones",
            "Las devoluciones se aceptan dentro de 30 días con el empaque original.",
        ),
        ("Envíos", "Los envíos se entregan entre 3 y 5 días hábiles."),
        ("Pagos", "Aceptamos pagos con tarjeta y transferencia bancaria."),
    ):
        request(
            "/api/v1/documents",
            {"title": title, "content": content, "source": "offline-demo"},
        )
    knowledge = request(
        "/api/v1/assistant/ask", {"question": "¿Qué política de devoluciones tienen?"}
    )
    fallback = request(
        "/api/v1/assistant/ask", {"question": "¿Hay garantía de cinco años?"}
    )
    customer = request(
        "/api/v1/customers",
        {"name": "Portfolio Demo", "email": f"demo-{uuid4()}@example.com"},
    )
    product = request(
        "/api/v1/products",
        {
            "sku": f"DEMO-{uuid4()}",
            "name": "Demo Product",
            "price": "25.50",
            "stock": 10,
        },
    )
    order = request(
        "/api/v1/orders",
        {
            "customer_id": customer["id"],
            "items": [{"product_id": product["id"], "quantity": 2}],
        },
    )
    lookup = request(
        "/api/v1/assistant/ask", {"question": f"Consulta la orden {order['id']}"}
    )
    pending = request(
        "/api/v1/assistant/ask", {"question": f"Cancelar la orden {order['id']}"}
    )
    print(
        json.dumps(
            {
                "knowledge": knowledge,
                "fallback": fallback,
                "lookup": lookup,
                "pending_approval": pending,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    print(
        "La orden sigue pendiente. Revisa la vista previa y ejecuta --approve RUN_ID o --reject RUN_ID en un paso separado."
    )


if __name__ == "__main__":
    main()
