"""
Módulo para ingestão flexível de dados de múltiplas fontes.
Suporta JSON, CSV, TXT, PDF e outros formatos.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class DataIngestion:
    """Gerenciador de ingestão de dados flexível."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.temp_dir = self.data_dir / "temp_uploads"
        self.temp_dir.mkdir(exist_ok=True)

    def generate_doc_id(self, content: str, source: str) -> str:
        """Gera ID único baseado no conteúdo."""
        hash_content = hashlib.md5(f"{source}_{content}".encode()).hexdigest()
        return f"custom_{hash_content[:16]}"

    def ingest_json(
        self, 
        file_path: Path,
        profile_name: str = "custom_data",
        content_type: str = "custom_ingestion"  # 🆕 NOVO PARÂMETRO
    ) -> List[Dict[str, Any]]:
        """
        Ingere arquivo JSON.
        
        Aceita tanto formato de posts do Instagram quanto JSON genérico.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Se for lista, processa cada item
        if isinstance(data, list):
            return [self._normalize_document(item, profile_name, i, content_type) 
                    for i, item in enumerate(data)]
        
        # Se for dict único, processa como documento único
        return [self._normalize_document(data, profile_name, 0, content_type)]

    def ingest_csv(
        self,
        file_path: Path,
        profile_name: str = "custom_data",
        content_type: str = "custom_ingestion",  # 🆕 NOVO PARÂMETRO
        text_column: str = "text",
        title_column: Optional[str] = None,
        date_column: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Ingere arquivo CSV.
        
        Args:
            file_path: Caminho do CSV
            profile_name: Nome do perfil/fonte
            content_type: Tipo de conteúdo customizado
            text_column: Nome da coluna com texto principal
            title_column: Nome da coluna com título (opcional)
            date_column: Nome da coluna com data (opcional)
        """
        documents = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                if text_column not in row:
                    raise ValueError(f"Coluna '{text_column}' não encontrada no CSV")
                
                doc = {
                    'text': row[text_column],
                    'title': row.get(title_column, '') if title_column else f"Documento {i+1}",
                    'metadata': {k: v for k, v in row.items() if k != text_column}
                }
                
                if date_column and date_column in row:
                    doc['date'] = row[date_column]
                
                documents.append(self._normalize_document(doc, profile_name, i, content_type))
        
        return documents

    def ingest_text(
        self,
        file_path: Path,
        profile_name: str = "custom_data",
        content_type: str = "custom_ingestion",  # 🆕 NOVO PARÂMETRO
        split_by: str = "\n\n"
    ) -> List[Dict[str, Any]]:
        """
        Ingere arquivo de texto.
        
        Args:
            file_path: Caminho do arquivo TXT
            profile_name: Nome do perfil/fonte
            content_type: Tipo de conteúdo customizado
            split_by: Separador para dividir texto em documentos
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Divide texto em documentos
        chunks = [c.strip() for c in content.split(split_by) if c.strip()]
        
        return [
            self._normalize_document(
                {'text': chunk, 'title': f"Trecho {i+1}"},
                profile_name,
                i,
                content_type  # 🆕 PASSA TIPO CUSTOMIZADO
            )
            for i, chunk in enumerate(chunks)
        ]

    def ingest_pdf(
        self,
        file_path: Path,
        profile_name: str = "custom_data",
        content_type: str = "custom_ingestion"  # 🆕 NOVO PARÂMETRO
    ) -> List[Dict[str, Any]]:
        """
        Ingere arquivo PDF.
        
        Requer: pip install pypdf2
        """
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 não instalado. Execute: uv pip install pypdf2")
        
        reader = PdfReader(str(file_path))
        documents = []
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text().strip()
            if text:
                documents.append(
                    self._normalize_document(
                        {'text': text, 'title': f"Página {i+1}"},
                        profile_name,
                        i,
                        content_type  # 🆕 PASSA TIPO CUSTOMIZADO
                    )
                )
        
        return documents

    def _normalize_document(
        self,
        doc: Dict[str, Any],
        profile_name: str,
        index: int,
        content_type: str = "custom_ingestion"  # 🆕 NOVO PARÂMETRO
    ) -> Dict[str, Any]:
        """
        Normaliza documento para formato padrão do sistema.
        
        Formato compatível com embedding_manager.py e data_loader.py
        
        Args:
            doc: Documento a ser normalizado
            profile_name: Nome do perfil/fonte
            index: Índice do documento
            content_type: Tipo de conteúdo customizado
        """
        # Extrai texto principal
        text = doc.get('text', '') or doc.get('content', '') or doc.get('caption', '')
        
        if not text:
            text = json.dumps(doc, ensure_ascii=False)
        
        # Gera ID único
        doc_id = self.generate_doc_id(text, profile_name)
        
        # Cria timestamp
        timestamp = datetime.now()
        if 'date' in doc:
            try:
                from dateutil import parser as date_parser
                timestamp = date_parser.parse(doc['date'])
            except:
                pass
        
        # Formato normalizado (compatível com InstagramDataLoader)
        normalized = {
            'id': doc.get('id', doc_id),
            'profile': profile_name,
            'content_type': content_type,  # 🆕 USA O TIPO CUSTOMIZADO
            'type': doc.get('type', 'Document'),
            'text': text,
            'url': doc.get('url', ''),
            'title': doc.get('title', ''),
            'description': doc.get('description', ''),
            'timestamp': timestamp,
            'likesCount': doc.get('likesCount', 0),
            'commentsCount': doc.get('commentsCount', 0),
            'hashtags': doc.get('hashtags', []),
            'mentions': doc.get('mentions', []),
            'metadata': doc.get('metadata', {})
        }
        
        return normalized

    def get_supported_formats(self) -> List[str]:
        """Retorna formatos suportados."""
        return ['.json', '.csv', '.txt', '.pdf']

    def validate_file(self, file_path: Path) -> tuple[bool, str]:
        """
        Valida arquivo antes de processar.
        
        Returns:
            (is_valid, error_message)
        """
        if not file_path.exists():
            return False, "Arquivo não encontrado"
        
        if file_path.suffix.lower() not in self.get_supported_formats():
            return False, f"Formato {file_path.suffix} não suportado"
        
        if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
            return False, "Arquivo muito grande (máx: 50MB)"
        
        return True, ""

    def process_file(
        self,
        file_path: Path,
        profile_name: str = "custom_data",
        content_type: str = "custom_ingestion",  # 🆕 NOVO PARÂMETRO
        **kwargs
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Processa arquivo baseado na extensão.
        
        Args:
            file_path: Caminho do arquivo
            profile_name: Nome do perfil/fonte
            content_type: Tipo de conteúdo customizado
            **kwargs: Argumentos específicos por formato
    
        Returns:
            (documents, status_message)
        """
        # Valida arquivo
        is_valid, error = self.validate_file(file_path)
        if not is_valid:
            return [], f"❌ Erro: {error}"
        
        try:
            extension = file_path.suffix.lower()
            
            if extension == '.json':
                docs = self.ingest_json(file_path, profile_name, content_type)
            elif extension == '.csv':
                # CSV aceita: text_column, title_column, date_column
                csv_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k in ['text_column', 'title_column', 'date_column']
                }
                docs = self.ingest_csv(file_path, profile_name, content_type, **csv_kwargs)
            elif extension == '.txt':
                # TXT aceita apenas: split_by
                txt_kwargs = {
                    k: v for k, v in kwargs.items() 
                    if k in ['split_by']
                }
                docs = self.ingest_text(file_path, profile_name, content_type, **txt_kwargs)
            elif extension == '.pdf':
                # PDF não aceita kwargs extras
                docs = self.ingest_pdf(file_path, profile_name, content_type)
            else:
                return [], f"❌ Formato {extension} não implementado"
            
            return docs, f"✅ {len(docs)} registros processados com sucesso"
        
        except Exception as e:
            return [], f"❌ Erro ao processar: {str(e)}"


def main():
    """Teste do módulo."""
    ingestion = DataIngestion()
    
    print("Formatos suportados:")
    for fmt in ingestion.get_supported_formats():
        print(f"  - {fmt}")


if __name__ == "__main__":
    main()