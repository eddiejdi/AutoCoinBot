
#!/usr/bin/env python3
"""
Agent Config — Configuração para modelos pequenos com tokens limitados.

Estratégias para LLMs menores:
1. CHUNKING: Divide tarefas em partes pequenas
2. CAMADAS: Processa em etapas (análise → decisão → ação)
3. CACHE: Reutiliza resultados intermediários
4. CONTEXTO MÍNIMO: Apenas informações essenciais

Uso:
    from agents.agent_config import AgentConfig, TaskChunker
    
    config = AgentConfig(max_tokens=2048, chunk_size=512)
    chunker = TaskChunker(config)
    
    for chunk in chunker.process("tarefa grande"):
        resultado = processar(chunk)
"""

import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Generator
from pathlib import Path
from enum import Enum
import time


class ModelSize(Enum):
    """Tamanhos de modelo suportados."""
    NANO = "nano"       # ~100M params, 128 tokens (ex: phi-2, tinyllama)
    MICRO = "micro"     # ~500M params, 256 tokens
    TINY = "tiny"       # ~1B params, 512 tokens
    SMALL = "small"     # ~3B params, 2048 tokens
    MEDIUM = "medium"   # ~7B params, 4096 tokens
    LARGE = "large"     # ~13B+ params, 8192+ tokens


