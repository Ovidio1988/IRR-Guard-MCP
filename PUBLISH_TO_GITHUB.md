# Publicación recomendada en GitHub

Nombre sugerido del repositorio: **IRR-Guard-MCP**

## 1. Crear repositorio público vacío

En GitHub, crear `IRR-Guard-MCP` como **Public**, sin inicializar README/LICENSE (ya están incluidos).

## 2. Publicar el repositorio local

Desde esta carpeta:

```bash
git remote add origin https://github.com/<TU_USUARIO>/IRR-Guard-MCP.git
git push -u origin main
git push origin v0.1.0
```

## 3. GitHub Pages

El repositorio incluye `.github/workflows/pages.yml`. En `Settings → Pages`, seleccionar **GitHub Actions** si GitHub no lo habilita automáticamente.

La URL quedará normalmente como:

```text
https://<TU_USUARIO>.github.io/IRR-Guard-MCP/
```

## 4. Release v0.1.0

Crear una Release desde el tag `v0.1.0`, usando `RELEASE_NOTES_v0.1.0.md`. Se puede adjuntar también el ZIP distribuible.

## 5. QR para la charla

Recomendación: apuntar el QR a **GitHub Pages**, porque es más presentable que el árbol de archivos y desde allí se puede acceder al repositorio y descargar el ZIP.

```bash
python scripts/make_qr.py https://<TU_USUARIO>.github.io/IRR-Guard-MCP/ -o IRR_Guard_QR.png
```
