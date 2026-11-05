## Levantar Proyecto

### Docker

`docker compose up --build`

#### Abrir backend

Docs: `http://localhost:8000/api/docs`

#### Abrir frontend

`http://localhost:3000/`


#### Desarrollo con recarga automática (opcional)

`docker compose --profile dev up`

En este modo el frontend se abre en `http://localhost:5173/`. Para el uso normal, alcanza con `docker compose up --build` y abrir `http://localhost:3000/`.