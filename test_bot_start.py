#!/usr/bin/env python3
"""
Script para testar o start dos bots via frontend (simulação)
Testa os cenários dry-run e real diretamente nos módulos
"""

import sys
import os
import time

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock do streamlit para evitar problemas
sys.modules['streamlit'] = type('MockStreamlit', (), {
    'session_state': type('MockSessionState', (), {
        'get': lambda key, default=None: {
            'symbol': 'BTC-USDT',
            'entry': 0.0,
            'mode': 'sell',
            'targets': '1:0.3,3:0.5,5:0.2',
            'interval': 5.0,
            'size': 0.0006,
            'funds': 20.0,
            'reserve_pct': 50.0,
            'eternal_mode': False,
            'num_bots': 1
        }.get(key, default),
        'active_bots': []
    })(),
    'sidebar': type('MockSidebar', (), {})(),
    'columns': lambda *args: [type('MockCol', (), {'__enter__': lambda self: self, '__exit__': lambda self, *args: None})() for _ in range(args[0] if args else 2)],
    'button': lambda *args, **kwargs: False,
    'divider': lambda: None,
    'subheader': lambda *args: None
})()

def test_start_bot_dry_run():
    """Testa o start de bot em modo dry-run"""
    print("\n🧪 TESTANDO START BOT - DRY RUN")
    print("=" * 50)

    try:
        from bot_controller import BotController

        # Criar controller
        controller = BotController()
        print("✅ Controller criado")

        # Parâmetros de teste
        symbol = "BTC-USDT"
        entry = 0.0
        mode = "sell"
        targets = "1:0.3,3:0.5,5:0.2"
        interval = 5.0
        size = 0.0006
        funds = 20.0
        dry_run = True  # DRY RUN
        eternal_mode = False

        print(f"📊 Parâmetros: symbol={symbol}, entry={entry}, mode={mode}")
        print(f"📊 dry_run={dry_run}, eternal_mode={eternal_mode}")

        # Iniciar bot
        print("🚀 Iniciando bot...")
        bot_id = controller.start_bot(
            symbol, entry, mode, targets,
            interval, size, funds, dry_run,
            eternal_mode=eternal_mode
        )

        if bot_id:
            print(f"✅ Bot iniciado com sucesso! ID: {bot_id}")
            print("✅ Modo: DRY RUN (simulação)")

            # Verificar se o bot está rodando
            time.sleep(2)
            is_running = controller.is_running(bot_id)
            if is_running:
                print(f"📊 Status do bot: ATIVO (PID: {controller.processes.get(bot_id).pid if controller.processes.get(bot_id) else 'N/A'})")
            else:
                print("⚠️  Bot não está rodando")

            return True
        else:
            print("❌ Falha ao iniciar bot")
            return False

    except Exception as e:
        print(f"❌ Erro durante teste dry-run: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_start_bot_real():
    """Testa o start de bot em modo real"""
    print("\n💰 TESTANDO START BOT - REAL MODE")
    print("=" * 50)

    try:
        from bot_controller import BotController

        # Criar controller
        controller = BotController()
        print("✅ Controller criado")

        # Parâmetros de teste
        symbol = "BTC-USDT"
        entry = 0.0
        mode = "sell"
        targets = "1:0.3,3:0.5,5:0.2"
        interval = 5.0
        size = 0.0006
        funds = 20.0
        dry_run = False  # REAL MODE
        eternal_mode = False

        print(f"📊 Parâmetros: symbol={symbol}, entry={entry}, mode={mode}")
        print(f"📊 dry_run={dry_run}, eternal_mode={eternal_mode}")

        # AVISO IMPORTANTE
        print("⚠️  ATENÇÃO: Este teste irá iniciar um bot em MODO REAL!")
        print("⚠️  Isso pode resultar em trades reais na KuCoin!")
        print("💡 Recomendação: Use apenas para testar a funcionalidade, com fundos mínimos")

        # Verificar se devemos continuar
        import os
        auto_confirm = os.getenv('AUTO_CONFIRM_REAL_TEST', '').lower() == 'true'

        if not auto_confirm:
            try:
                resposta = input("Deseja continuar? (digite 'SIM' para confirmar ou pressione Enter para pular): ").strip()
                if resposta.upper() != 'SIM':
                    print("❌ Teste real cancelado pelo usuário")
                    return None
            except EOFError:
                # Se não há input interativo (como em CI/CD), pular
                print("⏭️  Ambiente não-interativo detectado, pulando teste real")
                return None

        # Iniciar bot
        print("🚀 Iniciando bot REAL...")
        bot_id = controller.start_bot(
            symbol, entry, mode, targets,
            interval, size, funds, dry_run,
            eternal_mode=eternal_mode
        )

        if bot_id:
            print(f"✅ Bot REAL iniciado com sucesso! ID: {bot_id}")
            print("🚨 ATENÇÃO: Bot rodando em modo REAL - monitorar trades!")

            # Verificar se o bot está rodando
            time.sleep(2)
            is_running = controller.is_running(bot_id)
            if is_running:
                print(f"📊 Status do bot: ATIVO (PID: {controller.processes.get(bot_id).pid if controller.processes.get(bot_id) else 'N/A'})")
            else:
                print("⚠️  Bot não está rodando")

            return True
        else:
            print("❌ Falha ao iniciar bot real")
            return False

    except Exception as e:
        print(f"❌ Erro durante teste real: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_bots():
    """Para todos os bots de teste"""
    print("\n🧹 LIMPANDO BOTS DE TESTE")
    print("=" * 30)

    try:
        from bot_controller import BotController
        controller = BotController()

        # Parar bots que começam com "bot_"
        bots_to_stop = [bot_id for bot_id in controller.processes.keys() if bot_id.startswith("bot_")]
        for bot_id in bots_to_stop:
            print(f"Parando bot: {bot_id}")
            controller.stop_bot(bot_id)

        if bots_to_stop:
            print(f"✅ {len(bots_to_stop)} bot(s) parado(s)")
        else:
            print("ℹ️  Nenhum bot de teste encontrado para parar")
    except Exception as e:
        print(f"❌ Erro ao limpar bots: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DE START DOS BOTS")
    print("=" * 60)

    # Teste 1: Dry Run
    dry_success = test_start_bot_dry_run()

    # Aguardar um pouco
    time.sleep(3)

    # Teste 2: Real Mode (com confirmação de segurança)
    real_success = test_start_bot_real()

    # Resultados
    print("\n📊 RESULTADOS DOS TESTES")
    print("=" * 40)
    print(f"🧪 Dry Run: {'✅ PASSOU' if dry_success else '❌ FALHOU'}")
    if real_success is None:
        print("💰 Real Mode: ⏭️  PULADO (segurança)")
    else:
        print(f"💰 Real Mode: {'✅ PASSOU' if real_success else '❌ FALHOU'}")

    if dry_success or (real_success is not None and real_success):
        print("\n🧹 Limpando bots de teste...")
        cleanup_test_bots()

    print("\n🎯 TESTES CONCLUÍDOS!")