@dataclass
class AgentConfig:
    """
    Configuração otimizada para modelos pequenos.
    
    Atributos:
        model_size: Tamanho do modelo (tiny/small/medium/large)
        max_tokens: Limite de tokens por chamada
        chunk_size: Tamanho de cada chunk de processamento
        overlap: Overlap entre chunks (contexto)
        max_retries: Tentativas em caso de falha
        cache_enabled: Ativa cache de resultados
        verbose: Modo verboso para debug
    """
    model_size: ModelSize = ModelSize.SMALL
    max_tokens: int = 2048
    chunk_size: int = 512
    overlap: int = 64
    max_retries: int = 3
    cache_enabled: bool = True
    verbose: bool = False
    
    # Configurações por camada (8 camadas para processamento granular)
    layers: Dict[str, Dict] = field(default_factory=lambda: {
        "parse": {"tokens": 64, "priority": 1},      # Parseia entrada
        "classify": {"tokens": 32, "priority": 2},   # Classifica tipo
        "analysis": {"tokens": 256, "priority": 3},  # Analisa problema
        "plan": {"tokens": 64, "priority": 4},       # Planeja passos
        "decision": {"tokens": 128, "priority": 5},  # Decide ação
        "action": {"tokens": 512, "priority": 6},    # Executa
        "verify": {"tokens": 64, "priority": 7},     # Verifica parcial
        "validation": {"tokens": 128, "priority": 8} # Validação final
    })
    
    # Configuração de streaming para modelos pequenos
    stream_enabled: bool = True
    stream_chunk_tokens: int = 32
    
    # Compressão de contexto
    context_compression: bool = True
    compression_ratio: float = 0.5
    
    @classmethod
    def for_nano_model(cls) -> "AgentConfig":
        """Configuração para modelos nano (~100M-300M params).
        
        Otimizado para: TinyLlama, Phi-2, Qwen-0.5B, etc.
        Usa 8 micro-camadas com tokens mínimos.
        """
        return cls(
            model_size=ModelSize.NANO,
            max_tokens=128,
            chunk_size=32,
            overlap=4,
            stream_enabled=True,
            stream_chunk_tokens=8,
            context_compression=True,
            compression_ratio=0.3,
            layers={
                "parse": {"tokens": 8, "priority": 1},
                "classify": {"tokens": 8, "priority": 2},
                "analysis": {"tokens": 16, "priority": 3},
                "plan": {"tokens": 8, "priority": 4},
                "decision": {"tokens": 16, "priority": 5},
                "action": {"tokens": 32, "priority": 6},
                "verify": {"tokens": 8, "priority": 7},
                "validation": {"tokens": 16, "priority": 8}
            }
        )
    
    @classmethod
    def for_micro_model(cls) -> "AgentConfig":
        """Configuração para modelos micro (~500M-1B params).
        
        Otimizado para: Qwen-1.5B, Gemma-2B, etc.
        """
        return cls(
            model_size=ModelSize.MICRO,
            max_tokens=256,
            chunk_size=64,
            overlap=8,
            stream_enabled=True,
            stream_chunk_tokens=16,
            context_compression=True,
            compression_ratio=0.4,
            layers={
                "parse": {"tokens": 16, "priority": 1},
                "classify": {"tokens": 12, "priority": 2},
                "analysis": {"tokens": 32, "priority": 3},
                "plan": {"tokens": 16, "priority": 4},
                "decision": {"tokens": 24, "priority": 5},
                "action": {"tokens": 64, "priority": 6},
                "verify": {"tokens": 16, "priority": 7},
                "validation": {"tokens": 24, "priority": 8}
            }
        )
    
    @classmethod
    def for_tiny_model(cls) -> "AgentConfig":
        """Configuração para modelos tiny (~1B-2B params).
        
        Otimizado para: Llama-3.2-1B, Gemma-2B, etc.
        """
        return cls(
            model_size=ModelSize.TINY,
            max_tokens=512,
            chunk_size=128,
            overlap=16,
            stream_enabled=True,
            stream_chunk_tokens=24,
            context_compression=True,
            compression_ratio=0.5,
            layers={
                "parse": {"tokens": 24, "priority": 1},
                "classify": {"tokens": 16, "priority": 2},
                "analysis": {"tokens": 64, "priority": 3},
                "plan": {"tokens": 24, "priority": 4},
                "decision": {"tokens": 32, "priority": 5},
                "action": {"tokens": 128, "priority": 6},
                "verify": {"tokens": 24, "priority": 7},
                "validation": {"tokens": 32, "priority": 8}
            }
        )
    
    @classmethod
    def for_small_model(cls) -> "AgentConfig":
        """Configuração para modelos pequenos (~3B).
        
        Otimizado para: Llama-3.2-3B, Phi-3-mini, etc.
        """
        return cls(
            model_size=ModelSize.SMALL,
            max_tokens=2048,
            chunk_size=512,
            overlap=64,
            stream_enabled=True,
            stream_chunk_tokens=64,
            context_compression=True,
            compression_ratio=0.6,
            layers={
                "parse": {"tokens": 64, "priority": 1},
                "classify": {"tokens": 32, "priority": 2},
                "analysis": {"tokens": 256, "priority": 3},
                "plan": {"tokens": 64, "priority": 4},
                "decision": {"tokens": 128, "priority": 5},
                "action": {"tokens": 512, "priority": 6},
                "verify": {"tokens": 64, "priority": 7},
                "validation": {"tokens": 128, "priority": 8}
            }
        )
    
    @classmethod
    def for_medium_model(cls) -> "AgentConfig":
        """Configuração para modelos médios (~7B).
        
        Otimizado para: Llama-3.1-8B, Mistral-7B, etc.
        """
        return cls(
            model_size=ModelSize.MEDIUM,
            max_tokens=4096,
            chunk_size=1024,
            overlap=128,
            stream_enabled=True,
            stream_chunk_tokens=128,
            context_compression=False,
            compression_ratio=0.7,
            layers={
                "parse": {"tokens": 128, "priority": 1},
                "classify": {"tokens": 64, "priority": 2},
                "analysis": {"tokens": 512, "priority": 3},
                "plan": {"tokens": 128, "priority": 4},
                "decision": {"tokens": 256, "priority": 5},
                "action": {"tokens": 1024, "priority": 6},
                "verify": {"tokens": 128, "priority": 7},
                "validation": {"tokens": 256, "priority": 8}
            }
        )
    
    @classmethod
    def for_large_model(cls) -> "AgentConfig":
        """Configuração para modelos grandes (~13B+).
        
        Otimizado para: Llama-3.1-70B, Mixtral-8x7B, etc.
        """
        return cls(
            model_size=ModelSize.LARGE,
            max_tokens=8192,
            chunk_size=2048,
            overlap=256,
            stream_enabled=False,
            stream_chunk_tokens=256,
            context_compression=False,
            compression_ratio=1.0,
            layers={
                "parse": {"tokens": 256, "priority": 1},
                "classify": {"tokens": 128, "priority": 2},
                "analysis": {"tokens": 1024, "priority": 3},
                "plan": {"tokens": 256, "priority": 4},
                "decision": {"tokens": 512, "priority": 5},
                "action": {"tokens": 2048, "priority": 6},
                "verify": {"tokens": 256, "priority": 7},
                "validation": {"tokens": 512, "priority": 8}
            }
        )


