🧠 Local Translator Server (MBART50 + FastAPI)

Este proyecto levanta un servidor de traducción local compatible con XUnity.AutoTranslator. Utiliza el modelo multilingüe facebook/mbart-large-50-many-to-many-mmt para ofrecer traducciones de alta calidad sin necesidad de APIs externas.

⸻

🚀 Requisitos
	•	Python 3.9+ (recomendado 3.10 o 3.11)
	•	pip

⸻

🛠 Instalación
	1.	Clona el repositorio y entra en el directorio:

git clone https://github.com/victoryil/LocalXUnityTranslatorApi.git
cd LocalXUnityTranslatorApi

	2.	Crea un entorno virtual (opcional pero recomendado):

python -m venv .venv
source .venv/bin/activate  # o .venv\Scripts\activate en Windows

	3.	Instala las dependencias:

pip install -r requirements.txt



⸻

▶️ Ejecutar el servidor

uvicorn main:app --reload

El servidor se iniciará en http://localhost:8000

⸻

🧩 Integración con XUnity.AutoTranslator
	1.	Abre tu archivo AutoTranslatorConfig.ini dentro del juego/mod donde tienes instalado XUnity.
	2.	Modifica las siguientes líneas:

[General]
Endpoint=CustomTranslate

[Custom]
Url=http://<IP_DEL_SERVIDOR>:8000/translate

Ejemplo si estás en el mismo equipo:

Url=http://localhost:8000/translate

Ejemplo si usas otro ordenador:

Url=http://192.168.1.179:8000/translate

⚠️ Asegúrate de que el firewall o antivirus no bloquee la conexión.

⸻

🖥 Panel Web

Disponible en http://localhost:8000
	•	🔍 Buscar traducciones
	•	✏️ Editar traducciones manualmente
	•	🗑️ Eliminar traducciones
	•	📤 Exportar cache como .txt
	•	📄 Ver logs del servidor en /logs (con refresco automático)

⸻

📦 Estructura

LocalXUnityTranslatorApi/
├── main.py                  # Servidor FastAPI con modelo
├── requirements.txt         # Dependencias
├── translations_cache.txt   # Cache en formato ini (clave=valor)
├── server.log               # Registro de logs
└── templates/
    ├── index.html           # Panel de traducciones
    └── logs.html            # Visor de logs



⸻

🧠 Modelo

Este proyecto usa:
	•	facebook/mbart-large-50-many-to-many-mmt
	•	50 idiomas disponibles
	•	Traducciones contextuales y naturales

Puedes modificarlo en main.py si deseas usar otro modelo más ligero como:
	•	Helsinki-NLP/opus-mt-en-es

⸻

📌 Notas
	•	Si no se encuentra una traducción, el servidor devuelve el mismo texto.
	•	Los errores se registran automáticamente en server.log.
	•	Cache persistente entre ejecuciones.

⸻

¿Preguntas o mejoras? ¡Crea un issue o contáctame!