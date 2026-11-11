# Plan de ejecución — PFO 3 (Flask + SQLite + JWT + cliente de consola)

> Documento de trabajo interno. No es un entregable de la materia: es la hoja de ruta
> para ejecutar la consigna sin improvisar y con testing en cada fase.
>
> **Este archivo no se versiona.** Está excluido con una regla local en
> `.git/info/exclude`, no en `.gitignore`: el repo es público y entregable, el plan no.
> Por eso todo lo que el repo *sí* necesita (las decisiones y el catálogo de puntos de
> prueba) se persiste como documento versionado — ver `docs/decisiones.md` (Fase 0.2) y
> `docs/casos-de-prueba.md` (Fase 1.6).
>
> **Excepción de idioma declarada:** `AGENTS.md` fija que la documentación del repo
> (README, docs) va en inglés. Este plan queda en español a propósito, porque está
> dirigido a la persona que va a aprender ejecutándolo, no al evaluador. Los artefactos
> técnicos del repo (README, página de presentación, docstrings, nombres de tests)
> siguen la regla de `AGENTS.md`: **documentación en inglés, código e identificadores
> en español**.

---

## Cómo usar este documento

1. Leé la **Parte A** primero: es el veredicto sobre la consigna. Ahí están los defectos
   que vas a tener que resolver vos, y por qué resolverlos es trabajo de QA, no de código.
2. Aprobá o cambiá las **decisiones de alcance** de la Parte B. Nada se construye antes
   de que esas decisiones estén cerradas. Cada una tiene un ID (`D-xx`) para poder
   citarla en commits y en el README.
3. Ejecutá la **Parte C** en orden. Cada paso tiene: **Qué** (acción), **Por qué**
   (el criterio que lo justifica), **Cómo** (lo concreto) y **QA** (qué se verifica,
   con qué técnica y qué evidencia deja).
4. Al cerrar cada paso: el checklist de *Definition of Done* de `AGENTS.md` + su commit.

---

# PARTE A — Revisión rigurosa de la consigna

## A.1 Qué pide explícitamente

| # | Requisito textual | Naturaleza |
|---|---|---|
| 1 | `POST /registro` con `{"usuario": "...", "contraseña": "..."}` | Funcional |
| 2 | Guardar usuarios en SQLite con contraseña hasheada, **nunca texto plano** | Funcional + Seguridad |
| 3 | `POST /login` que verifica credenciales y **permite acceso a las tareas** | Funcional + Autorización (implícita) |
| 4 | `GET /tareas` que "muestre un html de bienvenida" | Funcional |
| 5 | Usar una librería de hashing | Restricción técnica |
| 6 | Persistencia en SQLite | Restricción técnica |
| 7 | Cliente en consola que consuma la API | Objetivo declarado (punto 4) |
| 8 | `servidor.py`, `README.md`, capturas de pruebas, repo GitHub + GitHub Pages | Entregables |
| 9 | Responder por qué hashear y ventajas de SQLite | Conceptual |

## A.2 Defectos y ambigüedades (los que la consigna NO dice)

Esto es *requirements review*: el defecto más caro de un proyecto es el que nace en el
requisito. Cada hallazgo trae severidad y la decisión que lo cierra.

| ID | Hallazgo | Severidad | Decisión que lo cierra |
|---|---|---|---|
| R-01 | `GET /tareas` "muestre un html de bienvenida" **contradice** el título "Gestión de Tareas": no hay CRUD, no hay contrato JSON, y un cliente de consola **no puede consumir HTML** | Alta | D-06 |
| R-02 | GitHub Pages **no puede alojar Flask**: Pages sirve solo estático. La consigna pide algo técnicamente imposible | Alta | D-02, D-08 |
| R-03 | "Autenticación básica" es ambiguo (HTTP Basic ≠ sesión ≠ token). Si fuera HTTP Basic puro, `/login` sobraría | Media-Alta | D-03 |
| R-04 | No define **ningún** código HTTP ni el formato de las respuestas | Media | D-07 (contrato en API) |
| R-05 | No dice que `/tareas` deba estar protegido ni que un usuario no pueda ver tareas de otro. Está implícito en "permite acceso a las tareas" | Alta (seguridad) | D-04, D-09 |
| R-06 | No define validaciones: usuario vacío, usuario duplicado, contraseña vacía, títulos inválidos | Media | D-10, D-11 |
| R-07 | No dice qué pasa si el JSON viene malformado o sin `Content-Type` | Media-Baja | D-12 |
| R-08 | El cliente de consola está en los objetivos pero **no** en la lista de entregables | Media | D-05 |
| R-09 | No especifica dónde vive la base ni que no debe versionarse | Media | D-13 |
| R-10 | No hay criterios de aceptación: nada es verificable objetivamente | Alta (QA) | Toda la Fase 1.6 |
| R-11 | No especifica algoritmo de hashing ni política de contraseñas | Baja | D-14 |
| R-12 | No indica si la API va en la raíz o versionada | Baja | D-15 |

## A.3 Crítica al relevamiento de la sesión anterior

Lo que ya está resuelto y **no** se toca: los 5 hallazgos de alcance, la lista `TP-01..TP-17`
de puntos críticos de testing y la tabla de casos `TC-*`. Es material válido y ya aprobado;
**no se renumera** (renumerar una lista aprobada genera ruido y rompe la trazabilidad).

Lo que hay que corregir:

| Problema | Por qué está mal | Corrección |
|---|---|---|
| La "FASE 9 — Automatización de pruebas" deja la infraestructura de tests para el final | Contradice el propio principio "test-as-you-go" de la sección 2. Si la infraestructura llega al final, las fases 3–8 se escriben sin red de seguridad: exactamente lo que el documento dice evitar | La infraestructura de tests se mueve a **Fase 2.5**, antes de la primera línea de producción |
| No menciona el *app factory* (`create_app`) | Es el mecanismo técnico que hace posible testear con `test_client()` y con config distinta por test. Sin él, la estrategia de testing de todo el documento no es implementable | Nueva **Fase 1.1** |
| No menciona `PRAGMA foreign_keys = ON` | SQLite **no aplica** claves foráneas por defecto: el `FK` de `tareas → usuarios` sería decorativo y se podrían crear tareas de usuarios inexistentes | Nueva **Fase 3.1** + TP-20 |
| No menciona el sistema de archivos efímero del hosting | En Render/Railway el contenedor se recrea: **el archivo SQLite se borra** en cada deploy y en cada reinicio. Eso invalida la promesa de persistencia del proyecto en producción | Decisión **D-08** |
| No resuelve el caso `"Juan"` vs `"juan"` | En SQLite, `UNIQUE` sobre texto es *case-sensitive*: serían dos usuarios distintos. Es una regla de negocio no definida | Decisión **D-11** + TP-19 |
| No advierte el riesgo del ejemplo de la consigna | La consigna usa `"1234"` como contraseña de ejemplo. Una política mínima de 8 caracteres **rompería el ejemplo del enunciado** | Decisión **D-14** + TP-24 |
| No trata el encoding de `contraseña` (con `ñ`) en Windows | PowerShell y la consola de Windows pueden mangonear UTF-8: un bug que solo aparece en la máquina del desarrollador | Decisión **D-12** + TP-23 |
| No hay matriz de trazabilidad | RF, TP y TC viven en tres tablas separadas sin vínculo. Sin trazabilidad no podés demostrar cobertura ni saber qué requisito quedó sin probar | Nueva **Fase 9.2** |
| No define evidencia verificable | Pide "capturas de pantalla" sin decir de qué. Una captura sin el comando que la produjo no es evidencia reproducible | Nueva **Parte E** |

---

# PARTE B — Decisiones de alcance

Estado: `CERRADA` = ya decidido en la sesión anterior. `PROPUESTA` = recomendación mía,
necesita tu aprobación antes de construir.

| ID | Decisión | Valor | Estado |
|---|---|---|---|
| D-01 | Alcance de tareas | CRUD real de tareas, no placeholder | CERRADA |
| D-02 | Alojamiento | GitHub Pages = documentación/presentación estática. La API va a un runtime Python. Queda escrito en el README | CERRADA |
| D-03 | Mecanismo de auth | JWT (token firmado con `exp`) | CERRADA |
| D-04 | Protección | `/tareas` y todo el CRUD requieren token válido; aislamiento por dueño. **D-04 revisada (2026-10-12)**: `/tareas` (HTML) pasa a ser público y sin datos, y toda la protección queda en el CRUD JSON — ver `docs/decisiones.md` §7 | **CERRADA** |
| D-05 | Cliente de consola | Es entregable real (se suma a la lista) | CERRADA |
| D-06 | Representación de la ruta `/tareas` | `GET /tareas` → **HTML de bienvenida** (cumple la consigna al pie de la letra) · CRUD JSON → **`/api/tareas`**. Separa las dos representaciones, satisface el enunciado y no ensucia el contrato del cliente | **CERRADA** |
| D-07 | Recurso de otro dueño | **404**, no 403. No revela que el recurso existe. Coherente con no filtrar datos en el login | PROPUESTA |
| D-08 | Runtime de la API | **PythonAnywhere** (filesystem persistente → SQLite sobrevive) antes que Render/Railway (efímeros → la DB se borra en cada deploy). Si se elige Render, hay que documentarlo como limitación honesta | **CERRADA** |
| D-09 | Autorización | Sin token → 401 · token inválido/expirado → 401 · recurso ajeno → 404 | PROPUESTA |
| D-10 | Nombre del campo | `contraseña` exacto, con `ñ`, como pide la consigna (el evaluador puede probar con ese nombre) | PROPUESTA |
| D-11 | Unicidad de usuario | `COLLATE NOCASE`: `"Juan"` y `"juan"` son el mismo usuario. Se documenta la regla | PROPUESTA |
| D-12 | Manejo de JSON inválido | `request.get_json(silent=True)`; `None` → 400 con mensaje claro. Sin `traceback` en la respuesta | PROPUESTA |
| D-13 | Ubicación de la base | `instance/pfo3.db` (convención Flask), fuera de Git | PROPUESTA |
| D-14 | Política de contraseña | Solo "no vacía". **No** imponer mínimo de longitud: la consigna usa `"1234"` | PROPUESTA |
| D-15 | Rutas | Raíz, sin prefijo `/api/v1`: `/registro`, `/login`, `/tareas` (como el enunciado). Coherencia de barra final documentada | PROPUESTA |
| D-16 | Librerías | `werkzeug.security` (ya viene con Flask) para hashing · `PyJWT` para el token · `pytest` + `pytest-cov` para tests. **Sin** flask-jwt-extended (más magia, menos testeable) | PROPUESTA |
| D-17 | No-goals explícitos | Fuera de alcance: CORS, refresh tokens, rate limiting, roles, paginación, logout con blacklist server-side, ORM, Docker. Todo token JWT es *stateless*: el "logout" del cliente borra el token local | PROPUESTA |

