from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import mysql.connector
import json
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔌 CONEXIONES A BASES DE DATOS
MONGO_URI = "mongodb://srv_app_comerciotech:Python1!@comerciotech-nosql-v2:27017/comerciotech_catalogo?authSource=comerciotech_catalogo"
client = MongoClient(MONGO_URI)
db = client["comerciotech_catalogo"]
productos_collection = db["productos"]

MYSQL_CONFIG = {
    "host": "comerciotech-sql",
    "user": "srv_app_sql",
    "password": "AppSqlPass2026*",
    "database": "comerciotech_financiero"
}

# 🛠️ TRANSACCIÓN POLÍGLOTA: SIMULAR PAGO CHECKOUT
def simular_pago_checkout(carrito_id: str):
    # 1. Obtener carrito activo desde MongoDB
    carrito = db["carritos"].find_one({"_id": ObjectId(carrito_id), "estado": "activo"})
    if not carrito:
        raise Exception("El carrito especificado no existe o no está activo.")
        
    items = carrito.get("items", [])
    if not items:
        raise Exception("El carrito seleccionado no tiene productos.")
        
    monto_total = 0.0
    for item in items:
        monto_total += item["cantidad"] * item["precio_capturado"]
        
    impuesto_iva = monto_total * 0.19

    # 2. Iniciar Transacción ACID en MySQL
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    try:
        # Iniciar transacción manual desactivando autocommit
        conn.autocommit = False
        
        # Bloquear y comprobar stock de inventario_critico (FOR UPDATE)
        for item in items:
            sku = item["sku"]
            cantidad_requerida = item["cantidad"]
            
            cursor.execute(
                "SELECT cantidad_bodega FROM inventario_critico WHERE sku = %s FOR UPDATE",
                (sku,)
            )
            res = cursor.fetchone()
            if not res:
                raise Exception(f"El SKU '{sku}' no existe en el inventario crítico de MySQL.")
                
            cantidad_actual = res[0]
            if cantidad_actual < cantidad_requerida:
                raise Exception(f"Stock insuficiente para SKU '{sku}' en MySQL. Requerido: {cantidad_requerida}, Disponible: {cantidad_actual}.")
                
            # Descontar stock
            nueva_cantidad = cantidad_actual - cantidad_requerida
            cursor.execute(
                "UPDATE inventario_critico SET cantidad_bodega = %s WHERE sku = %s",
                (nueva_cantidad, sku)
            )
            
        # Obtener un cliente de facturación válido de MySQL
        cursor.execute("SELECT id_cliente FROM clientes_financiero LIMIT 1")
        cliente_res = cursor.fetchone()
        if not cliente_res:
            raise Exception("No hay clientes registrados en la tabla clientes_financiero de MySQL.")
        id_cliente = cliente_res[0]
        
        # Registrar la factura
        cursor.execute(
            "INSERT INTO facturas (id_cliente, monto_total, impuesto_iva, estado_pago) VALUES (%s, %s, %s, 'PAGADO')",
            (id_cliente, monto_total, impuesto_iva)
        )
        nro_factura = cursor.lastrowid
        
        # Guardar cambios en MySQL
        conn.commit()
        
        # 3. Si MySQL es exitoso, actualizar estado del carrito a 'convertido' en MongoDB
        db["carritos"].update_one(
            {"_id": ObjectId(carrito_id)},
            {"$set": {"estado": "convertido", "actualizado_en": datetime.utcnow()}}
        )
        
        return {
            "success": True,
            "nro_factura": nro_factura,
            "monto_total": monto_total,
            "impuesto_iva": impuesto_iva
        }
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

# 🏠 VISTA INICIO & LOGIN CENTRALIZADO
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request, error: str = None):
    return templates.TemplateResponse(request, "index.html", {"error": error})

# 🔐 CONTROLADOR DE LOGIN CON BIFURCACIÓN DE ROL
@app.post("/login", response_class=RedirectResponse)
async def login(username: str = Form(...), password: str = Form(...)):
    if username == "admin" and password == "admin123":
        return RedirectResponse(url="/admin", status_code=303)
    elif username == "user" and password == "user123":
        return RedirectResponse(url="/user", status_code=303)
    else:
        return RedirectResponse(url="/?error=auth_failed", status_code=303)

