# MarketLink – Frontend (Flask + Jinja + Caddy)

Este repositorio contiene la **capa de presentación de MarketLink**, desarrollada con **Flask**, **HTML5**, **CSS3** y plantillas **Jinja2**.  
La aplicación se ejecuta en un contenedor Docker y, para entornos de producción, puede exponerse a través de **Caddy** como reverse proxy con HTTPS.

---

## 🚀 Ejecución con Docker

- Clonar el repositorio:
  
```bash
git clone <URL-del-repo>
cd marketlink-frontend
```

- Instalar dependencias:
  
```
pip install -r requirements.txt
```

- Ejecutar con Docker

```
docker compose up --build
```

