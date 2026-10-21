## Backend: cómo funciona y cómo agregar una entidad nueva

Esta guía está pensada para quien **nunca usó FastAPI**. Si seguís el paso a paso de la sección 5 podés agregar una entidad nueva (equipo, partido, sanción, etc.) copiando un molde, sin tener que entender todo el framework de antemano.

El backend está en `backend/app/`, usa **FastAPI + PyMySQL** y **no usa ORM**: el SQL se escribe a mano.
 
---

### 1. FastAPI en cinco minutos

| Concepto | Qué es | Dónde está en este proyecto |
|---|---|---|
| **Endpoint (ruta)** | Una URL + un método HTTP que ejecuta una función. Ej: `GET /api/jugadores/1234567`. | Funciones con `@router.get(...)`, `@router.post(...)`, etc. |
| **Router** | Agrupa los endpoints de una entidad bajo un prefijo (`/jugadores`). | `routers/<entidad>.py` |
| **Schema** (modelo Pydantic) | Una clase que describe qué datos se esperan y **los valida**. Si no cumplen, FastAPI responde 422 solo. | `schemas/<entidad>.py` |
| **Dependencia** (`Depends`) | Algo que FastAPI calcula antes de ejecutar tu función (por ejemplo, quién es el usuario). | `deps.py` |
| **`response_model`** | La forma de la respuesta. FastAPI descarta lo que no esté declarado y valida lo que devuelve. | Parámetro del decorador |
| **Swagger** | Documentación interactiva generada automáticamente, donde se puede probar cada endpoint. | `http://localhost:8000/api/docs` |

**Cómo sabe FastAPI de dónde sale cada parámetro.** Mira la firma de la función:

```python
@router.patch("/{ci}")                            # {ci} está en la URL
def modificar(ci: int, data: JugadorPatch, user: AdminUser): ...
#             ^^        ^^^^^^^^^^^^^^^^   ^^^^
#   parámetro de ruta   cuerpo JSON        dependencia (no viene del cliente)
```

- Si el nombre aparece en la ruta (`{ci}`), es un **parámetro de ruta**.
- Si el tipo es un modelo Pydantic, es el **cuerpo JSON** de la petición.
- Si es un tipo simple que no está en la ruta (`tipo: str | None = None`), es un **parámetro de query** (`?tipo=docente`).
  Los endpoints se escriben con `def` y no con `async def` porque PyMySQL es bloqueante: FastAPI ejecuta las funciones `def` en un hilo aparte y no frena al resto de las peticiones.

---

### 2. Estructura

```
backend/app/
├── main.py          # crea la app, registra los routers y traduce errores de MySQL a HTTP
├── config.py        # variables de entorno (credenciales de la base, etc.)
├── db.py            # pools de conexión por rol + helpers fetch_all / fetch_one / execute
├── deps.py          # usuario actual y rol  (STUB temporal hasta que esté el login)
├── routers/         # un archivo por entidad: endpoints + SQL
│   ├── jugadores.py     ← entidad plana, ejemplo principal
│   └── complejos.py     ← recurso padre + hijo anidado (canchas, PK compuesta)
└── schemas/         # un archivo por entidad: validación de entrada y salida
    ├── jugador.py
    └── complejo.py
```

Convención de nombres: **routers en plural** (`jugadores.py`), **schemas en singular** (`jugador.py`). Cada carpeta lleva un `__init__.py` (puede estar vacío); sin él Python no la reconoce como paquete y aparece `ImportError: cannot import name ... (unknown location)`.
 
---

### 3. El camino de una petición

```
Cliente (React / Swagger / curl)
   │   PATCH /api/jugadores/1234567     {"tipo": "docente"}
   ▼
main.py        el prefijo /api viene de main.py, el /jugadores del router
   ▼
Validación     schemas/jugador.py: ¿la CI está en rango?, ¿el tipo es uno de la lista?...
   │                                                              └─ si falla ──► 422
   ▼
deps.py        ¿quién es y qué rol tiene?  (administrador / planillero)
   │                                                              └─ sin permiso ──► 403
   ▼
db.py          get_connection(user.rol): toma una conexión del pool del usuario de MySQL
   │           que corresponde al rol (usuario_admin o usuario_planillero)
   ▼
SQL            UPDATE jugador SET tipo = %s WHERE ci = %s      (valores siempre parametrizados)
   ▼
MySQL          aplica constraints (UNIQUE, FK, CHECK) y triggers (reglas del torneo)
   │                                       └─ si rechaza ──► main.py lo traduce a 409 / 422 / 403
   ▼
Commit         automático al salir del bloque `with get_connection(...)`
   ▼
Respuesta      response_model da forma al JSON  ──►  200
```
 
