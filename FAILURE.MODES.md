# FAILURE-MODES.md - catalogo de fallos en payments-svc

Este archivo registra los modos de falla que aparecen al usar IA para generar pruebas y revisar codigo en `payments-svc`.

## Categoría: Generación de tests
- [n1] La IA genera solo happy-path. Omite frontera amount == 0 y casos de equivalencia. Tests pasando que no prueban nada.
 
## Categoría: Revisión de código
- [n1] La IA comenta estilo (nombres, espacios) y se pierde lo crítico:
       autorización ausente y reembolso por encima del monto original.

## Frontera

### FRO-01: Unidad mínima de moneda
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Medio — un monto "positivo" puede ser monetariamente insignificante y aun así generar cobro completo. |
| **Entrada que lo desestima** | `amount = Decimal("0.001")`, `currency = "USD"` |
| **Comportamiento actual** | `validate_amount` (líneas 60-65) solo rechaza `amount < 0`; no existe un piso distinto de cero (p. ej. `>= 0.01`). `calculate_fee` (línea 76) solo exime de fee cuando `amount == Decimal("0")` exactamente, así que `0.001` no cae en esa rama y termina pagando el `MINIMUM_FEES["USD"] = 0.30` completo (verificado). |
| **Contrato esperado** | Definir un monto mínimo significativo (p. ej. igual a `CENT`) por debajo del cual `validate_amount` rechace el monto, en vez de dejar pasar cualquier valor `> 0`. |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Sin un piso explícito, un error de cliente (enviar centavos de centavo) no se distingue de un monto real y se factura igual que un pago normal, lo cual puede sorprender a un usuario o a conciliación contable. |

### FRO-02: Techo de monto no escalado por moneda
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Medio — asimetría de diseño dentro del propio módulo. |
| **Entrada que lo desestima** | `amount = Decimal("100000.00")`, `currency = "COP"` |
| **Comportamiento actual** | `FEE_RATES` y `MINIMUM_FEES` (líneas 10-20) sí varían por moneda, pero `MAX_AMOUNT` (línea 8) es una sola constante aplicada igual a USD, EUR y COP. 100.000 COP (~USD 25) y 100.000 USD son órdenes de magnitud distintos, pero comparten el mismo techo. |
| **Contrato esperado** | Si el negocio ya modela reglas por moneda (tasas, mínimos), `MAX_AMOUNT` probablemente debería seguir el mismo patrón (`dict[str, Decimal]`), salvo que el techo sea deliberadamente global (p. ej. límite regulatorio en una sola divisa de referencia). |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Un techo mal calibrado por moneda puede bloquear pagos legítimos en una divisa o dejar pasar montos desproporcionados en otra. |

### FRO-03 / FM-FRONT-03: Monto de cobro en cero — CERRADO
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Medio — un monto cero pasa hoy la validación de rango como si fuera un cobro legítimo. |
| **Entrada que lo desestima** | `validate_amount(Decimal("0"))` |
| **Comportamiento actual (previo al cierre, aún vigente en el código)** | `validate_amount` (líneas 60-65) solo rechaza `amount < 0` y `amount > MAX_AMOUNT`; `Decimal("0")` no cae en ninguna de las dos condiciones, así que hoy es aceptado sin error. Este comportamiento actual **contradice** el contrato cerrado abajo y debe cambiar. |
| **Decisión humana** | Los montos de cobro en cero son inválidos; `validate_amount(Decimal("0"))` debe fallar con `AmountError`. |
| **Contrato (confirmado)** | `validate_amount(amount)` debe lanzar `AmountError` cuando `amount == Decimal("0")` (equivalencia numérica: cubre también `Decimal("0.00")` y `Decimal("-0.00")`). El rango válido de `validate_amount` pasa de `[0, MAX_AMOUNT]` a `(0, MAX_AMOUNT]`. No se define aquí ningún piso adicional distinto de cero — esa pregunta sigue abierta en **FRO-01**, que no se cierra con esta decisión. |
| **Estado del contrato** | Confirmado — decisión humana registrada el 2026-08-16. Cierra FM-FRONT-03. Pendiente de implementación en código y de tests. |
| **Importancia para pagos** | Un cobro de $0 no representa una transferencia de valor real; permitirlo como "válido" en la capa de validación de monto puede ocultar errores de integración (campo mal poblado, cálculo previo que colapsó a cero) en vez de rechazarlos temprano. |
| **Nota de alcance (no cierra otros pendientes)** | `calculate_fee` y `total_with_fee` llaman `validate_amount(amount)` antes de su propia lógica; con este contrato, `calculate_fee(Decimal("0"), "USD")` y `total_with_fee(Decimal("0"), "USD")` pasarían a propagar `AmountError` en vez de devolver `Decimal("0.00")`, dejando inalcanzable la rama de exención de fee en cero (líneas 76-77). Esa rama y su justificación de negocio son el objeto de **NEG-01**, que **permanece pendiente** — se documenta aquí solo como efecto en cascada a tener en cuenta al implementar, no como decisión tomada sobre NEG-01. |

