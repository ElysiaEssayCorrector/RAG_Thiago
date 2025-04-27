"""
Utilitário para processamento de diferentes formatos de arquivo
"""
import os
import tempfile
from pathlib import Path
import logging
import io

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileProcessor:
    """Classe para processar diferentes formatos de arquivo e extrair texto"""
    
    def __init__(self):
        """Inicializa o processador de arquivos"""
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Verifica dependências para processamento de diferentes formatos"""
        # Tentar importar dependências necessárias
        self.has_pdf_support = self._check_pdf_support()
        self.has_docx_support = self._check_docx_support()
        self.has_doc_support = self._check_doc_support()
    
    def _check_pdf_support(self):
        """Verifica se o suporte a PDF está disponível"""
        try:
            import PyPDF2
            return True
        except ImportError:
            logger.warning("PyPDF2 não está instalado. Instale com: pip install PyPDF2")
            return False
    
    def _check_docx_support(self):
        """Verifica se o suporte a DOCX está disponível"""
        try:
            import docx
            return True
        except ImportError:
            logger.warning("python-docx não está instalado. Instale com: pip install python-docx")
            return False
    
    def _check_doc_support(self):
        """Verifica se o suporte a DOC está disponível"""
        try:
            import textract
            return True
        except ImportError:
            logger.warning("textract não está instalado. Instale com: pip install textract")
            return False
    
    def extract_text(self, file_content, file_name=None, content_type=None):
        """
        Extrai texto de um objeto de arquivo
        
        Args:
            file_content: Conteúdo do arquivo (bytes)
            file_name: Nome do arquivo (opcional)
            content_type: Tipo MIME do arquivo (opcional)
        
        Returns:
            texto extraído
        """
        if not file_content:
            return ""
        
        # Determinar tipo de arquivo
        file_type = self._determine_file_type(file_name, content_type)
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(file_content)
            temp_path = temp.name
        
        try:
            # Extrair texto com base no tipo de arquivo
            if file_type == "pdf":
                text = self._extract_from_pdf(temp_path)
            elif file_type == "docx":
                text = self._extract_from_docx(temp_path)
            elif file_type == "doc":
                text = self._extract_from_doc(temp_path)
            elif file_type == "txt":
                text = self._extract_from_txt(temp_path)
            else:
                raise ValueError(f"Formato de arquivo não suportado: {file_type}")
            
            return text
        finally:
            # Limpar arquivo temporário
            os.unlink(temp_path)
    
    def _determine_file_type(self, file_name=None, content_type=None):
        """Determina o tipo de arquivo com base no nome ou tipo MIME"""
        
        # Primeiro verificar pelo content_type se disponível
        if content_type:
            if content_type == "application/pdf":
                return "pdf"
            elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return "docx"
            elif content_type == "application/msword":
                return "doc"
            elif content_type == "text/plain":
                return "txt"
        
        # Se não tiver content_type, verificar pela extensão
        if file_name:
            extension = Path(file_name).suffix.lower()
            if extension == ".pdf":
                return "pdf"
            elif extension == ".docx":
                return "docx"
            elif extension == ".doc":
                return "doc"
            elif extension == ".txt":
                return "txt"
        
        # Se não conseguir determinar, levantar erro
        raise ValueError("Não foi possível determinar o tipo de arquivo")
    
    def _extract_from_pdf(self, file_path):
        """Extrai texto de arquivo PDF"""
        if not self.has_pdf_support:
            raise ImportError("Suporte a PDF não disponível")
        
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""
    
    def _extract_from_docx(self, file_path):
        """Extrai texto de arquivo DOCX"""
        if not self.has_docx_support:
            raise ImportError("Suporte a DOCX não disponível")
        
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOCX: {e}")
            return ""
    
    def _extract_from_doc(self, file_path):
        """Extrai texto de arquivo DOC"""
        if not self.has_doc_support:
            raise ImportError("Suporte a DOC não disponível")
        
        try:
            import textract
            text = textract.process(file_path).decode('utf-8')
            return text
        except Exception as e:
            logger.error(f"Erro ao extrair texto do DOC: {e}")
            return ""
    
    def _extract_from_txt(self, file_path):
        """Extrai texto de arquivo TXT"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao extrair texto do TXT: {e}")
            return ""

# Instância global para reutilização
file_processor = FileProcessor()
