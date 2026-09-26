# 🎬 LAB 05 — Catálogo de Películas con Panel de Administración en Django

Laboratorio práctico de **Aplicaciones Empresariales** consistente en construir una
aplicación web de catálogo de películas llamada `movies`, con un panel de administración
avanzado, control de acceso por permisos y un sitio público de consulta.

---

## 📖 ¿De qué trata este proyecto?

Es una pequeña aplicación web donde se registran películas, sus géneros, las personas que
participan en ellas (actores, directores) y las valoraciones que reciben los usuarios.

La idea es tener **dos mundos separados dentro de la misma aplicación**:

- **El panel de administración** (`/admin/`), donde el equipo interno carga y corrige
  información. Es la "oficina" del catálogo.
- **El sitio público** (la portada), donde cualquier visitante consulta películas y recibe
  recomendaciones. No necesita crear ninguna cuenta.

Esto refleja algo muy común en las empresas reales: la información se gestiona con
cuidado por unos pocos, pero se consulta libremente por millones.

---

## 🎯 Requerimientos funcionales

### Módulo 1 — Catálogo de películas

1. Registrar películas con **título, año de estreno, póster (imagen) y sinopsis**.
2. Cada película debe quedar **clasificada por uno o varios géneros**.
3. Registrar **actores, directores y otros participantes** de cada película.
4. Cada película debe tener **votaciones con puntuación de 1 a 5**, un comentario y su fecha.
5. El sistema debe **guardar automáticamente** cuándo se creó y cuándo se modificó cada
   registro, de forma que el usuario no pueda alterarlo.
6. La información debe estar **buscable y ordenable** por título, año y género.

### Módulo 2 — Panel de administración

7. El panel debe permitir **gestionar los cuatro elementos** del catálogo (géneros,
   personas, películas y reseñas) desde una misma pantalla.
8. La lista de películas debe mostrar **información útil de un vistazo**: póster, título,
   año, géneros, puntuación media y cantidad de valoraciones.
9. Debe poder **filtrar** la lista por género, por año y por fecha, y **buscar** por
   título o por nombre de persona.
10. Al abrir una película, las **valoraciones y el reparto deben poder editarse en la
    misma pantalla**, sin tener que salir y buscar en otra parte.
11. Las fechas de creación y modificación deben mostrarse **solo como lectura**.

### Módulo 3 — Seguridad y permisos

12. Debe existir un usuario **administrador** con acceso total.
13. Debe existir un perfil de **editor**, que puede crear y modificar películas
    pero **no puede borrarlas**.
14. El sistema debe **impedir el borrado** al editor, tanto desde la pantalla de
    eliminación como desde el borrado masivo.
15. El editor **no debe poder** administrar géneros, personas ni reseñas.

### Módulo 4 — Sitio público

16. Cualquier visitante, **sin iniciar sesión**, debe poder ver el catálogo completo.
17. Debe poder **filtrar por género** y **buscar por título o sinopsis**.
18. Cada película debe tener su **ficha**: póster, sinopsis, reparto y valoraciones.
19. El sitio debe ofrecer una sección de **recomendaciones**, mostrando **la película
    mejor valorada de cada género** y un ranking general.

---

## ⭐ ¿Por qué es importante utilizar `ModelAdmin`?

Django permite registrar un modelo en el panel de administración con una sola línea:

```python
admin.site.register(Movie)
```

Esto funciona, pero entrega una pantalla **genérica y básica**: solo aparecen el título
y el año, no hay buscador, no hay filtros, y buscar algo obliga a recorrer la lista a
mano. Además, las valoraciones de una película no se pueden editar desde su propia ficha,
sino que hay que buscarlas en otra pantalla.

`ModelAdmin` es la clase que permite **personalizar ese panel**. Al escribir una clase
propia se logra lo siguiente:

| Con `register` a secas | Con `ModelAdmin` |
|---|---|
| Solo título y año en la tabla | Póster, título, año, géneros, nota media y número de valoraciones |
| Sin buscador | Búsqueda por título, sinopsis y nombres de actores |
| Sin filtros | Filtros por género, año y rango de fechas |
| Datos relacionados en otra pantalla | Valoraciones y reparto editables dentro de la ficha |
| Fechas editables a mano | Fechas bloqueadas en solo lectura |