---

## Equivalencia

### EQ-01 / FM-EQUIV-01: Precisión de punto flotante — CERRADO
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Alto — corrupción silenciosa de precisión monetaria. |
| **Entrada que lo desestima** | `parse_amount(0.1 + 0.2)` |
| **Comportamiento actual (previo al cierre, aún vigente en el código)** | La firma acepta `float` explícitamente (línea 31) y `Decimal(str(raw).strip())` (línea 36) toma literalmente el string del float. Verificado: `0.1 + 0.2` en Python es `0.30000000000000004`, y `parse_amount` lo acepta tal cual (no hay redondeo ni rechazo por exceso de dígitos), quedando como un "monto" válido con 17 decimales. Este comportamiento actual **contradice** el contrato cerrado abajo y debe cambiar. |
| **Decisión humana** | `parse_amount` debe rechazar entradas `float` con `AmountError`. |
| **Contrato (confirmado)** | `parse_amount` debe lanzar `AmountError` para cualquier `raw` cuyo tipo en tiempo de ejecución sea `float` (`isinstance(raw, float) is True`), sin excepción por valor — incluye enteros exactos representables (`100.0`), `float('nan')`, `float('inf')`, `float('-inf')`. Tipos soportados para `raw` quedan reducidos a `None` (ya cubierto), `str`, `int`, `Decimal`. |
| **Estado del contrato** | Confirmado — decisión humana registrada el 2026-08-16. Cierra FM-EQUIV-01. Pendiente de implementación en código y de tests. |
| **Importancia para pagos** | Es la clase de bug clásica de "nunca uses float para dinero"; aquí sí puede colarse porque el tipo lo permite explícitamente y no hay redondeo antes de usar el valor como base de cálculo de fee. |

### EQ-02: Notación científica
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Bajo/Medio — forma de entrada no anticipada para un API de pagos. |
| **Entrada que lo desestima** | `parse_amount("1e2")` |
| **Comportamiento actual** | `Decimal("1e2")` es una construcción válida y finita, así que pasa `parse_amount` sin objeción. Verificado: se acepta como `Decimal('1E+2')`, y su representación en string (`str(amount)`) queda como `"1E+2"`, no `"100.00"` — relevante porque `api.py` hace `str(amount)` para la respuesta JSON. |
| **Contrato esperado** | Decidir explícitamente si la notación científica es una entrada válida para un monto de pago; si no lo es, rechazarla en `parse_amount`. |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Si se acepta, un cliente que reciba `"1E+2"` en la respuesta de la API puede no saber interpretarlo como monto monetario estándar. |

---

## Null / Vacío