---

### 4. Las piezas

#### 4.1 `db.py`: hablar con MySQL

```python
with get_connection(user.rol) as conn:            # abre conexión; commit al salir bien, rollback si hay error
    fila   = fetch_one(conn, "SELECT ... WHERE ci = %s", (ci,))   # un dict, o None
    filas  = fetch_all(conn, "SELECT ... ", ())                    # lista de dicts
    res    = execute(conn, "INSERT/UPDATE/DELETE ...", (valores,)) # res.rowcount, res.lastrowid
```

- **Un solo `with` = una sola transacción.** Si hacés varias sentencias dentro del mismo bloque y una falla, se deshace todo. Es lo que necesitás, por ejemplo, para crear un equipo, inscribir su plantel y asignar el capitán (el orden de tu esquema es: insertar equipo con `ci_capitan` NULL, insertar jugadores, y recién ahí el `UPDATE` del capitán):
```python
  with get_connection(user.rol) as conn:
      res = execute(conn, "INSERT INTO equipo (nombre, id_torneo, id_facultad) VALUES (%s, %s, %s)", (...))
      id_equipo = res.lastrowid
      for j in data.jugadores:
          execute(conn, "INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) VALUES (%s, %s, %s, %s)", (...))
      execute(conn, "UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s", (data.ci_capitan, id_equipo))
  # si algo falla en el medio, no queda nada a medias
```
- `res.lastrowid` es el `AUTO_INCREMENT` que acaba de generar MySQL (para tablas con `id_...`).
- `res.rowcount` es la cantidad de filas afectadas. **No lo uses para detectar 404 en un `UPDATE`**: MySQL devuelve 0 si el valor nuevo es igual al viejo. Para eso, volvé a leer la fila (como hacen los PATCH de los ejemplos). Sí sirve para el `DELETE`.
- Hay un pool de conexiones **por rol**, cada uno con su usuario de MySQL: así los permisos se aplican también en la base de datos, no solo en Python.
#### 4.2 `deps.py`: usuario y rol

Expone tres atajos para usar como tipo de un parámetro:

| Atajo | Quién puede |
|---|---|
| `AnyUser` | cualquier usuario autenticado (para lecturas) |
| `AdminUser` | solo administradores (altas, bajas y modificaciones) |
| `PlanilleroOrAdmin` | administradores y planilleros (planillas, goles y tarjetas) |

Todos devuelven un objeto con `.rol`, y ese rol es el que se pasa a `get_connection(user.rol)`.

> ⚠️ **Hoy `deps.py` es un stub**: todos los requests corren como administrador y no hay autenticación. El login aun no esta implementado. **solo reemplaza este archivo**; los routers no cambian mientras se respete el contrato (los tres atajos, que devuelven un objeto con `rol`). No dejar el stub en la entrega.

#### 4.3 `schemas/`: validar datos

Por cada entidad se definen tres clases:

| Clase | Para qué | Particularidad |
|---|---|---|
| `XCreate` | cuerpo del `POST` | todos los campos obligatorios |
| `XPatch` | cuerpo del `PATCH` | todos opcionales (`... \| None = None`); **no incluye la clave primaria** |
| `XOut` | forma de la respuesta | puede incluir datos del `JOIN` (ej. el nombre de la facultad) |

Herramientas que se usan:

- `Field(min_length=1, max_length=100)`, `Field(ge=1, le=99)`, `Field(gt=0)`, `Field(pattern=r"...")`: largo, rango o formato.
- `Literal["grado", "posgrado", ...]` para los enums. **Los valores tienen que ser idénticos a los del `CHECK` de la base** (ojo: `'en curso'` del torneo lleva espacio, y el motivo de sanción es `'acumulacion de amarillas'`).
- `model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")`: recorta espacios y **rechaza campos que no estén declarados**. Este `extra="forbid"` es importante para la seguridad del PATCH (ver reglas de oro).
- Validaciones propias con `@field_validator` (ver la fecha de nacimiento en `schemas/jugador.py`).
  La validación se repite en las tres capas que pide el enunciado: frontend, Pydantic y la base (`CHECK`, `UNIQUE`, FK, triggers).

