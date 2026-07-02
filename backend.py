from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates # 👈 ¡CORREGIDO AQUÍ!
from pymongo import MongoClient
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔌 CONEXIÓN REAL A MONGODB (Usando el DNS interno de la red Docker)
MONGO_URI = "mongodb://srv_app_comerciotech:Python1!@comerciotech-nosql:27017/?authSource=admin"
client = MongoClient(MONGO_URI)
db = client["comerciotech_catalogo"]
productos_collection = db["productos"]

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    # 🔍 LEER: Traemos todos los productos desde MongoDB reales
    productos_db = list(productos_collection.find())
    productos = []
    for p in productos_db:
        p["_id"] = str(p["_id"])
        productos.append(p)
        
    return templates.TemplateResponse("index.html", {"request": request, "productos": productos})

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
        "precio": precio
    }
    productos_collection.insert_one(nuevo_producto)
    
    return RedirectResponse(url="/", status_code=303)