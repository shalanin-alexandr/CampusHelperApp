import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

nltk.download('punkt')

def compress_text(text):
    sentences = nltk.sent_tokenize(text)
    tf_idf = TfidfVectorizer().fit_transform(sentences)
    scores = tf_idf.sum(axis=1).A1
    top_n = max(4, len(sentences) // 4)
    top_idx = scores.argsort()[-top_n:][::-1]
    summary = [sentences[i] for i in sorted(top_idx)]
    return summary

def save_docx(summary, filename):
    if not filename.endswith(".docx"):
        filename += ".docx"
    path = os.path.join("compressed", filename)
    os.makedirs("compressed", exist_ok=True)

    doc = Document()
    center = doc.add_heading("Сокращённый текст", level=1)
    center.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in summary:
        doc.add_paragraph(line)
    doc.save(path)
    return path
