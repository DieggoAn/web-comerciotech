// OJO: NO uses "use admin;" ni "use comerciotech_catalogo;". 
// Dejamos que Docker maneje el contexto inicial.

// Abre la sesión con los datos fijos del compose en bruto
db.getSiblingDB('admin').auth('admin_root', 'SecretMongo2026*');

// El resto del script sigue igual para crear el usuario srv_app_comerciotech...
db = db.getSiblingDB('comerciotech_catalogo');
db.createUser({
    user: 'srv_app_comerciotech',
    pwd: 'Python1!',
    roles: [{ role: 'readWrite', db: 'comerciotech_catalogo' }]
});
db.createCollection('productos');

// Ahora creamos las colecciones directamente en la BD del proyecto
var dbProyecto = db.getSiblingDB('comerciotech_catalogo');

dbProyecto.createCollection("productos", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "sku", "nombre", "precio", "stock", "categoria", "atributos" ],
         properties: {
            sku: { bsonType: "string" },
            nombre: { bsonType: "string" },
            precio: { bsonType: "double", minimum: 0.0 },
            stock: { bsonType: "int", minimum: 0 },
            categoria: { bsonType: "string" },
            atributos: { bsonType: "object" }
         }
      }
   }
});

dbProyecto.productos.createIndex({ sku: 1 }, { unique: true });
dbProyecto.productos.createIndex({ categoria: 1, precio: 1 });

dbProyecto.createCollection("carritos", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "usuario_id", "estado", "items", "actualizado_en" ],
         properties: {
            usuario_id: { bsonType: "string" },
            estado: { bsonType: "string", enum: [ "activo", "abandonado", "convertido" ] },
            actualizado_en: { bsonType: "date" },
            items: {
               bsonType: "array",
               items: {
                  bsonType: "object",
                  required: [ "sku", "cantidad", "precio_capturado", "añadido_en" ],
                  properties: {
                     sku: { bsonType: "string" },
                     cantidad: { bsonType: "int", minimum: 1 },
                     precio_capturado: { bsonType: "double", minimum: 0.0 },
                     añadido_en: { bsonType: "date" }
                  }
               }
            }
         }
      }
   }
});

dbProyecto.carritos.createIndex({ usuario_id: 1, estado: 1 }, { unique: true });
dbProyecto.carritos.createIndex({ actualizado_en: 1 }, { expireAfterSeconds: 1209600 });

print("🔒 ¡Entorno NoSQL inicializado con db.getSiblingDB de forma segura!");