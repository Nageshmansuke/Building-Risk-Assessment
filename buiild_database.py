import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# 1. Create a list of exact file paths
pdf_paths = [
    "docs/IS4326.pdf", 
    "docs/IS13828.pdf"
]

all_pages = []

print("[INFO] Loading multiple PDFs...")
for path in pdf_paths:
    print(f"Reading {path}...")
    loader = PyPDFLoader(path)
    pages = loader.load()
    all_pages.extend(pages)

print(f"[OK] Loaded a total of {len(all_pages)} pages across all documents.")

# 2. Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, 
    chunk_overlap=200 
)
chunks = text_splitter.split_documents(all_pages)
print(f"[OK] Split documents into {len(chunks)} chunks.")

print("[INFO] Converting text into embeddings and saving to Chroma database...")

# 3. Create Vector Database using HuggingFace all-MiniLM-L6-v2
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

db = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory="./my_local_database"
)

print("[OK] Database built and saved successfully to ./my_local_database")

# 4. Verification test
query = "How to retrofit masonry buildings?"
print(f"[INFO] Testing search for: '{query}'")
search_results = db.similarity_search(query, k=2)

print("[OK] Top results found:")
for i, result in enumerate(search_results):
    print(f"\n--- Result {i+1} ---")
    print(result.page_content[:200] + "...")