Lo más importante es que **`ModelAdmin` también respeta los permisos automáticamente**.
Al usar clases, Django sabe qué puede ver y hacer cada usuario: si al editor no se le da
el permiso de borrar, la pantalla de borrado simplemente no existe para él y el botón de
borrado masivo desaparece de la lista. Esa protección viene gratis por usar el panel de
Django, sin escribir una sola línea de validación propia.

En resumen: `ModelAdmin` convierte un panel genérico en una **herramienta de trabajo
real**, donde lo que se ve depende de quién lo está mirando y de qué permisos tiene.

---

## ✅ Tres conclusiones formales

**Primera.** El uso de clases `ModelAdmin` transforma el panel de administración de
Django de una herramienta genérica y difícil de usar en un sistema de trabajo
verdaderamente operativo. Al definir columnas, filtros, búsquedas y bloques de
edición en línea, el usuario deja de recorrer listas manualmente y pasa a localizar
y corregir información de forma inmediata, lo que reduce de forma notable el tiempo
y los errores de las tareas de mantenimiento del catálogo.

**Segunda.** La seguridad de una aplicación no debe depender de ocultar botones en la
interfaz, sino de permisos evaluados en el servidor. En este laboratorio se demostró
que el sistema de permisos de Django opera de forma automática y coherente: el perfil
editor puede crear y modificar películas, pero el acceso a la eliminación y a los demás
módulos queda bloqueado, mientras que las restricciones se aplican de manera uniforme
tanto en las pantallas del panel como en los bloques de edición en línea. Esta
arquitectura garantiza que la protección se mantenga incluso si un usuario intenta
acceder directamente a una dirección no autorizada.

**Tercera.** La separación entre la lógica de administración y la de consulta pública
resulta ser una decisión de diseño beneficiosa para ambos tipos de usuario. El panel
interno, restringido por permisos, permite mantener la información organizada y
auditable, mientras que el sitio público ofrece recomendaciones calculadas a partir de
las valoraciones sin exponer datos sensibles ni exigir autenticación. Esta
combinación de acceso controlado y consulta abierta es un patrón replicable en
aplicaciones empresariales reales donde la información debe estar disponible para
muchos y editable solo para unos pocos.

---

## 🚀 Cómo ejecutarlo

```bash
# 1. Instalar las dependencias
pip install Django Pillow

# 2. Aplicar las migraciones
python manage.py migrate

# 3. Cargar datos de ejemplo (4 géneros, 10 películas, 10 valoraciones)
python manage.py seed_movies

# 4. Crear el usuario administrador
python manage.py createsuperuser

# 5. Crear el grupo "Editores" y su usuario de prueba
python manage.py create_editors_group

# 6. Levantar el servidor
python manage.py runserver
```

### Direcciones web

| Dirección | Descripción | Acceso |
|---|---|---|
| `/` | Catálogo de películas | Público |
| `/peliculas/` | Catálogo con filtros y búsqueda | Público |
| `/peliculas/<id>/` | Ficha de una película | Público |
| `/recomendaciones/` | Mejor valorada por género | Público |
| `/admin/` | Panel de administración | Con usuario |

### Usuarios de prueba

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador — acceso total |
| `editor1` | `editor123` | Editor — crea y edita, **no borra** |

---

## 📁 Estructura del proyecto

```
LAB05_V2/
├── manage.py
├── movies/
│   ├── models.py          # Géneros, personas, películas y reseñas
│   ├── admin.py           # Panel de administración personalizado
│   ├── views.py           # Catálogo, fichas y recomendaciones
│   ├── urls.py            # Direcciones del sitio público
│   ├── tests.py           # Pruebas automáticas
│   ├── templates/movies/  # Plantillas HTML del sitio público
│   └── management/commands/
│       ├── seed_movies.py           # Carga de datos de ejemplo
│       └── create_editors_group.py  # Grupo y usuario de prueba
└── movies_project/        # Configuración general del proyecto
```

---

## 🧪 Pruebas

El proyecto incluye **27 pruebas automáticas** que verifican el comportamiento esperado:

```bash
python manage.py test movies
```

Cubren el funcionamiento de los modelos, el respeto de los permisos por parte del
editor (confirmando que el borrado queda bloqueado) y el correcto funcionamiento de
las páginas públicas con sus filtros y recomendaciones.

---

## 👥 Autor

Proyecto de laboratorio académico — Aplicaciones Empresariales