#### 4.4 Cómo llegan los errores de MySQL al cliente

`main.py` tiene un manejador que traduce los errores de la base a respuestas HTTP con un mensaje legible. No hace falta hacer `try/except` en los routers.

| Error de MySQL | Respuesta | Cuándo ocurre |
|---|---|---|
| 1062 | **409** | Duplicado (`UNIQUE` / `PRIMARY KEY`) |
| 1451 | **409** | Se borra algo de lo que otros registros dependen (FK) |
| 1452 | **422** | Referencia a algo que no existe (FK al insertar) |
| 1048 | **422** | Falta un dato `NOT NULL` |
| 3819 | **422** | No cumple un `CHECK` |
| **1644** | **422** | **Un trigger rechazó la operación** (`SIGNAL`): el mensaje del trigger llega tal cual al cliente |
| 1142 | **403** | El usuario de MySQL del rol no tiene permiso (falta un `GRANT`) |
| 2003, 1045, ... | **503** | La base no está disponible o las credenciales no coinciden |
| otro | **500** | Error no previsto (mirar `docker compose logs backend`) |
 
---

### 5. Paso a paso: agregar una entidad nueva

1. **Mirá la tabla** en `db/init/01_schema.sql`: columnas, clave primaria, claves foráneas, enums y `CHECK`.
2. **Creá `schemas/<entidad>.py`** con `Create`, `Patch` y `Out` (copiá el ejemplo de la sección 6 o `schemas/jugador.py`).
3. **Creá `routers/<entidad>s.py`** copiando el molde de la sección 6. Cambiá la tabla, las columnas y los mensajes.
4. **Registralo en `main.py`**: sumá el módulo al `import` y una línea `api.include_router(<entidad>s.router)`.
5. **Reconstruí y probá** (ver sección 8). La entidad aparece sola en `http://localhost:8000/api/docs`.
6. **Si tiene reglas de negocio**, implementalas como trigger en la base (sección 7) y probá que el mensaje llegue bien.
7. **Si el planillero tiene que escribir en esa tabla**, agregá el `GRANT` correspondiente en `db/init/02_users.sh`. Sin eso, MySQL rechaza la operación con un 403.
8. Probá con `docker compose down -v && docker compose up --build` desde cero, y hacé el commit.
#### Qué usar según el caso

| Caso | Dónde mirar |
|---|---|
| Entidad simple con PK autoincremental | el molde de la sección 6 |
| PK que no es autoincremental (ej. la CI) | `routers/jugadores.py` |
| Filtros, búsqueda y paginación en el listado | `listar` de `routers/jugadores.py` |
| Recurso hijo con PK compuesta y rutas anidadas (`/complejos/{id}/canchas`) | `routers/complejos.py`; sirve de molde para el plantel de un equipo |
| Varias tablas en una sola operación | transacción de la sección 4.1 |
| Reportes | sección 6.2 |
 
---

### 6. Moldes para copiar

#### 6.1 Entidad completa mínima: `facultad`

`schemas/facultad.py`

```python
from pydantic import BaseModel, ConfigDict, Field
 
 
class FacultadCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
 
    nombre: str = Field(min_length=2, max_length=150)
 
 
class FacultadPatch(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
 
    nombre: str | None = Field(default=None, min_length=2, max_length=150)
 
 
class FacultadOut(BaseModel):
    id_facultad: int
    nombre: str
```

`routers/facultades.py`