> **Las dos decisiones de fondo ya están cerradas.**
> **D-06** → `GET /tareas` devuelve el HTML de bienvenida y el CRUD JSON vive en `/api/tareas`.
> **D-08** → la API se despliega en **PythonAnywhere**, por su filesystem persistente:
> es el único host gratuito de la lista donde el archivo SQLite **no** se borra en cada
> deploy. Con Render o Railway la persistencia sería ficticia y habría que declararlo
> como limitación en el README.
> El resto de la Parte B son decisiones técnicas con recomendación fundada: se implementan
> como están escritas salvo que las discutas.

---

# PARTE C — Plan por fases

## Prólogo: por qué este orden

**Entender → Decidir → Preparar → Construir de adentro hacia afuera → Verificar por capa →
Documentar → Publicar.**

Es *bottom-up*: los endpoints dependen de la capa de datos, y la capa de datos depende del
esquema. Construir al revés (endpoints primero y después ver dónde guardar) obliga a
reescribir. Y los tests **acompañan** cada capa, no se dejan para el final: un bug
encontrado a los 5 minutos cuesta una fracción de lo que cuesta uno encontrado en producción.

---

## FASE 0 — Requisitos y decisiones

### Paso 0.1 — Consolidar requisitos funcionales y no funcionales

- **Qué**: pasar la consigna a una lista numerada de RF/RNF en `docs/requisitos.md`.
- **Por qué**: separar *qué hace* el sistema (funcional) de *cómo debe comportarse*
  (no funcional: seguridad, persistencia, reproducibilidad). Los RNF son los que
  después se convierten en los TPs de seguridad.
- **Cómo**: partir de la tabla A.1 y los RF/RNF de la sesión anterior. Cada RF con
  ID estable (`RF-01`…) porque vas a citarlos en la matriz de trazabilidad.
- **QA**: nada todavía. Este paso produce el insumo que QA revisa en 0.3.

### Paso 0.2 — Cerrar las decisiones de alcance

- **Qué**: aprobar la Parte B y volcarla a `docs/decisiones.md` (tabla ID / decisión /
  motivo / alternativa descartada).
- **Por qué**: `AGENTS.md` prohíbe desviaciones silenciosas. Una decisión escrita es
  defendible ante el docente; una decisión en tu cabeza no existe.
- **QA**: verificá que **no quede ningún `PROPUESTA` sin cerrar**. Una decisión abierta
  es un requisito ambiguo que reaparece como bug en la Fase 7.

### Paso 0.3 — QA: revisión estática de requisitos (*Testability Review*)

- **Qué**: recorrer cada RF/RNF y preguntar: ¿es claro, medible y verificable?
- **Por qué**: es la actividad más temprana y más rentable de QA. Si un requisito no se
  puede convertir en un caso con resultado esperado concreto, **el requisito está
  defectuoso**, no el test.
- **Cómo**: checklist de 4 preguntas por requisito:

  | Pregunta | Si la respuesta es "no" |
  |---|---|
  | ¿Está claro (una sola interpretación)? | Ambigüedad → volver a 0.2 |
  | ¿Es medible (resultado observable)? | No testeable → reescribir |
  | ¿Es alcanzable en el alcance cerrado? | Scope creep → cortar o mover a no-goals |
  | ¿Es consistente con los demás? | Contradicción → conflicto de requisitos |

- **Evidencia**: `docs/revision-testabilidad.md` — matriz de las 41 piezas (17 RF, 16 RNF,
  8 entregables) con veredicto por requisito, y los 10 defectos encontrados con severidad y
  disposición.

- **Resultado (cerrado)**: 31 APROBADO, 10 OBSERVADO. Seis defectos se corrigieron en el
  acto, sin tocar ninguna decisión (F-02..F-07): un status inalcanzable, dos contratos de
  campo sin nombre, una regla de rechazo faltante y dos criterios subjetivos. Tres
  observaciones de severidad baja se aceptaron y quedaron documentadas: F-08 (la
  verificación de UTF-8 depende del entorno), F-09 (la excepción de idioma del plan) y F-10
  (una restricción de proceso que no se puede automatizar).

- **Hallazgo principal — F-01, severidad alta, y ya cerrado**: RF-09 exigía un token en el
  header `Authorization` sobre una página HTML. **Un navegador no manda ese header al
  navegar**, así que la página solo era alcanzable con `curl`, y la evidencia E-04
  ("navegador, autenticado") era irrealizable tal como estaba escrita. Volvió a la Fase 0.2 y
  se cerró como **D-04 revisada** (`docs/decisiones.md` §7): la página de bienvenida pasa a ser
  pública y sin datos, y toda la protección queda donde siempre estuvo la información — el CRUD
  JSON. Las tres opciones evaluadas quedan en `docs/revision-testabilidad.md` §3.
  Consecuencia para la Fase 1.2: `docs/api.md` tiene que decir explícitamente que
  `/api/tareas` exige token en todos sus métodos y `/tareas` no.

### Paso 0.4 — QA: análisis de riesgo

- **Qué**: matriz *Probabilidad × Impacto* de los TPs, para priorizar el esfuerzo.
- **Por qué**: QA **no** testea todo por igual. Prioriza por riesgo. El TP que puede
  filtrar credenciales (TP-04) pesa más que el que devuelve 405 en un método erróneo.
- **Cómo**: para cada TP, puntaje 1–3 en probabilidad e impacto, y prioridad resultante.
  Los de prioridad alta se escriben primero y no se negocian por falta de tiempo.

  Las escalas con sus anclajes concretos quedan escritas en `docs/matriz-de-riesgo.md` §1:
  sin anclajes, "probabilidad 2" es una opinión y la matriz no se puede discutir ni corregir.

- **Ajuste documentado — piso de impacto.** `P × I` tiene un punto ciego conocido: TP-04
  (contraseñas) da `1 × 3 = 3` y cae en *Medio*, **por debajo** de una validación que da 6. La
  multiplicación no está mal; el operador está mal elegido para una catástrofe. *Raro y fatal
  no se promedia contra frecuente y molesto.* Entonces: todo TP con impacto 3 es *Alto* como
  mínimo, y los dos casos que mueve (TP-04 y TP-14) quedan marcados en la tabla. Un ajuste
  silencioso sería peor que no hacerlo.

- **Evidencia**: `docs/matriz-de-riesgo.md` — grilla 3×3, las 25 filas con la justificación de
  cada puntaje, y la lista de **riesgo residual aceptado** (lo que NO se testea y por qué).

- **Resultado (cerrado)**: 1 Crítico, 15 Alto, 8 Medio, 1 Bajo. El dato útil no son los
  conteos sino dos cosas. Primero: **TP-11 (IDOR) es el único Crítico**, porque el filtro por
  dueño hay que repetirlo en cada consulta y olvidarlo es **invisible** — tus propias tareas
  siguen funcionando perfecto. Segundo: **los TPs que uno escribe primero por instinto (TP-06
  login, TP-13 CRUD) son los de menor riesgo**, porque el camino feliz se rompe a la vista.
  Los tests que se saltean son donde viven los defectos.

- **Riesgo alto ≠ se ejecuta primero.** El riesgo ordena el **esfuerzo**; la dependencia ordena
  la **ejecución**. `TP-02 → TP-06 → TP-08/09/10 → TP-11`. TP-02 es *Medio* pero va primero
  porque sin usuario no hay login; TP-21 es *Alto* pero necesita la app corriendo. Son dos
  órdenes distintos y confundirlos produce errores reales.

- **DoD de la fase**: requisitos, decisiones cerradas, revisión estática y matriz de riesgo,
  todo versionado. **Fase 0.4 cerrada.**

---

## FASE 1 — Diseño técnico

### Paso 1.1 — Arquitectura por capas + *app factory*

- **Qué**: definir la estructura de módulos y el patrón de creación de la app.

  ```
  servidor.py            # punto de entrada: create_app() + app.run() solo en desarrollo
  config.py              # Config base / ConfigTest, lee SECRET_KEY y ruta de DB del entorno
  db.py                  # conexión SQLite, row_factory, init_db(), PRAGMA
  repository.py          # DAO: todo el SQL, nada más
  security.py            # hashing + JWT, nada más
  routes.py              # HTTP: parsea, valida, llama, responde
  cliente.py             # cliente de consola
  tests/                 # ver Fase 2.5
  docs/                  # requisitos, api, decisiones, diagrama, evidencias (+ sitio de Pages)
  requirements.txt
  .env.example
  ```

- **Por qué**:
  - **SRP**: cada archivo tiene una sola razón para cambiar.
  - **`create_app(config)`** es la pieza que habilita *todo* el testing: permite instanciar
    la app con una base en memoria para los tests y con la base real en producción,
    sin tocar el código.
  - Sin esto, el resto de la estrategia de testing no es implementable.
- **Nota de YAGNI**: `repository.py` es una función-módulo, no un ORM ni una jerarquía de
  clases. No hay inyección de dependencias ni interfaces con una sola implementación:
  según `AGENTS.md`, la abstracción se introduce solo cuando hay un *seam* real (y acá lo
  hay: el seam es la base en memoria de los tests).

