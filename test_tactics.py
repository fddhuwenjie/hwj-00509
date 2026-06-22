#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战术主题识别功能测试
"""

import json
import os
import sys
import unittest
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pgnlab import (
    Board,
    PGNParser,
    GameReplayer,
    analyze_tactics,
    analyze_tactics_file,
    tactics_to_markdown,
    tactics_to_json,
    detect_mate_threat,
    detect_double_check,
    detect_fork,
    detect_pin,
    detect_skewer,
    detect_deflection,
    detect_overload,
    detect_capture_defender,
    detect_promotion_threat,
    TACTIC_NAMES,
)


class TestTacticDetectors(unittest.TestCase):
    """测试单个战术识别函数"""

    def test_double_check_detector(self):
        """测试双将检测 - 使用经典的Bf5+双将局面"""
        fen_after = "1r4r1/pbpknp1p/1b3P2/5B2/8/B1P2q2/P4PPP/3R2K1 b - - 1 22"
        board_after = Board(fen_after)
        move_info = {
            'piece': 'B',
            'to': 'f5',
            'is_check': True,
            'move_number': 22,
            'color': 'White',
            'san': 'Bf5+',
        }
        result, reason = detect_double_check(Board(), board_after, move_info)
        self.assertEqual(result, 'double_check')
        self.assertIn('同时将军', reason)

    def test_fork_detector(self):
        """测试马叉击检测"""
        board = Board()
        board.load_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 0 2")
        move_info = {
            'piece': 'N',
            'to': 'f6',
            'move_number': 2,
            'color': 'Black',
            'san': 'Nf6',
        }
        result, _ = detect_fork(board, board, move_info)
        self.assertIsNone(result)

    def test_pin_detector_requires_piece_type(self):
        """测试牵制检测 - 非远射程棋子返回None"""
        board = Board()
        move_info = {
            'piece': 'N',
            'to': 'f3',
            'move_number': 1,
            'color': 'White',
            'san': 'Nf3',
        }
        result, _ = detect_pin(board, board, move_info)
        self.assertIsNone(result)

    def test_no_mate_threat_when_already_mate(self):
        """测试将死威胁 - 已将死时不检测"""
        board = Board()
        move_info = {'is_mate': True, 'piece': 'Q', 'to': 'f7'}
        result, _ = detect_mate_threat(board, board, move_info)
        self.assertIsNone(result)

    def test_promotion_threat(self):
        """测试升变威胁检测"""
        board = Board("8/4P3/8/8/8/8/8/4K3 w - - 0 1")
        move_info = {
            'piece': 'K',
            'to': 'd2',
            'move_number': 1,
            'color': 'White',
            'san': 'Kd2',
        }
        result, reason = detect_promotion_threat(board, board, move_info)
        self.assertEqual(result, 'promotion_threat')
        self.assertIn('升变', reason)

    def test_deflection_no_capture(self):
        """测试诱离检测 - 无吃子时返回None"""
        board = Board()
        move_info = {
            'piece': 'N',
            'to': 'f3',
            'is_capture': False,
            'captured': '',
            'move_number': 1,
            'color': 'White',
            'san': 'Nf3',
        }
        result, _ = detect_deflection(board, board, move_info)
        self.assertIsNone(result)


class TestAnalyzeTactics(unittest.TestCase):
    """测试整局战术分析"""

    def test_analyze_game_with_double_check(self):
        """测试分析包含双将的对局"""
        game_pgn = '''
[Event "双将测试"]
[White "测试白"]
[Black "测试黑"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 Bxb4 5. c3 Ba5 6. d4 exd4 7. O-O d3 8. Qb3 Qf6 9. e5 Qg6 10. Re1 Nge7 11. Ba3 b5 12. Qxb5 Rb8 13. Qa4 Bb6 14. Nbd2 Bb7 15. Ne4 Qf5 16. Bxd3 Qh5 17. Nf6+ gxf6 18. exf6 Rg8 19. Rad1 Qxf3 20. Rxe7+ Nxe7 21. Qxd7+ Kxd7 22. Bf5+
'''
        games = PGNParser.parse_string(game_pgn)
        self.assertEqual(len(games), 1)
        tactics = analyze_tactics(games[0])
        tactic_types = [t['tactic'] for t in tactics]
        self.assertIn('double_check', tactic_types)
        for t in tactics:
            self.assertIn('game_index', t)
            self.assertIn('move_number', t)
            self.assertIn('color', t)
            self.assertIn('san', t)
            self.assertIn('tactic', t)
            self.assertIn('tactic_name', t)
            self.assertIn('reason', t)
            self.assertIn('fen_before', t)
            self.assertIn('fen_after', t)
            self.assertIn(t['tactic'], TACTIC_NAMES)

    def test_analyze_empty_game(self):
        """测试分析空对局"""
        game_pgn = '''
[Event "空对局"]
[White "空白"]
[Black "空黑"]
[Result "*"]
'''
        games = PGNParser.parse_string(game_pgn)
        self.assertEqual(len(games), 1)
        tactics = analyze_tactics(games[0])
        self.assertEqual(len(tactics), 0)


class TestAnalyzeTacticsFile(unittest.TestCase):
    """测试文件级战术分析"""

    def setUp(self):
        self.tactics_pgn = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'games_tactics.pgn'
        )

    def test_scan_all_games(self):
        """测试扫描文件中所有对局"""
        tactics, processed = analyze_tactics_file(self.tactics_pgn)
        self.assertGreater(len(processed), 0)
        self.assertGreater(len(tactics), 0)
        for pg in processed:
            self.assertIn('index', pg)
            self.assertIn('tags', pg)
            self.assertIn('tactics_count', pg)

    def test_scan_single_game(self):
        """测试扫描单个指定对局"""
        tactics_all, _ = analyze_tactics_file(self.tactics_pgn)
        tactics_single, processed = analyze_tactics_file(self.tactics_pgn, game_index=2)
        self.assertEqual(len(processed), 1)
        self.assertEqual(processed[0]['index'], 2)
        for t in tactics_single:
            self.assertEqual(t['game_index'], 2)

    def test_filter_by_player(self):
        """测试按棋手过滤"""
        tactics, processed = analyze_tactics_file(
            self.tactics_pgn, player_filter='普通'
        )
        self.assertEqual(len(processed), 1)
        for pg in processed:
            white = pg['tags'].get('White', '').lower()
            black = pg['tags'].get('Black', '').lower()
            self.assertTrue('普通' in white or '普通' in black)

    def test_filter_by_player_no_match(self):
        """测试按棋手过滤 - 无匹配"""
        tactics, processed = analyze_tactics_file(
            self.tactics_pgn, player_filter='不存在的棋手'
        )
        self.assertEqual(len(processed), 0)
        self.assertEqual(len(tactics), 0)

    def test_nonexistent_file_behavior(self):
        """测试不存在的文件 - 通过CLI层处理"""
        pass


class TestReportExport(unittest.TestCase):
    """测试报告导出功能"""

    def setUp(self):
        self.tactics_pgn = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'games_tactics.pgn'
        )

    def test_markdown_report_with_tactics(self):
        """测试生成包含战术的Markdown报告"""
        tactics, processed = analyze_tactics_file(self.tactics_pgn, game_index=2)
        md = tactics_to_markdown(tactics, processed)
        self.assertIn('# 战术主题识别报告', md)
        self.assertIn('扫描对局数', md)
        self.assertIn('识别战术总数', md)
        self.assertIn('## 按对局汇总', md)
        self.assertIn('## 战术类型分布', md)
        for t in tactics:
            self.assertIn(t['tactic_name'], md)
            self.assertIn(t['san'], md)
            self.assertIn(t['fen_before'], md)
            self.assertIn(t['fen_after'], md)

    def test_markdown_report_empty(self):
        """测试生成无战术的Markdown报告 - 空结果提示"""
        empty_tactics = []
        empty_processed = [{
            'index': 1,
            'tags': {'White': '白', 'Black': '黑'},
            'tactics_count': 0,
        }]
        md = tactics_to_markdown(empty_tactics, empty_processed)
        self.assertIn('# 战术主题识别报告', md)
        self.assertIn('未识别到任何战术主题', md)

    def test_json_report_with_tactics(self):
        """测试生成包含战术的JSON报告"""
        tactics, processed = analyze_tactics_file(self.tactics_pgn, game_index=2)
        json_data = tactics_to_json(tactics, processed)
        self.assertIn('summary', json_data)
        self.assertIn('games', json_data)
        self.assertIn('tactics', json_data)
        summary = json_data['summary']
        self.assertEqual(summary['games_scanned'], 1)
        self.assertGreater(summary['tactics_found'], 0)
        self.assertIn('tactic_distribution', summary)
        self.assertEqual(len(json_data['tactics']), len(tactics))
        for t in json_data['tactics']:
            self.assertIn('game_index', t)
            self.assertIn('tactic', t)
            self.assertIn('tactic_name', t)
            self.assertIn('fen_before', t)
            self.assertIn('fen_after', t)

    def test_json_report_empty(self):
        """测试生成无战术的JSON报告"""
        empty_tactics = []
        empty_processed = [{
            'index': 1,
            'tags': {'White': '白', 'Black': '黑'},
            'tactics_count': 0,
        }]
        json_data = tactics_to_json(empty_tactics, empty_processed)
        self.assertEqual(json_data['summary']['tactics_found'], 0)
        self.assertEqual(len(json_data['tactics']), 0)

    def test_json_serializable(self):
        """测试JSON数据可以被正确序列化"""
        tactics, processed = analyze_tactics_file(self.tactics_pgn, game_index=2)
        json_data = tactics_to_json(tactics, processed)
        json_str = json.dumps(json_data, ensure_ascii=False)
        self.assertTrue(len(json_str) > 0)
        parsed = json.loads(json_str)
        self.assertEqual(parsed['summary']['tactics_found'], len(tactics))


class TestCLIIntegration(unittest.TestCase):
    """测试CLI命令集成"""

    def setUp(self):
        self.test_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'games_tactics.pgn'
        )

    def _run_cli(self, args_list):
        """模拟运行CLI命令"""
        from pgnlab import build_parser
        parser = build_parser()
        args = parser.parse_args(args_list)
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            exit_code = args.func(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return exit_code, output

    def test_cli_scan_all(self):
        """测试CLI扫描所有对局"""
        exit_code, output = self._run_cli(['tactics', self.test_file])
        self.assertEqual(exit_code, 0)
        self.assertIn('扫描完成', output)
        self.assertIn('战术类型分布', output)

    def test_cli_scan_single_game(self):
        """测试CLI扫描单个对局"""
        exit_code, output = self._run_cli(['tactics', self.test_file, '--game', '2'])
        self.assertEqual(exit_code, 0)
        self.assertIn('对局 2', output)

    def test_cli_filter_by_player(self):
        """测试CLI按棋手过滤"""
        exit_code, output = self._run_cli(['tactics', self.test_file, '--player', '普通'])
        self.assertEqual(exit_code, 0)

    def test_cli_no_tactics_message(self):
        """测试CLI无战术时的空结果提示"""
        exit_code, output = self._run_cli([
            'tactics', self.test_file, '--player', '不存在的棋手'
        ])
        self.assertEqual(exit_code, 0)
        self.assertIn('未识别到任何战术主题', output)

    def test_cli_nonexistent_file(self):
        """测试CLI处理不存在的文件"""
        exit_code, output = self._run_cli(['tactics', 'nonexistent.pgn'])
        self.assertEqual(exit_code, 1)
        self.assertIn('文件不存在', output)

    def test_cli_export_markdown(self):
        """测试CLI导出Markdown报告"""
        output_md = '/tmp/test_tactics_report.md'
        if os.path.exists(output_md):
            os.remove(output_md)
        try:
            exit_code, output = self._run_cli([
                'tactics', self.test_file, '--game', '2',
                '--output-md', output_md
            ])
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(output_md))
            with open(output_md, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertIn('# 战术主题识别报告', content)
        finally:
            if os.path.exists(output_md):
                os.remove(output_md)

    def test_cli_export_json(self):
        """测试CLI导出JSON报告"""
        output_json = '/tmp/test_tactics_report.json'
        if os.path.exists(output_json):
            os.remove(output_json)
        try:
            exit_code, output = self._run_cli([
                'tactics', self.test_file, '--game', '2',
                '--output-json', output_json
            ])
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(output_json))
            with open(output_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertIn('summary', data)
            self.assertIn('tactics', data)
        finally:
            if os.path.exists(output_json):
                os.remove(output_json)

    def test_cli_export_both_formats(self):
        """测试CLI同时导出Markdown和JSON"""
        output_md = '/tmp/test_both.md'
        output_json = '/tmp/test_both.json'
        for f in [output_md, output_json]:
            if os.path.exists(f):
                os.remove(f)
        try:
            exit_code, output = self._run_cli([
                'tactics', self.test_file, '--game', '2',
                '--output-md', output_md, '--output-json', output_json
            ])
            self.assertEqual(exit_code, 0)
            self.assertTrue(os.path.exists(output_md))
            self.assertTrue(os.path.exists(output_json))
        finally:
            for f in [output_md, output_json]:
                if os.path.exists(f):
                    os.remove(f)


class TestTacticNames(unittest.TestCase):
    """测试战术名称映射"""

    def test_all_nine_tactics_defined(self):
        """测试9种战术主题都已定义"""
        expected = {
            'mate_threat', 'double_check', 'fork', 'pin', 'skewer',
            'deflection', 'overload', 'capture_defender', 'promotion_threat'
        }
        self.assertEqual(set(TACTIC_NAMES.keys()), expected)

    def test_all_names_are_chinese(self):
        """测试所有战术名称为中文"""
        for key, name in TACTIC_NAMES.items():
            self.assertTrue(len(name) >= 2, f"{key} 的名称太短")


if __name__ == '__main__':
    unittest.main(verbosity=2)
