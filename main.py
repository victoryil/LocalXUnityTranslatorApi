from fastapi import FastAPI, Query, Request, Form
from starlette.responses import RedirectResponse, FileResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from transformers import MBartForConditionalGeneration, MBartTokenizer
import torch
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

model_name = "facebook/mbart-large-50-many-to-many-mmt"
tokenizer = MBartTokenizer.from_pretrained(model_name)
model = MBartForConditionalGeneration.from_pretrained(model_name)

LANG_MAP = {
    "en": "en_XX",
    "es": "es_XX",
    "fr": "fr_XX",
    "de": "de_DE",
    "it": "it_IT",
    "pt": "pt_XX",
    "ru": "ru_RU",
    "ja": "ja_XX"
}

CACHE_FILE = "translations_cache.txt"
translation_cache = {}

# ------------------ Cache ------------------
def load_cache():
    if not os.path.exists(CACHE_FILE):
        logging.info("No se encontró archivo de caché, se creará uno nuevo.")
        return
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if '=' in line:
                src, tgt = line.strip().split("=", 1)
                translation_cache[src.strip()] = tgt.strip()
    logging.info(f"Caché cargada con {len(translation_cache)} entradas.")

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        for k, v in translation_cache.items():
            f.write(f"{k}={v}\n")
    logging.info("Caché guardada correctamente.")

load_cache()

# ------------------ API ------------------
@app.get("/translate")
async def translate(text: str = Query(...), from_: str = Query("en", alias="from"), to: str = Query("es")):
    text = text.strip()
    logging.info(f"📥 Solicitud: '{text}' (from: {from_} → to: {to})")
    if not text:
        logging.warning("⚠️ Texto vacío recibido.")
        return text

    if text in translation_cache:
        logging.info("✅ Traducción encontrada en caché.")
        return translation_cache[text]

    src_lang = LANG_MAP.get(from_.lower(), "en_XX")
    tgt_lang = LANG_MAP.get(to.lower(), "es_XX")

    try:
        tokenizer.src_lang = src_lang
        encoded = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            generated = model.generate(
                **encoded, forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang]
            )
        translated = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()

        if not translated or len(translated) > 200 or "el comité recomienda" in translated:
            logging.warning("🔄 Traducción sospechosa, devolviendo texto original.")
            return text

        translation_cache[text] = translated
        save_cache()
        logging.info(f"💬 Traducción generada: '{translated}'")
        return translated
    except Exception as e:
        logging.error(f"❌ Error durante la traducción: {e}")
        return text

# ------------------ Interfaz Web ------------------
@app.get("/", response_class=HTMLResponse)
def read_translations(request: Request, q: str = "", page: int = 1):
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
        "total_pages": total_pages
    })

@app.post("/edit")
def edit_translation(source: str = Form(...), target: str = Form(...)):
    translation_cache[source] = target
    save_cache()
    logging.info(f"✏️ Traducción editada: '{source}' → '{target}'")
    return RedirectResponse(url="/", status_code=303)

@app.post("/delete")
def delete_translation(source: str = Form(...)):
    if source in translation_cache:
        del translation_cache[source]
        save_cache()
        logging.info(f"🗑️ Traducción eliminada: '{source}'")
    return RedirectResponse(url="/", status_code=303)

@app.get("/export")
def export_cache():
    logging.info("📤 Exportación del archivo de traducciones solicitada.")
    return FileResponse(CACHE_FILE, media_type="text/plain", filename="translations_cache.txt")

@app.get("/logs", response_class=HTMLResponse)
def show_logs(request: Request, raw: bool = False):
    try:
        with open("server.log", "r", encoding="utf-8") as f:
            lines = f.readlines()[-200:]
        log_text = "".join(lines)
    except Exception as e:
        log_text = f"Error al leer el archivo de log: {e}"

    if raw:
        return log_text
    return templates.TemplateResponse("logs.html", {"request": request, "logs": log_text})
@app.get("/download-logs")
def download_logs():
    return FileResponse("server.log", media_type="text/plain", filename="server.log")
