try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover - fallback for lean environments
    RecursiveCharacterTextSplitter = None


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    if RecursiveCharacterTextSplitter is not None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )
        return splitter.split_text(text)

    step = max(chunk_size - overlap, 1)
    chunks = []
    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks
