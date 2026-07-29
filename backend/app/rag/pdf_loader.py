# from pypdf import PdfReader
from langchain_community.document_loaders import PyPDFLoader


def extract_text_from_pdf(file_path: str) -> str:

    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text = "\n".join(doc.page_content for doc in documents)
    return text

    # reader = PdfReader(file_path)

    # text = ""

    # for page in reader.pages:

    #     text += page.extract_text() + "\n"

    # return text

# from pypdf import PdfReader
# def extract_text_from_pdf(file_path: str):

#     reader = PdfReader(file_path)

#     text = ""

#     for page in reader.pages:

#         text += page.extract_text() + "\n"

#     return text
# print(extract_text_from_pdf("/home/karthik/Downloads/Karthik_S_Resume.pdf"))
