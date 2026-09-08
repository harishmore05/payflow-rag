import pymupdf
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parent
SEPA_FILE = BASE_DIR / '../data/EPC125-05-2025-SCT-Rulebook-version1.1.pdf'
PDF_DIR = BASE_DIR / '../data/pdfs'
CHROMA_DIR  = BASE_DIR / '../data/chroma'            # vector store (gitignored)
COLLECTION  = 'payments'
EMBED_MODEL = 'BAAI/bge-small-en-v1.5'
CHUNK_SIZE  = 1500
CHUNK_OVERLAP = 200

def parse_pdf(file_path) -> list[tuple[int, str]]:
    doc = pymupdf.open(file_path)
    pages = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            pages.append((i, text))
    doc.close()
    return pages

def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start+size])
        start = start + size - overlap
    return chunks

def build_records(pdf_dir):
    ids = []
    docs = []
    metas = []
    for pdf in sorted(pdf_dir.glob('*.pdf')):
        for page_no, page_text in parse_pdf(pdf):
            for idx, chunk in enumerate(chunk_text(page_text, CHUNK_SIZE, CHUNK_OVERLAP)):
                ids.append(f'{pdf.stem}_p{page_no}_c{idx}')
                docs.append(chunk)
                metas.append({'source': pdf.name, 'page': page_no, 'chunk': idx})
    return ids, docs, metas

def main():
    ids, docs, metas = build_records(PDF_DIR)
    if not docs:
        print(f'No text found in {PDF_DIR} — are the PDFs there? Are they scanned images?')
        return
    print(f'Parsed {len(docs)} chunks from {PDF_DIR}')

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(docs, normalize_embeddings=True, show_progress_bar=True).tolist()

    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:                               # start clean so re-runs don't duplicate
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION)
    collection.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    print(f"Stored {collection.count()} chunks in Chroma collection '{COLLECTION}'")

if __name__ == '__main__':
    main()