# 💼 VISTA DE ADMINISTRADOR
@app.get("/admin", response_class=HTMLResponse)
async def read_admin(request: Request):
    try:
        # Traer catálogo completo de MongoDB
        productos_db = list(productos_collection.find())
        productos = []
        for p in productos_db:
            productos.append({
                "sku": str(p.get("sku", "SIN-SKU")),
                "nombre": str(p.get("nombre", "Sin Nombre")),
                "precio": float(p.get("precio", 0.0)),
                "stock": int(p.get("stock", 0)),
                "categoria": str(p.get("categoria", "Sin Categoría")),
                "atributos": p.get("atributos", {})
            })
            
        # Traer historial de facturación global desde MySQL (INNER JOIN con clientes_financiero)
        facturas_historial = []
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT f.nro_factura, c.nombre_completo, c.rut_cliente, f.fecha_emision, f.monto_total, f.impuesto_iva, f.estado_pago
                FROM facturas f
                INNER JOIN clientes_financiero c ON f.id_cliente = c.id_cliente
                ORDER BY f.fecha_emision DESC
            """)
            rows = cursor.fetchall()
            for r in rows:
                fecha_str = r["fecha_emision"].strftime("%Y-%m-%d %H:%M:%S") if r.get("fecha_emision") else ""
                facturas_historial.append({
                    "nro_factura": r["nro_factura"],
                    "nombre_completo": r["nombre_completo"],
                    "rut_cliente": r["rut_cliente"],
                    "fecha_emision": fecha_str,
                    "monto_total": float(r["monto_total"]),
                    "impuesto_iva": float(r["impuesto_iva"]),
                    "estado_pago": r["estado_pago"]
                })
            cursor.close()
            conn.close()
        except Exception as sql_ex:
            print(f"⚠️ Error al obtener historial financiero global MySQL: {sql_ex}")
            
        return templates.TemplateResponse(
            request,
            "admin.html",
            {
                "productos": productos,
                "facturas_historial": facturas_historial
            }
        )
    except Exception as e:
        print(f"❌ ERROR EN READ_ADMIN: {e}")
        return templates.TemplateResponse(
            request,
            "admin.html",
            {"productos": [], "facturas_historial": [], "error": str(e)}
        )

# 💾 CREAR PRODUCTO (CON AUDITORÍA DE ESQUEMA MONGO & REGISTRO DE STOCK CRÍTICO SQL)
@app.post("/guardar", response_class=RedirectResponse)
async def guardar_producto(
    sku: str = Form(...),
    nombre: str = Form(...),
    precio: float = Form(...),
    stock: int = Form(...),
    categoria: str = Form(...),
    atributos: str = Form(...)
):
    try:
        # Deserializar subdocumento atributos flexible (JSON)
        atributos_dict = {}
        if atributos.strip():
            try:
                atributos_dict = json.loads(atributos)
            except Exception:
                atributos_dict = {"detalle": atributos}
                
        nuevo_producto = {
            "sku": str(sku),
            "nombre": str(nombre),
            "precio": float(precio),
            "stock": int(stock),
            "categoria": str(categoria),
            "atributos": atributos_dict
        }
        # Guardar en MongoDB
        productos_collection.insert_one(nuevo_producto)
        print(f"💾 Producto {sku} guardado con éxito en MongoDB.")
        
        # Registrar o actualizar stock crítico en MySQL
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT sku FROM inventario_critico WHERE sku = %s", (sku,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO inventario_critico (sku, cantidad_bodega, punto_reorden) VALUES (%s, %s, 10)",
                    (sku, int(stock))
                )
                conn.commit()
                print(f"🔄 Stock crítico de {sku} registrado en MySQL.")
            cursor.close()
            conn.close()
        except Exception as my_ex:
            print(f"⚠️ Error al sincronizar stock crítico en MySQL: {my_ex}")
            
    except Exception as e:
        print(f"❌ Error al guardar en MongoDB: {e}")
        
    return RedirectResponse(url="/admin", status_code=303)

# 🗑️ ELIMINAR PRODUCTO
@app.post("/eliminar", response_class=RedirectResponse)
async def eliminar_producto(sku: str = Form(...)):
    try:
        productos_collection.delete_one({"sku": sku})
        print(f"🗑️ Producto con SKU {sku} eliminado de MongoDB.")
        
        # Eliminar stock de MySQL
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM inventario_critico WHERE sku = %s", (sku,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"🗑️ Stock de {sku} eliminado de MySQL.")
        except Exception as my_ex:
            print(f"⚠️ Error al eliminar stock de MySQL: {my_ex}")
    except Exception as e:
        print(f"❌ Error al eliminar producto: {e}")
        
    return RedirectResponse(url="/admin", status_code=303)

# 🛍️ VISTA DE USUARIO
@app.get("/user", response_class=HTMLResponse)
async def read_user(
    request: Request,
    checkout_success: str = None,
    nro_factura: str = None,
    monto: str = None,
    iva: str = None,
    checkout_error: str = None
):
    try:
        # Catálogo para usuario
        productos_db = list(productos_collection.find())
        productos = []
        for p in productos_db:
            productos.append({
                "sku": str(p.get("sku", "SIN-SKU")),
                "nombre": str(p.get("nombre", "Sin Nombre")),
                "precio": float(p.get("precio", 0.0)),
                "stock": int(p.get("stock", 0)),
                "categoria": str(p.get("categoria", "Sin Categoría")),
                "atributos": p.get("atributos", {})
            })
            
        usuario_id = "usuario_estandar"
        carrito = db["carritos"].find_one({"usuario_id": usuario_id, "estado": "activo"})
        carrito_items = []
        total_carrito = 0.0
        if carrito:
            for item in carrito.get("items", []):
                subtotal = item["cantidad"] * item["precio_capturado"]
                total_carrito += subtotal
                carrito_items.append({
                    "sku": item["sku"],
                    "cantidad": item["cantidad"],
                    "precio_capturado": item["precio_capturado"],
                    "subtotal": subtotal
                })
                
        # Obtener historial de compras del usuario en MySQL (id_cliente = 1)
        compras = []
        try:
            conn = mysql.connector.connect(**MYSQL_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT nro_factura, monto_total, impuesto_iva, fecha_emision, estado_pago FROM facturas WHERE id_cliente = %s ORDER BY fecha_emision DESC",
                (1,)
            )
            rows = cursor.fetchall()
            for r in rows:
                fecha_str = r["fecha_emision"].strftime("%Y-%m-%d %H:%M:%S") if r.get("fecha_emision") else ""
                compras.append({
                    "nro_factura": r["nro_factura"],
                    "monto_total": float(r["monto_total"]),
                    "impuesto_iva": float(r["impuesto_iva"]),
                    "fecha_emision": fecha_str,
                    "estado_pago": r["estado_pago"]
                })
            cursor.close()
            conn.close()
        except Exception as sql_ex:
            print(f"⚠️ Error al obtener historial de facturas MySQL: {sql_ex}")
                
        return templates.TemplateResponse(
            request,
            "user.html",
            {
                "productos": productos,
                "carrito": {
                    "id": str(carrito["_id"]) if carrito else None,
                    "items": carrito_items,
                    "total": total_carrito
                },
                "compras": compras,
                "checkout_success": checkout_success,
                "nro_factura": nro_factura,
                "monto": monto,
                "iva": iva,
                "checkout_error": checkout_error
            }
        )
    except Exception as e:
        print(f"❌ ERROR EN READ_USER: {e}")
        return templates.TemplateResponse(request, "user.html", {"productos": [], "carrito": None, "compras": [], "error": str(e)})

# 🛒 AGREGAR AL CARRITO DE COMPRAS MONGO
@app.post("/carrito/agregar", response_class=RedirectResponse)
async def agregar_al_carrito(sku: str = Form(...), precio: float = Form(...)):
    try:
        usuario_id = "usuario_estandar"
        carrito = db["carritos"].find_one({"usuario_id": usuario_id, "estado": "activo"})
        
        if not carrito:
            nuevo_carrito = {
                "usuario_id": usuario_id,
                "estado": "activo",
                "actualizado_en": datetime.utcnow(),
                "items": [
                    {
                        "sku": sku,
                        "cantidad": 1,
                        "precio_capturado": float(precio),
                        "añadido_en": datetime.utcnow()
                    }
                ]
            }
            db["carritos"].insert_one(nuevo_carrito)
        else:
            items = carrito.get("items", [])
            found = False
            for item in items:
                if item["sku"] == sku:
                    item["cantidad"] += 1
                    item["añadido_en"] = datetime.utcnow()
                    found = True
                    break
            if not found:
                items.append({
                    "sku": sku,
                    "cantidad": 1,
                    "precio_capturado": float(precio),
                    "añadido_en": datetime.utcnow()
                })
            db["carritos"].update_one(
                {"_id": carrito["_id"]},
                {
                    "$set": {
                        "items": items,
                        "actualizado_en": datetime.utcnow()
                    }
                }
            )
        print(f"🛒 SKU {sku} agregado al carrito.")
    except Exception as e:
        print(f"❌ Error al agregar al carrito: {e}")
        
    return RedirectResponse(url="/user", status_code=303)

# 🗑️ VACIAR CARRITO
@app.post("/carrito/vaciar", response_class=RedirectResponse)
async def vaciar_carrito():
    try:
        usuario_id = "usuario_estandar"
        db["carritos"].delete_one({"usuario_id": usuario_id, "estado": "activo"})
        print(f"🗑️ Carrito vaciado.")
    except Exception as e:
        print(f"❌ Error al vaciar el carrito: {e}")
        
    return RedirectResponse(url="/user", status_code=303)

# 💳 PROCESAR FACTURACIÓN Y CHECKOUT AUTOMÁTICO (USUARIO)
@app.post("/user/checkout", response_class=RedirectResponse)
async def user_checkout(carrito_id: str = Form(...)):
    try:
        # Iniciar checkout con la lógica políglota transaccional
        resultado = simular_pago_checkout(carrito_id)
        nro = resultado["nro_factura"]
        monto = resultado["monto_total"]
        iva = resultado["impuesto_iva"]
        return RedirectResponse(
            url=f"/user?checkout_success=1&nro_factura={nro}&monto={monto}&iva={iva}",
            status_code=303
        )
    except Exception as e:
        print(f"❌ Error en checkout del usuario: {e}")
        return RedirectResponse(
            url=f"/user?checkout_error={str(e)}",
            status_code=303
        )