- **Desviación documentada — `init_db()` sale de 1.1.** El listado de arriba lo pone en
  `db.py`, pero en 1.1 todavía no existe esquema que aplicar: el DDL se diseña en 1.3 y se
  implementa en la Fase 3. Un `init_db()` con un esquema vacío es código sin requisito que
  lo pida. Se difiere a 1.3, cuando tenga DDL real que ejecutar. `db.py` entrega lo que sí
  hace falta hoy: `conectar()` con los PRAGMA, el `row_factory` y el ciclo de vida.

- **Resultado (cerrado)**: `config.py`, `db.py`, `routes.py`, `servidor.py` y
  `templates/bienvenida.html`. Los tres primeros archivos del listado (`repository.py`,
  `security.py`, `cliente.py`) **no** se crean todavía: sus requisitos llegan en las Fases 3,
  4 y 6, y un archivo vacío "para completar la estructura" es exactamente lo que `AGENTS.md`
  prohíbe. La estructura es un destino, no algo que se rellena.

  `db.py` queda partido en dos mitades con una razón: `conectar(ruta)` es Python puro y sin
  Flask — es el seam que necesitan los tests de DAO, que así ejercitan el SQL sin levantar la
  aplicación —, mientras que `obtener_conexion()`/`cerrar_conexion()` son el ciclo de vida de
  Flask, que existe solo para que una petición no abra una conexión por consulta. Si el DAO
  importara `g`, los tests de DAO exigirían contexto de petición y la capa "unit" del plan
  dejaría de ser unit.

  El `PRAGMA foreign_keys = ON` vive **dentro** de `conectar()`, no en la inicialización: es
  un PRAGMA por conexión, así que un solo punto de apertura de conexiones lo vuelve imposible
  de olvidar. La verificación incluyó la contrapueba (sin el PRAGMA, la fila huérfana entra),
  que es el defecto que TP-20 caza.

  `create_app(config_objeto=None)` recibe una **clase** de configuración y usa `Config` por
  defecto. La prueba del seam no es que exista la función, sino que dos apps instanciadas con
  configuraciones distintas no compartan estado, y que `ConfigTest` (base en memoria) no toque
  la base real. También se verificó que `create_app` **falla rápido y con mensaje útil** si no
  hay `SECRET_KEY` en el entorno, en vez de reventar más tarde al firmar un token.

  Se sumó una ruta en 1.1 — `GET /tareas`, la página pública de bienvenida (RF-09, D-04
  revisada) — por una razón concreta: sin al menos un endpoint, "la fábrica habilita el
  testing" es una afirmación sin forma de comprobarse. Esta ruta es la candidata correcta
  porque es **requisito**, no necesita token ni base de datos, y es el objetivo del smoke test
  post-deploy de DEL-08. La verificación la ejerce contra una base **sin tablas**: si la página
  tocara la base, fallaría. Responde 200 — la prueba de que no lleva datos.

  **Sin blueprint**, deliberadamente: hoy es una abstracción con una sola implementación.

  **Verificación**: 30 comprobaciones automáticas + 2 escenarios de entorno en procesos
  separados (el modo real de `Config` se evalúa una sola vez, al importar; de ahí los procesos
  aparte), más `py_compile` de los cuatro módulos. Evidencia: cifrado de los 5 archivos (UTF-8
  sin BOM), `ConfigTest` pisando a `Config`, fila huérfana rechazada con el PRAGMA y aceptada
  sin él, `GET /tareas` 200 `text/html; charset=utf-8` con `é`/`ñ` en UTF-8 real, `/api/tareas`
  todavía 404, `POST /tareas` 405, y `RuntimeError` nombrando `SECRET_KEY` cuando falta.

  **Pendiente honesto**: el script de verificación de 1.1 no se versiona; es una comprobación
  de una sola vez, no la suite. La suite real es 2.4/2.5, y es la que va a fijar estas
  conductas de forma permanente. Verificar con Flask 3.1.3 global es válido pero **no
  reproducible**: 1.4 fija versiones y 2.1 crea el venv.

### Paso 1.2 — Escribir el contrato de la API

- **Qué**: una tabla completa en `docs/api.md`: para cada endpoint → método, ruta,
  requiere token, request, respuesta, códigos posibles.
- **Por qué**: el contrato es el acuerdo entre la API y el cliente. Si no lo escribís,
  el cliente espera `usuario` y la API devuelve `username`, y depurás un fantasma.

  | Método | Ruta | Auth | Éxito | Errores |
  |---|---|---|---|---|
  | POST | `/registro` | — | 201 `{usuario}` | 400, 405, 409 |
  | POST | `/login` | — | 200 `{token}` | 400, 401, 405 |
  | GET | `/tareas` | — | 200 HTML | 405 |
  | GET | `/api/tareas` | token | 200 `[tareas]` | 401 |
  | POST | `/api/tareas` | token | 201 `{tarea}` | 400, 401 |
  | GET | `/api/tareas/<id>` | token | 200 `{tarea}` | 401, 404 |
  | PUT | `/api/tareas/<id>` | token | 200 `{tarea}` | 400, 401, 404 |
  | DELETE | `/api/tareas/<id>` | token | 204 sin cuerpo | 401, 404 |

- **Cómo**: además, **una sola forma de error** en toda la API:
  `{"error": "<mensaje>"}` con `Content-Type: application/json`. La consistencia es
  parte del contrato: un cliente que sabe leer un error sabe leerlos todos.
- **Detalle**: la respuesta de `/registro` **nunca** incluye `password_hash`
  (regla dura, TP-05).
- **Detalle (D-04 revisada)**: `docs/api.md` tiene que decir explícitamente que `/api/tareas`
  exige token en **todos** sus métodos y que `/tareas` **no**. Es la única fila del contrato
  donde la ausencia de token es la regla, y la excepción tiene que estar escrita: una
  excepción implícita se lee como un olvido.

### Paso 1.3 — Diseñar el modelo de datos

- **Qué**: el DDL exacto.

  ```sql
  CREATE TABLE IF NOT EXISTS usuarios (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
      usuario       TEXT NOT NULL UNIQUE COLLATE NOCASE,
      password_hash TEXT NOT NULL
  );

  CREATE TABLE IF NOT EXISTS tareas (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      titulo     TEXT NOT NULL,
      completada INTEGER NOT NULL DEFAULT 0,
      usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE
  );
  ```

- **Por qué**: las reglas de negocio se garantizan en la base, no solo en el código.
  La base es la **última línea de defensa**: aunque un bug en el código se salte la
  validación, el `UNIQUE` y el `NOT NULL` siguen ahí.
- **Detalle crítico**: `PRAGMA foreign_keys = ON` en cada conexión. Sin eso, SQLite
  ignora el `REFERENCES`: sería decorativo.
- **Regla documentada** (D-11): `COLLATE NOCASE` ⇒ usuario único sin distinguir mayúsculas.

### Paso 1.4 — Elegir librerías y fijar versiones

- **Qué**: `requirements.txt` con versiones fijadas + motivo de cada dependencia.
- **Por qué**: una dependencia sin justificar es deuda técnica; una versión sin fijar
  produce "funciona en mi máquina".
- **Cómo**: `werkzeug.security` (viene con Flask → cero dependencias nuevas para el
  hashing) · `PyJWT` (mínima y explícita: vos controlás el payload y la verificación) ·
  `pytest`, `pytest-cov`. Justificar explícitamente por qué **no** flask-jwt-extended.

### Paso 1.5 — QA: diagrama de flujo de información (drawio)

- **Qué**: diagrama del flujo completo: cliente → HTTP → router → validación →
  seguridad → DAO → SQLite, y de vuelta la respuesta.
- **Por qué**: **no es un dibujo decorativo**. Al trazar el flujo por dónde pasa la
  información aparecen los **puntos de cruce de confianza** (donde el usuario deja de ser
  confiable → validás), los **puntos que tocan un secreto** (contraseña, token → seguridad)
  y los puntos que **persisten** (DB → integridad). Ahí se concentra el riesgo, y ahí
  nacen los TPs.
- **Cómo**: archivo `docs/diagramas/flujo-pfo3.drawio`. Marcar visualmente los puntos
  TP-01…TP-25 sobre las flechas/etapas del flujo.
- **Entregable doble**: sirve para diseñar el testing **y** para sumar al portfolio /
  presentación.
- **Nota**: el MCP de drawio (`search_shapes`, `open_drawio_csv`, `set_page`, `list_pages`,
  `get_page`) ya está disponible en esta sesión; se valida su comportamiento al ejecutar
  el paso.

### Paso 1.6 — QA: derivar casos de prueba y la matriz de trazabilidad

- **Qué**: por cada TP → uno o más TC, cada uno con técnica y resultado esperado.
  Y la matriz `RF ↔ TP ↔ TC ↔ archivo de test ↔ resultado`.
- **Por qué**: convertís cada requisito en un escenario verificable **antes** de codear.
  Te obliga a pensar los casos borde antes de escribir una línea, y evita el test
  "que confirma lo que el código ya hace".
- **Cómo**: los 25 TPs (17 originales + 8 nuevos de esta revisión) y sus TC. Ver Parte D.
- **Entregable versionado**: el catálogo de TPs y TCs se persiste en
  `docs/casos-de-prueba.md`. `docs/requisitos.md` ya referencia los IDs `TP-xx`, así que
  deben existir **dentro del repo**: `PLAN.md` no se versiona y no puede ser el único lugar
  donde estén definidos.

- **DoD de la fase**: estructura, `docs/api.md`, DDL, `requirements.txt`, `.drawio` y
  matriz de trazabilidad. Todavía **cero** código de producción.

---

## FASE 2 — Entorno reproducible y control de versiones

### Paso 2.1 — Crear estructura y entorno virtual

- **Qué**: carpetas según 1.1 + `python -m venv venv` + `requirements.txt` + `.env.example`.
- **Por qué**: reproducibilidad (RNF-09). Un entorno que solo funciona en tu máquina no
  cumple el requisito.
- **Cómo (Windows/PowerShell, que es tu caso)**:
  - Activar: `venv\Scripts\Activate.ps1`
  - Si PowerShell bloquea el script: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
    (solo para esa sesión de terminal; no es un cambio permanente del sistema).
  - Verificar la versión de Python antes de crear el venv y dejarla escrita en el README.
