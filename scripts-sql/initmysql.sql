-- ==============================================================================
-- ComercioTech - Módulo Relacional (SQL)
-- Objetivo: Facturación, Cuentas por Pagar, Stock Crítico y Cumplimiento ACID
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS comerciotech_financiero;
USE comerciotech_financiero;

-- ------------------------------------------------------------------------------
-- 1. ESTRUCTURAS DE TABLAS (Esquema Rígido para consistencia financiera)
-- ------------------------------------------------------------------------------

-- Tabla de Proveedores (Para gestionar "Cuentas por pagar a proveedores")
CREATE TABLE proveedores (
    id_proveedor INT AUTO_INCREMENT PRIMARY KEY,
    rut_empresa VARCHAR(20) UNIQUE NOT NULL,
    razon_social VARCHAR(150) NOT NULL,
    email_contacto VARCHAR(100) NOT NULL,
    estado ENUM('ACTIVO', 'INACTIVO', 'BLOQUEADO') DEFAULT 'ACTIVO',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Stock Crítico (Control transaccional para evitar ventas sin stock real)
-- Nota: El 'sku' es el nexo de unión con los documentos de MongoDB
CREATE TABLE inventario_critico (
    sku VARCHAR(50) PRIMARY KEY,
    cantidad_bodega INT NOT NULL CHECK (cantidad_bodega >= 0),
    punto_reorden INT NOT NULL DEFAULT 10,
    ultima_auditoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de Clientes (Datos duros para facturación y auditoría GDPR)
CREATE TABLE clientes_financiero (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    rut_cliente VARCHAR(20) UNIQUE NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    email_facturacion VARCHAR(100) NOT NULL,
    direccion_tributaria VARCHAR(255) NOT NULL,
    anonimizado BOOLEAN DEFAULT FALSE, -- Flag para cumplimiento GDPR (Derecho al olvido)
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Facturación (Transacciones contables)
CREATE TABLE facturas (
    nro_factura INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    monto_total DECIMAL(12, 2) NOT NULL CHECK (monto_total >= 0),
    impuesto_iva DECIMAL(12, 2) NOT NULL,
    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado_pago ENUM('PENDIENTE', 'PAGADO', 'ANULADO') DEFAULT 'PENDIENTE',
    FOREIGN KEY (id_cliente) REFERENCES clientes_financiero(id_cliente)
);

-- Tabla de Cuentas por Pagar (Control de deuda con integradores/proveedores)
CREATE TABLE cuentas_por_pagar (
    id_cuenta INT AUTO_INCREMENT PRIMARY KEY,
    id_proveedor INT NOT NULL,
    nro_documento_prov VARCHAR(50) NOT NULL,
    monto_deuda DECIMAL(12, 2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado ENUM('POR_PAGAR', 'PAGADO', 'RETRASADO') DEFAULT 'POR_PAGAR',
    FOREIGN KEY (id_proveedor) REFERENCES proveedores(id_proveedor)
);

-- ------------------------------------------------------------------------------
-- 2. CONTROL DE ACCESO BASADO EN ROLES (RBAC) Y SEGURIDAD
-- Requisito del caso: Autenticación basada en roles (RBAC)
-- ------------------------------------------------------------------------------

-- Usuario Administrador (DBA)
CREATE USER IF NOT EXISTS 'admin_financiero'@'%' IDENTIFIED BY 'AdminComercio2026*';
GRANT ALL PRIVILEGES ON comerciotech_financiero.* TO 'admin_financiero'@'%';

-- Usuario de Aplicación (Python/Backend) - Privilegio mínimo (CRUD de operaciones)
CREATE USER IF NOT EXISTS 'srv_app_sql'@'%' IDENTIFIED BY 'AppSqlPass2026*';
GRANT SELECT, INSERT, UPDATE, DELETE ON comerciotech_financiero.* TO 'srv_app_sql'@'%';

FLUSH PRIVILEGES;

-- Usuario de Auditoría Contable - Solo lectura (Reporting corporativo)
CREATE USER IF NOT EXISTS 'auditor_contable'@'%' IDENTIFIED BY 'AuditTech2026*';
GRANT SELECT ON comerciotech_financiero.* TO 'auditor_contable'@'%';

FLUSH PRIVILEGES;

-- ------------------------------------------------------------------------------
-- 3. DATOS INICIALES DE PRUEBA (Seed Data)
-- ------------------------------------------------------------------------------

INSERT INTO proveedores (rut_empresa, razon_social, email_contacto) VALUES 
('76.543.210-K', 'Lenovo Chile S.A.', 'facturacion@lenovo.cl'),
('77.123.456-7', 'Logitech Latam', 'pagos@logitech.com');

INSERT INTO inventario_critico (sku, cantidad_bodega, punto_reorden) VALUES 
('CT-LAP-001', 50, 10),
('CT-TECLADO-02', 120, 20);

INSERT INTO clientes_financiero (rut_cliente, nombre_completo, email_facturacion, direccion_tributaria) VALUES 
('15.444.333-2', 'Empresa Retail Tech Ltda', 'compras@retailtech.cl', 'Av. Providencia 1234, Santiago');

INSERT INTO facturas (id_cliente, monto_total, impuesto_iva, estado_pago) VALUES 
(1, 1500000.00, 285000.00, 'PAGADO');

INSERT INTO cuentas_por_pagar (id_proveedor, nro_documento_prov, monto_deuda, fecha_vencimiento) VALUES 
(1, 'FAC-99201', 850000.00, '2026-07-15');