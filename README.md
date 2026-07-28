# El Impostor - Game Show Management System

Sistema interactivo de gestión de juego de trivia en tiempo real para producción de televisión/broadcast (Paramount / Telefe).

---

## 🏗 Arquitectura del Proyecto

El proyecto está organizado en una arquitectura monorepo de dos capas principales:

```
el_impostor/
├── backend/            # Django 5.2 + DRF + Django Channels (WebSockets) + Redis + PostgreSQL + Nginx
├── frontend/           # React 18 + TypeScript + Vite + TailwindCSS v4 + HeroUI + Framer Motion
└── README.md
```

---

## 🚀 Backend (`/backend`)

### Tecnologías
- **Python**: 3.13 / Django 5.2
- **API REST**: Django REST Framework (DRF)
- **Tiempo Real (WebSockets)**: Django Channels 4.1.0, ASGI (`Daphne` / `Uvicorn`)
- **Mensajería / Channel Layer**: Redis (`channels-redis`)
- **Base de Datos**: PostgreSQL
- **Servidor Web / Reverse Proxy**: Nginx + Gunicorn

### Modelos Principales ([models.py](api/models.py))
- **`QuestionGroup`**: Grupos/categorías de preguntas con orden configurable.
- **`Question`**: Pregunta individual vinculada a un grupo (dificultad: fácil/media/alta, texto, orden).
- **`Alternative`**: Opciones de respuesta para una pregunta (texto, imagen opcional, flag `is_correct`, orden).
- **`Player`**: Concursantes/participantes (`name`, `description`, estado `active`/`inactive`).
- **`GameSession`**: Sesión global del juego. Define si la sesión está al aire (`is_active`) y el turno activo (`current_player_session`).
- **`PlayerSession`**: Turno individual de un jugador en la sesión de juego.
  - Límite de tiempo: 30s, 60s, 180s, 300s.
  - Estado del cronómetro: `stopped`, `running`, `paused`.
  - Control de tiempo acumulado y última hora de inicio.
  - Índice de la pregunta actual (`current_question_index`).
- **`PlayerQuestionAnswer`**: Registro del estado de cada pregunta por jugador (`pending`, `correct`, `incorrect`, `postponed`), alternativa seleccionada y hora de respuesta.

### WebSockets ([consumers.py](api/consumers.py))
Canal global WebSocket en el endpoint `ws://<host>/ws/game/` (grupo `"game"`):
- `get_state`: Solicita la emisión del estado completo del juego.
- `set_active_player_session`: Establece qué jugador se muestra en pantalla.
- `control_timer`: Comandos del cronómetro (`play`, `pause`, `reset`).
- `submit_answer`: Registra la respuesta del jugador. Pausa el timer automáticamente en respuesta incorrecta o fin de ronda y avanza a la siguiente pregunta.
- `postpone_question`: Marca la pregunta como postergada y avanza.
- `set_current_question`: Salta manualmente a una pregunta por orden.
- `reset_game_session`: Reinicia los temporizadores y respuestas de la sesión de juego.

---

## 🎨 Frontend (`/frontend`)

### Tecnologías
- **React 18** con **TypeScript**
- **Vite** (Dev Server & Bundler)
- **TailwindCSS v4** + **HeroUI** + **Framer Motion**
- **Zustand** & **React Context API** (`GameWebSocketContext.tsx`)

### Vistas Principales (`frontend/src/pages/`)
1. **Consola del Operador** ([operator_remote.tsx](../frontend/src/pages/operator_remote.tsx)):
   - Control en tiempo real de temporizadores, selección de jugador activo, avance/retroceso de preguntas y validación de respuestas (`correcta`, `incorrecta`, `postergar`).
2. **Pantalla de Emisión / TV** ([tv_display.tsx](../frontend/src/pages/tv_display.tsx)):
   - Gráficos en pantalla para emisión en vivo (pregunta activa, alternativas, cronómetro animado y contador de aciertos/errores).
3. **Banco de Preguntas** ([question_groups.tsx](../frontend/src/pages/question_groups.tsx) / [question_detail.tsx](../frontend/src/pages/question_detail.tsx)):
   - Administración CRUD y reordenamiento drag-and-drop de grupos de preguntas y sus alternativas.
4. **Gestión de Jugadores** ([players.tsx](../frontend/src/pages/players.tsx)):
   - Alta, modificación y reordenamiento de concursantes.

---

## ⚙️ Instrucciones de Instalación y Despliegue en Producción

Siga estos pasos para instalar y desplegar el sistema en un servidor de producción:

### 1. Requisitos Previos
Instalar Docker y Docker Compose en el servidor.

### 2. Crear Carpeta para Almacenamiento de Imágenes (Media)
```bash
mkdir -p /opt/el_impostor/media
sudo chown -R 33:33 /opt/el_impostor/media
```

### 3. Configurar la Dirección IP del Servidor
Editar la variable `SERVER_IP` en el archivo `.env`:
```env
SERVER_IP="SU_IP_DE_SERVIDOR"
```

### 4. Compilar y Levantar Contenedores
```bash
cd backend
./deploy.sh up
```

### 5. Verificar Estado de los Contenedores
```bash
docker ps
```

### 6. Reiniciar Servicios (Si Requiere Sincronización)
```bash
./deploy.sh down
./deploy.sh up
```

### 7. Crear Estructura de Base de Datos (Migraciones)
```bash
docker exec -it server-backend python manage.py migrate
```

### 8. (Opcional) Cargar Base de Datos de Prueba
Para poblar la base de datos con 3 jugadores, 3 grupos de preguntas (30 preguntas c/u) y alternativas con imágenes:
```bash
docker exec -it server-backend python manage.py create_testing_db
```

### 9. Acceso en el Navegador
Acceder en el navegador web a la dirección del servidor:
`http://[IP_ADDRESS]`

### 10. Comandos Útiles de Reinicio
```bash
# Reiniciar servidor web (Nginx)
./deploy.sh nginx

# Reiniciar backend (Django/Daphne)
./deploy.sh backend

# Detener todos los servicios
./deploy.sh down
```

---

## 📌 Guía de Convenciones de Código
- **Estilo de variables y funciones**: Usar `snake_case` (ejemplo: `format_number_fun()`, `user_name`).
- **Simplicidad**: Código mínimo, legible y enfocado en la funcionalidad sin abstracciones innecesarias.