- **Detalle**: `.env.example` va versionado (con valores de ejemplo); `.env` va en
  `.gitignore`. Esa distinción es la que permite documentar sin filtrar secretos.

### Paso 2.2 — Git desde el minuto cero

- **Qué**: repo, convención de commits, `.gitignore` explicado línea por línea.
- **Por qué**: el versionado no es "al final", es la red de seguridad: cada paso
  verificable = un commit. Si rompés algo, comparás contra el último estado bueno.
- **Cómo**: Conventional Commits en español (regla de `AGENTS.md`), p. ej.
  `feat(registro): agrega endpoint POST /registro con hashing`.
- **`.gitignore`**: `venv/`, `__pycache__/`, `*.db`, `.env`, `.pytest_cache/`,
  `.coverage`, `!.env.example`, `.atl/`. Cada línea con su motivo: los `.db` y `.env` son
  datos y secretos, no código; `.env.example` sí viaja, porque documenta sin filtrar; `.atl/`
  es cache local y regenerable de herramientas de agentes.
- **Adelantado al abrir la Fase 0.3.** Los dos defectos ya detectados se corrigieron en un
  commit propio `chore(gitignore)`: se borró el heredoc de PowerShell que había quedado como
  texto literal, y se agregó `!.env.example` (que va **después** de `.env.*`, o la negación
  no funciona) junto con `.atl/`. Verificado de forma empírica, no por el exit code de
  `git check-ignore` —que es ambiguo frente a una regla de negación—: creando los dos
  archivos y corriendo `git add --dry-run`, entra `.env.example` y se rechaza `.env`. La
  Fase 2.2 queda entonces como **explicación línea por línea y re-verificación**, no como
  reparación.

### Paso 2.3 — QA: verificar reproducibilidad

- **Qué**: borrar el venv (o clonar en una carpeta limpia) y levantar el proyecto
  siguiendo **solo** los pasos documentados.
- **Por qué**: es la única forma de probar que el entorno es reproducible. Si no podés,
  el defecto está en la documentación, y lo descubrís hoy y no el día de la entrega.
- **Evidencia**: el README todavía no existe; este paso se repite completo en 10.3.
  Acá se valida la mecánica del entorno.

### Paso 2.4 — QA: infraestructura de tests **antes** del código de producción

- **Qué**: `tests/conftest.py` con las fixtures base:
  - `app` → `create_app(ConfigTest)` con base **en memoria** (`:memory:`) o en `tmp_path`.
  - `client` → `app.test_client()`.
  - `usuario_registrado` / `token_valido` → estado inicial reutilizable.
  - `db_vacia` → base limpia por test (aislamiento).
- **Por qué**: acá es donde el plan anterior fallaba (tenía esto en la Fase 9).
  Si la infraestructura de tests llega al final, las Fases 3–8 se construyen **sin red**.
  Ponerla ahora hace posible escribir el test *junto* con cada pieza.
- **Regla dura**: los tests **nunca** tocan `instance/pfo3.db`. Si un test toca la base
  real, la suite deja de ser confiable y empieza a destruir datos.
- **Verificación de la propia infraestructura**: un test trivial que afirme que el cliente
  responde y que la base está vacía. Si esto no pasa, nada de lo que siga es creíble.

---

## FASE 3 — Capa de persistencia

### Paso 3.1 — `db.py`: conexión e inicialización

- **Qué**: `get_db()` (conexión atada al ciclo de request vía `g`), `row_factory` para
  obtener filas como diccionarios, `close_db()` en teardown, `init_db()` idempotente
  (`CREATE TABLE IF NOT EXISTS`) y **`PRAGMA foreign_keys = ON`**.
- **Por qué**:
  - Una conexión por request evita compartir conexiones entre hilos.
  - `row_factory` evita que el resto del código dependa de índices posicionales.
  - `init_db()` idempotente permite correrlo en cada arranque sin romper nada.
  - **El PRAGMA es el detalle que se olvida todo el mundo** y el que hace que el
    `REFERENCES` del esquema no sirva para nada.

### Paso 3.2 — `repository.py`: DAO

- **Qué**: funciones pequeñas, todas con consultas parametrizadas:
  `crear_usuario`, `buscar_usuario_por_nombre`, `crear_tarea`, `listar_tareas_de`,
  `obtener_tarea_de`, `actualizar_tarea_de`, `borrar_tarea_de`.
- **Por qué**: aislar el SQL del resto hace que el HTTP no sepa de tablas. Y las
  consultas parametrizadas (`?`) son la defensa real contra inyección SQL: **nunca**
  f-strings armando SQL.
- **Diseño clave**: las funciones de tareas reciben `usuario_id` **siempre**. El
  aislamiento por dueño se garantiza en la consulta (`WHERE id = ? AND usuario_id = ?`),
  no filtrando después en Python. Así es imposible olvidarse un caso.

### Paso 3.3 — QA: probar la capa de datos directamente

- **Qué y por qué**: se testea la base **antes** de que la API la use. Si la base falla,
  todo lo de arriba falla, y depurarlo a través de tres capas es el doble de caro.

  | Caso | Qué verifica | Esperado |
  |---|---|---|
  | Insertar usuario válido | Camino feliz | Fila creada con `id` |
  | Insertar usuario duplicado | Constraint `UNIQUE` | `IntegrityError` |
  | Insertar `"Juan"` y `"juan"` | Regla `COLLATE NOCASE` (TP-19) | `IntegrityError` |
  | Insertar con `usuario` nulo/vacío | `NOT NULL` | `IntegrityError` |
  | Insertar tarea con `usuario_id` inexistente | **PRAGMA** `foreign_keys` (TP-20) | `IntegrityError` |
  | Borrar usuario con tareas | `ON DELETE CASCADE` | Tareas huérfanas: 0 |
  | **Inspección real de la tabla** (TP-04) | La contraseña guardada ≠ original | `password_hash != "1234"` |
  | Input `' OR 1=1 --` (TP-14) | Query parametrizada | Sin efecto; no borra ni devuelve todo |
  | Aislamiento en el query (TP-11) | `listar_tareas_de(usuario_A)` | No incluye tareas de B |

- **Nota sobre TP-04**: este test **no** se hace por la API. Se hace abriendo la base y
  leyendo la columna. Por la API nunca vas a ver el hash: el punto es confirmar que en
  disco está hasheado. Es un test de *inspección*, no de contrato.

---

## FASE 4 — Capa de seguridad: hashing y token

### Paso 4.1 — `security.py`: hashing

- **Qué**: `hashear_password(plano)` y `verificar_password(hash_guardado, plano)`.
- **Por qué**: centraliza el hashing en un solo lugar (DRY) y aplica automáticamente
  *salt* aleatorio por contraseña. Si mañana cambia el algoritmo, se cambia acá y nada
  más. Dos llamadas idénticas producen hashes distintos: eso es el salt, no un bug.

### Paso 4.2 — `security.py`: creación y validación del token

- **Qué**: `crear_token(usuario_id)` → JWT firmado `HS256` con claims `sub`, `iat`, `exp`.
  `decodificar_token(token)` → payload o error.
- **Por qué**: JWT permite validar *stateless*: el servidor no guarda sesiones.
- **Detalles que son el 90% de la seguridad del token**:
  - El algoritmo se declara **explícitamente** al decodificar (`algorithms=["HS256"]`).
    Si no, un atacante puede mandar `alg: none` o cambiar el algoritmo: es la
    vulnerabilidad clásica de las librerías JWT.
  - `exp` obligatorio, validado por la librería.
  - `sub` como string (la spec lo exige) → convertir el `id` a texto.
  - La `SECRET_KEY` sale del entorno (RNF-03), nunca del código.
  - El payload **no** lleva la contraseña ni el hash: el JWT es firmado, no cifrado;
    cualquiera lo puede leer decodificando base64.

### Paso 4.3 — QA: probar seguridad

| Caso | Técnica | Esperado |
|---|---|---|
| `hashear_password("1234") != "1234"` | Irreversibilidad (TP-04) | Distinto |
| Dos hashes de `"1234"` | Salt (TP-04) | Distintos entre sí |
| `verificar_password` con la correcta / incorrecta | Feliz + negativo | `True` / `False` |
| Token propio decodifica y trae el `sub` correcto | Feliz | Payload esperado |
| Token con la firma alterada (1 char) | Seguridad (TP-08) | Error |
| Token firmado con **otra** clave | Seguridad (TP-08) | Error |
| Token `alg: none` | Seguridad (TP-08) | Error / rechazado |
| Token con `exp` en el pasado (TP-09) | Valores límite | Error |
| Payload del token inspeccionado | No filtrar (TP-05/RNF-06) | Sin contraseña ni hash |

- **Truco para TP-09 (expiración)**: no agregues `freezegun` ni esperes. Generá el token
  con tu **propia** función de creación, pasándole un `exp` ya pasado. Cero dependencias
  nuevas y test instantáneo. Ojo: eso implica que `crear_token` acepte el `exp` como
  parámetro (con default) en lugar de calcularlo siempre adentro.
- **Por qué este orden**: es el requisito de seguridad más crítico de la consigna.
  Si falla el hashing, el sistema entero es inseguro por más que todo lo demás funcione.

---

## FASE 5 — Endpoint `POST /registro`

### Paso 5.1 — Implementar

- **Qué**: parsear JSON seguro, validar, hashear, delegar al DAO, responder.
- **Cómo**: `request.get_json(silent=True)`; si es `None` → 400 (D-12). Validar
  `usuario`/`contraseña` presentes, de tipo texto, y no vacíos **después de `strip()`**
  el usuario. `contraseña` **no** se le hace `strip`: recortar una contraseña en silencio
  cambia la credencial del usuario. Mapear `IntegrityError` (UNIQUE) → **409**.
  Respuesta 201 `{"usuario": "..."}`. **Nunca** `password_hash`.
- **Por qué cada código**: 201 porque se creó un recurso · 400 porque el request está mal
  · 409 porque hay conflicto con el estado actual (el usuario ya existe). Si devolvés 400
  para el duplicado, el cliente no puede distinguir "mandaste mal los datos" de
  "ese usuario ya está tomado", y la UX no puede reaccionar distinto.

