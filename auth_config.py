# auth_config.py - Configurações de autenticação
import os
import hashlib

# Credenciais padrão (ALTERE ISTO!)
USUARIO_PADRAO = os.getenv("KUCOIN_USER", "admin")
SENHA_HASH_PADRAO = hashlib.sha256(os.getenv("KUCOIN_PASS", "senha123").encode()).hexdigest()

# Função para verificar credenciais
def verificar_credenciais(usuario, senha):
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    return usuario == USUARIO_PADRAO and senha_hash == SENHA_HASH_PADRAO

# Função para alterar senha (opcional)
def alterar_senha(nova_senha):
    global SENHA_HASH_PADRAO
    SENHA_HASH_PADRAO = hashlib.sha256(nova_senha.encode()).hexdigest()
    return True