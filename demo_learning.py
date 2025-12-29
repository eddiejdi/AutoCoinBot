#!/usr/bin/env python3
"""
Demonstração do Sistema de Aprendizado Multi-Armed Bandit
do AutoCoinBot

Este script mostra como o bot aprende com trades anteriores
para otimizar parâmetros automaticamente.
"""

import time
import random
from database import DatabaseManager

def demo_bandit_learning():
    """Demonstra o aprendizado do bandit"""
    print("🤖 AutoCoinBot - Demonstração do Sistema de Aprendizado")
    print("=" * 60)

    db = DatabaseManager()

    # Parâmetros para teste
    symbol = "BTCUSDT"
    param_name = "take_profit_trailing_pct"
    candidates = [0.5, 1.0, 2.0, 5.0]  # diferentes percentuais de trailing

    print(f"Símbolo: {symbol}")
    print(f"Parâmetro: {param_name}")
    print(f"Candidatos: {candidates}")
    print()

    # Simula alguns trades com diferentes parâmetros
    print("📊 Simulando trades e aprendizado...")
    print()

    # Simulação de trades
    simulated_trades = [
        (0.5, 2.1),   # 0.5% trailing, profit 2.1%
        (0.5, -1.5),  # 0.5% trailing, loss -1.5%
        (1.0, 5.2),   # 1.0% trailing, profit 5.2%
        (1.0, 3.8),   # 1.0% trailing, profit 3.8%
        (2.0, 1.2),   # 2.0% trailing, profit 1.2%
        (2.0, -2.1),  # 2.0% trailing, loss -2.1%
        (5.0, 0.5),   # 5.0% trailing, small profit 0.5%
    ]

    for i, (param_value, reward) in enumerate(simulated_trades, 1):
        success = db.update_bandit_reward(symbol, param_name, param_value, reward)
        print(f"Trade {i}: {param_name}={param_value} → Reward: {reward:+.1f}% {'✅' if success else '❌'}")

        # Mostra escolha atual (com exploração)
        choice = db.choose_bandit_param(symbol, param_name, candidates, epsilon=0.2)
        print(f"  Escolha atual (ε=0.2): {choice}")
        print()

    print("📈 Estatísticas Finais de Aprendizado:")
    print("-" * 40)

    stats = db.get_learning_stats(symbol, param_name)
    for stat in sorted(stats, key=lambda x: x['mean_reward'], reverse=True):
        print(".1f"
              f"n={stat['n']}")

    print()
    print("🎯 Escolha Ótima (Greedy, ε=0):")
    best_choice = db.choose_bandit_param(symbol, param_name, candidates, epsilon=0.0)
    print(f"Parâmetro recomendado: {param_name} = {best_choice}")

    print()
    print("📊 Histórico de Recompensas:")
    print("-" * 30)

    history = db.get_learning_history(symbol, param_name, limit=10)
    for entry in history[-5:]:  # últimos 5
        print(".1f")

    print()
    print("✅ Demonstração concluída!")
    print("O bot agora aprenderá automaticamente com trades reais.")

if __name__ == "__main__":
    demo_bandit_learning()