### Paso 5.2 — QA: suite del endpoint

Esto se diseña con técnicas formales, no por intuición:

| Técnica | Qué genera | Ejemplos |
|---|---|---|
| Particiones de equivalencia | Datos válidos vs. inválidos | válido / sin contraseña / tipos erróneos |
| Análisis de valores límite | Los bordes de cada partición | usuario vacío, 1 char, **`"1234"` (el ejemplo de la consigna, TP-24)**, string muy largo |
| Casos negativos | Conflictos y entradas rotas | duplicado → 409; JSON malformado → 400 (TP-18); sin `Content-Type` → 400 |
| Método / ruta | Contrato HTTP | `GET /registro` → 405 |
| Seguridad | Fugas y validación no confiable | la respuesta no trae hash ni contraseña; `' OR 1=1 --` como usuario no rompe |

- **TP-24 merece atención**: el caso borde más importante es el que **la propia consigna
  usa como ejemplo**. Si agregás una política de mínimo 8 caracteres "por buenas
  prácticas", el evaluador va a probar con `"1234"` y va a recibir un 400. Vas a haber
  roto el enunciado cumpliendo el enunciado. Por eso D-14 dice "solo no vacía".
- **Dato de borde que casi nadie prueba**: `usuario` con espacios (`"  juan  "`). Decidir
  y testear si el `strip` normaliza o no.

- **Resultado (cerrado)**: `POST /registro` implementado en `routes.py` (vista `registrar`)
  con TDD. 20 tests nuevos en `tests/test_registro.py`, uno por TC-REG (01..16) mas las
  tres propiedades que solo se ven integradas: la password queda hasheada en la base
  (TP-04 por el camino real del endpoint), la respuesta no filtra hash ni texto plano
  (TC-REG-13) y un nombre con `' OR 1=1 --` se guarda como valor, no como SQL (TP-14).
  Suite total: 46 en verde. Commits `a4e8f07` y `157f1ff`.

  Decisiones de borde tomadas al implementar: un JSON que **no es objeto** (`[1,2]`) es
  400, no 500 — el contrato dice "JSON malformado → 400" y un array bien formado rompe
  el mismo supuesto del cliente. `contraseña` se valida con `isinstance(str)` primero:
  un `null` y un `123` dan 400, no un `TypeError` disfrazado de 500.

- **Verificación independiente (2026-11-10)**: PASS con advertencias sobre `f2604ff..HEAD`.
  Sin bloqueantes: ningún camino devuelve hash, texto plano, traceback ni ruta interna. Sí
  encontró dos cosas que se corrigieron en el acto (commit `157f1ff`): los mensajes de
  error se habían escrito **sin acentos** y `docs/api.md` §7 los fija "en español con
  acentos" — un incumplimiento de contrato que ningún test detectaba. Además se cerraron
  tres huecos de cobertura (sin `Content-Type`, `PUT /registro` → 405 y `Content-Type:
  application/json` en toda respuesta de error) y la línea de estado del contrato ya no
  decía que `/registro` no existía. Suite: 46 en verde.

  **Riesgos residuales nuevos, documentados y no implementados** (ninguno filtra nada):
  (1) un string JSON con *surrogate* suelto (`"\ud800"`) parsea bien y revienta en el bind
  de SQLite → 500; el contrato no define esa clase de entrada y no conviene inventar una
  regla de encoding sin requisito. (2) `OPTIONS /registro` responde 200 automático de
  Flask mientras el contrato dice "método distinto de POST → 405": la frase es absoluta y
  la realidad de HTTP no lo es.

---

## FASE 6 — Endpoint `POST /login`

### Paso 6.1 — Implementar

- **Qué**: buscar usuario, verificar contraseña, emitir token, responder 200 `{"token": ...}`.
- **Detalle de seguridad (TP-07)**: si el usuario no existe **y** si la contraseña está mal,
  devolver el **mismo** 401 con el **mismo** cuerpo. Si diferenciás los mensajes
  ("usuario no existe" vs "contraseña incorrecta"), le regalás a un atacante un buscador
  de usuarios válidos: eso es *user enumeration*.
- **Cómo**: `if usuario is None or not verificar_password(...)` → un solo camino de error.
- **Nota**: verificar la contraseña **aunque** el usuario no exista no es necesario en este
  alcance (YAGNI), pero sí conviene saber que existe un ataque de *timing* por la diferencia
  de tiempo. Se documenta como riesgo residual, no se implementa. **Medido al cerrar la fase:
  335,7 ms vs 1,1 ms, ~296x, sin solapamiento de distribuciones.** Riesgo aceptado en D-29.

### Paso 6.2 — QA: pruebas de login

| Caso | Esperado |
|---|---|
| Credenciales correctas | 200 + `token` presente y no vacío |
| Contraseña incorrecta (TC-LOG-02) | 401 |
| Usuario inexistente (TC-LOG-03) | 401, **cuerpo byte a byte idéntico** al anterior |
| Sin `contraseña` en el body | 400 |
| JSON malformado | 400 |
| `GET /login` | 405 |

- **Cómo se testea "mensaje idéntico"**: comparar el JSON completo de ambas respuestas,
  no solo el status. El test que solo compara `401 == 401` pasa aunque los mensajes
  difieran, y no te protege de nada.
- **Conexión con TP-17**: el contrato de `/login` que estás testeando acá es el mismo que
  el cliente va a consumir en la Fase 8. Si la clave se llama `token` y el cliente busca
  `access_token`, el E2E lo va a detectar *recién ahí*. Por eso el contrato (1.2) se
  escribe antes.

### Resultado (cerrado)

`POST /login` implementado en `routes.py` (vista `iniciar_sesion`) con TDD. 13 tests en
`tests/test_login.py`, uno por TC-LOG (01..09) más el contenido del token que consume la
Fase 7: `sub` como string con el id, `iat`/`exp` presentes y payload sin credenciales.
Commit `5ecfaff`, más `a753d22` que alarga la `SECRET_KEY` de test a 39 bytes para callar
`InsecureKeyLengthWarning` (RFC 7518 §3.2). Suite: 59 en verde.

Decisiones tomadas al implementar:

- La `SECRET_KEY` se pasa **explícita** desde la capa HTTP (`current_app.config`), no se deja
  que `security.py` la busque en el entorno. Sin eso, la clave configurada por la app se
  ignoraba en silencio: la firma usaba otra clave distinta de la configurada.
- El test del payload compara **valor por valor**, no el diccionario serializado: un `exp`
  puede contener la secuencia `"1234"` por casualidad y haría fallar un test correcto.
- TC-LOG-04 ahora afirma también el cuerpo esperado, no solo que las dos respuestas sean
  iguales: comparar dos respuestas entre sí pasa aunque las dos estén mal.

**Verificación independiente (2026-11-10): FAIL**, con un bloqueante y varias advertencias.

- **Bloqueante — canal de tiempo en `/login`**: el `or` corta en corto, así que el usuario
  inexistente nunca paga scrypt. Medido: **335,7 ms vs 1,1 ms (~296x)**, p95 434,7 vs 1,9,
  sin solapamiento, reproducible. El contrato (§5) fija status, cuerpo y `Content-Type`, y
  los tres se cumplen; el tiempo no está en el contrato y no hay requisito de
  side-channels. **Decisión del usuario: riesgo aceptado y documentado en `docs/decisiones.md`
  D-29**, con la medición completa y el argumento: cerrarlo agrega ~200 ms de CPU por login
  fallido sin rate limiting, lo que cambia un leak difícil de explotar por una palanca de
  DoS fácil de explotar. El límite queda escrito en el docstring de la vista y en el de la
  suite para que nadie confunda un suite verde con un canal cerrado.
- **Advertencias corregidas en el mismo cierre**: `import json` sin usar en `test_login.py`;
  bloque de validación de credenciales duplicado entre `registro` y `login` (extraído a
  `_validar_credenciales`, que es la misma regla del contrato en los dos endpoints);
  `Config.HORAS_EXPIRACION_TOKEN` muerta y contradictoria (`crear_token` nunca lee la config,
  así que la constante era una trampa: cambiarla no cambiaba nada); `exp − iat = 8 h` de
  TC-TOK-01 afirmado de verdad en `tests/test_seguridad.py` (el documento decía que estaba
  fijado y no lo estaba); `Allow` en el 405 (RFC 7231 §6.5.5: sin él el cliente no sabe qué
  método sí funciona); y el ejemplo del 401 en `docs/api.md` §5 tenía punto final que el
  código no tiene — se fijó la convención "sin acentos no, con acentos y sin punto final" y
  se ancló con aserciones literales.


---

## FASE 7 — Endpoints de tareas (protegidos y autorizados)

### Paso 7.1 — Middleware de autenticación

- **Qué**: un decorador `@requiere_token` que lee `Authorization: Bearer <token>`, valida
  `exp` y firma, resuelve el usuario y lo inyecta en el request. Si falta o es inválido
  → 401 con el formato de error estándar.
- **Por qué un decorador y no repetir el chequeo en cada función**: es DRY y, más
  importante, **no se puede olvidar**. Un endpoint nuevo que no lleva el decorador es un
  endpoint abierto: el olvido es el bug, y el decorador lo hace visible en el código.

### Paso 7.2 — `GET /tareas` (HTML de bienvenida)

- **Qué**: devuelve la página HTML que pide la consigna. **Sin token**: es pública y sin datos.
- **Por qué**: cumple el enunciado literal (R-01/D-06). Como un cliente de consola no puede
  consumir HTML, el CRUD JSON vive aparte.
- **Por qué sin token (D-04 revisada)**: una página de bienvenida no lleva información que
  proteger, y un navegador **no puede** mandar el header `Authorization` al navegar. Exigirlo
  dejaba la página alcanzable solo con `curl` y volvía irrealizable la evidencia E-04.
- **Cuidado**: el HTML se sirve como `Content-Type: text/html`, y los errores de la API
  siguen siendo JSON. Si mezclás, el cliente no sabe qué parsear.

### Paso 7.3 — `GET/POST/GET-id/PUT/DELETE /api/tareas`

