from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔌 CONEXIÓN USANDO EL USUARIO ADMINISTRADOR RAÍZ REAL
# 🔌 CONEXIÓN USANDO EL USUARIO DEDICADO CREADO POR TU SCRIPT
MONGO_URI = "mongodb://srv_app_comerciotech:Python1!@comerciotech-nosql-v2:27017/comerciotech_catalogo?authSource=comerciotech_catalogo"
client = MongoClient(MONGO_URI)
db = client["comerciotech_catalogo"]
productos_collection = db["productos"]

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    try:
        # 🔍 LEER: Traemos todos los productos desde MongoDB reales
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
        # ✅ Posición de argumentos corregida para la nueva versión de Starlette
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
    try:
        # 💾 ESCRIBIR: Insertamos el nuevo producto directamente en MongoDB
        nuevo_producto = {
            "sku": sku,
            "nombre": nombre,
            "precio": float(precio)
        }
        productos_collection.insert_one(nuevo_producto)
        print(f"💾 Producto {sku} guardado con éxito.")
    except Exception as e:
        print(f"❌ Error al guardar en MongoDB: {e}")
        
    return RedirectResponse(url="/", status_code=303)
    @app.post("/eliminar", response_class=RedirectResponse)
    
async def eliminar_producto(sku: str = Form(...)):
    try:
        # 🗑️ ELIMINAR: Borramos el producto que coincida con el SKU recibido
        resultado = productos_collection.delete_one({"sku": sku})
        if resultado.deleted_count > 0:
            print(f"🗑️ Producto con SKU {sku} eliminado con éxito.")
        else:
            print(f"⚠️ No se encontró ningún producto con el SKU {sku}.")
    except Exception as e:
        print(f"❌ Error al eliminar en MongoDB: {e}")
        
    return RedirectResponse(url="/", status_code=303)