## Descripción
Cuando le hice un resumen con estadísticas personalizadas a mi pololo por su titulación, me di cuenta que yo también iba querer uno, y que me encantaría darle uno a mis amigas... ¡Pero era mucho trabajo!

<p align="center" width="100%">
  <img width="261" height="312" alt="image" src="https://github.com/user-attachments/assets/a848871a-2286-4dbd-81d9-5ed308b03335" />
</p>

Así que, me puse manos a la obra a intentar hacer web scrapping usando la información de ucampus y u-cursos. Con esta info mi idea es generar dos cosas: 

1. Una especie de receiptify, donde se identifica automáticamente un acta milagrosa y se genera una boleta.
2. Un html + css bonito que automaticamente se actualice con los datos del scrapping, y que se pueda exportar como un pdf para impresión.
   
## Estado del proyecto

**Scrapping**
- Proceso de extracción logrado. Se exportan archivos Excel con los datos extraídos.
- Hay hitos académicos no considerados en la extracción, como la participación en grupos organizados, u otros que desconozca.
- También hay casos borde sin considerar, como es el caso de las doble titulaciones, o si se tiene una carrera previa, etc.
- PENDIENTE: Limpieza de los datos extraídos y creación de nuevas variables.

**Acta milagrosa**
- Se tiene un prototipo al estilo de receiptify, con datos de prueba.
- PENDIENTE: Algoritmo que identifique el ramo milagroso, es decir, cargar automaticamente los datos reales para la acta milagrosa

<p align="left" width="100%">
  <img width="170" height="250" alt="image" src="https://github.com/user-attachments/assets/b2699326-aac3-42d1-95f3-d4747dd8a040" />
</p>

**HTML a PDF**
- Diseño de HTML creado en Webflow (webflow.com) y exportado.
- PENDIENTE: Automatización del proceso de actualización del html con los datos personalizados del usuario.
- PENDIENTE: Tranformación de html final a pdf.

## Consideraciones

Al correr main.py hay que imputar el usuario y contraseña de ucampus, y el rut. Lo que actualmente entrega son archivos de excel con el resultado del scrapping.

