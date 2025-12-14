"""
文本切分服务
"""
from typing import List
from app.models.document_config import DocumentConfig


class TextSplitterService:
    """文本切分服务"""
    
    def split_text(self, text: str, config: DocumentConfig) -> List[str]:
        """
        根据配置切分文本
        
        Args:
            text: 要切分的文本
            config: 文档配置
            
        Returns:
            切分后的文本片段列表
        """
        split_method = config.split_method
        
        # 兼容旧的配置值 "fixed"，映射为 "length"
        if split_method == "fixed":
            split_method = "length"
        
        if split_method == "length":
            return self.split_by_length(text, config.chunk_size, config.chunk_overlap)
        elif split_method == "paragraph":
            return self.split_by_paragraph(text, config.chunk_size)
        elif split_method == "keyword":
            if not config.split_keyword:
                raise ValueError("按关键字切分时，split_keyword不能为空")
            return self.split_by_keyword(text, config.split_keyword, config.chunk_size)
        else:
            raise ValueError(f"不支持的切分方法: {split_method}")
    
    def split_by_length(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        按固定长度切分（支持overlap）
        
        Args:
            text: 要切分的文本
            chunk_size: 块大小
            chunk_overlap: 重叠大小
            
        Returns:
            切分后的文本片段列表
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap必须小于chunk_size")
        
        chunks = []
        start = 0
        step = chunk_size - chunk_overlap
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():  # 跳过空片段
                chunks.append(chunk)
            start += step
        
        return chunks
    
    def split_by_paragraph(self, text: str, max_chunk_size: int) -> List[str]:
        """
        按段落切分（智能识别段落边界）
        
        Args:
            text: 要切分的文本
            max_chunk_size: 最大块大小
            
        Returns:
            切分后的文本片段列表
        """
        # 先按双换行符分割段落
        paragraphs = text.split("\n\n")
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 如果当前段落加上新段落不超过最大大小，则合并
            if len(current_chunk) + len(para) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个段落超过最大大小，按长度切分
                if len(para) > max_chunk_size:
                    sub_chunks = self.split_by_length(para, max_chunk_size, max_chunk_size // 4)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = para
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def split_by_keyword(self, text: str, keyword: str, max_chunk_size: int) -> List[str]:
        """
        按关键字切分
        
        Args:
            text: 要切分的文本
            keyword: 切分关键字
            max_chunk_size: 最大块大小
            
        Returns:
            切分后的文本片段列表
        """
        # 按关键字分割
        parts = text.split(keyword)
        
        chunks = []
        current_chunk = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # 如果当前片段加上新片段不超过最大大小，则合并
            if len(current_chunk) + len(keyword) + len(part) <= max_chunk_size:
                if current_chunk:
                    current_chunk += keyword + part
                else:
                    current_chunk = part
            else:
                # 保存当前chunk
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 如果单个片段超过最大大小，按长度切分
                if len(part) > max_chunk_size:
                    sub_chunks = self.split_by_length(part, max_chunk_size, max_chunk_size // 4)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