```python
from typing import Annotated
 
from fastapi import APIRouter, HTTPException, Path, status
 
from ..db import execute, fetch_all, fetch_one, get_connection
from ..deps import AdminUser, AnyUser
from ..schemas.facultad import FacultadCreate, FacultadOut, FacultadPatch
 
router = APIRouter(prefix="/facultades", tags=["facultades"])
 
IdFacultad = Annotated[int, Path(gt=0)]
 
_SELECT = "SELECT id_facultad, nombre FROM facultad"
 
 
def _obtener(conn, id_facultad: int) -> dict | None:
    return fetch_one(conn, _SELECT + " WHERE id_facultad = %s", (id_facultad,))
 
 
def _no_encontrada() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Facultad no encontrada")
 
 
@router.get("", response_model=list[FacultadOut])
def listar(user: AnyUser):
    with get_connection(user.rol) as conn:
        return fetch_all(conn, _SELECT + " ORDER BY nombre")
 
 
@router.get("/{id_facultad}", response_model=FacultadOut)
def obtener(id_facultad: IdFacultad, user: AnyUser):
    with get_connection(user.rol) as conn:
        fila = _obtener(conn, id_facultad)
    if fila is None:
        raise _no_encontrada()
    return fila
 
 
@router.post("", response_model=FacultadOut, status_code=status.HTTP_201_CREATED)
def crear(data: FacultadCreate, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(conn, "INSERT INTO facultad (nombre) VALUES (%s)", (data.nombre,))
        return _obtener(conn, res.lastrowid)
 
 
@router.patch("/{id_facultad}", response_model=FacultadOut)
def modificar(id_facultad: IdFacultad, data: FacultadPatch, user: AdminUser):
    cambios = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if not cambios:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se envió ningún campo para modificar")
    sets = ", ".join(f"{columna} = %s" for columna in cambios)
    with get_connection(user.rol) as conn:
        execute(conn, f"UPDATE facultad SET {sets} WHERE id_facultad = %s", (*cambios.values(), id_facultad))
        fila = _obtener(conn, id_facultad)
    if fila is None:
        raise _no_encontrada()
    return fila
 
 
@router.delete("/{id_facultad}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(id_facultad: IdFacultad, user: AdminUser):
    with get_connection(user.rol) as conn:
        res = execute(conn, "DELETE FROM facultad WHERE id_facultad = %s", (id_facultad,))
    if res.rowcount == 0:
        raise _no_encontrada()
```

Y en `main.py`:

```python
from .routers import complejos, facultades, jugadores   # sumar el módulo nuevo
 
api.include_router(facultades.router)                    # sumar esta línea
```

Los cinco endpoints siguen siempre el mismo patrón:

| Operación | Método y URL | Rol | Éxito | Errores típicos |
|---|---|---|---|---|
| Listar | `GET /facultades` | `AnyUser` | 200 | |
| Obtener uno | `GET /facultades/{id}` | `AnyUser` | 200 | 404 |
| Crear | `POST /facultades` | `AdminUser` | **201** | 409 duplicado, 422 datos inválidos o FK |
| Modificar | `PATCH /facultades/{id}` | `AdminUser` | 200 | 400 sin campos, 404, 422 |
| Eliminar | `DELETE /facultades/{id}` | `AdminUser` | **204** (sin cuerpo) | 404, 409 si tiene dependientes |

#### 6.2 Reportes

Un reporte es un `GET` que ejecuta un `SELECT` con `JOIN` / `GROUP BY` y devuelve una lista. Se define un `response_model` propio para la forma de cada fila.

`schemas/reporte.py`

```python
from pydantic import BaseModel
 
 
class JugadoresPorFacultadOut(BaseModel):
    facultad: str
    tipo: str
    cantidad: int
```

`routers/reportes.py`

```python
from fastapi import APIRouter
 
from ..db import fetch_all, get_connection
from ..deps import AnyUser
from ..schemas.reporte import JugadoresPorFacultadOut
 
router = APIRouter(prefix="/reportes", tags=["reportes"])
 
 
@router.get("/jugadores-por-facultad", response_model=list[JugadoresPorFacultadOut])
def jugadores_por_facultad(user: AnyUser):
    sql = """
        SELECT f.nombre AS facultad, j.tipo, COUNT(*) AS cantidad
        FROM jugador j
        JOIN facultad f ON f.id_facultad = j.id_facultad
        GROUP BY f.nombre, j.tipo
        ORDER BY f.nombre, j.tipo
    """
    with get_connection(user.rol) as conn:
        return fetch_all(conn, sql)
```

Si un reporte necesita un filtro (por ejemplo el torneo), se recibe como parámetro de ruta o de query y se pasa **siempre con `%s`**, nunca dentro de un f-string: `fetch_all(conn, sql, (id_torneo,))`. Los alias del `SELECT` (`AS facultad`) tienen que coincidir con los nombres de los campos del `response_model`.
 
---

### 7. Reglas del torneo: se implementan en la base

Reglas como "plantel de máximo 10 jugadores", "un equipo juega una sola vez por fecha" o "no se puede anotar a un suspendido" se implementan como **triggers** en MySQL, no en Python. Así valen sin importar desde dónde se escriba en la base. El backend solo se limita a mostrar el mensaje al usuario.

