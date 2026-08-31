try:
    from langchain_community.document_loaders import PyPDFLoader
except ImportError:  # pragma: no cover - fallback for lean environments
    PyPDFLoader = None


def extract_text_from_pdf(file_path: str) -> str:
    if PyPDFLoader is not None:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        return "\n".join(doc.page_content for doc in documents)

    from pypdf import PdfReader

    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)
