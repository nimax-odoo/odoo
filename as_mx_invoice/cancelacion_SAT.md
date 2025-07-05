# 📋 GUÍA COMPLETA: MOTIVOS DE CANCELACIÓN DE CFDI

## 🎯 **INTRODUCCIÓN PARA CONTADORES**

Esta guía explica los **4 motivos oficiales** de cancelación de Comprobantes Fiscales Digitales por Internet (CFDI) según las disposiciones del Servicio de Administración Tributaria (SAT).

*Elaborado por: Ahorasoft - Especialistas en Facturación Electrónica* 📊  
*Sitio Web: http://www.ahorasoft.com*

---

## 📚 **CATÁLOGO OFICIAL SAT - MOTIVOS DE CANCELACIÓN**

**01** - Comprobantes emitidos con errores con relación  
**02** - Comprobantes emitidos con errores sin relación  
**03** - No se llevó a cabo la operación  
**04** - Operación nominativa relacionada en una factura global

---

## 🔥 **MOTIVO 01: COMPROBANTES EMITIDOS CON ERRORES CON RELACIÓN**

### **Definición Legal**
Se utiliza cuando el **Comprobante Fiscal Digital** contiene errores y debe **emitirse un CFDI sustituto**. El nuevo comprobante debe relacionar el UUID (Folio Fiscal) del documento original que se cancela.

### **Características Fiscales**
- ✅ **OBLIGATORIO emitir CFDI de reemplazo**
- ✅ **Relación tipo "04" (Sustitución)**
- ✅ **Folio Fiscal del sustituto en cancelación**
- ⚠️ **NO procede cancelación sin documento sustituto**

### **Proceso Contable**

1. **Detectar Error en CFDI Emitido**
2. **Crear Nuevo CFDI Corregido** (con relación al original)
3. **Timbrar CFDI Sustituto** 
4. **Solicitar Cancelación del Original** (motivo 01)
5. **Referenciar Folio Fiscal del Sustituto**

### **Casos de Aplicación**
1. **RFC del receptor incorrecto** o inexistente
2. **Domicilio fiscal erróneo** del cliente
3. **Régimen fiscal incorrecto** del receptor
4. **Clave de producto/servicio SAT** errónea
5. **Unidad de medida incorrecta**
6. **Descripción de mercancías** no conforme
7. **Cálculo incorrecto de impuestos** (IVA, IEPS, ISR)
8. **Tipo de comprobante erróneo**
9. **Método o forma de pago** incorrectos

### **Ejemplo de Aplicación**
**Situación**: Se facturó con RFC incorrecto del cliente
- **CFDI Original**: RFC = XAXX010101000 (Genérico - ERROR)
- **CFDI Sustituto**: RFC = XEXX010101000 (Correcto)
- **Relación**: El CFDI sustituto debe incluir el UUID del original en "CFDI Relacionados"
- **Cancelación**: Se solicita cancelación del original con motivo 01, indicando el UUID del sustituto

---

## ⚡ **MOTIVO 02: COMPROBANTES EMITIDOS CON ERRORES SIN RELACIÓN**

### **Definición Legal**
Se aplica cuando el **CFDI contiene errores** pero **NO se emitirá un comprobante de reemplazo**. Es una cancelación definitiva sin generar nuevo documento fiscal.

### **Características Fiscales**
- ❌ **NO requiere CFDI sustituto**
- ✅ **Cancelación definitiva del comprobante**
- ✅ **Motivo más utilizado en la práctica**
- ✅ **Aplica para todo tipo de comprobantes**

### **Proceso Contable**

1. **Identificar Error en CFDI**
2. **Evaluar que NO se requiere reemplazo**
3. **Solicitar Cancelación** (motivo 02)
4. **Proceso concluido** - Sin documentos adicionales

### **Casos de Aplicación**
1. **Comprobantes de prueba** enviados por error
2. **Duplicación accidental** de facturas
3. **Cambios en condiciones comerciales** (descuentos posteriores)
4. **Cancelación por solicitud del cliente**
5. **Errores menores** que no ameritan corrección
6. **Facturación anticipada** no autorizada
7. **Documentos mal dirigidos** a otro cliente

