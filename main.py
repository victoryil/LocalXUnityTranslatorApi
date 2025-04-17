from fastapi import FastAPI, Query, Request, Form
from starlette.responses import RedirectResponse, FileResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from transformers import MarianMTModel, MarianTokenizer
import os
import logging

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configurar logging
LOG_FILE = "server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

translation_cache = {}

# ------------------ Cache ------------------

def get_cache_file(from_lang, to_lang):
    return f"translations_{from_lang}_{to_lang}.txt"

def load_cache(from_lang, to_lang):
    filename = get_cache_file(from_lang, to_lang)
    translation_cache.clear()
    if not os.path.exists(filename):
        logging.info(f"No se encontró archivo de caché para {from_lang}-{to_lang}, se creará uno nuevo.")
        return
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if '=' in line:
                src, tgt = line.strip().split("=", 1)
                translation_cache[src.strip()] = tgt.strip()
    logging.info(f"Caché {filename} cargada con {len(translation_cache)} entradas.")

def save_cache(from_lang, to_lang):
    filename = get_cache_file(from_lang, to_lang)
    with open(filename, "w", encoding="utf-8") as f:
        for k, v in translation_cache.items():
            f.write(f"{k}={v}\n")
    logging.info(f"Caché {filename} guardada correctamente.")

# ------------------ Modelo ------------------

def load_model(from_lang: str, to_lang: str):
    model_name = f"Helsinki-NLP/opus-mt-{from_lang}-{to_lang}"
    try:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        return tokenizer, model
    except Exception as e:
        logging.error(f"Error al cargar el modelo {model_name}: {e}")
        return None, None

# ------------------ API de Traducción ------------------

@app.get("/translate")
async def translate(text: str = Query(...), from_: str = Query("en", alias="from"), to: str = Query("es")):
    text = text.strip()
    logging.info(f"📥 Solicitud: '{text}' (from: {from_} → to: {to})")
    if not text:
        logging.warning("⚠️ Texto vacío recibido.")
        return text

    load_cache(from_, to)

    if text in translation_cache:
        logging.info("✅ Traducción encontrada en caché.")
        return translation_cache[text]

    tokenizer, model = load_model(from_, to)
    if not tokenizer or not model:
        return text

    try:
        encoded = tokenizer([text], return_tensors="pt", padding=True)
        translated_tokens = model.generate(**encoded)
        translated = tokenizer.decode(translated_tokens[0], skip_special_tokens=True).strip()

        if not translated or len(translated) > 200:
            logging.warning("🔄 Traducción sospechosa, devolviendo texto original.")
            return text

        translation_cache[text] = translated
        save_cache(from_, to)
        logging.info(f"💬 Traducción generada: '{translated}'")
        return translated
    except Exception as e:
        logging.error(f"❌ Error durante la traducción: {e}")
        return text

# ------------------ Interfaz Web ------------------

@app.get("/", response_class=HTMLResponse)
def read_translations(request: Request, q: str = "", page: int = 1, from_: str = "en", to: str = "es"):
    load_cache(from_, to)
    PER_PAGE = 25
    filtered = {k: v for k, v in translation_cache.items() if q.lower() in k.lower() or q.lower() in v.lower()}
    total = len(filtered)
    items = list(filtered.items())
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    current_page_items = dict(items[start:end])
    total_pages = (total + PER_PAGE - 1) // PER_PAGE
    logging.info(f"📄 Mostrando página {page} con {len(current_page_items)} entradas (filtro: '{q}')")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "translations": current_page_items,
        "query": q,
        "page": page,
        "total_pages": total_pages,
        "from_": from_,
        "to": to
    })

@app.post("/edit")
def edit_translation(source: str = Form(...), target: str = Form(...), from_: str = Form(...), to: str = Form(...)):
    load_cache(from_, to)
    translation_cache[source] = target
    save_cache(from_, to)
    logging.info(f"✏️ Traducción editada: '{source}' → '{target}'")
    return RedirectResponse(url=f"/?from_={from_}&to={to}", status_code=303)

@app.post("/delete")
def delete_translation(source: str = Form(...), from_: str = Form(...), to: str = Form(...)):
    load_cache(from_, to)
    if source in translation_cache:
        del translation_cache[source]
        save_cache(from_, to)
        logging.info(f"🗑️ Traducción eliminada: '{source}'")
    return RedirectResponse(url=f"/?from_={from_}&to={to}", status_code=303)

@app.get("/export")
def export_cache(from_: str = Query("en"), to: str = Query("es")):
    filename = get_cache_file(from_, to)
    logging.info(f"📤 Exportando caché {filename}")
    return FileResponse(filename, media_type="text/plain", filename=filename)

@app.get("/download-logs")
def download_logs():
    return FileResponse(LOG_FILE, media_type="text/plain", filename="server.log")

@app.get("/logs", response_class=HTMLResponse)
def show_logs(request: Request, raw: bool = False):
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
        log_text = "".join(lines)
    except Exception as e:
        log_text = f"Error al leer el archivo de log: {e}"
    if raw:
        return log_text
    return templates.TemplateResponse("logs.html", {"request": request, "logs": log_text})