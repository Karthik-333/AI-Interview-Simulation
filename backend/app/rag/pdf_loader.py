from pypdf import PdfReader


def extract_text_from_pdf(file_path: str):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        text += page.extract_text() + "\n"

    return text

# from pypdf import PdfReader
# def extract_text_from_pdf(file_path: str):

#     reader = PdfReader(file_path)

#     text = ""

#     for page in reader.pages:

#         text += page.extract_text() + "\n"

#     return text
# print(extract_text_from_pdf("/home/karthik/Downloads/Karthik_S_Resume.pdf"))