### NUL-01: String vacío tratado distinto a None
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Bajo — inconsistencia de mensaje, no de seguridad. |
| **Entrada que lo desestima** | `parse_amount("")` o `parse_amount("   ")` |
| **Comportamiento actual** | `raw is None` (línea 32) da `"amount is required"`, pero `""`/`"   "` no entra por esa rama; cae en `Decimal("".strip())` → `InvalidOperation` → `"amount must be numeric"` (línea 38). Ambos casos representan "no se envió un monto", pero producen mensajes distintos. Nótese que `normalize_currency` (líneas 46-52) sí unifica `None` y string vacío bajo el mismo mensaje `"currency is required"` — el propio archivo resuelve el problema correctamente para `currency` pero no para `amount`. |
| **Contrato esperado** | Tratar string vacío/solo-espacios como equivalente a `None` en `parse_amount`, igual que ya hace `normalize_currency`. |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Si algo consumidor (frontend, integrador) distingue tipos de error por mensaje/código, un campo vacío vs. ausente hoy dispara rutas de error distintas sin razón de negocio clara. |

### NUL-02: Sin guarda contra None/NaN fuera de parse_amount
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Alto — excepción no controlada en producción. |
| **Entrada que lo desestima** | `validate_amount(None)`, y en cadena real: `POST /refunds` con `original_amount: "NaN"` o `original_amount: "abc"` |
| **Comportamiento actual** | `validate_amount`, `calculate_fee` y `total_with_fee` asumen que ya reciben un `Decimal` finito; ninguna repite el chequeo `is_finite()` de `parse_amount`, ni valida el tipo. Verificado en runtime: `validate_amount(None)` lanza `TypeError` sin capturar. Verificado también el camino real: `api.py` (líneas 71-73) construye `Decimal(payload.original_amount)` directamente para refunds, sin pasar por `parse_amount`. `Decimal("abc")` lanza `decimal.InvalidOperation` en la propia línea de `api.py`, y `Decimal("NaN")` se construye sin error pero luego `validate_amount` con `amount < Decimal("0")` lanza `decimal.InvalidOperation` (verificado). Ninguna de las dos excepciones es `ValueError`, así que el `except AmountError` de `api.py` (línea 75) no las captura → Error 500 no controlado. |
| **Contrato esperado** | Todo monto que llegue a `validate_amount` debe ser un `Decimal` finito, y cualquier violación debe manifestarse como `AmountError`, nunca como excepción no controlada — ya sea agregando la guarda dentro de `validate_amount`, o documentando/forzando que todo llamador pase primero por `parse_amount`. |
| **Estado del contrato** | Confirmado que hoy existe una ruta real hacia una excepción no controlada; pendiente decidir en qué capa se coloca la guarda (dentro de `amounts.py` vs. responsabilidad exclusiva del llamador). |
| **Importancia para pagos** | Un endpoint de reembolsos que puede tumbarse (o filtrar detalles de excepción) con un input malformado es una superficie de riesgo operacional y potencialmente de disponibilidad, no solo un detalle cosmético. |

---

## Contrato de negocio

### NEG-01: Exención total de fee en monto cero
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Medio — regla de negocio no documentada. |
| **Entrada que lo desestima** | `calculate_fee(Decimal("0"), "USD")` |
| **Comportamiento actual** | Línea 76-77: si `amount == 0`, se retorna `Decimal("0.00")` sin pasar por `MINIMUM_FEES`. Sin este atajo, un monto de 0 pagaría el fee mínimo completo (por el `max()` de la línea 80). El propio `scripts/smoke_test.py` (línea 35) marca esto como `sentinel` — es decir, el propio equipo ya lo señaló como un comportamiento a vigilar, no como una regla confirmada. |
| **Contrato esperado** | Confirmar explícitamente si una transacción de $0 es una operación de negocio válida (p. ej. autorización sin cargo) y si debe estar exenta de fee mínimo por diseño, o si el monto cero debería rechazarse directamente en `validate_amount`. |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Cobrar o no cobrar fee mínimo sobre transacciones de $0 tiene impacto directo en ingresos y en la interpretación contable de "pago" vs. "no-operación". |

