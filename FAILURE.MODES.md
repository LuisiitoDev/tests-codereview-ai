# FAILURE-MODES.md - Catalogo de fallos de IA en payments-svc

## Categoria: Generacion de tests
- [n1] Para amount == 0 en calculate/total_with_free, la IA documento el comportamiento actual del codigo (sin fee) como si fuera el contrato de negocio, sin cuestionar si deberia aplicar el fee minimo como en cualquier otro monto.