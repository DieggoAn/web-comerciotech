from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔌 CONEXIÓN USANDO EL USUARIO ADMINISTRADOR RAÍZ REAL
MONGO_URI = "mongodb://admin_root:SecretMongo2026*@comerciotech-nosql-v2:27017/?authSource=admin"
client = MongoClient(MONGO_URI)
db = client["comerciotech_catalogo"]
productos_collection = db["productos"]

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    # 🔍 LEER: Traemos todos los productos desde MongoDB reales
    productos_db = list(productos_collection.find())
    lista_limpia = []
    
    for p in productos_db:
        # Aislamos los datos de manera primitiva y estricta en strings y floats puros
        sku_val = str(p.get("sku") if p.get("sku") is not None else "")
        nombre_val = str(p.get("nombre") if p.get("nombre") is not None else "")
        
        # Nos aseguramos de que el precio sea obligatoriamente un número flotante puro
        try:
            precio_val = float(p.get("precio", 0.0))
        except (TypeError, ValueError):
            precio_val = 0.0

        item = {
            "sku": sku_val,
            "nombre": nombre_val,
            "precio": precio_val
        }
        lista_limpia.append(item)
        
    # Enviamos una copia explícita a la plantilla
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "productos": list(lista_limpia)}
    )

@app.post("/guardar", response_class=RedirectResponse)
async def guardar_producto(
    sku: str = Form(...), 
    nombre: str = Form(...), 
    precio: float = Form(...)
):
    # 💾 ESCRIBIR: Insertamos el nuevo producto directamente en MongoDB
    nuevo_producto = {
        "sku": sku,
        "nombre": nombre,
        "precio": float(precio) # Forzado a float para el jsonSchema estricto de Mongo
    }
    productos_collection.insert_one(nuevo_producto)
    
    return RedirectResponse(url="/", status_code=303)