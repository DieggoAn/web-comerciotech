from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os

app = FastAPI(title="ComercioTech API - Catálogo Simulado")

# 1. Estructura de datos que se espera recibir (Esquema equivalente a tu BSON)
class Producto(BaseModel):
    sku: str
    nombre: str
    precio: float
    stock: int
    categoria: str
    marca: str

# 2. Base de datos simulada en memoria RAM
CATALOGO_SIMULADO = [
    {
        "sku": "PROD-001",
        "nombre": "Audífonos Bluetooth Pro X1",
        "precio": 49990.0,
        "stock": 150,
        "categoria": "Electrónica",
        "marca": "ComercioTech"
    },
    {
        "sku": "PROD-002",
        "nombre": "Teclado Mecánico RGB",
        "precio": 35000.0,
        "stock": 45,
        "categoria": "Accesorios",
        "marca": "ComercioTech"
    }
]

# ==================== RUTAS DEL CRUD (API) ====================

# LEER TODOS (Read)
@app.get("/api/productos", response_model=List[Producto])
def obtener_productos():
    return CATALOGO_SIMULADO

# CREAR UNO (Create)
@app.post("/api/productos", status_code=201)
def crear_producto(producto: Producto):
    # Validar si el SKU ya existe para evitar duplicados
    for p in CATALOGO_SIMULADO:
        if p["sku"] == producto.sku:
            raise HTTPException(status_code=400, detail="El SKU ya existe en el catálogo.")
    
    nuevo_producto = producto.dict()
    CATALOGO_SIMULADO.append(nuevo_producto)
    return {"message": "Producto creado con éxito", "producto": nuevo_producto}

# ELIMINAR UNO (Delete)
@app.delete("/api/productos/{sku}")
def eliminar_producto(sku: str):
    for indice, p in enumerate(CATALOGO_SIMULADO):
        if p["sku"] == sku:
            eliminado = CATALOGO_SIMULADO.pop(indice)
            return {"message": "Producto eliminado con éxito", "producto": eliminado}
    raise HTTPException(status_code=404, detail="Producto no encontrado")


# ==================== RUTA PARA SERVIR LA PÁGINA WEB ====================

@app.get("/", response_class=HTMLResponse)
def index():
    # Busca el archivo index.html dentro de la carpeta templates
    ruta_html = os.path.join("templates", "index.html")
    if os.path.exists(ruta_html):
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            return archivo.read()
    return "<h3>Error: No se encontró el archivo templates/index.html</h3>"

# Comando para ejecutar de forma local:
# uvicorn backend:app --reload --port 8080