@dataclass
class TaskChunk:
    """Um chunk de tarefa para processamento."""
    id: str
    content: str
    layer: str
    tokens_estimated: int
    context: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    result: Optional[Any] = None
    processed: bool = False


class TaskChunker:
    """
    Divide tarefas em chunks pequenos para processamento em camadas.
    
    Estratégia de camadas:
    1. ANALYSIS: Entende o problema (tokens mínimos)
    2. DECISION: Decide ação (tokens mínimos)
    3. ACTION: Executa ação (tokens maiores)
    4. VALIDATION: Valida resultado (tokens mínimos)
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._cache: Dict[str, Any] = {}
        self._chunks: List[TaskChunk] = []
    
    def _generate_chunk_id(self, content: str, layer: str) -> str:
        """Gera ID único para um chunk."""
        hash_input = f"{layer}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:8]
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima tokens (~4 chars por token)."""
        return len(text) // 4 + 1
    
    def chunk_text(self, text: str, max_chunk_size: int = None) -> Generator[str, None, None]:
        """
        Divide texto em chunks menores.
        
        Args:
            text: Texto para dividir
            max_chunk_size: Tamanho máximo (usa config se None)
            
        Yields:
            Chunks de texto
        """
        if max_chunk_size is None:
            max_chunk_size = self.config.chunk_size
        
        # Divide por linhas primeiro para preservar estrutura
        lines = text.split('\n')
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_tokens = self._estimate_tokens(line)
            
            if current_size + line_tokens > max_chunk_size and current_chunk:
                yield '\n'.join(current_chunk)
                # Mantém overlap
                overlap_lines = current_chunk[-2:] if len(current_chunk) > 2 else []
                current_chunk = overlap_lines
                current_size = sum(self._estimate_tokens(l) for l in current_chunk)
            
            current_chunk.append(line)
            current_size += line_tokens
        
        if current_chunk:
            yield '\n'.join(current_chunk)
    
    def create_layered_task(self, task_description: str, context: Dict[str, Any] = None) -> List[TaskChunk]:
        """
        Cria tarefa em camadas para processamento incremental.
        
        Args:
            task_description: Descrição da tarefa
            context: Contexto adicional
            
        Returns:
            Lista de TaskChunks ordenados por prioridade
        """
        context = context or {}
        self._chunks = []
        
        # Camada 1: Análise (tokens mínimos)
        analysis_chunk = TaskChunk(
            id=self._generate_chunk_id(task_description, "analysis"),
            content=self._create_analysis_prompt(task_description),
            layer="analysis",
            tokens_estimated=self.config.layers["analysis"]["tokens"],
            context={"original_task": task_description, **context}
        )
        self._chunks.append(analysis_chunk)
        
        # Camada 2: Decisão (depende da análise)
        decision_chunk = TaskChunk(
            id=self._generate_chunk_id(task_description, "decision"),
            content="",  # Preenchido após análise
            layer="decision",
            tokens_estimated=self.config.layers["decision"]["tokens"],
            context=context,
            dependencies=[analysis_chunk.id]
        )
        self._chunks.append(decision_chunk)
        
        # Camada 3: Ação (depende da decisão)
        action_chunk = TaskChunk(
            id=self._generate_chunk_id(task_description, "action"),
            content="",  # Preenchido após decisão
            layer="action",
            tokens_estimated=self.config.layers["action"]["tokens"],
            context=context,
            dependencies=[decision_chunk.id]
        )
        self._chunks.append(action_chunk)
        
        # Camada 4: Validação (depende da ação)
        validation_chunk = TaskChunk(
            id=self._generate_chunk_id(task_description, "validation"),
            content="",  # Preenchido após ação
            layer="validation",
            tokens_estimated=self.config.layers["validation"]["tokens"],
            context=context,
            dependencies=[action_chunk.id]
        )
        self._chunks.append(validation_chunk)
        
        return self._chunks
    
    def _create_analysis_prompt(self, task: str) -> str:
        """Cria prompt curto para análise."""
        return f"""TASK: {task[:200]}
ANALYZE:
1. What is needed?
2. What files/data?
3. What risks?
RESPOND: JSON {{need, files, risks}}"""
    
    def _create_decision_prompt(self, analysis_result: Dict) -> str:
        """Cria prompt curto para decisão."""
        return f"""ANALYSIS: {json.dumps(analysis_result)[:150]}
DECIDE:
1. Action to take?
2. Order of steps?
RESPOND: JSON {{action, steps}}"""
    
    def _create_action_prompt(self, decision_result: Dict, context: Dict) -> str:
        """Cria prompt para execução."""
        return f"""DECISION: {json.dumps(decision_result)[:200]}
CONTEXT: {json.dumps(context)[:150]}
EXECUTE:
- Follow steps exactly
- Output result
RESPOND: JSON {{done, output}}"""
    
    def _create_validation_prompt(self, action_result: Dict) -> str:
        """Cria prompt curto para validação."""
        return f"""RESULT: {json.dumps(action_result)[:200]}
VALIDATE:
1. Success?
2. Errors?
RESPOND: JSON {{valid, errors}}"""
    
    def get_next_chunk(self) -> Optional[TaskChunk]:
        """Retorna próximo chunk a processar."""
        for chunk in self._chunks:
            if chunk.processed:
                continue
            
            # Verifica dependências
            deps_satisfied = all(
                self._get_chunk_by_id(dep_id).processed
                for dep_id in chunk.dependencies
            )
            
            if deps_satisfied:
                return chunk
        
        return None
    
    def _get_chunk_by_id(self, chunk_id: str) -> Optional[TaskChunk]:
        """Busca chunk por ID."""
        for chunk in self._chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def update_chunk(self, chunk_id: str, result: Any) -> None:
        """Atualiza resultado de um chunk."""
        chunk = self._get_chunk_by_id(chunk_id)
        if chunk:
            chunk.result = result
            chunk.processed = True
            
            # Prepara próximo chunk com base no resultado
            self._prepare_next_chunk(chunk)
    
    def _prepare_next_chunk(self, completed_chunk: TaskChunk) -> None:
        """Prepara o próximo chunk baseado no resultado."""
        for chunk in self._chunks:
            if completed_chunk.id in chunk.dependencies and not chunk.processed:
                if chunk.layer == "decision":
                    chunk.content = self._create_decision_prompt(completed_chunk.result)
                elif chunk.layer == "action":
                    chunk.content = self._create_action_prompt(
                        completed_chunk.result,
                        chunk.context
                    )
                elif chunk.layer == "validation":
                    chunk.content = self._create_validation_prompt(completed_chunk.result)
    
    # ========== CACHE ==========
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        if not self.config.cache_enabled:
            return None
        return self._cache.get(key)
    
    def cache_set(self, key: str, value: Any) -> None:
        """Armazena valor no cache."""
        if self.config.cache_enabled:
            self._cache[key] = value
    
    def cache_clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()


