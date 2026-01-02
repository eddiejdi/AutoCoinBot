"""
Agente Dev Sênior - AutoCoinBot

Agente padrão para levantamento de requisitos, análise, autoaprendizagem e suporte ao desenvolvimento.
Especialista em Python, Streamlit e PostgreSQL.

- Obtém especificações do usuário
- Segue padrões de desenvolvimento do projeto
- Realiza levantamento de requisitos
- Aprende com histórico e feedback
- Sugere melhorias e automatiza tarefas

Uso:
    from agent_dev_sr import DevSeniorAgent
    agent = DevSeniorAgent()
    agent.iniciar_fluxo()
"""

import os
import json

class DevSeniorAgent:
    """
    Agente padrão para AutoCoinBot: levantamento de requisitos, análise, autoaprendizagem e suporte ao desenvolvimento.
    """
    def __init__(self, user_spec_path='user_spec.json', history_path='dev_history.json'):
        self.user_spec_path = user_spec_path
        self.history_path = history_path
        self.spec = self._carregar_especificacoes()
        self.history = self._carregar_historico()

    def _carregar_especificacoes(self):
        if os.path.exists(self.user_spec_path):
            with open(self.user_spec_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _carregar_historico(self):
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def obter_especificacoes(self):
        """Obtém as especificações do usuário."""
        return self.spec

    def seguir_padroes(self):
        """Segue os padrões de desenvolvimento definidos no projeto."""
        # Exemplo: pode ler copilot-instructions.md ou outros padrões
        padroes = []
        if os.path.exists('.github/copilot-instructions.md'):
            with open('.github/copilot-instructions.md', 'r', encoding='utf-8') as f:
                padroes = f.readlines()
        return padroes

    def levantar_requisitos(self):
        """Levanta requisitos a partir das especificações e histórico."""
        requisitos = []
        if self.spec:
            for k, v in self.spec.items():
                requisitos.append(f"{k}: {v}")
        return requisitos

    def aprender_com_feedback(self, feedback):
        """Atualiza histórico de aprendizagem com feedback do usuário."""
        self.history['feedback'] = self.history.get('feedback', []) + [feedback]
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def sugerir_melhorias(self):
        """Sugere melhorias com base no histórico e padrões."""
        melhorias = []
        if self.history.get('feedback'):
            melhorias.append('Ajustar pontos levantados em feedbacks anteriores.')
        melhorias.append('Revisar código para aderência aos padrões.')
        return melhorias

    def iniciar_fluxo(self):
        """Fluxo principal do agente: obtém specs, levanta requisitos, sugere melhorias."""
        print('=== Agente Dev Sênior - AutoCoinBot ===')
        print('Especificações do usuário:')
        print(self.obter_especificacoes())
        print('\nPadrões de desenvolvimento:')
        for linha in self.seguir_padroes()[:10]:
            print(linha.strip())
        print('\nRequisitos levantados:')
        for req in self.levantar_requisitos():
            print(f'- {req}')
        print('\nSugestões de melhoria:')
        for m in self.sugerir_melhorias():
            print(f'- {m}')
        print('========================================')

# Exemplo de uso direto
if __name__ == '__main__':
    agent = DevSeniorAgent()
    agent.iniciar_fluxo()
