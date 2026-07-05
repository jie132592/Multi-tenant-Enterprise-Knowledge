"""
文档解析器
"""
import io
import re
from typing import List

from pypdf import PdfReader

from config import settings


class DocumentParser:
    """文档解析器"""

    @staticmethod
    def parse_text(content: str, chunk_size: int = None) -> List[str]:
        """解析文本并分块"""
        if chunk_size is None:
            chunk_size = settings.CHUNK_SIZE

        content = DocumentParser._clean_text(content)

        paragraphs = re.split(r'\n\s*\n', content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""

                sentences = re.split(r'([。！？.!?])', para)
                temp_chunk = ""

                for i in range(0, len(sentences) - 1, 2):
                    sentence = sentences[i] + sentences[i + 1] if i + 1 < len(sentences) else sentences[i]

                    if len(temp_chunk) + len(sentence) <= chunk_size:
                        temp_chunk += sentence
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = sentence

                if temp_chunk:
                    current_chunk = temp_chunk
            else:
                if len(current_chunk) + len(para) + 1 <= chunk_size:
                    current_chunk += "\n" + para if current_chunk else para
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理文本"""
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    @staticmethod
    def parse_pdf(content: bytes, chunk_size: int = None) -> List[str]:
        """解析 PDF 并分块"""
        if chunk_size is None:
            chunk_size = settings.CHUNK_SIZE

        text_parts = []
        reader = PdfReader(io.BytesIO(content))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n\n".join(text_parts)
        return DocumentParser.parse_text(full_text, chunk_size)

    @staticmethod
    def parse_file(content: bytes, filename: str, chunk_size: int = None) -> List[str]:
        """根据文件类型解析并分块"""
        if filename.lower().endswith('.pdf'):
            return DocumentParser.parse_pdf(content, chunk_size)
        elif filename.lower().endswith(('.txt', '.md')):
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('gbk')
                except UnicodeDecodeError:
                    text = content.decode('latin-1', errors='ignore')
            return DocumentParser.parse_text(text, chunk_size)
        else:
            raise ValueError(f"不支持的文件类型: {filename}")
