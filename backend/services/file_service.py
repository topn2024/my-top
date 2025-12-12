"""
文件处理服务
负责文件上传、验证和文本提取
"""
import os
import logging
from werkzeug.utils import secure_filename
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# 条件导入文档处理库
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available, .doc/.docx support disabled")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available, PDF support disabled")


class FileService:
    """文件处理服务类"""

    def __init__(self, config):
        """
        初始化文件服务

        Args:
            config: 配置对象，包含UPLOAD_FOLDER和ALLOWED_EXTENSIONS
        """
        self.upload_folder = config.UPLOAD_FOLDER
        self.allowed_extensions = config.ALLOWED_EXTENSIONS
        self.max_file_size = config.MAX_FILE_SIZE

    def allowed_file(self, filename: str) -> bool:
        """
        检查文件扩展名是否允许

        Args:
            filename: 文件名

        Returns:
            bool: 是否允许该文件类型
        """
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def validate_file(self, file) -> Tuple[bool, str]:
        """
        验证文件

        Args:
            file: 上传的文件对象

        Returns:
            tuple: (是否有效, 错误消息)
        """
        if not file:
            return False, '没有选择文件'

        if file.filename == '':
            return False, '文件名为空'

        if not self.allowed_file(file.filename):
            return False, f'不支持的文件类型。允许的类型: {", ".join(self.allowed_extensions)}'

        return True, ''

    def save_file(self, file) -> Tuple[bool, str, Optional[str]]:
        """
        保存上传的文件

        Args:
            file: 上传的文件对象

        Returns:
            tuple: (是否成功, 消息, 文件路径)
        """
        try:
            # 验证文件
            is_valid, error_msg = self.validate_file(file)
            if not is_valid:
                return False, error_msg, None

            # 安全的文件名
            filename = secure_filename(file.filename)
            filepath = os.path.join(self.upload_folder, filename)

            # 保存文件
            file.save(filepath)
            logger.info(f"File saved successfully: {filepath}")

            return True, '文件上传成功', filepath

        except Exception as e:
            logger.error(f"Error saving file: {e}", exc_info=True)
            return False, f'文件保存失败: {str(e)}', None

    def extract_text(self, filepath: str) -> Optional[str]:
        """
        从文件中提取文本

        Args:
            filepath: 文件路径

        Returns:
            提取的文本内容，失败返回None
        """
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return None

        ext = filepath.rsplit('.', 1)[1].lower()

        try:
            if ext in ['txt', 'md']:
                return self._extract_text_file(filepath)
            elif ext == 'pdf':
                return self._extract_pdf(filepath)
            elif ext in ['doc', 'docx']:
                return self._extract_docx(filepath)
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return None

        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {e}", exc_info=True)
            return None

    def _extract_text_file(self, filepath: str) -> Optional[str]:
        """从文本文件提取内容"""
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue

        logger.error(f"Failed to decode text file with all encodings: {filepath}")
        return None

    def _extract_pdf(self, filepath: str) -> Optional[str]:
        """从PDF文件提取文本"""
        if not PDF_AVAILABLE:
            logger.error("PyPDF2 not available")
            return None

        text = ''
        with open(filepath, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                text += page.extract_text() + '\n'

        return text.strip() if text.strip() else None

    def _extract_docx(self, filepath: str) -> Optional[str]:
        """从DOCX文件提取文本"""
        if not DOCX_AVAILABLE:
            logger.error("python-docx not available")
            return None

        doc = Document(filepath)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return text.strip() if text.strip() else None

    def delete_file(self, filepath: str) -> bool:
        """
        删除文件

        Args:
            filepath: 文件路径

        Returns:
            bool: 是否成功删除
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"File deleted: {filepath}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}", exc_info=True)
            return False
