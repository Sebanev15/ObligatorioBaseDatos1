# Torneo Interfacultades de Fútbol 5

## Iniciar la aplicación

La forma más sencilla es iniciar Docker Desktop y ejecutar un único comando desde la carpeta del proyecto.

### Paso a paso

1. Instala Docker Desktop y ábrelo. Espera a que indique que Docker está en funcionamiento.
2. Crea tu archivo de configuración local a partir de la plantilla:
   ```powershell
   Copy-Item .env.example .env
   ```
   Esto crea una copia llamada `.env` y conserva `.env.example` en el repositorio. Abre `.env` y reemplaza **todos** los valores `CAMBIAR_...` por contraseñas largas y únicas; para `JWT_SECRET`, usa una cadena aleatoria de al menos 32 caracteres. No compartas ni subas `.env`: contiene secretos y está excluido del repositorio.
3. Abre PowerShell en la carpeta del proyecto y ejecuta:
   ```powershell
   docker compose up --build
   ```
4. Espera a que Docker termine de construir y arrancar los servicios. La primera vez puede tardar varios minutos.
5. Abre la aplicación:
   - **Frontend:** http://localhost:3000/
   - **Documentación de la API:** http://localhost:8000/api/docs

Para apagar los servicios, vuelve a la ventana donde ejecutaste el comando y presiona `Ctrl+C`. Los datos de MySQL se conservan en el volumen de Docker al apagar la aplicación; no uses `docker compose down -v` si quieres conservarlos.

### Problemas frecuentes

- **Docker no está disponible:** abre Docker Desktop, espera a que termine de iniciar y vuelve a ejecutar el comando.
- **Falta `.env`:** créalo copiando `.env.example` y reemplaza los valores de ejemplo antes de iniciar la aplicación.
- **Un puerto ya está ocupado:** libera el puerto `3000` (frontend), `8000` (API) o `3307` (MySQL) y vuelve a iniciar la aplicación.

## Desarrollo del frontend

Para trabajar en el frontend con recarga automática, ejecuta desde PowerShell:

```powershell
docker compose --profile dev up --build
```

En ese modo, abre http://localhost:5173/. La API sigue disponible en http://localhost:8000/api/docs.
