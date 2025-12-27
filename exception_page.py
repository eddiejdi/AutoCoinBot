import streamlit as st
import traceback

def render_exception_page(exc: Exception, context: str = None):
    """
    Renderiza uma página de erro amigável exibindo o traceback completo em um textbox copiável.
    Args:
        exc (Exception): Exceção capturada.
        context (str, opcional): Contexto ou mensagem adicional.
    """
    st.error('Ocorreu um erro inesperado.')
    if context:
        st.warning(f'Contexto: {context}')
    tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    st.text_area('Detalhes do erro (copiável):', tb_str, height=350)
    st.info('Copie o conteúdo acima e envie para o suporte, se necessário.')