### **Ventajas Operativas**
- 🚀 **Proceso más ágil** (sin documentos adicionales)
- 💰 **Menor costo operativo** 
- 🎯 **Ideal para errores que no requieren corrección**
- 📋 **Simplifica la contabilidad**

---

## 🚫 **MOTIVO 03: NO SE LLEVÓ A CABO LA OPERACIÓN**

### **Definición Legal**
Se utiliza cuando se **emitió un CFDI por una operación que NO se materializó**. Implica que la venta, prestación de servicios o enajenación **nunca ocurrió físicamente**.

### **Características Fiscales**
- ✅ **Cancelación por operación inexistente**
- ✅ **NO requiere CFDI sustituto**
- ⚠️ **ALTO RIESGO FISCAL - Auditorías SAT**
- 📋 **Requiere documentación soporte**
- 🔍 **Debe justificarse ante autoridades**

### **Proceso Contable**

1. **Identificar Operación No Realizada**
2. **Verificar Inexistencia de Entrega/Servicio**
3. **Documentar Motivos de No Ejecución**
4. **Solicitar Cancelación** (motivo 03)
5. **Realizar Ajustes Contables Correspondientes**

### **Casos de Aplicación**
1. **Ventas canceladas** por el cliente antes de entrega
2. **Servicios contratados** pero no prestados
3. **Mercancías no entregadas** por problemas logísticos
4. **Contratos rescindidos** antes de ejecución
5. **Órdenes de compra canceladas** por el cliente
6. **Servicios profesionales** no realizados
7. **Eventos cancelados** (capacitación, consultoría)

### **⚠️ IMPORTANTE - Limitaciones**
- **NO aplicar** si ya se entregó mercancía
- **NO usar** si el servicio ya se prestó
- **NO procede** si ya hubo transferencia de propiedad
- **Conservar evidencia** de la no realización

### **Implicaciones Contables y Fiscales**
- 💼 **Reversión total** de ingresos registrados
- 📊 **Afecta declaraciones** de IVA e ISR
- 🔍 **Revisiones SAT** más frecuentes
- 📋 **Documentación obligatoria** del motivo
- ⚖️ **Posible requerimiento** de información

---

## 🌐 **MOTIVO 04: OPERACIÓN NOMINATIVA RELACIONADA EN FACTURA GLOBAL**

### **Definición Legal**
Se utiliza cuando una **operación incluida en CFDI Global** (al público en general) debe **excluirse** para emitir un **comprobante nominativo individual** a solicitud del cliente.

### **Características Fiscales**
- 🌍 **Exclusivo para CFDI Globales**
- 👤 **Conversión de operación pública a nominativa**
- ✅ **Requiere emisión de CFDI individual**
- 📋 **Proceso de segregación fiscal**
- 🔄 **Mantenimiento del resto de la factura global**

### **Proceso Contable**

1. **Cliente solicita CFDI nominativo** de operación incluida en factura global
2. **Crear CFDI individual** con datos del cliente
3. **Timbrar comprobante nominativo**
4. **Cancelar porción en factura global** (motivo 04)
5. **Relacionar ambos comprobantes** (global y nominativo)

### **Casos de Aplicación**
1. **Cliente requiere CFDI para deducción fiscal**
2. **Empresa solicita comprobante nominativo** para gastos deducibles
3. **Requerimientos de auditoría interna** del cliente
4. **Necesidades contables específicas** de la empresa
5. **Solicitudes posteriores** a la venta al público
6. **Comprobación de gastos corporativos**
7. **Requisitos de comprobación** ante autoridades

### **Ventajas del Proceso**
- 📊 **Mejor control fiscal** para el cliente
- 💼 **Deducibilidad de gastos** empresariales
- 🎯 **Cumplimiento normativo** específico
- 📋 **Trazabilidad individualizada** de operaciones

### **Consideraciones Importantes**
- ⏰ **Plazo limitado** para solicitar segregación
- 📝 **Documentación** de la solicitud del cliente
- 🔍 **Verificación** de datos del receptor
- 💰 **Impacto en declaraciones** fiscales correspondientes

---

## 🔧 **PROCESO DE CANCELACIÓN EN ODOO**

### **Acceso al Sistema de Cancelación**
1. **Ingresar a la factura** que requiere cancelación
2. **Verificar estado** del CFDI (debe estar "Firmado")
3. **Hacer clic** en botón "Solicitar Cancelación"
4. **Seleccionar motivo** apropiado (01, 02, 03, 04)
5. **Completar información** adicional si es requerida

