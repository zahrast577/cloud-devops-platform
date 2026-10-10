"""API FastAPI du projet.

Ce que cette API apporte à la plateforme :
  /health        sonde de VIE (liveness)       -> Kubernetes redémarre le pod si elle échoue
  /ready         sonde de DISPONIBILITÉ        -> Kubernetes n'envoie du trafic que si elle répond 200
  /metrics       métriques Prometheus          -> scrapées par Prometheus, affichées dans Grafana
  /api/info      nom du pod + version          -> visualiser le load balancing et les rollouts
  /api/items     lecture / écriture PostgreSQL -> avec cache Redis
  /api/stress    charge CPU contrôlée          -> déclencher l'autoscaling (HPA)
"""
import logging
import math
import socket
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .cache import cache
from .config import APP_VERSION
from .database import Base, engine, get_db
from .models import Item
from .schemas import ItemCreate, ItemOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("app")

# Dans Kubernetes, le hostname d'un conteneur est le nom de son pod.
HOSTNAME = socket.gethostname()
ITEMS_CACHE_KEY = "items:list"

# --- Métriques Prometheus ---------------------------------------------------
REQUESTS = Counter(
    "http_requests_total",
    "Nombre de requetes HTTP",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duree des requetes HTTP en secondes",
    ["method", "path"],
)
CACHE_EVENTS = Counter(
    "items_cache_total",
    "Acces au cache de la liste des items",
    ["result"],
)


def init_db(retries: int = 15, delay: float = 2.0) -> None:
    """Crée les tables, en réessayant tant que la base n'est pas prête.

    Sur Kubernetes, l'API peut démarrer avant PostgreSQL : on réessaie au lieu
    de planter. Avec plusieurs réplicas qui démarrent en même temps, un des
    essais peut aussi échouer (table déjà créée par l'autre) : le nouvel essai
    règle le problème. En production, on utiliserait plutôt des migrations
    (Alembic) lancées par un Job dédié.
    """
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Base de données initialisée")
            return
        except SQLAlchemyError as exc:
            logger.warning("Base indisponible (essai %s/%s) : %s", attempt, retries, exc)
            if attempt == retries:
                raise
            time.sleep(delay)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Items API", version=APP_VERSION, lifespan=lifespan)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    """Mesure chaque requête pour Prometheus et indique quel pod a répondu."""
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Served-By"] = HOSTNAME
        return response
    finally:
        route = request.scope.get("route")
        # On utilise le modèle de route (/api/items/{item_id}) et non l'URL réelle,
        # pour éviter une explosion du nombre de séries de métriques.
        path = route.path if route else "unmatched"
        if path != "/metrics":
            REQUESTS.labels(request.method, path, str(status)).inc()
            LATENCY.labels(request.method, path).observe(time.perf_counter() - start)


# --- Sondes et métriques (à la racine, hors /api) ----------------------------
@app.get("/health")
def health():
    """Liveness : le processus répond. Ne dépend de rien d'externe."""
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness : l'API peut-elle réellement servir ? Elle a besoin de la base."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# --- Routes métier (préfixe /api) --------------------------------------------
router = APIRouter(prefix="/api")


@router.get("/info")
def info():
    return {"hostname": HOSTNAME, "version": APP_VERSION}


@router.get("/items", response_model=list[ItemOut])
def list_items(response: Response, db: Session = Depends(get_db)):
    cached = cache.get_json(ITEMS_CACHE_KEY)
    if cached is not None:
        CACHE_EVENTS.labels("hit").inc()
        response.headers["X-Cache"] = "HIT"
        return cached

    items = db.scalars(select(Item).order_by(Item.id.desc())).all()
    payload = [ItemOut.model_validate(i).model_dump(mode="json") for i in items]
    cache.set_json(ITEMS_CACHE_KEY, payload)
    CACHE_EVENTS.labels("miss").inc()
    response.headers["X-Cache"] = "MISS"
    return payload


@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(name=payload.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    cache.delete(ITEMS_CACHE_KEY)  # la liste en cache n'est plus à jour
    return item


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    db.delete(item)
    db.commit()
    cache.delete(ITEMS_CACHE_KEY)
    return Response(status_code=204)


@router.get("/stress")
def stress(iterations: int = Query(200_000, ge=1, le=2_000_000)):
    """Consomme du CPU de façon bornée. Sert uniquement à tester l'autoscaling.

    À ne jamais exposer tel quel en production.
    """
    start = time.perf_counter()
    total = 0.0
    for i in range(1, iterations + 1):
        total += math.sqrt(i) * math.sin(i)
    return {
        "iterations": iterations,
        "result": round(total, 3),
        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
        "hostname": HOSTNAME,
    }


app.include_router(router)