- **Qué**: el CRUD completo, cada uno con `@requiere_token`.
- **Cómo**: validar `titulo` (presente, texto, no vacío tras `strip`, largo máximo
  razonable) → 400. Las consultas siempre filtran por `usuario_id` del token.
- **Por qué `PUT` y no `PATCH`**: `PUT` con el recurso completo es más simple de testear
  (idempotente, sin semántica de campos parciales). YAGNI: no hace falta `PATCH`.
- **Códigos**: 201 al crear · 200 al leer/editar · **204 con cuerpo vacío** al borrar
  (no devolver `{"ok": true}`: 204 significa justamente "listo, sin cuerpo").

### Paso 7.4 — QA: autorización y CRUD

| Caso | Técnica | Esperado |
|---|---|---|
| `/api/tareas` sin `Authorization` (TP-10) | Autorización | 401 |
| Token alterado / expirado / de otra clave (TP-08, TP-09) | Seguridad | 401 |
| `Authorization: Bearer` vacío o malformado | Valores límite | 401 |
| Ciclo completo crear→listar→editar→borrar (TP-13) | Flujo | 201 / 200 / 200 / 204 |
| Crear sin `titulo` o con `titulo` vacío (TP-12) | Valores límite | 400 |
| `titulo` numérico en vez de texto | Partición inválida | 400 |
| `GET /api/tareas/<id>` inexistente | Negativo | 404 |
| **Usuario A pide la tarea de B — GET** (TP-11) | Autorización / **IDOR** | **404** |
| **Usuario A edita la tarea de B — PUT** (TP-11) | IDOR | **404** |
| **Usuario A borra la tarea de B — DELETE** (TP-11) | IDOR | **404** |
| **Usuario A lista tareas y no ve las de B** (TP-11) | IDOR | Solo las propias |
| `GET /api/tareas` con método no permitido | Contrato | 405 |

- **Por qué el IDOR es el test más importante de la fase**: es el bug más probable y el
  más grave de este diseño. La autorización **no** se prueba con el camino feliz: se prueba
  intentando exactamente lo que no se debe poder hacer. Un test que solo verifica que el
  dueño ve su tarea pasa aunque **el aislamiento no exista**.
- **Por qué 404 y no 403 (D-07)**: si A pide la tarea 42 de B y devolvés 403, le confirmás
  que la tarea 42 existe. Con 404, tu API es consistente con la decisión del login: no
  revela lo que no te corresponde.

### Paso 7.5 — QA: manejo de errores global

- **Qué**: `@app.errorhandler` para 404, 405 y 500, todos en JSON con el formato estándar.
- **Por qué**: Flask devuelve **HTML** por defecto en los errores. Eso rompe el contrato
  que el cliente espera y, en modo debug, expone el *debugger interactivo* de Werkzeug,
  que permite ejecutar código arbitrario en el servidor. Es la falla de seguridad más
  grave posible en un deploy.
- **Cómo se testea el 500 (TP-16)**: forzá una excepción con `monkeypatch` en el DAO y
  verificá: (a) status 500, (b) cuerpo JSON, (c) **sin** `traceback` ni nombres de rutas
  internas, (d) que la excepción **sí** quedó registrada en el log del servidor. Un error
  silencioso es tan malo como uno que filtra.

- **Adelantado a la Fase 5 (2026-11-10, decisión del usuario)**: los tres manejadores
  (`404`, `405` y `Exception` → 500) se implementaron en `routes.py` en el commit
  `7f33004`, junto con `tests/test_errores.py`. La razón: TC-REG-15 exige
  `GET /registro → 405` **con cuerpo JSON**, y esa garantía no se puede afirmar sin el
  manejador. Queda para 7.5 lo que depende de código que todavía no existe:
  `TC-ERR-02` (`GET /api/tareas/999` → 404 JSON) y el 401 de autorización. El detalle
  interno del 500 se verifica, además de por ausencia de texto, por presencia en
  `caplog`: el test prueba que el error **no se silencia**.

### Resultado (cerrado)

Fase 7 completa en `routes.py` con TDD: `requiere_token` (7.1), el CRUD de cinco vistas
(7.3) y lo que faltaba de 7.5 (`TC-ERR-02` y el 401 de autorización; los manejadores ya
estaban desde la Fase 5). El paso 7.2 (`GET /tareas`) ya se había cerrado en la Fase 5 con
`bienvenida`. Commit `a892bb8`. **59 tests nuevos**: 18 en `tests/test_autorizacion.py` y 41
en `tests/test_tareas.py`. Suite: **120 en verde**.

RED antes de implementar: 54 de los 59 fallaban. Los 5 que pasaban eran los 404, que
"aciertan" porque la ruta todavía no existía; por eso cada uno tiene su par positivo que sí
fallaba y que prueba que la ruta existe. Un 404 verde por ausencia de ruta es un falso verde.

Decisiones tomadas al implementar:

- **Sin blueprint**, aunque ahora exista el prefijo `/api`. Cinco reglas de una línea no se
  vuelven más simples con un objeto de registro aparte, y lo que las vistas comparten (el
  401, `g.usuario_id`, los manejadores de error) es de la app, no del prefijo. Queda escrito
  en el docstring de `registrar_rutas` para que nadie lo "arregle" después.
- **La clave se pasa explícita** a `security.decodificar_token` desde `current_app.config`,
  igual que en el login. Sin eso el middleware firma con una clave y valida con otra.
- **El esquema es case-insensitive** (`bearer`, `Bearer`, `BEARER`): RFC 7235 §2.1. Se probó
  que es lo único que se acepta con tolerancia; el resto de las variantes son 401.
- **Un solo 401 para las seis causas**, verificado byte a byte: header ausente, sin `Bearer`,
  token vacío, malformado, alterado, expirado, firmado con otra clave y `sub` ausente o no
  numérico (que serían un 500 si no se atraparan). El test de identidad byte a byte está
  separado del test de cada causa: una implementación puede dar 401 en todos los casos y aun
  así delatar la causa con mensajes distintos.
- **El token no se acepta por query string ni por cookie**: viaja en el header o no viaja. Un
  token en la URL termina en logs, historial y proxies.
- **`PUT` valida el cuerpo antes de buscar la tarea**: un cuerpo inválido es 400 exista o no
  el id, así que la respuesta no filtra si ese id pertenece a alguien.
- **`_validar_tarea` es una sola regla para `POST` y `PUT`**, con el título recortado antes de
  medir el largo (D-19: 200 entra, 201 no) y `completada` comparada contra `bool`, no contra
  *truthy*.
- **`repository.crear_tarea` ganó `completada=False`**: el contrato deja el campo opcional al
  crear, y obligar a un `PUT` extra para marcarla serían dos escrituras donde el cliente pidió
  una.
- **El 204 necesitó código**: `return "", 204` no alcanza porque Werkzeug le pone igual
  `Content-Type: text/html; charset=utf-8`, que contradice D-23. Se construye la respuesta y
  se quita el header a mano. Sin el test literal del header, la violación del contrato pasaba
  con la suite verde.
- Los fixtures `usuario_registrado` y `token_valido` se crean **por el camino real**
  (`POST /registro` y `security.crear_token`), no con SQL inventado: si la suite construye el
  estado que la app no sabe construir, mide la suite.

---

## FASE 8 — Cliente de consola

### Paso 8.1 — Construir el cliente

- **Qué**: menú de consola → registro, login, listar, crear, editar, borrar, salir.
  `requests` con `timeout` explícito. Manejo de respuesta HTTP y de error de red.
- **Por qué**:
  - **`timeout`**: sin timeout, si la API no responde, el cliente se cuelga para siempre y
    el usuario no sabe si falló. Es un bug de UX que se ve en producción.
  - **El token vive en memoria**, no en un archivo. Escribir un JWT en disco en texto plano
    es exactamente el problema que el hashing busca evitar.
  - **Nunca** imprimir el traceback al usuario: mensaje claro + código de error.
- **Detalle de Windows**: la consola puede estar en `cp1252` y romper con acentos
  (TP-23). Forzar UTF-8 en la salida y probar con `contraseña` real.
- **Qué NO hace** (D-17): no hay "logout" del lado del servidor. El cliente borra el token
  local y listo. Un JWT es stateless: para invalidarlo habría que mantener una blacklist,
  que está fuera de alcance. Se documenta.

### Paso 8.2 — QA: pruebas end-to-end

- **Qué**: el ciclo completo con cliente + API + base reales.
- **Por qué**: los tests unitarios prueban piezas; los de integración prueban capas; solo
  el E2E prueba que **la integración funciona de verdad**. Ahí aparecen los bugs de
  contrato: el cliente espera `usuario` y la API devuelve `username` (TP-17).
- **Cómo se testea un cliente de consola**: separando la lógica de presentación de la de
  red, para poder llamar a las funciones del cliente desde pytest con el `test_client`
  de la app. No hace falta automatizar la interacción por teclado: se testea la capa de
  transporte y los flujos, y el menú se valida manualmente con evidencia.

| Caso | Esperado |
|---|---|
| Ciclo registro → login → crear → listar → editar → borrar (TC-E2E-01) | Todas las operaciones OK, salida correcta |
| Nombres de campos y status codes | Coinciden con `docs/api.md` (TP-17) |
| API caída (puerto cerrado) | Mensaje claro, **sin traceback** |
| Token expirado | Mensaje de sesión vencida, no crash |
| Contraseña con `ñ` de punta a punta (TP-23) | Funciona (registro y login) |

### Resultado (cerrado)

Fase 8 completa con TDD: `cliente.py` (transporte + menú) y dos archivos de test. **19 tests
nuevos** — 18 en `tests/test_cliente.py` y 1 en `tests/test_encoding.py` — y la suite pasa de
**126 a 145 en verde**.

El plan decía que el menú se valida a mano porque no hace falta automatizar el teclado, pero
TC-E2E-02/03 piden **código de salida distinto de cero y sin traceback**, y eso vive en el menú,
no en el transporte. Se resolvió inyectando `leer`/`escribir` en `menu(...)`: dos tests guionan
una sesión desde pytest y afirman el código de salida de verdad. El menú **además** se validó a
mano contra un servidor real.