class PromptOptimizer:
    """
    Otimiza prompts para modelos pequenos.
    
    Técnicas:
    - Remove redundâncias
    - Usa abreviações
    - Estrutura JSON compacta
    - Limita contexto
    """
    
    # Substituições para encurtar prompts
    ABBREVIATIONS = {
        "function": "fn",
        "parameter": "param",
        "return": "ret",
        "string": "str",
        "number": "num",
        "boolean": "bool",
        "undefined": "undef",
        "configuration": "cfg",
        "directory": "dir",
        "repository": "repo",
        "environment": "env",
        "application": "app",
        "database": "db",
        "timestamp": "ts",
        "message": "msg",
        "response": "resp",
        "request": "req",
    }
    
    @classmethod
    def optimize(cls, prompt: str, max_tokens: int = 512) -> str:
        """
        Otimiza prompt para caber no limite de tokens.
        
        Args:
            prompt: Prompt original
            max_tokens: Limite de tokens
            
        Returns:
            Prompt otimizado
        """
        # Estimativa de tokens
        estimated = len(prompt) // 4
        
        if estimated <= max_tokens:
            return prompt
        
        # Aplica abreviações
        optimized = prompt
        for full, abbr in cls.ABBREVIATIONS.items():
            optimized = optimized.replace(full, abbr)
        
        # Remove espaços extras
        import re
        optimized = re.sub(r'\s+', ' ', optimized)
        optimized = re.sub(r'\n\s*\n', '\n', optimized)
        
        # Trunca se ainda muito grande
        target_chars = max_tokens * 4
        if len(optimized) > target_chars:
            optimized = optimized[:target_chars-20] + "\n[TRUNCATED]"
        
        return optimized.strip()
    
    @classmethod
    def create_minimal_prompt(cls, task: str, context: str = "", max_total: int = 256) -> str:
        """
        Cria prompt mínimo para tarefas simples.
        
        Args:
            task: Descrição da tarefa
            context: Contexto adicional
            max_total: Máximo de tokens total
            
        Returns:
            Prompt mínimo
        """
        # Divide tokens: 60% tarefa, 40% contexto
        task_tokens = int(max_total * 0.6)
        ctx_tokens = int(max_total * 0.4)
        
        task_opt = cls.optimize(task, task_tokens)
        ctx_opt = cls.optimize(context, ctx_tokens) if context else ""
        
        if ctx_opt:
            return f"TASK:{task_opt}\nCTX:{ctx_opt}\nDO:Execute"
        return f"TASK:{task_opt}\nDO:Execute"


