"""
Pipeline de Ingestão de Dados com Docling.
Transforma documentos em JSON e vetoriza o conteúdo.
Suporta múltiplos formatos e tipos de fontes.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import tempfile
import shutil
from enum import Enum

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import ConversionStatus
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False

import hashlib


class ContentType(Enum):
    """Tipos de conteúdo suportados."""
    DOCUMENT = "document"
    ARTICLE = "article"
    REPORT = "report"
    RESEARCH = "research"
    MANUAL = "manual"
    POLICY = "policy"
    OTHER = "other"


class ContentSource(Enum):
    """Fontes de dados suportadas."""
    UPLOAD = "upload"  # Documento enviado pelo usuário
    INSTAGRAM = "instagram"  # Posts do Instagram
    NEWS = "news"  # Notícias
    WEB_SEARCH = "web_search"  # Resultados de busca web
    INTERNAL = "internal"  # Dados internos


@dataclass
class IngestionMetadata:
    """Metadados de um documento injetado."""
    id: str  # Hash único
    filename: str  # Nome do arquivo original
    content_type: ContentType  # Tipo de conteúdo
    source: ContentSource  # Fonte dos dados
    upload_date: str  # Data de upload (ISO format)
    file_size_bytes: int  # Tamanho em bytes
    page_count: Optional[int] = None  # Número de páginas (se PDF)
    language: str = "pt"  # Idioma
    custom_tags: List[str] = None  # Tags customizadas
    author: Optional[str] = None  # Autor/criador
    description: Optional[str] = None  # Descrição fornecida pelo usuário
    source_url: Optional[str] = None  # URL se aplicável
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        data = asdict(self)
        data['content_type'] = self.content_type.value
        data['source'] = self.source.value
        if self.custom_tags is None:
            data['custom_tags'] = []
        return data


class DocumentConverter:
    """Converte documentos para JSON usando Docling."""
    
    def __init__(self):
        """Inicializa o conversor."""
        if not DOCLING_AVAILABLE:
            raise RuntimeError(
                "Docling não está instalado. Execute: uv add docling"
            )
        
        from docling.document_converter import DocumentConverter as DoclingConverter
        self.converter = DoclingConverter()
        # Formatos suportados por Docling v2+
        self.supported_formats = ['.pdf', '.docx', '.pptx', '.md', '.html', '.xlsx', '.asciidoc', '.png', '.jpg', '.jpeg', '.tiff']
    
    def convert_file(self, file_path: str) -> Tuple[Dict[str, Any], bool]:
        """
        Converte um arquivo para JSON estruturado.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Tupla (dados_estruturados, sucesso)
        """
        file_path = Path(file_path)
        
        # Verifica se arquivo existe
        if not file_path.exists():
            return {"error": f"Arquivo não encontrado: {file_path}"}, False
        
        # Verifica formato
        if file_path.suffix.lower() not in self.supported_formats:
            return {
                "error": f"Formato não suportado. Suportados: {self.supported_formats}"
            }, False
        
        try:
            from docling.datamodel.base_models import ConversionStatus
            
            # Converte com Docling - use convert_all para uma ou múltiplas fontes
            results = list(self.converter.convert_all([file_path], raises_on_error=False))
            
            if not results:
                return {"error": "Nenhum resultado de conversão"}, False
            
            result = results[0]
            
            if result.status != ConversionStatus.SUCCESS:
                error_msg = "Falha na conversão"
                if hasattr(result, 'errors') and result.errors:
                    error_msg += f": {result.errors[0].error_message}"
                return {"error": error_msg}, False
            
            # Extrai conteúdo
            document = result.document
            
            # Estrutura o conteúdo
            structured_content = {
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "conversion_status": result.status.name,
                "pages": [],
                "metadata": {
                    "title": "",
                    "language": "pt",
                }
            }
            
            # Exporta markdown do documento completo
            full_markdown = document.export_to_markdown()
            
            if not full_markdown or not full_markdown.strip():
                return {"error": "Nenhum conteúdo textual foi extraído do documento"}, False
            
            # Divide por seções ou parágrafos para criar "páginas"
            # Para simplicidade, vamos considerar o documento como uma página
            # mas em PDFs reais, podemos dividir por página
            pages_content = [full_markdown]
            
            for i, page_text in enumerate(pages_content, 1):
                if page_text.strip():
                    page_content = {
                        "page_number": i,
                        "text": page_text.strip(),
                        "tables": [],
                        "figures": []
                    }
                    structured_content["pages"].append(page_content)
            
            # Texto completo
            structured_content["full_text"] = full_markdown.strip()
            
            return structured_content, True
        
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return {"error": f"Erro na conversão: {str(e)}\n{error_detail}"}, False


class DataInjestionPipeline:
    """Pipeline completo de ingestão de dados."""
    
    def __init__(
        self,
        embedding_manager,
        data_dir: str = "data/injected",
        temp_dir: Optional[str] = None
    ):
        """
        Inicializa o pipeline.
        
        Args:
            embedding_manager: Gerenciador de embeddings para vetorização
            data_dir: Diretório para armazenar dados injetados
            temp_dir: Diretório temporário (se None, usa tempfile)
        """
        self.embedding_manager = embedding_manager
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        
        # Inicializa conversor
        self.converter = DocumentConverter() if DOCLING_AVAILABLE else None
        
        # Metadados dos arquivos injetados
        self.metadata_file = self.data_dir / "injested_metadata.json"
        self.injected_metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Carrega metadados dos arquivos injetados."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Salva metadados dos arquivos injetados."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.injected_metadata, f, ensure_ascii=False, indent=2)
    
    def _generate_doc_id(self, filename: str, content: str) -> str:
        """Gera ID único para documento baseado em hash."""
        combined = f"{filename}_{content[:100]}"
        return hashlib.md5(combined.encode()).hexdigest()[:12]
    
    def ingest_document(
        self,
        file_path: str,
        content_type: ContentType = ContentType.DOCUMENT,
        custom_tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        description: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Ingere um documento e o vetoriza.
        
        Args:
            file_path: Caminho do arquivo a ingerir
            content_type: Tipo de conteúdo
            custom_tags: Tags customizadas
            author: Autor do documento
            description: Descrição
            source_url: URL de origem
            
        Returns:
            Tupla (sucesso, mensagem, resultado)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, f"Arquivo não encontrado: {file_path}", None
        
        if not self.converter:
            return False, "Docling não disponível", None
        
        # Lê arquivo original
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Converte com Docling
        converted_data, success = self.converter.convert_file(str(file_path))
        
        if not success:
            error_msg = converted_data.get('error', 'Erro desconhecido')
            return False, f"Falha na conversão: {error_msg}", None
        
        # Gera ID único
        doc_id = self._generate_doc_id(file_path.name, converted_data.get('full_text', ''))
        
        # Cria metadados
        metadata = IngestionMetadata(
            id=doc_id,
            filename=file_path.name,
            content_type=content_type,
            source=ContentSource.UPLOAD,
            upload_date=datetime.now().isoformat(),
            file_size_bytes=len(file_content),
            page_count=len(converted_data.get('pages', [])),
            language="pt",
            custom_tags=custom_tags or [],
            author=author,
            description=description,
            source_url=source_url
        )
        
        # Prepara dados para vetorização
        documents_to_add = []
        ids_to_add = []
        metadatas_to_add = []
        
        # Uma entrada por página
        full_text = converted_data.get('full_text', '')
        
        if full_text.strip():
            # Metadados base
            doc_metadata = {
                "doc_id": doc_id,
                "filename": file_path.name,
                "content_type": metadata.content_type.value,
                "source": metadata.source.value,
                "upload_date": metadata.upload_date,
                "author": author or "Desconhecido",
                "language": "pt",
                "tags": ",".join(custom_tags) if custom_tags else "",
                "description": description or "",
                "page_count": metadata.page_count or 0
            }
            
            # Divide texto em chunks menores (2000 chars cada)
            # Isso melhora a busca semântica para documentos grandes
            chunk_size = 2000
            chunks = []
            
            if len(full_text) > chunk_size:
                # Divide em chunks com overlap de 200 chars
                overlap = 200
                start = 0
                chunk_idx = 0
                
                while start < len(full_text):
                    end = start + chunk_size
                    chunk_text = full_text[start:end]
                    
                    if chunk_text.strip():
                        chunks.append((chunk_idx, chunk_text))
                        chunk_idx += 1
                    
                    start = end - overlap  # Overlap para não perder contexto
            else:
                # Documento pequeno - chunk único
                chunks = [(0, full_text)]
            
            # Adiciona cada chunk ao ChromaDB
            for chunk_idx, chunk_text in chunks:
                chunk_metadata = {
                    **doc_metadata,
                    "chunk_index": chunk_idx,
                    "total_chunks": len(chunks)
                }
                chunk_id = f"{metadata.source.value}_{doc_id}_chunk{chunk_idx}"
                
                documents_to_add.append(chunk_text)
                ids_to_add.append(chunk_id)
                metadatas_to_add.append(chunk_metadata)
        
        # Vetoriza no ChromaDB
        try:
            self.embedding_manager.add_documents(
                documents=documents_to_add,
                ids=ids_to_add,
                metadatas=metadatas_to_add
            )
        except Exception as e:
            return False, f"Erro ao vetorizar: {str(e)}", None
        
        # Salva arquivo JSON convertido
        json_path = self.data_dir / f"{doc_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=2)
        
        # Atualiza metadados
        self.injected_metadata[doc_id] = metadata.to_dict()
        self._save_metadata()
        
        # Retorna resultado
        result = {
            "doc_id": doc_id,
            "filename": file_path.name,
            "pages": metadata.page_count or 1,
            "chunks_created": len(ids_to_add),
            "metadata": metadata.to_dict()
        }
        
        return True, f"✅ Documento injetado com sucesso! {len(ids_to_add)} chunks criados.", result
    
    def ingest_raw_text(
        self,
        text: str,
        source_name: str,
        content_type: ContentType = ContentType.ARTICLE,
        custom_tags: Optional[List[str]] = None,
        author: Optional[str] = None,
        description: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Ingere texto bruto (não convertido com Docling).
        
        Args:
            text: Texto bruto
            source_name: Nome da fonte
            content_type: Tipo de conteúdo
            custom_tags: Tags
            author: Autor
            description: Descrição
            
        Returns:
            Tupla (sucesso, mensagem, resultado)
        """
        if not text.strip():
            return False, "Texto vazio fornecido", None
        
        # Gera ID único
        doc_id = self._generate_doc_id(source_name, text)
        
        # Cria metadados
        metadata = IngestionMetadata(
            id=doc_id,
            filename=source_name,
            content_type=content_type,
            source=ContentSource.UPLOAD,
            upload_date=datetime.now().isoformat(),
            file_size_bytes=len(text.encode()),
            page_count=1,
            language="pt",
            custom_tags=custom_tags or [],
            author=author,
            description=description
        )
        
        # Prepara para vetorização com chunking
        doc_metadata = {
            "doc_id": doc_id,
            "filename": source_name,
            "content_type": metadata.content_type.value,
            "source": metadata.source.value,
            "upload_date": metadata.upload_date,
            "author": author or "Desconhecido",
            "language": "pt",
            "tags": ",".join(custom_tags) if custom_tags else "",
            "description": description or ""
        }
        
        # Divide texto em chunks menores (2000 chars cada)
        chunk_size = 2000
        chunks = []
        documents_to_add = []
        ids_to_add = []
        metadatas_to_add = []
        
        if len(text) > chunk_size:
            overlap = 200
            start = 0
            chunk_idx = 0
            
            while start < len(text):
                end = start + chunk_size
                chunk_text = text[start:end]
                
                if chunk_text.strip():
                    chunks.append((chunk_idx, chunk_text))
                    chunk_idx += 1
                
                start = end - overlap
        else:
            chunks = [(0, text)]
        
        # Adiciona cada chunk
        for chunk_idx, chunk_text in chunks:
            chunk_metadata = {
                **doc_metadata,
                "chunk_index": chunk_idx,
                "total_chunks": len(chunks)
            }
            chunk_id = f"{metadata.source.value}_{doc_id}_chunk{chunk_idx}"
            
            documents_to_add.append(chunk_text)
            ids_to_add.append(chunk_id)
            metadatas_to_add.append(chunk_metadata)
        
        # Vetoriza
        try:
            self.embedding_manager.add_documents(
                documents=documents_to_add,
                ids=ids_to_add,
                metadatas=metadatas_to_add
            )
        except Exception as e:
            return False, f"Erro ao vetorizar: {str(e)}", None
        
        # Salva JSON
        json_data = {
            "filename": source_name,
            "full_text": text,
            "pages": [{"page_number": 1, "text": text}],
            "metadata": metadata.to_dict()
        }
        
        json_path = self.data_dir / f"{doc_id}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        # Atualiza metadados
        self.injected_metadata[doc_id] = metadata.to_dict()
        self._save_metadata()
        
        result = {
            "doc_id": doc_id,
            "filename": source_name,
            "pages": 1,
            "chunks_created": len(ids_to_add),
            "metadata": metadata.to_dict()
        }
        
        return True, f"✅ Texto injetado com sucesso! {len(ids_to_add)} chunks criados.", result
    
    def get_injected_documents(self) -> List[Dict[str, Any]]:
        """Retorna lista de documentos injetados."""
        return list(self.injected_metadata.values())
    
    def get_document_content(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retorna conteúdo JSON de um documento injetado."""
        json_path = self.data_dir / f"{doc_id}.json"
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def delete_document(self, doc_id: str) -> Tuple[bool, str]:
        """Delete um documento injetado e suas vetorizações."""
        if doc_id not in self.injected_metadata:
            return False, f"Documento não encontrado: {doc_id}"
        
        try:
            # Remove do ChromaDB
            # Busca todos os IDs relacionados ao documento
            where_clause = {"doc_id": doc_id}
            # Note: ChromaDB pode não suportar delete direto por where
            # Alternativa: manter registro e marcar como deletado
            
            # Remove arquivo JSON
            json_path = self.data_dir / f"{doc_id}.json"
            if json_path.exists():
                json_path.unlink()
            
            # Remove metadados
            del self.injected_metadata[doc_id]
            self._save_metadata()
            
            return True, f"✅ Documento {doc_id} deletado com sucesso"
        except Exception as e:
            return False, f"Erro ao deletar: {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas dos dados injetados."""
        stats = {
            "total_documents": len(self.injected_metadata),
            "by_content_type": {},
            "by_source": {},
            "total_size_mb": 0,
            "total_pages": 0
        }
        
        for metadata in self.injected_metadata.values():
            # Por tipo
            ct = metadata['content_type']
            stats["by_content_type"][ct] = stats["by_content_type"].get(ct, 0) + 1
            
            # Por fonte
            src = metadata['source']
            stats["by_source"][src] = stats["by_source"].get(src, 0) + 1
            
            # Tamanho
            stats["total_size_mb"] += metadata['file_size_bytes'] / (1024 * 1024)
            
            # Páginas
            stats["total_pages"] += metadata['page_count'] or 1
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        return stats


def main():
    """Teste do pipeline."""
    print("Pipeline de Ingestão de Dados")
    print("Este módulo não deve ser executado diretamente")


if __name__ == "__main__":
    main()