Decisiones tomadas al implementar (D-30):

- **Dos capas con una costura**: `ApiDeTareas` es transporte (URL, `Authorization`, `timeout`,
  traducción de errores) y `menu` es presentación. El seam de `sesion` existe por la regla
  YAGNI ⇄ SOLID de `AGENTS.md` — hay una segunda implementación real, un adaptador sobre el
  `test_client` de Flask — y es lo que permite ejercitar el contrato sin abrir un puerto.
- **`PUT` es reemplazo completo** (D-17): el cliente manda título **y** `completada`. Mandar solo
  el título devolvería la tarea a `false` sin que nadie lo pidiera.
- **`timeout` explícito en todas las llamadas**, verificado por un test que recorre los seis
  envíos: sin él, una API colgada cuelga al usuario para siempre.
- **204 sin cuerpo**: no se llama `.json()`, así que un `DELETE` no revienta parseando la nada.
- **Un solo `_enviar`** centraliza las cuatro cosas que no se pueden olvidar. Siete métodos
  copiando esas líneas es como se cuela la llamada sin timeout.
- **Un 401 de `/registro` o `/login` no cierra la sesión vigente**: esas dos rutas van con
  `autenticada=False`, así que no mandan header. Sin eso, un login fallido borraba el token de
  una sesión que ya estaba abierta — lo encontró la autorrevisión, no la suite original.
- **El mensaje de "volvé a iniciar sesión" depende de `sesion_cerrada`**, no del código 401:
  pedirle eso a alguien que justamente estaba intentando entrar no informa nada.

El E2E real (no el `test_client`) se corrió a mano contra `flask run` en un puerto libre, con
`DATABASE_PATH` en `%TEMP%`, entrada UTF-8 por archivo y código de salida capturado: ciclo completo
(registro → login → crear → listar → editar → borrar → sesión vacía → login fallido) con los
status 201/200/201/200/200/200/204/200, `contraseña` intacta en pantalla, y `exit 0` en la
sesión limpia / `exit 1` en la que tuvo una operación fallida. Lo que el `test_client` no puede
dar — `requests` real, HTTP real y consola real — queda cubierto por esa corrida.

**Un hueco preexistente, cerrado acá**: `docs/casos-de-prueba.md` documentaba TC-ENC-01 para
`tests/test_encoding.py`, y ese archivo nunca existió. El caso ahora existe y afirma los bytes
crudos (`b"\xc3\xb1"` presente, `b"\\u00f1"` ausente): un test que solo compara el JSON parseado
pasa igual si el servidor manda el escape, con lo cual no probaría nada de RNF-10.

El conteo de casos del documento también estaba viejo: decía 78 cuando las adiciones de la
Fase 7 ya lo habían movido. Se recalculó por script sobre la tabla: **86 casos sobre 25 puntos de
prueba**, y cuatro puntos con un solo caso (TP-06, TP-09, TP-15, TP-16).

---

## FASE 9 — Cierre de calidad

### Paso 9.1 — Cobertura y pirámide

- **Qué**: `pytest-cov`, y conteo de tests por nivel.
- **Por qué**: la forma ideal es una **pirámide**: muchos unitarios (rápidos, aislados),
  menos integración, pocos E2E (lentos, frágiles). Una pirámide invertida (todo E2E) es
  lenta y carísima de mantener, y cuando falla no te dice **dónde** está el problema.
- **Cómo interpretar la cobertura**: la cobertura te dice qué código **nunca** ejecutás.
  No te dice si el test está bien. Perseguir 100% produce tests que no verifican nada.
  Se prioriza cubrir los caminos de error y seguridad.

### Paso 9.2 — Matriz de trazabilidad y cierre

- **Qué**: completar la matriz `RF ↔ TP ↔ TC ↔ test ↔ resultado`.
- **Por qué**: es el documento que demuestra que no falta nada. Se lee en dos direcciones:
  - **Requisito sin test** → requisito no verificado → riesgo abierto.
  - **Test sin requisito** → test huérfano → o sobra, o falta documentar el requisito.
- **Evidencia**: `docs/trazabilidad.md` con el resultado de la suite.

### Paso 9.3 — Decisión de release

- **Qué**: veredicto **PASS / CONDITIONAL / FAIL** + riesgos residuales.
- **Por qué**: cerrar sin un veredicto explícito es lo mismo que no haber cerrado.
  Los riesgos residuales se enumeran (p. ej.: timing attack en login, DB efímera si el
  hosting elegido no es persistente, sin invalidación de tokens).

### Paso 9.4 — QA: verificar que no se filtraron secretos

- **Qué**: buscar `SECRET_KEY`, `.env`, `*.db`, contraseñas en **toda** la historia de Git.
- **Por qué**: un secreto commiteado queda en la historia **para siempre**, aunque lo
  borres en el commit siguiente. Clonar el repo alcanza para recuperarlo.
- **Cómo**: `git log -p` filtrando por los patrones sospechosos, `git grep` sobre toda la
  historia, y revisión visual del último commit. Si apareció uno: se **rota** el secreto
  (no alcanza con borrarlo).

---

## FASE 10 — Documentación y evidencia

### Paso 10.1 — `README.md` (en inglés, según `AGENTS.md`)

- **Qué**: descripción, requisitos, instalación paso a paso, cómo correr el servidor y el
  cliente, tabla de endpoints con ejemplos `curl`, cómo correr los tests, decisiones de
  alcance (D-01…D-26 resumidas), limitaciones conocidas y cómo se deploya.
- **Obligación registrada**: el README debe declarar los agregados fuera de la consigna —
  el CRUD real (D-01), el cliente de consola como entregable (D-05) y el campo `completada`
  (D-22). La consigna no los pide; el README los declara. Es la regla de `AGENTS.md` de no
  desviarse en silencio, aplicada al entregable que lee el evaluador.
- **Por qué**: es un entregable calificado y, además, la prueba de reproducibilidad del
  proyecto. Sin él, el punto 2.3 no se puede verificar.
- **Detalle que la consigna exige**: dejar escrito que **Pages no puede correr Flask**
  (R-02). Explicar los dos despliegues: estático (Pages) y runtime (API). Explicitar el
  error conceptual del enunciado es exactamente lo que se espera de un alumno que entiende.

### Paso 10.2 — Evidencia de las pruebas

- **Qué**: `docs/evidencias/` con las capturas que pide la consigna.
- **Por qué**: "capturas de pruebas exitosas" es un entregable, y una captura **sin el
  comando que la produjo no es evidencia**. Es una imagen de algo que no se puede repetir.
- **Cómo**: cada captura con un pie de foto que incluya el comando exacto y la versión.
  Mínimo: (1) `pytest -v` completo en verde, (2) el reporte de cobertura, (3) `curl` de
  registro/login/tareas con sus códigos, (4) la página HTML de `/tareas` en el navegador,
  (5) el cliente de consola en el ciclo completo, (6) el deploy público respondiendo.
- **Conexión QA**: la evidencia es la prueba objetiva del cierre. Si una captura no se
  puede regenerar, no es evidencia: es un recuerdo.

### Paso 10.3 — QA: *walkthrough* del README

- **Qué**: ejecutar el README al pie de la letra, como usuario nuevo, en un entorno limpio.
- **Por qué**: es una prueba de usabilidad y de documentación. Si no lográs levantar el
  proyecto siguiendo tu propio README, **el README tiene el defecto**. Es lo más cerca que
  vas a estar del evaluador antes de la entrega.
- **Evidencia**: lista de hallazgos (pasos que faltan, órdenes confusos, comandos que no
  funcionan en Windows) + su corrección.

---

## FASE 11 — Publicación

### Paso 11.1 — Repositorio en GitHub

- **Qué**: push, commits con Conventional Commits, `.gitignore` verificado.
- **Cómo**: revisar antes de cada push que `git status` no incluya `venv/`, `*.db`, `.env`
  ni `.pytest_cache/`.

### Paso 11.2 — Deploy de la API en un runtime Python

- **Qué**: `gunicorn` como servidor de producción (el de Flask es **solo** para desarrollo),
  `SECRET_KEY` por variable de entorno, `debug=False`, y una DB inicializada al arrancar.
- **Decisión D-08 — el punto que hay que entender bien**: en la mayoría de los hosts
  gratuitos el filesystem es **efímero**. El contenedor se recrea en cada deploy y en cada
  reinicio: el archivo SQLite **se borra**. La "persistencia en SQLite" del proyecto deja de
  ser persistencia.
  - **PythonAnywhere**: filesystem persistente en el plan gratuito → la DB sobrevive.
  - **Render / Railway**: la DB vuelve a cero en cada deploy → se puede usar igual, pero
    hay que **documentarlo como limitación honesta** (y sirve: demuestra que entendés la
    diferencia entre un archivo local y un volumen persistente).
- **Detalle de workers**: con SQLite, varios workers de gunicorn escribiendo a la vez
  producen `database is locked` (TP-15). Usar **un worker con threads**
  (`--workers 1 --threads 4`), no varios procesos.

### Paso 11.3 — GitHub Pages

- **Qué**: sitio de presentación en `docs/`, activado desde *Settings → Pages →
  Deploy from branch → main → /docs*.
- **Por qué `/docs`**: es la forma más simple: sin GitHub Actions, sin build, cero
  configuración. YAGNI.
- **Ojo**: si Pages sirve desde `/docs`, la página de entrada es `docs/index.html`, no el
  README. Hay que crear ese archivo (es la página de presentación del portfolio).
- **Qué mostrar**: qué hace el sistema, arquitectura, el diagrama de flujo, los endpoints,
  cómo correrlo y el link a la API deployada.

### Paso 11.4 — QA: verificación post-deploy

- **Qué**: *smoke test* contra la URL pública real.
- **Por qué**: el entorno donde corre de verdad es distinto al tuyo (Linux, otra versión de
  Python, otra config, otra base). "Funciona en mi máquina" no prueba nada sobre producción.
- **Cómo**: registro, login, CRUD completo contra la URL pública, con sus códigos HTTP y
  evidencia. Probar también la **primera** request después de un tiempo inactivo (si el host
  duerme el servicio, la primera tarda decenas de segundos: si el cliente tiene timeout
  corto, vas a ver una falla de "servicio caído" que en realidad es *cold start*).

