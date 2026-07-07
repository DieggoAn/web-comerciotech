// 1. Conectarse y autenticarse en la base administrativa
var adminDB = db.getSiblingDB('admin');
adminDB.auth('admin_root', 'SecretMongo2026*');

// 2. Definir e inicializar la base de datos del proyecto de forma limpia
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

// 6. Cargar datos iniciales del catálogo (Semilla/Seed matching SQL critical inventory)
dbProyecto.productos.insertMany([
  {
    sku: "CT-LAP-001",
    nombre: "Laptop Lenovo ThinkPad L14",
    precio: 850000.0,
    stock: NumberInt(50),
    categoria: "Computadores",
    atributos: { procesador: "Intel Core i7", ram: "16GB", almacenamiento: "512GB SSD" }
  },
  {
    sku: "CT-TECLADO-02",
    nombre: "Teclado Mecánico Logitech MX Mechanical",
    precio: 120000.0,
    stock: NumberInt(120),
    categoria: "Accesorios",
    atributos: { conectividad: "Bluetooth/Logi Bolt", retroiluminacion: "Blanca" }
  }
]);

print("🔒 ¡Entorno NoSQL inicializado con validadores y semillas corregidos de forma segura!");