### NEG-02: Orden de validación inconsistente entre funciones públicas
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Medio — el mismo input inválido produce distinto tipo/mensaje de error según el punto de entrada. |
| **Entrada que lo desestima** | `amount = Decimal("-5.00")`, `currency = "GBP"` (ambos inválidos simultáneamente) |
| **Comportamiento actual** | `calculate_fee` valida moneda primero, luego monto (línea 73-74) → lanza `CurrencyError`. `total_with_fee` valida monto primero (línea 85) antes de invocar `calculate_fee` → lanza `AmountError`. Verificado en runtime: mismos dos valores inválidos, dos tipos de excepción distintos según cuál función se llame. Hoy `api.py` llama `calculate_fee` antes que `total_with_fee` (línea 54-55), lo que enmascara el problema en ese endpoint específico, pero el módulo en sí no garantiza consistencia si se usa de otra forma. |
| **Contrato esperado** | Que `calculate_fee` y `total_with_fee` validen en el mismo orden, de modo que el mismo par (monto, moneda) inválido produzca siempre el mismo error, sin depender de cuál función se invoque. |
| **Estado del contrato** | Confirmado que la inconsistencia en sí es un defecto de diseño; pendiente decidir cuál campo debe validarse primero (moneda vs. monto). |
| **Importancia para pagos** | Si un cliente/API traduce el tipo de excepción a un mensaje de error específico ("moneda no soportada" vs. "monto inválido"), el mismo error de usuario recibiría explicaciones distintas según una implementación interna que el cliente no controla. |

### NEG-03: Precisión del monto base nunca se canonicaliza
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Medio — ambigüedad sobre qué precisión es "válida" para un monto de pago. |
| **Entrada que lo desestima** | `parse_amount("100.006")` |
| **Comportamiento actual** | Ni `parse_amount` ni `validate_amount` fuerzan máximo 2 decimales. Solo `round_money` redondea, y únicamente se aplica al fee y al total final (líneas 81, 86) — nunca al `amount` de entrada en sí. Un monto con 3+ decimales fluye como "válido" por todo el módulo sin normalizarse. |
| **Contrato esperado** | Decidir si el dominio permite montos con precisión mayor a centavos (p. ej. para casos de FX/contabilidad intermedia) o si `amount` debe canonizarse a `CENT` inmediatamente después de `parse_amount`/`validate_amount`. |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Si un monto con sub-centavos llega a persistirse o a otros módulos (p. ej. `refunds.py`, que recibe `original_amount` tal cual), puede haber desalineación entre lo que el sistema "valida como correcto" y lo que realmente es representable como dinero. |

### NEG-04: Lista blanca de monedas no distingue formato inválido de moneda no soportada
| Atributo | Detalle |
| :--- | :--- |
| **Riesgo** | Bajo — ambigüedad de diagnóstico, no de cálculo. |
| **Entrada que lo desestima** | `normalize_currency("GBP")` vs. `normalize_currency("XYZ123")` |
| **Comportamiento actual** | `normalize_currency` (líneas 46-57) solo compara contra las 3 llaves de `FEE_RATES`; cualquier código de 3+ letras no soportado, o un string sin forma de código de moneda, produce el mismo tipo de excepción y un mensaje con el mismo formato (`f"unsupported currency: {normalized}"`). |
| **Contrato esperado** | Si soporte/integradores necesitan diferenciar "typo/formato inválido" de "moneda real pero no habilitada en este servicio", valdría la pena un mensaje o código distinto; si no, el comportamiento actual es suficiente. |
| **Estado del contrato** | Pendiente de decisión. |
| **Importancia para pagos** | Afecta la velocidad de triage cuando un integrador reporta errores de moneda — no es un riesgo de corrección de cálculo, sino de soporte/operación. |

---

> **Nota:** No incluí como "modo de falla" los límites de `MAX_AMOUNT`/`0` inclusive en `validate_amount`, ni el trim de espacios en `currency`, porque los revisé y su comportamiento es internamente consistente y no encontré ambigüedad — los dejo fuera para no inflar la lista con no-hallazgos.