### Paso 11.5 — QA: verificación de no-filtración (público)

- **Qué**: revisar el repo **público** y las respuestas de la API desplegada.
- **Por qué**: el repo ahora es visible para cualquiera; una `SECRET_KEY` publicada permite
  **falsificar tokens válidos** para cualquiera.
- **Chequeo**: la respuesta de la API nunca incluye `password_hash`, `traceback`, rutas
  internas ni la `SECRET_KEY`; el repo no contiene `.env` ni `.db`.

---

## FASE 12 — Respuestas conceptuales

### Paso 12.1 — Redactar las dos respuestas

- **Qué**: (1) por qué se hashea una contraseña; (2) ventajas de SQLite en este proyecto.
- **Cómo hacerlas fuertes**: no contestar en abstracto. Anclá cada afirmación en **tu propio
  código**:
  - *Hashing*: irreversibilidad (por eso el hash no se "desencripta") · el *salt* aleatorio
    (por eso dos hashes de la misma contraseña son distintos, como verifica TP-04) · por qué
    no guardar cifrado reversible (la clave estaría en el servidor y un leak la filtra
    entera) · qué pasa si filtrás la tabla: los atacantes no obtienen contraseñas usables.
  - *SQLite*: cero configuración (viene en la stdlib) · todo en un archivo, sin servidor ·
    transaccional y ACID · ideal para desarrollo, prototipos y baja concurrencia ·
    **qué limitación tiene** (escrituras concurrentes → `database is locked`, y el
    filesystem efímero del hosting, que ya viviste en la Fase 11).

### Paso 12.2 — QA: revisión de consistencia técnica

- **Qué**: verificar que cada afirmación conceptual sea verdadera **y** consistente con lo
  implementado.
- **Por qué**: si en las respuestas decís "usamos bcrypt" y en el código hay
  `werkzeug.security`, el sistema se contradice a sí mismo y eso se nota.

- **DoD final**: las tres secciones de entregables de la consigna (código, documentación,
  conceptuales) + el cliente de consola, todos verificados con evidencia reproducible.

---

# PARTE D — Puntos críticos de testing y casos

## D.1 TPs originales (de la sesión anterior — no se renumera)

| ID | Etapa | Qué se verifica | Riesgo |
|---|---|---|---|
| TP-01 | Router | Ruta existe, método correcto → 405 | Contrato roto |
| TP-02 | Validación `/registro` | Campos, tipos, valores límite → 400 | Datos corruptos |
| TP-03 | DAO/DB | Usuario duplicado → 409 | Duplicados |
| TP-04 | Seguridad | Contraseña nunca en texto plano (inspección real) | Pérdida total de credenciales |
| TP-05 | Respuesta | `password_hash` jamás viaja en el JSON | Fuga de datos |
| TP-06 | Login | Credenciales válidas → 200 + token | No se puede entrar |
| TP-07 | Login | Usuario inexistente y contraseña mala → mismo 401 | Enumeración de usuarios |
| TP-08 | Token | Firma válida; alterado → 401 | Suplantación |
| TP-09 | Token | Expiración respetada → 401 | Sesión eterna |
| TP-10 | Middleware | `/api/tareas` sin token → 401; `/tareas` (HTML) es público | Acceso anónimo |
| TP-11 | Autorización | A no ve/edita/borra la tarea de B → 404 | **IDOR** |
| TP-12 | Validación tareas | Título vacío/largo/tipo erróneo → 400 | Datos basura |
| TP-13 | Flujo CRUD | Crear→Listar→Editar→Borrar | Funcionalidad core |
| TP-14 | DAO | `' OR 1=1 --` no rompe | SQL Injection |
| TP-15 | SQLite | Escrituras concurrentes no corrompen | Pérdida de datos |
| TP-16 | Errores | 500 no filtra stack trace; se loguea server-side | Fuga de info |
| TP-17 | Cliente↔API | Campos y status codes coinciden | Cliente roto |

## D.2 TPs nuevos (de esta revisión)

| ID | Etapa | Qué se verifica | Por qué se agrega |
|---|---|---|---|
| TP-18 | Entrada | Sin `Content-Type` o JSON malformado → 400, sin traceback | R-07 |
| TP-19 | Unicidad | `"Juan"` vs `"juan"` colisionan (`COLLATE NOCASE`) | Regla de negocio no definida |
| TP-20 | DB | `PRAGMA foreign_keys` efectivamente activo | La FK es decorativa sin el PRAGMA |
| TP-21 | Representación | `/tareas` (HTML) es **pública y sin datos**; `/api/tareas` (JSON) exige token en todos sus métodos | Una página de bienvenida no tiene nada que proteger, y un navegador no puede mandar el header de autorización |
| TP-22 | Errores | 404/405/500 responden JSON consistente | Flask devuelve HTML por defecto |
| TP-23 | Encoding | `contraseña` con `ñ` funciona de punta a punta | Bug exclusivo de Windows/consola |
| TP-24 | Borde | Contraseña `"1234"` (el ejemplo de la consigna) **se acepta** | No romper el enunciado |
| TP-25 | Sesión | El "logout" del cliente borra el token local; no hay blacklist | Limitación documentada, no bug oculto |

## D.3 Casos nuevos derivados

| ID | Caso | Técnica | Esperado |
|---|---|---|---|
| TC-REG-07 | Registro sin `Content-Type: application/json` | Entrada inválida | 400 |
| TC-REG-08 | Registro con contraseña `"1234"` | Borde / ejemplo del enunciado | 201 |
| TC-REG-09 | Registro con `"juan"` si ya existe `"Juan"` | Regla de negocio | 409 |
| TC-DB-01 | Crear tarea con `usuario_id` inexistente | Integridad referencial | `IntegrityError` |
| TC-DB-02 | Borrar usuario con tareas | `ON DELETE CASCADE` | 0 tareas huérfanas |
| TC-ERR-01 | Forzar excepción en el DAO | Manejo de errores | 500 JSON, sin traceback, logueado |
| TC-ERR-02 | `GET /api/tareas/999` inexistente | Negativo | 404 JSON |
| TC-ENC-01 | Registro + login con `contraseña` con `ñ` | Encoding E2E | 201 / 200 |

---

# PARTE E — Plan de evidencia

| # | Evidencia | Cómo se produce | Qué demuestra |
|---|---|---|---|
| E-01 | `pytest -v` en verde | Consola | La suite completa pasa |
| E-02 | Reporte de cobertura | `pytest --cov` | Qué código no se ejecuta nunca |
| E-03 | `curl` de registro / login / tareas | Consola, con los status code visibles | El contrato HTTP es el documentado |
| E-04 | Página `/tareas` en el navegador | Navegador, **sin** autenticación | El requisito del HTML se cumple; y se ve el motivo de D-04 revisada: al navegar no viaja el header |
| E-05 | Cliente de consola, ciclo completo | Consola | El E2E funciona de verdad |
| E-06 | Intento de acceso a tarea ajena | `curl` con token de A contra recurso de B | El aislamiento por dueño existe |
| E-07 | Inspección de la tabla `usuarios` | `sqlite3` / DB Browser | La contraseña está hasheada, no en texto plano |
| E-08 | Deploy público respondiendo | Navegador / `curl` sobre la URL pública | Producción funciona |
| E-09 | Diagrama de flujo con los TP marcados | drawio exportado | El análisis de flujo y riesgo |

Cada captura lleva pie de foto con **el comando exacto** y la versión. Sin eso, no es
evidencia.

---

# PARTE F — Riesgos residuales y no-goals

**Riesgos que quedan abiertos y se documentan (no se resuelven):**

| Riesgo | Por qué no se resuelve |
|---|---|
| *Timing attack* en `/login` | Requiere comparación de tiempo constante: desproporcionado para el alcance |
| Sin invalidación de tokens | JWT es stateless; una blacklist es infraestructura fuera de alcance |
| `database is locked` bajo alta concurrencia | Limitación propia de SQLite; se mitiga con 1 worker, no se elimina |
| DB efímera si el host no es persistente | Se resuelve eligiendo el host (D-08) o se documenta |

**No-goals explícitos (D-17)** — fuera de alcance por YAGNI, y se declaran en el README:
CORS, refresh tokens, rate limiting, roles/permisos, paginación, búsqueda, ORM, Docker,
caché, jobs, panel de administración.

Declarar los no-goals no es debilidad: es lo que demuestra que el alcance se decidió a
conciencia y no se recortó por falta de tiempo.

---

# PARTE G — Antes de empezar

1. **D-06: CERRADA** — `GET /tareas` devuelve el HTML de bienvenida y el CRUD JSON vive en
   `/api/tareas`. El HTML es **público y sin datos** (D-04 revisada), así que el contrato de la
   Fase 1.2 tiene que decirlo explícitamente: `/api/tareas` exige token en todos sus métodos.
2. **D-08: CERRADA** — la API se despliega en **PythonAnywhere**, por su filesystem
   persistente: es el único host gratuito evaluado donde el archivo SQLite sobrevive a los
   deploys. Con Render/Railway la persistencia sería ficticia.
3. El resto de la Parte B (D-07, D-09 a D-17) son decisiones técnicas con recomendación
   fundada; si no las discutís, se implementan como están escritas.
4. La ejecución arranca por la **Fase 0.1** y avanza de a una fase, con su commit y su
   evidencia.

> **Cerrado (adelantado a la Fase 0.3).** El `.gitignore` tenía dos defectos: la sintaxis de
> un heredoc de PowerShell como texto literal (primera línea `@'`, última línea
> `'@ | Set-Content ...`) y una regla `.env.*` que **ignoraba `.env.example`**, que sí debe
> versionarse. Ambos se corrigieron en el commit `chore(gitignore)`, junto con la entrada
> `.atl/`. Verificación empírica: `git add --dry-run` acepta `.env.example` y rechaza `.env`.

Nada de la Fase 3 en adelante se escribe antes de cerrar la Fase 1: el esquema y el
contrato son la base de todo lo demás.
