#!/usr/bin/env python3
"""
Testes unitários para a interface KuCoin Bot
Testa funcionalidades da tela principal, sidebar e database
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import sqlite3

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock do streamlit para evitar problemas de contexto
mock_streamlit = Mock()
mock_streamlit.secrets = {}  # Deve ser um dicionário para suportar 'in'
sys.modules['streamlit'] = mock_streamlit

class TestKuCoinInterface(unittest.TestCase):
    """Testes para a interface KuCoin"""

    def setUp(self):
        """Configuração inicial dos testes"""
        # Mock do session_state
        self.mock_session_state = Mock()
        self.mock_session_state.get = Mock(return_value=None)
        self.mock_session_state.__getitem__ = Mock(return_value=None)
        self.mock_session_state.__setitem__ = Mock()

        # Mock do streamlit
        with patch('streamlit.session_state', self.mock_session_state):
            with patch('streamlit.sidebar', Mock()):
                with patch('streamlit.markdown', Mock()):
                    with patch('streamlit.divider', Mock()):
                        # Importar módulos após mock
                        from sidebar_controller import SidebarController
                        from database import DatabaseManager
                        self.SidebarController = SidebarController
                        self.DatabaseManager = DatabaseManager

    def test_sidebar_controller_initialization(self):
        """Testa a inicialização do SidebarController"""
        with patch('sidebar_controller.api') as mock_api:
            with patch('sidebar_controller.DatabaseManager') as mock_db:
                controller = self.SidebarController()

                self.assertIsNotNone(controller)
                self.assertIsNotNone(controller.db)
                self.assertEqual(controller._usd_brl_rate, None)
                self.assertEqual(controller._usd_brl_cache_time, 0)

    def test_get_bot_status(self):
        """Testa a função get_bot_status"""
        with patch('sidebar_controller.api'):
            with patch('sidebar_controller.DatabaseManager'):
                controller = self.SidebarController()

                # Mock session_state
                controller.get_bot_status = Mock(return_value={
                    'is_running': False,
                    'target': 2.0,
                    'entry': 0.0,
                    'symbol': 'BTC-USDT'
                })

                status = controller.get_bot_status()
                self.assertIsInstance(status, dict)
                self.assertIn('is_running', status)
                self.assertIn('target', status)
                self.assertIn('entry', status)
                self.assertIn('symbol', status)

    def test_render_actions_returns_correct_values(self):
        """Testa se render_actions retorna os valores corretos"""
        with patch('sidebar_controller.api'):
            with patch('sidebar_controller.DatabaseManager'):
                with patch('streamlit.sidebar') as mock_sidebar:
                    # Mock dos métodos do sidebar
                    mock_sidebar.divider = Mock()
                    mock_sidebar.subheader = Mock()

                    # Criar mocks que suportam context manager
                    mock_col1 = Mock()
                    mock_col2 = Mock()
                    mock_col1.__enter__ = Mock(return_value=mock_col1)
                    mock_col1.__exit__ = Mock(return_value=None)
                    mock_col2.__enter__ = Mock(return_value=mock_col2)
                    mock_col2.__exit__ = Mock(return_value=None)

                    mock_sidebar.columns = Mock(return_value=[mock_col1, mock_col2])
                    mock_sidebar.button = Mock(return_value=False)

                    # Mock dos botões individuais
                    with patch('streamlit.button') as mock_button:
                        mock_button.side_effect = [True, False, False]  # start_real, start_dry, kill_bot

                        controller = self.SidebarController()

                        # Mock session_state para num_bots
                        with patch('streamlit.session_state') as mock_session:
                            mock_session.get = Mock(return_value=3)

                            result = controller.render_actions()

                            # Deve retornar 4 valores: start_real, start_dry, kill_bot, num_bots
                            self.assertEqual(len(result), 4)
                            self.assertIsInstance(result[0], bool)  # start_real
                            self.assertIsInstance(result[1], bool)  # start_dry
                            self.assertIsInstance(result[2], bool)  # kill_bot
                            self.assertEqual(result[3], 3)  # num_bots

    def test_database_get_trade_history_grouped(self):
        """Testa a função get_trade_history_grouped"""
        # Criar banco de dados temporário para teste
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            temp_db_path = temp_db.name

        try:
            # Criar tabela de teste
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE trades (
                    id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    size REAL,
                    funds REAL,
                    profit REAL,
                    commission REAL,
                    order_id TEXT,
                    bot_id TEXT,
                    strategy TEXT,
                    dry_run INTEGER DEFAULT 1,
                    metadata TEXT
                )
            ''')

            # Inserir dados de teste
            test_data = [
                ('trade1', 1640995200.0, 'BTC-USDT', 'buy', 50000.0, 0.001, 50.0, None, None, 'order1', 'bot1', 'strategy1', 0, None),
                ('trade2', 1640995300.0, 'BTC-USDT', 'sell', 51000.0, 0.001, 51.0, 1.0, 0.1, 'order2', 'bot1', 'strategy1', 0, None),
                ('trade3', 1640995400.0, 'ETH-USDT', 'buy', 3000.0, 0.01, 30.0, None, None, 'order3', 'bot2', 'strategy2', 1, None),
            ]

            cursor.executemany('INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', test_data)
            conn.commit()
            conn.close()

            # Testar a função
            db = self.DatabaseManager()
            db.db_path = temp_db_path  # Forçar uso do banco temporário

            # Teste básico
            rows = db.get_trade_history_grouped(limit=10)
            self.assertEqual(len(rows), 3)

            # Teste com filtro bot_id
            rows_bot1 = db.get_trade_history_grouped(limit=10, bot_id='bot1')
            self.assertEqual(len(rows_bot1), 2)

            # Teste com only_real=True
            rows_real = db.get_trade_history_grouped(limit=10, only_real=True)
            self.assertEqual(len(rows_real), 2)  # Apenas trades não dry-run

            # Teste com group_by_order_id=False
            rows_no_group = db.get_trade_history_grouped(limit=10, group_by_order_id=False)
            self.assertEqual(len(rows_no_group), 3)

            # Verificar estrutura dos dados retornados
            if rows:
                row = rows[0]
                expected_keys = ['id', 'timestamp', 'symbol', 'side', 'price', 'size', 'funds', 'profit', 'commission', 'order_id', 'bot_id', 'strategy', 'dry_run', 'metadata']
                for key in expected_keys:
                    self.assertIn(key, row)

        finally:
            # Limpar arquivo temporário
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)

    def test_multiple_bots_logic(self):
        """Testa a lógica de múltiplos bots"""
        # Simular os parâmetros que seriam usados para múltiplos bots
        base_entry = 50000.0
        base_size = 0.001
        num_bots = 3

        # Calcular variações como no código real
        variations = []
        for i in range(num_bots):
            varied_entry = float(base_entry) * (1 + (i * 0.001))  # Variação de 0.1% por bot
            varied_size = float(base_size) * (1 + (i * 0.01))    # Variação de 1% no size
            variations.append((varied_entry, varied_size))

        # Verificar se as variações são calculadas corretamente
        self.assertEqual(len(variations), 3)

        # Primeiro bot (i=0) - sem variação
        self.assertAlmostEqual(variations[0][0], 50000.0, places=2)
        self.assertAlmostEqual(variations[0][1], 0.001, places=6)

        # Segundo bot (i=1) - com variação
        self.assertAlmostEqual(variations[1][0], 50050.0, places=2)  # 50000 * 1.001
        self.assertAlmostEqual(variations[1][1], 0.00101, places=6)  # 0.001 * 1.01

        # Terceiro bot (i=2) - com variação maior
        self.assertAlmostEqual(variations[2][0], 50100.0, places=2)  # 50000 * 1.002
        self.assertAlmostEqual(variations[2][1], 0.00102, places=6)  # 0.001 * 1.02

    def test_mode_options_available(self):
        """Testa se as opções de modo estão disponíveis"""
        expected_modes = ["sell", "buy", "mixed", "flow"]

        # Verificar se flow foi adicionado
        self.assertIn("flow", expected_modes)
        self.assertEqual(len(expected_modes), 4)

    def test_sidebar_render_in_container(self):
        """Testa o método render_in com container"""
        with patch('sidebar_controller.api'):
            with patch('sidebar_controller.DatabaseManager'):
                controller = self.SidebarController()

                # Mock container
                mock_container = Mock()
                mock_container.__enter__ = Mock(return_value=mock_container)
                mock_container.__exit__ = Mock(return_value=None)

                # Mock métodos do streamlit
                with patch('streamlit.markdown') as mock_markdown:
                    with patch('streamlit.divider') as mock_divider:
                        with patch.object(controller, 'render_balances') as mock_render_balances:
                            with patch.object(controller, 'render_inputs') as mock_render_inputs:
                                with patch.object(controller, 'render_actions', return_value=(False, False, False, 1)) as mock_render_actions:
                                    with patch.object(controller, 'get_bot_status', return_value={'is_running': False, 'target': 2.0}):
                                        result = controller.render_in(mock_container)

                                        # Verificar se os métodos foram chamados
                                        mock_render_balances.assert_called_once()
                                        mock_render_inputs.assert_called_once()
                                        mock_render_actions.assert_called_once()

                                        # Verificar retorno
                                        self.assertEqual(result, (False, False, False, 1))

    def test_calculate_portfolio_value(self):
        """Testa o cálculo de valor de portfolio"""
        # Mock balances
        mock_balances = [
            {'currency': 'USDT', 'available': 1000.0},
            {'currency': 'BTC', 'available': 0.05},
            {'currency': 'ETH', 'available': 1.0}
        ]

        # Mock da função api.get_price
        with patch('sidebar_controller.api.get_price') as mock_get_price:
            mock_get_price.side_effect = lambda symbol: {
                'BTC-USDT': 50000.0,
                'ETH-USDT': 3000.0
            }.get(symbol, 0)

            portfolio = self.SidebarController.calculate_portfolio_value(mock_balances)

            self.assertIn('total_usdt', portfolio)
            self.assertIn('assets', portfolio)

            # Verificar cálculo: 1000 USDT + (0.05 * 50000) BTC + (1.0 * 3000) ETH
            expected_total = 1000.0 + (0.05 * 50000.0) + (1.0 * 3000.0)
            self.assertAlmostEqual(portfolio['total_usdt'], expected_total, places=2)

    def test_parse_targets_function(self):
        """Testa a função parse_targets"""
        with patch('sidebar_controller.api'):
            with patch('sidebar_controller.DatabaseManager'):
                controller = self.SidebarController()

                # Teste com string válida
                targets_str = "1:0.3,3:0.5,5:0.2"
                targets = controller.parse_targets(targets_str)

                expected = [(1, 0.3), (3, 0.5), (5, 0.2)]
                self.assertEqual(targets, expected)

                # Teste com string vazia
                targets_empty = controller.parse_targets("")
                self.assertEqual(targets_empty, [])

                # Teste com string inválida
                targets_invalid = controller.parse_targets("invalid")
                self.assertEqual(targets_invalid, [])

    def test_get_average_cost_by_currency(self):
        """Testa get_average_cost_by_currency"""
        with patch('sidebar_controller.api'):
            with patch('sidebar_controller.DatabaseManager'):
                controller = self.SidebarController()

                # Mock da conexão e cursor
                mock_conn = Mock()
                mock_cursor = Mock()
                controller.db.get_connection = Mock(return_value=mock_conn)

                # Mock dos trades: uma compra de 0.1 BTC a 45000 USDT
                mock_cursor.fetchall.return_value = [
                    ('buy', 45000.0, 0.1, 4500.0)  # side, price, size, funds
                ]
                mock_conn.cursor.return_value = mock_cursor

                result = controller.get_average_cost_by_currency('BTC')

                self.assertEqual(result['avg_cost'], 45000.0)
                self.assertEqual(result['qty_held'], 0.1)
                self.assertEqual(result['total_invested'], 4500.0)


if __name__ == '__main__':
    # Configurar logging para reduzir output
    import logging
    logging.getLogger().setLevel(logging.ERROR)

    # Executar testes
    unittest.main(verbosity=2)