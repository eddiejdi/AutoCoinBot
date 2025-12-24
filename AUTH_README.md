# Sistema de Login - KuCoin PRO

## Visão Geral
Este projeto agora inclui um sistema de autenticação básico para proteger o acesso à aplicação Streamlit.

## Configuração da Autenticação

### Método 1: Usando Variáveis de Ambiente (Recomendado)
Configure as credenciais através de variáveis de ambiente:

```bash
export KUCOIN_USER="seu_usuario"
export KUCOIN_PASS="sua_senha"
```

### Método 2: Editando o Código (Não Recomendado)
Edite o arquivo `auth_config.py` e altere as constantes:
```python
USUARIO_PADRAO = "seu_usuario"
SENHA_HASH_PADRAO = hashlib.sha256("sua_senha".encode()).hexdigest()
```

## Como Usar

1. **Login**: Ao acessar a aplicação, você verá uma tela de login
2. **Credenciais**: Use o usuário e senha configurados
3. **Logout**: Clique no botão "🚪 Logout" no topo direito da barra de navegação

## Segurança

- As senhas são armazenadas como hash SHA-256
- O estado de login é mantido na sessão do Streamlit
- Recomenda-se usar HTTPS em produção
- Para maior segurança, considere implementar OAuth ou integração com provedores de identidade

## Desenvolvimento

Para desenvolvimento local, você pode definir as variáveis de ambiente no arquivo `.env`:

```
KUCOIN_USER=admin
KUCOIN_PASS=minha_senha_segura
```

## Troubleshooting

- **Erro de login**: Verifique se as credenciais estão corretas
- **Sessão expirada**: Feche e reabra o navegador
- **Problemas com variáveis de ambiente**: Certifique-se de que estão definidas antes de iniciar a aplicação