### **Validaciones del Sistema**
- **Motivo 01**: Requiere obligatoriamente CFDI de reemplazo
- **Motivo 02**: Cancelación directa sin documentos adicionales  
- **Motivo 03**: Verificación de no entrega/no prestación del servicio
- **Motivo 04**: Solo disponible para CFDI Globales

### **Estados de Cancelación**
- **Cancelación Solicitada**: Enviado al PAC, pendiente respuesta SAT
- **Cancelación Aceptada**: SAT aprobó la cancelación
- **Cancelación Rechazada**: SAT rechazó la solicitud

## 🏢 **PROVEEDORES AUTORIZADOS DE CERTIFICACIÓN (PAC)**

El sistema trabaja con los principales PACs del mercado mexicano:

### **PACs Compatibles**
- ✅ **Finkok** - Proveedor líder en timbrado
- ✅ **SW (SmartWeb)** - Soluciones integrales CFDI
- ✅ **Solución Factible** - Especialista en facturación

### **Proceso con PAC**
1. **Sistema envía solicitud** de cancelación al PAC configurado
2. **PAC valida** motivo y documentación
3. **PAC envía** solicitud al SAT
4. **SAT responde** aprobación o rechazo
5. **Sistema actualiza** estado del CFDI

---

## 📊 **TABLA COMPARATIVA**

| Motivo | Requiere Sustituto | Casos de Uso | Flujo | Riesgo Fiscal |
|--------|-------------------|---------------|-------|---------------|
| **01** | ✅ SÍ | Errores con corrección | Complejo | Bajo |
| **02** | ❌ NO | Errores sin corrección | Simple | Bajo |
| **03** | ❌ NO | Operación inexistente | Simple | Alto |
| **04** | 🌐 Depende | Factura global | Complejo | Medio |

---

## ⚠️ **MEJORES PRÁCTICAS CONTABLES**

### **Criterios para Selección de Motivo**
1. **Motivo 01**: Solo cuando se emitirá CFDI corregido
2. **Motivo 02**: Para errores que no requieren corrección
3. **Motivo 03**: Solo si la operación NUNCA ocurrió
4. **Motivo 04**: Exclusivo para segregar CFDI Globales

### **Documentación Requerida**
- **Conservar emails** de solicitud de cancelación
- **Mantener contratos** o órdenes de compra canceladas
- **Guardar evidencia** de no entrega de mercancías
- **Documentar comunicación** con clientes
- **Conservar acuses** de cancelación del SAT

### **Control Interno Recomendado**
- 📋 **Autorización previa** del supervisor contable
- 🔍 **Revisión mensual** de cancelaciones
- 📊 **Reporte estadístico** por motivo de cancelación
- ⚖️ **Análisis de riesgo** para motivo 03
- 📁 **Archivo ordenado** de documentación soporte

---

## 🎯 **RESUMEN EJECUTIVO PARA CONTADORES**

### **Guía Rápida de Decisión**

| Situación | Motivo SAT | Requiere Sustituto | Riesgo Fiscal |
|-----------|------------|-------------------|---------------|
| RFC incorrecto del cliente | **01** | ✅ SÍ | Bajo |
| Factura duplicada | **02** | ❌ NO | Bajo |
| Venta cancelada antes de entrega | **03** | ❌ NO | Alto |
| Cliente pide CFDI de factura global | **04** | 🌐 Individual | Medio |

### **⚡ Recomendaciones Fiscales Críticas**
1. **NUNCA usar motivo 03** si ya se entregó mercancía
2. **SIEMPRE documentar** la razón de cancelación
3. **Motivo 01 OBLIGA** a emitir CFDI sustituto
4. **Conservar evidencia** para posibles requerimientos SAT

### **🚨 Alertas Importantes**
- **Motivo 03**: Sujeto a revisión SAT frecuente
- **Plazo cancelación**: 72 horas máximo después del timbrado
- **CFDI Global**: Solo motivos 01, 02 y 04 disponibles
- **Documentación**: Obligatoria para auditorías

---

---

**© 2025 Ahorasoft | Documentación Contable Especializada | Compatible SAT 2025** 