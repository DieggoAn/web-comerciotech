from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔌 CONEXIÓN USANDO EL USUARIO ADMINISTRADOR RAÍZ REAL
MONGO_URI = "mongodb://admin_root:SecretMongo2026@comerciotech-nosql-v2:27017/?authSource=admin"
client = MongoClient(MONGO_URI)
db = client["comerciotech_catalogo"]
productos_collection = db["productos"]

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    try:
        productos_db = list(productos_collection.find())
        productos = []
        for p in productos_db:
            item = {
                "sku": str(p.get("sku", "SIN-SKU")),
                "nombre": str(p.get("nombre", "Sin Nombre")),
                "precio": float(p.get("precio", 0.0))
            }
            productos.append(item)

        print(f"📦 ÉXITO: Se enviaron {len(productos)} productos a la plantilla.")
        return templates.TemplateResponse(request, "index.html", {"productos": productos})

    except Exception as e:
        print("❌ ERROR CRÍTICO EN READ_INDEX:")
        import traceback
        print(traceback.format_exc())
        return templates.TemplateResponse(request, "index.html", {"productos": [], "error": str(e)})

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