// 1. Conectarse y autenticarse en la base administrativa
var adminDB = db.getSiblingDB('admin');
adminDB.auth('admin_root', 'SecretMongo2026*');

// 2. Definir la base de datos del proyecto de forma limpia
var dbProyecto = db.getSiblingDB('comerciotech_catalogo');

// 3. Crear el usuario del servicio para la App de Python con FastAPI
dbProyecto.createUser({
    user: 'srv_app_comerciotech',
    pwd: 'Python1!',
    roles: [
        { role: 'readWrite', db: 'comerciotech_catalogo' }
    ]
});

// 4. Crear la colección de PRODUCTOS con validador flexible para la Fase Web
dbProyecto.createCollection("productos", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         // 💡 Ajustado: Solo requerimos lo que el formulario web de tu app envía hoy
         required: [ "sku", "nombre", "precio" ], 
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

// Índices para velocidad y unicidad del catálogo
dbProyecto.productos.createIndex({ sku: 1 }, { unique: true });

// 5. Crear la colección de CARRITOS
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

print("🔒 ¡Entorno NoSQL inicializado con validadores corregidos de forma segura!");