Los triggers van en `db/init/04_triggers.sql`, **después** del script de datos de prueba. Si estuvieran antes, el seed los dispararía mientras inserta jugador por jugador y fallaría.

```sql
DELIMITER //
CREATE TRIGGER trg_plantel_maximo
BEFORE INSERT ON equipo_jugador_torneo
FOR EACH ROW
BEGIN
  IF (SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_equipo = NEW.id_equipo) >= 10 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El plantel ya tiene 10 jugadores';
  END IF;
END//
DELIMITER ;
```

Cuando el trigger ejecuta `SIGNAL`, MySQL devuelve el error 1644 y `main.py` lo transforma en una respuesta **422** con el `MESSAGE_TEXT` como `detail`: `{"detail": "El plantel ya tiene 10 jugadores"}`. El frontend solo tiene que mostrar ese texto. Escribí los mensajes pensando en que los lee una persona.

Nota: reglas de tipo "mínimo" (por ejemplo, "al menos 5 jugadores") no se pueden validar al insertar, porque el plantel se arma de a uno. Se validan en el momento que importa: al programar un partido.
 
---

### 8. Cómo probar

**Swagger** (lo más cómodo): abrí `http://localhost:8000/api/docs`, elegí un endpoint, **Try it out**, completá y **Execute**. Muestra la respuesta, el código HTTP y el `curl` equivalente.

**curl:**

```bash
curl "http://localhost:8000/api/jugadores?tipo=docente&limit=5"
 
curl -X POST http://localhost:8000/api/jugadores \
  -H "Content-Type: application/json" \
  -d '{"ci": 1234567, "nombre": "Ana", "apellido": "Paz", "email": "ana@correo.edu.uy",
       "fecha_nacimiento": "2000-05-01", "id_facultad": 1, "tipo": "grado"}'
 
curl -X PATCH http://localhost:8000/api/jugadores/1234567 \
  -H "Content-Type: application/json" -d '{"tipo": "posgrado"}'
 
curl -X DELETE http://localhost:8000/api/jugadores/1234567
```

**Chequeos útiles:** `GET /api/health` (el backend está vivo) y `GET /api/health/db` (llega a MySQL con sus credenciales).

**Después de cambiar código del backend** hay que reconstruir la imagen, porque el código se copia dentro de ella:

```bash
docker compose up --build -d backend
docker compose logs -f backend      # ver errores y la salida de uvicorn
```

**Modo desarrollo con recarga automática** (no hace falta reconstruir en cada cambio). Creá `docker-compose.dev.yml`:

```yaml
services:
  backend:
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    volumes:
      - ./backend/app:/app/app:z
```

y levantá con `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`.
 
---

### 9. Reglas de oro

1. **Nunca armes SQL concatenando valores del usuario.** Los valores van siempre como parámetros (`%s`) y se pasan en la tupla:
```python
   execute(conn, "SELECT ... WHERE ci = %s", (ci,))          # ✅
   execute(conn, f"SELECT ... WHERE ci = {ci}")               # ❌ inyección SQL
```
Los únicos f-strings permitidos son los que arman **nombres de columna** a partir de campos de un modelo Pydantic con `extra="forbid"` (el `SET` del PATCH). Nunca a partir del JSON crudo. Los parámetros `%s` sirven para valores, **no para nombres de columna ni `ORDER BY`**: si agregás un orden dinámico, validalo contra una lista fija.
2. **Usá `get_connection(user.rol)`**, nunca una conexión con un usuario fijo. El rol decide qué usuario de MySQL se usa.
3. **En el PATCH filtrá con `is not None`, no con `if v`.** Si no, `techada = False` o un `0` se descartan como si no se hubieran enviado.
4. **La clave primaria no se modifica en el PATCH**: no la incluyas en el schema `Patch`.
5. **No hagas `try/except` de errores de MySQL en los routers**: ya los maneja `main.py`.
6. **Escrituras con `AdminUser`** (o `PlanilleroOrAdmin` para planillas, goles y tarjetas); lecturas con `AnyUser`.
7. **Los valores de los `Literal` tienen que ser idénticos a los de la base**, sin tildes ni variaciones.
8. **No devuelvas datos sensibles** (ej. la contraseña del login): el `response_model` solo debe declarar lo que se puede mostrar.
9. **Si una operación toca varias tablas, hacela dentro de un único `with get_connection(...)`**, para que sea una sola transacción.