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


# Guía de Ramas del Proyecto

## 📌 Estructura y Orden de Ramas

1. `prep/modulo-0-base-funcional` (Módulo 0 y 1)
2. `preclase-02-catalogo-inicial`
3. `preclase-03-decisiones-contrato`
4. `preclase-04-herramienta-mutacion`
5. `preclase-05-comparacion-prompts`
6. `develop` y `prep/modulo-b-base-limpia`
7. `preclase-07-schema-review`
8. `preclase-08-pr-mixto`
9. `preclase-09-ground-truth`
10. `preclase-10-legacy-settlement`
11. `preclase-11-semgrep-ruido`
12. `preclase-12-superficie-adversarial`
13. `preclase-13-dependencia-alucinada`
14. `preclase-14-ruta-llm-vulnerable`
15. **EXPLICACIÓN:** `preclase-15-openrouter-ready` y `test/clase-15-openrouter-check`
16. `preclase-16-shadow-ready`
17. `preclase-17-cost-ready`
18. `preclase-18-flywheel-ready`
19. `preclase-19-policy-ready`