class ResultAggregator:
    """
    Agrega resultados de múltiplos chunks/camadas.
    """
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.errors: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def add(self, chunk_id: str, layer: str, result: Any, success: bool = True) -> None:
        """Adiciona resultado de um chunk."""
        self.results.append({
            "chunk_id": chunk_id,
            "layer": layer,
            "result": result,
            "success": success,
            "timestamp": time.time()
        })
        
        if not success and isinstance(result, str):
            self.errors.append(f"[{layer}] {result}")
    
    def get_final_result(self) -> Dict[str, Any]:
        """Retorna resultado final agregado."""
        return {
            "success": len(self.errors) == 0,
            "layers_completed": len([r for r in self.results if r["success"]]),
            "total_layers": len(self.results),
            "errors": self.errors,
            "final_output": self.results[-1]["result"] if self.results else None,
            "metadata": self.metadata
        }
    
    def get_layer_result(self, layer: str) -> Optional[Any]:
        """Obtém resultado de uma camada específica."""
        for r in reversed(self.results):
            if r["layer"] == layer and r["success"]:
                return r["result"]
        return None


# ========== UTILITÁRIOS ==========

def load_agent_config(config_path: str = None) -> AgentConfig:
    """
    Carrega configuração de agente do arquivo ou usa padrão.
    
    Args:
        config_path: Caminho para arquivo de configuração
        
    Returns:
        AgentConfig configurado
    """
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
            
            model_size = ModelSize(data.get("model_size", "small"))
            
            if model_size == ModelSize.TINY:
                return AgentConfig.for_tiny_model()
            elif model_size == ModelSize.MEDIUM:
                return AgentConfig.for_medium_model()
            else:
                return AgentConfig.for_small_model()
        except Exception:
            pass
    
    return AgentConfig.for_small_model()


# ========== EXEMPLO DE USO ==========

if __name__ == "__main__":
    # Exemplo: Configuração para modelo pequeno
    config = AgentConfig.for_small_model()
    print(f"Config: {config.model_size.value}")
    print(f"Max tokens: {config.max_tokens}")
    print(f"Chunk size: {config.chunk_size}")
    print(f"Layers: {list(config.layers.keys())}")
    
    # Exemplo: Chunking de tarefa
    chunker = TaskChunker(config)
    chunks = chunker.create_layered_task(
        "Limpar cache do sistema e gerar relatório",
        context={"os": "linux"}
    )
    
    print(f"\nChunks criados: {len(chunks)}")
    for chunk in chunks:
        print(f"  - {chunk.layer}: {chunk.tokens_estimated} tokens")
    
    # Exemplo: Otimização de prompt
    long_prompt = """
    Analyze the following function and determine if it has any bugs.
    The function should process configuration parameters and return 
    a boolean indicating success or failure. Check for edge cases
    and potential null pointer exceptions.
    """
    
    optimized = PromptOptimizer.optimize(long_prompt, max_tokens=64)
    print(f"\nPrompt original: {len(long_prompt)} chars")
    print(f"Prompt otimizado: {len(optimized)} chars")
    print(f"Conteúdo: {optimized}")
