# payments-svc

API de pagos en Python para el curso sobre testing y code review con IA.

El proyecto esta preparado para avanzar por incrementos. La base inicial debe funcionar, pero conserva comportamientos ambiguos y bugs sembrados para que se pueda evidenciar como la IA genera, evalua y mejora pruebas.

## Instalacion

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## Smoke test

```powershell
python scripts/smoke_test.py
```

## API local

```powershell
uvicorn payments_svc.api:app --reload
```

Endpoints iniciales:

- `GET /health`
- `POST /payments`
- `POST /refunds`
