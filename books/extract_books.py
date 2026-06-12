# /// script
# requires-python = ">=3.10"
# dependencies = ["pymupdf", "requests", "python-dotenv", "Pillow"]
# ///

"""
宗教書籍4冊 画像抽出＋OCRパイプライン（009のocr.pyの発展版）
実行: uv run extract_books.py [書籍key]   ※key省略で全冊処理

【009からの進化点】
1. JPEG(q85)→ WebP 2種（表示用:長辺1600px/q90、サムネ:長辺480px/q80）
2. PDF物理ページindex(pdfPage)を保存 → #page=N リンクのズレ防止
3. 出力はJSON でなく JS変数形式（book_{key}.js）→ file:// で <script src> 読込
4. 完了時にOCRエラー/極短テキストのページ一覧をサマリー表示
※レンダリングは009実証済みの300dpi方式（無劣化抽出はPhase 1試走で比較検証）
"""

import base64, io, json, os, sys, time
from pathlib import Path
import fitz  # pymupdf
import requests
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
PDF_DIR = Path(r"G:\マイドライブ\保管用\宗教")

BOOKS = {
    "godai":    {"title": "図解 世界五大宗教全史",                  "pdf": "図解 世界五大宗教全史.pdf",                  "color": "#2E8B57"},
    "sekai":    {"title": "宗教と世界",                            "pdf": "宗教と世界.pdf",                            "color": "#AD4F7E"},
    "nemure":   {"title": "眠れなくなるほど面白い 図解 世界の宗教",  "pdf": "眠れなくなるほど面白い 図解 世界の宗教.pdf",  "color": "#C9762B"},
    "allcolor": {"title": "オールカラーでわかりやすい！ 世界の宗教", "pdf": "オールカラーでわかりやすい！ 世界の宗教.pdf", "color": "#3A7CA5"},
}

DATA_DIR = SCRIPT_DIR / "data"
IMG_DIR  = SCRIPT_DIR / "img"
DATA_DIR.mkdir(exist_ok=True)

# ===== APIキー =====
api_key = None
env_path = SCRIPT_DIR / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8-sig") as f:
        for line in f:
            if "GOOGLE_VISION_API_KEY" in line and "=" in line:
                api_key = line.strip().split("=", 1)[1]
                break
if not api_key:
    print("❌ books/.env に GOOGLE_VISION_API_KEY がありません（009の.envからコピー可）")
    sys.exit(1)
VISION_URL = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
print(f"✅ APIキーOK（末尾 ...{api_key[-4:]}）")


def save_webp(img: Image.Image, path: Path, max_long: int, quality: int):
    w, h = img.size
    scale = max_long / max(w, h)
    if scale < 1:
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(path), format="WEBP", quality=quality)


def ocr_image(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)  # OCR送信用のみJPEG（保存はしない）
    b64 = base64.b64encode(buf.getvalue()).decode()
    payload = {"requests": [{"image": {"content": b64},
                             "features": [{"type": "DOCUMENT_TEXT_DETECTION"}]}]}
    try:
        resp = requests.post(VISION_URL, json=payload, timeout=30)
        first = resp.json().get("responses", [{}])[0]
        if "error" in first:
            return f"[エラー: {first['error'].get('message','不明')}]"
        ann = first.get("fullTextAnnotation")
        return ann.get("text", "").strip() if ann else ""
    except Exception as e:
        return f"[エラー: {e}]"


def write_js(key: str, meta: dict, pages: list, js_path: Path):
    """JS変数形式で保存（アトミック書込・OneDriveロック対策）"""
    var = f"BOOK_{key.upper()}"
    body = (f"// 自動生成: extract_books.py（手編集しない）\n"
            f"const {var} = " +
            json.dumps({"meta": meta, "pages": sorted(pages, key=lambda x: x['page'])},
                       ensure_ascii=False, indent=1) + ";\n")
    tmp = js_path.with_suffix(".tmp")
    for attempt in range(5):
        try:
            tmp.write_text(body, encoding="utf-8")
            tmp.replace(js_path)
            return
        except PermissionError:
            time.sleep(attempt + 1)


def process_book(key: str):
    info = BOOKS[key]
    pdf_path = PDF_DIR / info["pdf"]
    print(f"\n{'='*52}\n📖 {info['title']}\n{'='*52}")
    if not pdf_path.exists():
        print(f"❌ PDFなし: {pdf_path}")
        return

    js_path = DATA_DIR / f"book_{key}.js"
    img_dir = IMG_DIR / key

    # 途中再開：既存JSから処理済みページを復元
    pages = []
    if js_path.exists():
        raw = js_path.read_text(encoding="utf-8")
        raw = raw[raw.index("{"): raw.rindex("}") + 1]
        pages = json.loads(raw)["pages"]
        print(f"  既存 {len(pages)} 見開きを読込（途中再開）")
    done = {p["page"] for p in pages}

    doc = fitz.open(str(pdf_path))
    total = len(doc)
    meta = {"key": key, "title": info["title"], "color": info["color"],
            "pdfPath": "file:///" + str(pdf_path).replace("\\", "/"),
            "totalSpreads": total}

    for i in range(total):
        page_no = i + 1
        if page_no in done:
            continue
        print(f"  [p{page_no:03d}/{total}] ", end="", flush=True)

        pix = doc[i].get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        fn = f"p{page_no:03d}.webp"
        save_webp(img, img_dir / fn, 1600, 90)            # 表示用
        save_webp(img, img_dir / "thumb" / fn, 480, 80)   # サムネ

        text = ocr_image(img)
        pages.append({
            "page": page_no,
            "pdfPage": i,                       # 物理index(0始まり)。リンクは pdfPage+1
            "bookPages": "",                    # 書籍上のページ表記はtag_map側で補完可
            "text": text,
            "img": f"books/img/{key}/{fn}",
            "thumb": f"books/img/{key}/thumb/{fn}",
            "tags": []                          # tag_map.py が後で付与
        })
        write_js(key, meta, pages, js_path)     # 1頁ごと保存（中断安全）
        print(f"{len(text)}文字")
        time.sleep(0.5)

    doc.close()

    # サマリー（要再OCR候補）
    bad = [p["page"] for p in pages if p["text"].startswith("[エラー:") or len(p["text"]) < 10]
    print(f"\n✅ {info['title']} 完了: {len(pages)}見開き")
    if bad:
        print(f"  ⚠ 要確認ページ（エラー/極短テキスト）: {bad}")


if __name__ == "__main__":
    targets = sys.argv[1:] or list(BOOKS)
    for k in targets:
        if k not in BOOKS:
            print(f"❌ 不明なkey: {k}（{list(BOOKS)}）"); continue
        process_book(k)
    print("\n🎉 完了。次は tag_map.py でタグ付与 → books_index.js 生成")
