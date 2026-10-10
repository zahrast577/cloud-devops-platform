# ---------- Étape 1 : installer les dépendances ----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
# --prefix : on installe dans un dossier isolé pour le copier ensuite
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Étape 2 : image finale, légère ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Utilisateur non root, avec un UID numérique (requis par runAsNonRoot sur Kubernetes)
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY app ./app

USER 10001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
