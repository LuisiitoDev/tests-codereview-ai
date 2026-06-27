# payments-svc

API de pagos en Python para el curso de Platzi sobre testing y code review con IA.

El proyecto esta preparado para avanzar por incrementos de clase. La base inicial debe funcionar, pero conserva comportamientos ambiguos y bugs sembrados para que los videos puedan mostrar como la IA genera, evalua y mejora pruebas.

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

## Notas para el curso

- No hay suite unitaria completa en la base inicial.
- `amounts.py` es el modulo principal para generar tests durante el Modulo A.
- `FAILURE-MODES.md` se crea durante la Clase 01, no antes.

