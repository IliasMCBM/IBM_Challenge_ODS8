# Asistente de Accesibilidad para Ofertas de Empleo y Currículums

Este proyecto forma parte del IBM Challenge ODS8, enfocado en el Objetivo de Desarrollo Sostenible 8: "Trabajo decente y crecimiento económico".

## Descripción

Esta herramienta utiliza la IA generativa (IBM Granite) para hacer más accesibles las ofertas de empleo y currículums, abordando barreras lingüísticas que dificultan el acceso al empleo para diversos grupos, como personas con diferentes niveles educativos, no hablantes nativos o personas con ciertas discapacidades cognitivas.

## Funcionalidades

La aplicación permite a los usuarios (reclutadores o candidatos) pegar texto de ofertas de empleo o secciones de CV para:

1. **Simplificar lenguaje técnico**: Convierte terminología compleja en expresiones más accesibles.
2. **Identificar lenguaje sesgado**: Detecta y sugiere alternativas para expresiones potencialmente excluyentes.
3. **Generar resúmenes**: Crea versiones concisas y fáciles de entender.
4. **Mejorar secciones de CV**: Ayuda a redactar contenido en lenguaje claro y efectivo.

## Instalación

1. Clone este repositorio:
```
git clone [URL_del_repositorio]
```

2. Instale las dependencias ejecutando el archivo que corresponda a su SO(Linux/Mac o Windows):
- En Linux o MacOS:
```
cd nombre_del_repositorio
./bash.sh
```
- En Windows:
```
cd nombre_del_repositorio
install.bat
```

3. Configure el archivo `.env` con sus credenciales de IBM WatsonX:
```
WATSONX_API_KEY=su_api_key
WATSONX_URL=su_url
WATSONX_PROJECT_ID=su_project_id
```

## Uso

1. Ejecute la aplicación:
```
python app.py
```

2. Acceda a la interfaz web a través de la URL local proporcionada.
3. Pegue el texto que desea procesar y seleccione la acción deseada.
4. Haga clic en "Procesar texto" para obtener resultados.

## Tecnologías utilizadas

- Python
- Gradio (para la interfaz de usuario)
- IBM WatsonX AI (con el modelo Granite-13B)
- LangChain

## Contribución al ODS 8

Este proyecto contribuye al ODS 8 al:
- Facilitar el acceso al empleo formal para grupos vulnerables
- Reducir barreras lingüísticas en procesos de reclutamiento
- Promover prácticas de contratación más inclusivas
- Mejorar la empleabilidad mediante una comunicación más efectiva
