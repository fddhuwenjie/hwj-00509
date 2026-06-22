#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PGN Lab - 国际象棋PGN解析和对局分析CLI工具
"""

import argparse
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime
from collections import Counter, defaultdict


# ============================================================
# 简化ECO开局表（覆盖常见开局）
# ============================================================
ECO_TABLE = [
    ("A00", "非常规开局", []),
    ("A01", "尼姆佐维奇开局", ["b3"]),
    ("A02", "伯德开局", ["f4"]),
    ("A04", "列蒂开局", ["Nf3"]),
    ("A05", "列蒂开局", ["Nf3", "Nf6"]),
    ("A06", "列蒂开局", ["Nf3", "d5"]),
    ("A10", "英式开局", ["c4"]),
    ("A15", "英式开局", ["c4", "Nf6"]),
    ("A20", "英式开局", ["c4", "e5"]),
    ("B00", "王兵开局(非常规)", ["e4"]),
    ("B01", "斯堪的纳维亚防御", ["e4", "d5"]),
    ("B02", "阿廖欣防御", ["e4", "Nf6"]),
    ("B06", "现代防御", ["e4", "g6"]),
    ("B07", "皮尔茨防御", ["e4", "d6"]),
    ("B10", "卡罗康防御", ["e4", "c6"]),
    ("B20", "西西里防御", ["e4", "c5"]),
    ("B30", "西西里防御-开放变例", ["e4", "c5", "Nf3"]),
    ("B50", "西西里防御", ["e4", "c5", "Nf3", "d6"]),
    ("B70", "西西里防御-龙式变例", ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "g6"]),
    ("B90", "西西里防御-纳伊多夫变例", ["e4", "c5", "Nf3", "d6", "d4", "cxd4", "Nxd4", "Nf6", "Nc3", "a6"]),
    ("C00", "法兰西防御", ["e4", "e6"]),
    ("C10", "法兰西防御", ["e4", "e6", "d4", "d5"]),
    ("C20", "王翼弃兵等", ["e4", "e5"]),
    ("C21", "中心弃兵", ["e4", "e5", "d4", "exd4"]),
    ("C23", "主教开局", ["e4", "e5", "Bc4"]),
    ("C25", "维也纳开局", ["e4", "e5", "Nc3"]),
    ("C40", "王翼马开局", ["e4", "e5", "Nf3"]),
    ("C41", "菲利道尔防御", ["e4", "e5", "Nf3", "d6"]),
    ("C42", "彼得罗夫防御", ["e4", "e5", "Nf3", "Nf6"]),
    ("C44", "王翼马开局", ["e4", "e5", "Nf3", "Nc6"]),
    ("C45", "苏格兰开局", ["e4", "e5", "Nf3", "Nc6", "d4"]),
    ("C46", "四马开局", ["e4", "e5", "Nf3", "Nc6", "Nc3", "Nf6"]),
    ("C47", "四马开局", ["e4", "e5", "Nf3", "Nc6", "Nc3", "Nf6", "Bb5"]),
    ("C50", "意大利开局", ["e4", "e5", "Nf3", "Nc6", "Bc4"]),
    ("C51", "埃文斯弃兵", ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "b4"]),
    ("C54", "意大利开局", ["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "c3"]),
    ("C55", "双马防御", ["e4", "e5", "Nf3", "Nc6", "Bc4", "Nf6"]),
    ("C60", "西班牙开局", ["e4", "e5", "Nf3", "Nc6", "Bb5"]),
    ("C65", "西班牙开局-柏林防御", ["e4", "e5", "Nf3", "Nc6", "Bb5", "Nf6"]),
    ("C68", "西班牙开局-兑换变例", ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Bxc6"]),
    ("C70", "西班牙开局-莫尔菲防御", ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4"]),
    ("C77", "西班牙开局-封闭式", ["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "Nf6", "O-O"]),
    ("D00", "后兵开局(非常规)", ["d4"]),
    ("D01", "后兵开局", ["d4", "d5"]),
    ("D02", "后兵开局-伦敦体系", ["d4", "d5", "Nf3", "Nf6", "Bf4"]),
    ("D06", "后兵开局", ["d4", "d5", "Nf3", "Nf6", "e3"]),
    ("D07", "后兵开局-后翼弃兵拒绝", ["d4", "d5", "c4"]),
    ("D10", "斯拉夫防御", ["d4", "d5", "c4", "c6"]),
    ("D20", "后翼弃兵接受", ["d4", "d5", "c4", "dxc4"]),
    ("D30", "后翼弃兵拒绝", ["d4", "d5", "c4", "e6"]),
    ("D40", "后翼弃兵拒绝-半斯拉夫", ["d4", "d5", "c4", "e6", "Nc3", "Nf6"]),
    ("D43", "半斯拉夫防御", ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Nf3", "c6"]),
    ("D50", "后翼弃兵拒绝-正统防御", ["d4", "d5", "c4", "e6", "Nc3", "Nf6", "Bg5"]),
    ("D70", "新印度防御/格林菲尔德", ["d4", "Nf6", "c4", "g6"]),
    ("D80", "格林菲尔德防御", ["d4", "Nf6", "c4", "g6", "Nc3", "d5"]),
    ("E00", "后兵开局-印度防御", ["d4", "Nf6", "c4"]),
    ("E01", "卡塔兰开局", ["d4", "Nf6", "c4", "e6", "g3"]),
    ("E10", "后兵开局", ["d4", "Nf6", "c4", "e6"]),
    ("E12", "尼姆佐维奇印度防御", ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4"]),
    ("E20", "尼姆佐维奇印度防御", ["d4", "Nf6", "c4", "e6", "Nc3", "Bb4"]),
    ("E60", "王翼印度防御", ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7"]),
    ("E61", "王翼印度防御", ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4"]),
    ("E70", "王翼印度防御", ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6"]),
    ("E80", "古印度防御", ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "f3"]),
    ("E90", "古印度防御-杰米什变例", ["d4", "Nf6", "c4", "g6", "Nc3", "Bg7", "e4", "d6", "f3", "O-O", "Be3"]),
]


def detect_opening(move_list_san, max_depth=12):
    """根据前几步SAN走法匹配ECO开局"""
    moves = move_list_san[:max_depth]
    best_code = "A00"
    best_name = "非常规开局"
    best_len = -1
    for code, name, pattern in ECO_TABLE:
        if not pattern:
            continue
        if len(pattern) > len(moves):
            continue
        match = True
        for i, pm in enumerate(pattern):
            if pm != moves[i]:
                match = False
                break
        if match and len(pattern) > best_len:
            best_code = code
            best_name = name
            best_len = len(pattern)
    return best_code, best_name


# ============================================================
# 棋盘引擎
# ============================================================

class Piece:
    KING = 'K'
    QUEEN = 'Q'
    ROOK = 'R'
    BISHOP = 'B'
    KNIGHT = 'N'
    PAWN = 'P'

    PIECES = {'K', 'Q', 'R', 'B', 'N', 'P'}

    @staticmethod
    def is_white(p):
        return p.isupper() and p in Piece.PIECES

    @staticmethod
    def is_black(p):
        return p.islower() and p.upper() in Piece.PIECES

    @staticmethod
    def is_piece(p):
        return Piece.is_white(p) or Piece.is_black(p)

    @staticmethod
    def color(p):
        if Piece.is_white(p):
            return 'w'
        elif Piece.is_black(p):
            return 'b'
        return None

    @staticmethod
    def type(p):
        return p.upper() if Piece.is_piece(p) else None


FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
RANKS = ['1', '2', '3', '4', '5', '6', '7', '8']


def sq_to_idx(sq):
    """a1 -> (0,0), h8 -> (7,7)"""
    f = ord(sq[0]) - ord('a')
    r = int(sq[1]) - 1
    return (f, r)


def idx_to_sq(f, r):
    return FILES[f] + RANKS[r]


class Board:
    INITIAL_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

    def __init__(self, fen=None):
        self.board = [[''] * 8 for _ in range(8)]
        self.turn = 'w'
        self.castling = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history = []
        self.captures = []
        self.checks = []
        if fen is None:
            fen = Board.INITIAL_FEN
        self.load_fen(fen)

    def load_fen(self, fen):
        parts = fen.split()
        if len(parts) < 4:
            raise ValueError(f"无效的FEN: {fen}")
        # 1. 棋盘部分
        rows = parts[0].split('/')
        if len(rows) != 8:
            raise ValueError(f"FEN棋盘部分无效: {parts[0]}")
        for r in range(8):
            row = rows[7 - r]
            f = 0
            for c in row:
                if c.isdigit():
                    for _ in range(int(c)):
                        self.board[f][r] = ''
                        f += 1
                else:
                    self.board[f][r] = c
                    f += 1
        # 2. 行棋方
        self.turn = parts[1] if len(parts) > 1 else 'w'
        # 3. 王车易位权利
        castling_str = parts[2] if len(parts) > 2 else '-'
        self.castling = {'K': False, 'Q': False, 'k': False, 'q': False}
        if castling_str != '-':
            for c in castling_str:
                self.castling[c] = True
        # 4. 吃过路兵
        ep_str = parts[3] if len(parts) > 3 else '-'
        self.en_passant = sq_to_idx(ep_str) if ep_str != '-' else None
        # 5. 半回合数
        self.halfmove_clock = int(parts[4]) if len(parts) > 4 else 0
        # 6. 全回合数
        self.fullmove_number = int(parts[5]) if len(parts) > 5 else 1

    def to_fen(self):
        rows = []
        for r in range(7, -1, -1):
            row = ''
            empty = 0
            for f in range(8):
                p = self.board[f][r]
                if p == '':
                    empty += 1
                else:
                    if empty > 0:
                        row += str(empty)
                        empty = 0
                    row += p
            if empty > 0:
                row += str(empty)
            rows.append(row)
        board_str = '/'.join(rows)
        turn = self.turn
        castling_str = ''
        for c in ['K', 'Q', 'k', 'q']:
            if self.castling[c]:
                castling_str += c
        if not castling_str:
            castling_str = '-'
        ep_str = idx_to_sq(*self.en_passant) if self.en_passant else '-'
        return f"{board_str} {turn} {castling_str} {ep_str} {self.halfmove_clock} {self.fullmove_number}"

    def copy(self):
        return deepcopy(self)

    def get_piece(self, f, r):
        if 0 <= f < 8 and 0 <= r < 8:
            return self.board[f][r]
        return None

    def set_piece(self, f, r, p):
        self.board[f][r] = p

    def find_king(self, color):
        king = 'K' if color == 'w' else 'k'
        for f in range(8):
            for r in range(8):
                if self.board[f][r] == king:
                    return (f, r)
        return None

    def is_square_attacked(self, f, r, by_color):
        """检查(f,r)是否被by_color方攻击"""
        # 兵攻击
        pawn_dir = 1 if by_color == 'w' else -1
        pawn = 'P' if by_color == 'w' else 'p'
        for df in [-1, 1]:
            pf = f + df
            pr = r - pawn_dir
            if 0 <= pf < 8 and 0 <= pr < 8:
                if self.board[pf][pr] == pawn:
                    return True
        # 马攻击
        knight = 'N' if by_color == 'w' else 'n'
        knight_moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        for df, dr in knight_moves:
            nf, nr = f + df, r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if self.board[nf][nr] == knight:
                    return True
        # 王攻击
        king = 'K' if by_color == 'w' else 'k'
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0:
                    continue
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    if self.board[nf][nr] == king:
                        return True
        # 象/后 - 斜线
        bishop = 'B' if by_color == 'w' else 'b'
        queen = 'Q' if by_color == 'w' else 'q'
        for df, dr in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nf, nr = f + df, r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                p = self.board[nf][nr]
                if p != '':
                    if p == bishop or p == queen:
                        return True
                    break
                nf += df
                nr += dr
        # 车/后 - 直线
        rook = 'R' if by_color == 'w' else 'r'
        for df, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nf, nr = f + df, r + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                p = self.board[nf][nr]
                if p != '':
                    if p == rook or p == queen:
                        return True
                    break
                nf += df
                nr += dr
        return False

    def in_check(self, color=None):
        if color is None:
            color = self.turn
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        enemy = 'b' if color == 'w' else 'w'
        return self.is_square_attacked(king_pos[0], king_pos[1], enemy)

    def get_pseudo_moves(self, f, r):
        """获取(f,r)位置棋子的伪合法走法（不检查将军）"""
        p = self.board[f][r]
        if p == '':
            return []
        color = Piece.color(p)
        ptype = Piece.type(p)
        moves = []
        enemy = 'b' if color == 'w' else 'w'

        if ptype == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 1 if color == 'w' else 6
            # 前进1格
            nr = r + direction
            if 0 <= nr < 8 and self.board[f][nr] == '':
                moves.append((f, r, f, nr))
                # 前进2格
                if r == start_rank:
                    nr2 = r + 2 * direction
                    if self.board[f][nr2] == '':
                        moves.append((f, r, f, nr2))
            # 吃子
            for df in [-1, 1]:
                nf = f + df
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = self.board[nf][nr]
                    if target != '' and Piece.color(target) == enemy:
                        moves.append((f, r, nf, nr))
            # 吃过路兵
            if self.en_passant:
                epf, epr = self.en_passant
                if epr == nr and abs(epf - f) == 1:
                    moves.append((f, r, epf, epr))
        elif ptype == 'N':
            knight_moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
            for df, dr in knight_moves:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = self.board[nf][nr]
                    if target == '' or Piece.color(target) == enemy:
                        moves.append((f, r, nf, nr))
        elif ptype == 'B':
            for df, dr in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = self.board[nf][nr]
                    if target == '':
                        moves.append((f, r, nf, nr))
                    else:
                        if Piece.color(target) == enemy:
                            moves.append((f, r, nf, nr))
                        break
                    nf += df
                    nr += dr
        elif ptype == 'R':
            for df, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = self.board[nf][nr]
                    if target == '':
                        moves.append((f, r, nf, nr))
                    else:
                        if Piece.color(target) == enemy:
                            moves.append((f, r, nf, nr))
                        break
                    nf += df
                    nr += dr
        elif ptype == 'Q':
            # 象 + 车
            for df, dr in [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    target = self.board[nf][nr]
                    if target == '':
                        moves.append((f, r, nf, nr))
                    else:
                        if Piece.color(target) == enemy:
                            moves.append((f, r, nf, nr))
                        break
                    nf += df
                    nr += dr
        elif ptype == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        target = self.board[nf][nr]
                        if target == '' or Piece.color(target) == enemy:
                            moves.append((f, r, nf, nr))
            # 王车易位
            if not self.in_check(color):
                # 短易位
                k_right = 'K' if color == 'w' else 'k'
                if self.castling[k_right]:
                    rank = 0 if color == 'w' else 7
                    if self.board[5][rank] == '' and self.board[6][rank] == '':
                        if not self.is_square_attacked(5, rank, enemy) and not self.is_square_attacked(6, rank, enemy):
                            moves.append((f, r, 6, rank))
                # 长易位
                q_right = 'Q' if color == 'w' else 'q'
                if self.castling[q_right]:
                    rank = 0 if color == 'w' else 7
                    if self.board[1][rank] == '' and self.board[2][rank] == '' and self.board[3][rank] == '':
                        if not self.is_square_attacked(2, rank, enemy) and not self.is_square_attacked(3, rank, enemy):
                            moves.append((f, r, 2, rank))
        return moves

    def get_legal_moves(self, f, r):
        """获取合法走法（不使己方被将军）"""
        pseudo = self.get_pseudo_moves(f, r)
        legal = []
        for move in pseudo:
            sf, sr, tf, tr = move
            if self._make_move_test(sf, sr, tf, tr):
                legal.append(move)
        return legal

    def get_all_legal_moves(self, color=None):
        if color is None:
            color = self.turn
        moves = []
        for f in range(8):
            for r in range(8):
                p = self.board[f][r]
                if p != '' and Piece.color(p) == color:
                    moves.extend(self.get_legal_moves(f, r))
        return moves

    def _make_move_test(self, sf, sr, tf, tr):
        """尝试走一步，返回是否合法（不被将军），用于校验"""
        piece = self.board[sf][sr]
        if piece == '':
            return False
        color = Piece.color(piece)
        ptype = Piece.type(piece)
        captured = self.board[tf][tr]
        saved_board = deepcopy(self.board)
        saved_ep = self.en_passant
        saved_castling = dict(self.castling)

        # 王车易位
        if ptype == 'K' and abs(tf - sf) == 2:
            rank = sr
            if tf > sf:  # 短易位
                self.board[tf][tr] = piece
                self.board[sf][sr] = ''
                self.board[5][rank] = self.board[7][rank]
                self.board[7][rank] = ''
            else:  # 长易位
                self.board[tf][tr] = piece
                self.board[sf][sr] = ''
                self.board[3][rank] = self.board[0][rank]
                self.board[0][rank] = ''
        else:
            # 吃过路兵
            if ptype == 'P' and self.en_passant and (tf, tr) == self.en_passant:
                capture_rank = tr - (1 if color == 'w' else -1)
                self.board[tf][capture_rank] = ''
            self.board[tf][tr] = piece
            self.board[sf][sr] = ''

        # 检查是否被将军
        in_check = self.in_check(color)

        # 恢复
        self.board = saved_board
        self.en_passant = saved_ep
        self.castling = saved_castling

        return not in_check

    def make_move(self, sf, sr, tf, tr, promotion=None):
        """真正执行一步走法，返回移动信息字典"""
        piece = self.board[sf][sr]
        if piece == '':
            return None
        color = Piece.color(piece)
        ptype = Piece.type(piece)
        captured = self.board[tf][tr]
        move_info = {
            'from': idx_to_sq(sf, sr),
            'to': idx_to_sq(tf, tr),
            'piece': piece,
            'captured': captured,
            'is_capture': captured != '',
            'is_check': False,
            'is_mate': False,
            'is_castle_k': False,
            'is_castle_q': False,
            'is_en_passant': False,
            'is_promotion': False,
            'promoted_to': None,
        }

        # 王车易位 - 添加防御性二次校验
        if ptype == 'K' and abs(tf - sf) == 2:
            rank = sr
            enemy = 'b' if color == 'w' else 'w'
            # 防御性校验：检查易位合法性
            if tf > sf:  # 短易位
                right_key = 'K' if color == 'w' else 'k'
                # 1. 检查易位权利
                if not self.castling.get(right_key, False):
                    return None
                # 2. 检查路径占用 (f1/f8, g1/g8)
                if self.board[5][rank] != '' or self.board[6][rank] != '':
                    return None
                # 3. 检查王是否被将军
                if self.in_check(color):
                    return None
                # 4. 检查经过格和到达格是否受攻击
                if self.is_square_attacked(5, rank, enemy) or self.is_square_attacked(6, rank, enemy):
                    return None
                # 5. 检查车位置是否正确
                rook_piece = 'R' if color == 'w' else 'r'
                if self.board[7][rank] != rook_piece:
                    return None
            else:  # 长易位
                right_key = 'Q' if color == 'w' else 'q'
                # 1. 检查易位权利
                if not self.castling.get(right_key, False):
                    return None
                # 2. 检查路径占用 (d1/d8, c1/c8, b1/b8)
                if self.board[1][rank] != '' or self.board[2][rank] != '' or self.board[3][rank] != '':
                    return None
                # 3. 检查王是否被将军
                if self.in_check(color):
                    return None
                # 4. 检查经过格和到达格是否受攻击
                if self.is_square_attacked(2, rank, enemy) or self.is_square_attacked(3, rank, enemy):
                    return None
                # 5. 检查车位置是否正确
                rook_piece = 'R' if color == 'w' else 'r'
                if self.board[0][rank] != rook_piece:
                    return None
            # 校验通过，执行易位
            if tf > sf:  # 短易位
                move_info['is_castle_k'] = True
                self.board[tf][tr] = piece
                self.board[sf][sr] = ''
                self.board[5][rank] = self.board[7][rank]
                self.board[7][rank] = ''
            else:  # 长易位
                move_info['is_castle_q'] = True
                self.board[tf][tr] = piece
                self.board[sf][sr] = ''
                self.board[3][rank] = self.board[0][rank]
                self.board[0][rank] = ''
            # 更新易位权利
            if color == 'w':
                self.castling['K'] = False
                self.castling['Q'] = False
            else:
                self.castling['k'] = False
                self.castling['q'] = False
        else:
            # 吃过路兵
            if ptype == 'P' and self.en_passant and (tf, tr) == self.en_passant:
                move_info['is_en_passant'] = True
                move_info['is_capture'] = True
                capture_rank = tr - (1 if color == 'w' else -1)
                captured_pawn = self.board[tf][capture_rank]
                move_info['captured'] = captured_pawn
                self.board[tf][capture_rank] = ''
            # 兵升变
            if ptype == 'P' and (tr == 7 or tr == 0):
                move_info['is_promotion'] = True
                if promotion:
                    promoted = promotion.upper() if color == 'w' else promotion.lower()
                    piece = promoted
                else:
                    promoted = 'Q' if color == 'w' else 'q'
                    piece = promoted
                move_info['promoted_to'] = piece
            self.board[tf][tr] = piece
            self.board[sf][sr] = ''

        # 更新吃过路兵目标
        if ptype == 'P' and abs(tr - sr) == 2:
            ep_r = (sr + tr) // 2
            self.en_passant = (sf, ep_r)
        else:
            self.en_passant = None

        # 更新王车易位权利
        if ptype == 'K':
            if color == 'w':
                self.castling['K'] = False
                self.castling['Q'] = False
            else:
                self.castling['k'] = False
                self.castling['q'] = False
        if ptype == 'R':
            if sf == 0 and sr == 0:
                self.castling['Q'] = False
            elif sf == 7 and sr == 0:
                self.castling['K'] = False
            elif sf == 0 and sr == 7:
                self.castling['q'] = False
            elif sf == 7 and sr == 7:
                self.castling['k'] = False
        # 如果车被吃掉
        if tf == 0 and tr == 0:
            self.castling['Q'] = False
        elif tf == 7 and tr == 0:
            self.castling['K'] = False
        elif tf == 0 and tr == 7:
            self.castling['q'] = False
        elif tf == 7 and tr == 7:
            self.castling['k'] = False

        # 半回合数
        if ptype == 'P' or move_info['is_capture']:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        # 全回合数
        if color == 'b':
            self.fullmove_number += 1
        # 切换行棋方
        self.turn = 'b' if color == 'w' else 'w'

        # 检查将军
        if self.in_check(self.turn):
            move_info['is_check'] = True
            # 检查是否将死
            legal_moves = self.get_all_legal_moves(self.turn)
            if len(legal_moves) == 0:
                move_info['is_mate'] = True

        self.move_history.append(move_info)
        if move_info['is_capture']:
            self.captures.append(move_info)
        if move_info['is_check']:
            self.checks.append(move_info)
        return move_info

    def to_ascii(self):
        """生成ASCII棋盘"""
        lines = []
        lines.append("  +" + "---+" * 8)
        for r in range(7, -1, -1):
            row = f"{r+1} |"
            for f in range(8):
                p = self.board[f][r]
                if p == '':
                    # 交替颜色
                    if (f + r) % 2 == 0:
                        p = '.'
                    else:
                        p = ' '
                row += f" {p} |"
            lines.append(row)
            lines.append("  +" + "---+" * 8)
        lines.append("    a   b   c   d   e   f   g   h")
        return "\n".join(lines)


# ============================================================
# SAN解析 - 将SAN走法字符串解析为棋盘移动
# ============================================================

def parse_san(board, san):
    """
    解析SAN走法，返回(sf, sr, tf, tr, promotion)或None
    """
    original_san = san
    # 移除将军/将死标记
    san = san.rstrip('+#')
    # 检查王车易位 - 走统一的合法走法判断
    if san in ('O-O', '0-0'):
        rank = 0 if board.turn == 'w' else 7
        king_from = (4, rank)
        king_to = (6, rank)
        # 获取王的合法走法，验证易位是否合法
        legal_moves = board.get_legal_moves(king_from[0], king_from[1])
        for move in legal_moves:
            if move[2] == king_to[0] and move[3] == king_to[1]:
                return (king_from[0], king_from[1], king_to[0], king_to[1], None)
        return None
    if san in ('O-O-O', '0-0-0'):
        rank = 0 if board.turn == 'w' else 7
        king_from = (4, rank)
        king_to = (2, rank)
        # 获取王的合法走法，验证易位是否合法
        legal_moves = board.get_legal_moves(king_from[0], king_from[1])
        for move in legal_moves:
            if move[2] == king_to[0] and move[3] == king_to[1]:
                return (king_from[0], king_from[1], king_to[0], king_to[1], None)
        return None

    promotion = None
    # 检查升变
    if '=' in san:
        parts = san.split('=')
        san = parts[0]
        if parts[1]:
            promotion = parts[1][0].upper()

    # 兵走法: e4, e5, exd5, exd6=Q
    is_pawn = False
    piece_type = 'P'
    from_file = None
    from_rank = None
    to_sq = None
    is_capture = 'x' in san

    if san[0].islower():
        # 兵走法
        is_pawn = True
        piece_type = 'P'
        if is_capture:
            # exd5
            parts = san.split('x')
            from_file = parts[0]
            to_sq = parts[1][:2]
        else:
            to_sq = san[:2]
        from_file = san[0] if from_file is None else from_file
    else:
        # 棋子走法
        piece_type = san[0].upper()
        rest = san[1:]
        # 找目标格（最后两个字符）
        if is_capture:
            parts = rest.split('x')
            # 前面可能是起始文件/_rank
            disambig = parts[0]
            to_sq = parts[1][:2]
        else:
            to_sq = rest[-2:] if len(rest) >= 2 else rest
            disambig = rest[:-2] if len(rest) > 2 else ''
        if len(disambig) >= 1:
            if disambig[0].islower():
                from_file = disambig[0]
            elif disambig[0].isdigit():
                from_rank = disambig[0]
        if len(disambig) >= 2:
            if disambig[1].isdigit():
                from_rank = disambig[1]

    if to_sq is None or len(to_sq) < 2:
        return None

    tf = ord(to_sq[0]) - ord('a')
    tr = int(to_sq[1]) - 1

    # 找所有合法的起始位置
    color = board.turn
    candidates = []
    for f in range(8):
        for r in range(8):
            p = board.board[f][r]
            if p == '' or Piece.color(p) != color:
                continue
            if Piece.type(p) != piece_type:
                continue
            # 消除歧义
            if from_file and FILES[f] != from_file:
                continue
            if from_rank and RANKS[r] != from_rank:
                continue
            # 检查是否能走到目标格
            legal = board.get_legal_moves(f, r)
            for move in legal:
                if move[2] == tf and move[3] == tr:
                    candidates.append((f, r))
                    break

    if len(candidates) == 0:
        # 吃过路兵特殊处理
        if is_pawn and is_capture and board.en_passant:
            epf, epr = board.en_passant
            if epf == tf and epr == tr:
                direction = 1 if color == 'w' else -1
                sf = tf + (-1 if from_file and ord(from_file) > ord(to_sq[0]) else 1)
                sr = tr - direction
                if 0 <= sf < 8:
                    p = board.board[sf][sr]
                    if p != '' and Piece.color(p) == color and Piece.type(p) == 'P':
                        return (sf, sr, tf, tr, promotion)
        return None
    if len(candidates) > 1:
        return None

    sf, sr = candidates[0]
    return (sf, sr, tf, tr, promotion)


# ============================================================
# PGN解析器
# ============================================================

class PGNParser:
    def __init__(self):
        pass

    @staticmethod
    def parse_file(filepath):
        """解析PGN文件，返回对局列表"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return PGNParser.parse_string(content)

    @staticmethod
    def parse_string(content):
        """解析PGN字符串，返回对局列表"""
        games = []
        # 按空行分割，处理标签对
        lines = content.split('\n')
        current_game_tags = {}
        current_moves_text = ''
        in_tags = True
        moves_buffer = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('['):
                # 标签对
                if moves_buffer:
                    # 之前的走法需要保存
                    if current_game_tags:
                        game = PGNParser._process_game(current_game_tags, moves_buffer)
                        if game:
                            games.append(game)
                    current_game_tags = {}
                    moves_buffer = []
                # 解析标签对
                match = re.match(r'\[(\w+)\s+"(.*)"\]', line)
                if match:
                    key = match.group(1)
                    value = match.group(2)
                    current_game_tags[key] = value
            elif line == '' or line.startswith('%'):
                # 空行或注释
                pass
            else:
                # 走法文本
                moves_buffer.append(line)
            i += 1
        # 处理最后一局
        if current_game_tags and moves_buffer:
            game = PGNParser._process_game(current_game_tags, moves_buffer)
            if game:
                games.append(game)
        elif current_game_tags and not moves_buffer:
            # 只有标签的对局
            game = {
                'tags': current_game_tags,
                'moves_san': [],
                'moves_with_comments': [],
                'variations': [],
                'comments': '',
                'result': current_game_tags.get('Result', '*'),
            }
            games.append(game)
        return games

    @staticmethod
    def _process_game(tags, moves_lines):
        """处理单局走法"""
        moves_text = ' '.join(moves_lines)
        # 移除花括号注释，保存
        comments = []
        # 提取花括号注释
        def extract_braces(m):
            comments.append(m.group(1).strip())
            return ' '
        clean_text = re.sub(r'\{([^}]*)\}', extract_braces, moves_text)
        # 移除分号注释
        clean_text = re.sub(r';[^\n]*', ' ', clean_text)
        # 移除变体（圆括号）- 简化处理，记录变体存在
        variations = []
        def extract_variations(m):
            variations.append(m.group(1).strip())
            return ' '
        clean_text = re.sub(r'\(([^)]*)\)', extract_variations, clean_text)
        # 解析走法
        san_moves = []
        moves_with_info = []
        # 移除回合编号: "1. Nf3" -> "Nf3"
        tokens = clean_text.split()
        for token in tokens:
            # 跳过回合编号
            if re.match(r'^\d+[\.\.]+$', token):
                continue
            if re.match(r'^\d+\.', token):
                token = re.sub(r'^\d+\.', '', token)
                if not token:
                    continue
            # 检查是否是结果
            if token in ('1-0', '0-1', '1/2-1/2', '*'):
                if 'Result' not in tags or tags['Result'] == '*':
                    tags['Result'] = token
                continue
            if token:
                san_moves.append(token)
                moves_with_info.append({
                    'san': token,
                    'comment': '',
                })
        return {
            'tags': tags,
            'moves_san': san_moves,
            'moves_with_comments': moves_with_info,
            'variations': variations,
            'comments': comments,
            'result': tags.get('Result', '*'),
        }


# ============================================================
# 对局播放器 - 逐步应用SAN走法还原棋盘
# ============================================================

class GameReplayer:
    def __init__(self, game, start_fen=None):
        self.game = game
        self.start_fen = start_fen
        # 如果没有指定start_fen，检查游戏标签中的FEN
        if self.start_fen is None and 'FEN' in game.get('tags', {}):
            self.start_fen = game['tags']['FEN']
        self.board = Board(self.start_fen) if self.start_fen else Board()
        self.board_states = [self.board.to_fen()]
        self.move_results = []
        self.errors = []

    def replay(self, stop_at_move=None):
        """回放所有走法，返回每步结果"""
        moves = self.game['moves_san']
        if stop_at_move is not None:
            moves = moves[:stop_at_move]
        for i, san in enumerate(moves):
            move_number = i // 2 + 1
            color = 'White' if i % 2 == 0 else 'Black'
            parsed = parse_san(self.board, san)
            if parsed is None:
                self.errors.append({
                    'move_index': i,
                    'move_number': move_number,
                    'color': color,
                    'san': san,
                    'fen': self.board.to_fen(),
                    'reason': '无法解析走法或无合法移动',
                })
                break
            sf, sr, tf, tr, promotion = parsed
            move_info = self.board.make_move(sf, sr, tf, tr, promotion)
            if move_info is None:
                self.errors.append({
                    'move_index': i,
                    'move_number': move_number,
                    'color': color,
                    'san': san,
                    'fen': self.board.to_fen(),
                    'reason': '移动执行失败',
                })
                break
            move_info['san'] = san
            move_info['move_index'] = i
            move_info['move_number'] = move_number
            move_info['color'] = color
            self.move_results.append(move_info)
            self.board_states.append(self.board.to_fen())
        return self.move_results, self.errors

    def get_board_at_move(self, move_num):
        """获取第N步后的棋盘状态"""
        if move_num < 0:
            move_num = 0
        if move_num >= len(self.board_states):
            move_num = len(self.board_states) - 1
        board = Board(self.board_states[move_num])
        return board


# ============================================================
# 战术主题识别引擎
# ============================================================

TACTIC_NAMES = {
    'mate_threat': '将死威胁',
    'double_check': '双将',
    'fork': '叉击',
    'pin': '牵制',
    'skewer': '串击',
    'deflection': '诱离',
    'overload': '过载',
    'capture_defender': '防守子被吃',
    'promotion_threat': '升变威胁',
}

PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}


def _piece_value(piece):
    if not piece:
        return 0
    return PIECE_VALUES.get(piece.upper(), 0)


def _find_pieces(board, color, ptype=None):
    pieces = []
    for f in range(8):
        for r in range(8):
            p = board.board[f][r]
            if p and Piece.color(p) == color:
                if ptype is None or Piece.type(p) == ptype:
                    pieces.append((f, r, p))
    return pieces


def _get_squares_attacked_by(board, color):
    """获取color方攻击的所有格子"""
    attacked = set()
    for f, r, p in _find_pieces(board, color):
        ptype = Piece.type(p)
        if ptype == 'P':
            direction = 1 if color == 'w' else -1
            for df in [-1, 1]:
                nf, nr = f + df, r + direction
                if 0 <= nf < 8 and 0 <= nr < 8:
                    attacked.add((nf, nr))
        elif ptype == 'N':
            knight_moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
            for df, dr in knight_moves:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    attacked.add((nf, nr))
        elif ptype == 'B' or ptype == 'Q':
            for df, dr in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    attacked.add((nf, nr))
                    if board.board[nf][nr] != '':
                        break
                    nf += df
                    nr += dr
        if ptype == 'R' or ptype == 'Q':
            for df, dr in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    attacked.add((nf, nr))
                    if board.board[nf][nr] != '':
                        break
                    nf += df
                    nr += dr
        elif ptype == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        attacked.add((nf, nr))
    return attacked


def _line_squares(sf, sr, tf, tr):
    """获取两点之间的直线或斜线上的格子(不含起点，含终点)"""
    df = tf - sf
    dr = tr - sr
    if df == 0 and dr == 0:
        return []
    if df != 0 and dr != 0 and abs(df) != abs(dr):
        return []
    step_f = 0 if df == 0 else (1 if df > 0 else -1)
    step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
    squares = []
    nf, nr = sf + step_f, sr + step_r
    while (nf, nr) != (tf, tr):
        if not (0 <= nf < 8 and 0 <= nr < 8):
            break
        squares.append((nf, nr))
        nf += step_f
        nr += step_r
    if 0 <= tf < 8 and 0 <= tr < 8:
        squares.append((tf, tr))
    return squares


def detect_double_check(board_before, board_after, move_info):
    """检测双将：走子后，对方王被两个不同来源的棋子同时将军"""
    if not move_info.get('is_check'):
        return None, ''
    enemy = board_after.turn
    king_pos = board_after.find_king(enemy)
    if not king_pos:
        return None, ''
    kf, kr = king_pos
    attacker_color = 'b' if enemy == 'w' else 'w'
    attackers = []
    for f, r, p in _find_pieces(board_after, attacker_color):
        legal = board_after.get_legal_moves(f, r)
        for move in legal:
            if move[2] == kf and move[3] == kr:
                attackers.append((f, r, p))
                break
    if len(attackers) >= 2:
        names = [p.upper() for _, _, p in attackers]
        return 'double_check', f"{', '.join(names)} 同时将军，共 {len(attackers)} 个攻击来源"
    return None, ''


def detect_fork(board_before, board_after, move_info):
    """检测叉击：一个棋子同时攻击对方两个或更多高价值棋子"""
    mover = move_info['piece']
    mover_color = Piece.color(mover)
    target_color = 'b' if mover_color == 'w' else 'w'
    tf = ord(move_info['to'][0]) - ord('a')
    tr = int(move_info['to'][1]) - 1
    legal_moves_from_target = board_after.get_legal_moves(tf, tr)
    high_value_targets = []
    for move in legal_moves_from_target:
        ttf, ttr = move[2], move[3]
        target_piece = board_after.board[ttf][ttr]
        if target_piece and Piece.color(target_piece) == target_color:
            pv = _piece_value(target_piece)
            if pv >= 3:
                high_value_targets.append((idx_to_sq(ttf, ttr), target_piece))
    if len(high_value_targets) >= 2:
        targets_desc = ', '.join([f"{p}@{sq}" for sq, p in high_value_targets])
        return 'fork', f"{mover.upper()} 同时攻击 {len(high_value_targets)} 个目标: {targets_desc}"
    return None, ''


def detect_pin(board_before, board_after, move_info):
    """检测牵制：走子后，对方某个棋子被攻击，移动它会暴露后面更高价值的棋子(通常是王)"""
    attacker_color = Piece.color(move_info['piece'])
    defender_color = 'b' if attacker_color == 'w' else 'w'
    af = ord(move_info['to'][0]) - ord('a')
    ar = int(move_info['to'][1]) - 1
    attacker_ptype = Piece.type(move_info['piece'])
    mover = move_info['piece']
    if attacker_ptype not in ('B', 'R', 'Q'):
        return None, ''
    king_pos = board_after.find_king(defender_color)
    if not king_pos:
        return None, ''
    kf, kr = king_pos
    directions = []
    if attacker_ptype in ('R', 'Q'):
        directions.extend([(0, -1), (0, 1), (-1, 0), (1, 0)])
    if attacker_ptype in ('B', 'Q'):
        directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
    for df, dr in directions:
        nf, nr = af + df, ar + dr
        first_piece = None
        first_sq = None
        hit_king = False
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board_after.board[nf][nr]
            if p != '':
                if Piece.color(p) == defender_color:
                    if first_piece is None:
                        first_piece = p
                        first_sq = (nf, nr)
                    else:
                        if Piece.type(p) == 'K' and (nf, nr) == (kf, kr):
                            hit_king = True
                        break
                else:
                    break
            nf += df
            nr += dr
        if hit_king and first_piece is not None and first_sq is not None:
            pinned_sq = idx_to_sq(first_sq[0], first_sq[1])
            return 'pin', f"{first_piece.upper()}@{pinned_sq} 被 {mover.upper()} 牵制，移动会暴露王"
        if first_piece is not None and first_sq is not None:
            nf2, nr2 = first_sq[0] + df, first_sq[1] + dr
            second_piece = None
            while 0 <= nf2 < 8 and 0 <= nr2 < 8:
                p = board_after.board[nf2][nr2]
                if p != '':
                    if Piece.color(p) == defender_color:
                        second_piece = p
                    break
                nf2 += df
                nr2 += dr
            if second_piece and _piece_value(second_piece) > _piece_value(first_piece):
                pinned_sq = idx_to_sq(first_sq[0], first_sq[1])
                return 'pin', f"{first_piece.upper()}@{pinned_sq} 被牵制，保护后面更高价值的 {second_piece.upper()}"
    return None, ''


def detect_skewer(board_before, board_after, move_info):
    """检测串击：走子后攻击一条线上的高价值棋子，它移开后会暴露后面较低价值的棋子"""
    attacker_color = Piece.color(move_info['piece'])
    defender_color = 'b' if attacker_color == 'w' else 'w'
    af = ord(move_info['to'][0]) - ord('a')
    ar = int(move_info['to'][1]) - 1
    attacker_ptype = Piece.type(move_info['piece'])
    if attacker_ptype not in ('B', 'R', 'Q'):
        return None, ''
    directions = []
    if attacker_ptype in ('R', 'Q'):
        directions.extend([(0, -1), (0, 1), (-1, 0), (1, 0)])
    if attacker_ptype in ('B', 'Q'):
        directions.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
    for df, dr in directions:
        nf, nr = af + df, ar + dr
        first_piece = None
        first_sq = None
        second_piece = None
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board_after.board[nf][nr]
            if p != '':
                if Piece.color(p) == defender_color:
                    if first_piece is None:
                        first_piece = p
                        first_sq = (nf, nr)
                    else:
                        second_piece = p
                        break
                else:
                    break
            nf += df
            nr += dr
        if first_piece and second_piece and _piece_value(first_piece) >= _piece_value(second_piece) and _piece_value(first_piece) >= 3:
            first_sq_str = idx_to_sq(first_sq[0], first_sq[1])
            return 'skewer', f"{first_piece.upper()}@{first_sq_str} 被串击，移开后 {second_piece.upper()} 会被吃"
    return None, ''


def detect_mate_threat(board_before, board_after, move_info):
    """检测将死威胁：走子后，下一步可以将死对方"""
    if move_info.get('is_mate'):
        return None, ''
    if move_info.get('is_check'):
        return None, ''
    enemy_color = board_after.turn
    legal_moves = board_after.get_all_legal_moves()
    for move in legal_moves:
        sf, sr, tf, tr = move
        test_board = board_after.copy()
        result = test_board.make_move(sf, sr, tf, tr)
        if result and result.get('is_mate'):
            return 'mate_threat', f"存在将死威胁: {idx_to_sq(sf, sr)}{idx_to_sq(tf, tr)}#"
    return None, ''


def detect_deflection(board_before, board_after, move_info):
    """检测诱离：通过吃子或攻击，迫使对方棋子离开原本防守的关键位置"""
    if not move_info.get('is_capture'):
        return None, ''
    captured = move_info.get('captured')
    if not captured or captured == '':
        return None, ''
    captured_color = Piece.color(captured)
    cf = ord(move_info['to'][0]) - ord('a')
    cr = int(move_info['to'][1]) - 1
    defender_color = captured_color
    attacker_color = 'b' if defender_color == 'w' else 'w'
    captured_defended_before = board_before.is_square_attacked(cf, cr, defender_color)
    if not captured_defended_before:
        return None, ''
    now_attacked = board_after.is_square_attacked(cf, cr, attacker_color)
    squares = _get_squares_attacked_by(board_after, attacker_color)
    major_gain = False
    for (sf, sr) in squares:
        p = board_after.board[sf][sr]
        if p and Piece.color(p) == defender_color and _piece_value(p) >= 5:
            major_gain = True
            break
    if major_gain or True:
        return 'deflection', f"吃 {captured.upper()}@{idx_to_sq(cf, cr)} 诱离防守子，暴露后续攻击点"
    return None, ''


def detect_overload(board_before, board_after, move_info):
    """检测过载：对方一个棋子同时需要防守多个关键目标"""
    attacker_color = Piece.color(move_info['piece'])
    defender_color = 'b' if attacker_color == 'w' else 'w'
    captured = move_info.get('captured')
    if not captured or captured == '':
        return None, ''
    defender_pieces = _find_pieces(board_before, defender_color)
    for df, dr, dp in defender_pieces:
        ptype = Piece.type(dp)
        if ptype in ('K', 'P'):
            continue
        attacked_squares = set()
        if ptype == 'N':
            knight_moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
            for mdf, mdr in knight_moves:
                nf, nr = df + mdf, dr + mdr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    tp = board_before.board[nf][nr]
                    if tp and Piece.color(tp) == attacker_color:
                        attacked_squares.add((nf, nr))
        elif ptype in ('B', 'R', 'Q'):
            dirs = []
            if ptype in ('R', 'Q'):
                dirs.extend([(0, -1), (0, 1), (-1, 0), (1, 0)])
            if ptype in ('B', 'Q'):
                dirs.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
            for mdf, mdr in dirs:
                nf, nr = df + mdf, dr + mdr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    tp = board_before.board[nf][nr]
                    if tp != '':
                        if Piece.color(tp) == attacker_color:
                            attacked_squares.add((nf, nr))
                        break
                    nf += mdf
                    nr += mdr
        if len(attacked_squares) >= 2:
            targets = [idx_to_sq(sf, sr) for sf, sr in attacked_squares]
            return 'overload', f"{dp.upper()}@{idx_to_sq(df, dr)} 同时防守 {len(targets)} 个目标: {', '.join(targets)}"
    return None, ''


def detect_capture_defender(board_before, board_after, move_info):
    """检测防守子被吃：吃掉正在防守关键位置或重要棋子的对方棋子"""
    captured = move_info.get('captured')
    if not captured or captured == '':
        return None, ''
    captured_color = Piece.color(captured)
    attacker_color = 'b' if captured_color == 'w' else 'w'
    cf = ord(move_info['to'][0]) - ord('a')
    cr = int(move_info['to'][1]) - 1
    defended_squares = set()
    cp_type = Piece.type(captured)
    if cp_type == 'N':
        knight_moves = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
        for df, dr in knight_moves:
            nf, nr = cf + df, cr + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                tp = board_before.board[nf][nr]
                if tp and Piece.color(tp) == attacker_color:
                    defended_squares.add((nf, nr))
    elif cp_type in ('B', 'R', 'Q'):
        dirs = []
        if cp_type in ('R', 'Q'):
            dirs.extend([(0, -1), (0, 1), (-1, 0), (1, 0)])
        if cp_type in ('B', 'Q'):
            dirs.extend([(-1, -1), (-1, 1), (1, -1), (1, 1)])
        for df, dr in dirs:
            nf, nr = cf + df, cr + dr
            while 0 <= nf < 8 and 0 <= nr < 8:
                tp = board_before.board[nf][nr]
                if tp != '':
                    if Piece.color(tp) == attacker_color:
                        defended_squares.add((nf, nr))
                    break
                nf += df
                nr += dr
    if len(defended_squares) >= 1:
        targets = [idx_to_sq(sf, sr) for sf, sr in defended_squares]
        target_pieces = [board_before.board[sf][sr].upper() for sf, sr in defended_squares]
        desc = ', '.join([f"{p}@{sq}" for p, sq in zip(target_pieces, targets)])
        return 'capture_defender', f"吃掉防守子 {captured.upper()}@{idx_to_sq(cf, cr)}，该棋子原本防守: {desc}"
    return None, ''


def detect_promotion_threat(board_before, board_after, move_info):
    """检测升变威胁：走子后，己方有兵可以在下一步升变"""
    mover_color = Piece.color(move_info['piece'])
    promotion_rank = 7 if mover_color == 'w' else 0
    near_rank = 6 if mover_color == 'w' else 1
    pawns = _find_pieces(board_after, mover_color, 'P')
    for pf, pr, pp in pawns:
        if pr == near_rank:
            direction = 1 if mover_color == 'w' else -1
            nr = pr + direction
            if 0 <= nr < 8 and board_after.board[pf][nr] == '':
                return 'promotion_threat', f"兵 @{idx_to_sq(pf, pr)} 可下一步升变"
            for df in [-1, 1]:
                nf = pf + df
                if 0 <= nf < 8 and 0 <= nr < 8:
                    target = board_after.board[nf][nr]
                    if target and Piece.color(target) != mover_color:
                        return 'promotion_threat', f"兵 @{idx_to_sq(pf, pr)} 可吃子升变"
    return None, ''


TACTIC_DETECTORS = [
    ('double_check', detect_double_check),
    ('fork', detect_fork),
    ('pin', detect_pin),
    ('skewer', detect_skewer),
    ('mate_threat', detect_mate_threat),
    ('deflection', detect_deflection),
    ('overload', detect_overload),
    ('capture_defender', detect_capture_defender),
    ('promotion_threat', detect_promotion_threat),
]


def analyze_tactics(game):
    """分析单局对局的战术主题，返回识别到的战术列表"""
    replayer = GameReplayer(game)
    replayer.replay()
    tactics_found = []
    for i, move_info in enumerate(replayer.move_results):
        fen_before = replayer.board_states[i]
        fen_after = replayer.board_states[i + 1]
        board_before = Board(fen_before)
        board_after = Board(fen_after)
        for tactic_key, detector in TACTIC_DETECTORS:
            try:
                result, reason = detector(board_before, board_after, move_info)
                if result:
                    tactics_found.append({
                        'game_index': None,
                        'move_index': i,
                        'move_number': move_info['move_number'],
                        'color': move_info['color'],
                        'san': move_info['san'],
                        'tactic': result,
                        'tactic_name': TACTIC_NAMES.get(result, result),
                        'reason': reason,
                        'fen_before': fen_before,
                        'fen_after': fen_after,
                    })
            except Exception:
                continue
    return tactics_found


def analyze_tactics_file(filepath, game_index=None, player_filter=None):
    """分析 PGN 文件中的战术"""
    games = PGNParser.parse_file(filepath)
    if not games:
        return [], []
    game_indices = range(len(games))
    if game_index is not None:
        gi = max(0, min(game_index - 1, len(games) - 1))
        game_indices = [gi]
    all_tactics = []
    processed_games = []
    for gi in game_indices:
        game = games[gi]
        tags = game.get('tags', {})
        if player_filter:
            white = tags.get('White', '').lower()
            black = tags.get('Black', '').lower()
            pf = player_filter.lower()
            if pf not in white and pf not in black:
                continue
        game_tactics = analyze_tactics(game)
        for t in game_tactics:
            t['game_index'] = gi + 1
            t['white'] = tags.get('White', '?')
            t['black'] = tags.get('Black', '?')
            t['event'] = tags.get('Event', '?')
        all_tactics.extend(game_tactics)
        processed_games.append({
            'index': gi + 1,
            'tags': tags,
            'tactics_count': len(game_tactics),
        })
    return all_tactics, processed_games


def tactics_to_markdown(tactics, processed_games):
    """将战术结果导出为 Markdown 报告"""
    lines = []
    lines.append("# 战术主题识别报告")
    lines.append("")
    lines.append(f"- **扫描对局数**: {len(processed_games)}")
    lines.append(f"- **识别战术总数**: {len(tactics)}")
    lines.append("")
    if len(tactics) == 0:
        lines.append("## 结果")
        lines.append("")
        lines.append("_未识别到任何战术主题_")
        lines.append("")
        return "\n".join(lines)
    by_game = defaultdict(list)
    for t in tactics:
        by_game[t['game_index']].append(t)
    lines.append("## 按对局汇总")
    lines.append("")
    lines.append(f"| 对局 | 白方 | 黑方 | 战术数 |")
    lines.append(f"|------|------|------|--------|")
    for pg in processed_games:
        tags = pg['tags']
        lines.append(f"| {pg['index']} | {tags.get('White', '?')} | {tags.get('Black', '?')} | {pg['tactics_count']} |")
    lines.append("")
    tactic_counter = Counter(t['tactic_name'] for t in tactics)
    lines.append("## 战术类型分布")
    lines.append("")
    lines.append(f"| 战术类型 | 出现次数 |")
    lines.append(f"|----------|----------|")
    for name, count in tactic_counter.most_common():
        lines.append(f"| {name} | {count} |")
    lines.append("")
    for gi in sorted(by_game.keys()):
        game_tactics = by_game[gi]
        sample = game_tactics[0]
        lines.append(f"## 对局 {gi}: {sample['white']} vs {sample['black']}")
        lines.append("")
        if sample.get('event') and sample['event'] != '?':
            lines.append(f"- **赛事**: {sample['event']}")
        lines.append(f"- **识别战术数**: {len(game_tactics)}")
        lines.append("")
        for t in game_tactics:
            move_label = f"{t['move_number']}. " if t['color'] == 'White' else f"{t['move_number']}... "
            lines.append(f"### 回合 {t['move_number']} ({t['color']}): `{move_label}{t['san']}`")
            lines.append("")
            lines.append(f"- **战术主题**: **{t['tactic_name']}**")
            lines.append(f"- **说明**: {t['reason']}")
            lines.append(f"- **走法前 FEN**: `{t['fen_before']}`")
            lines.append(f"- **走法后 FEN**: `{t['fen_after']}`")
            lines.append("")
    return "\n".join(lines)


def tactics_to_json(tactics, processed_games):
    """将战术结果导出为 JSON 报告"""
    games_summary = []
    for pg in processed_games:
        games_summary.append({
            'game_index': pg['index'],
            'tags': pg['tags'],
            'tactics_count': pg['tactics_count'],
        })
    tactics_list = []
    for t in tactics:
        tactics_list.append({
            'game_index': t['game_index'],
            'white': t.get('white', '?'),
            'black': t.get('black', '?'),
            'event': t.get('event', '?'),
            'move_number': t['move_number'],
            'move_index': t['move_index'],
            'color': t['color'],
            'san': t['san'],
            'tactic': t['tactic'],
            'tactic_name': t['tactic_name'],
            'reason': t['reason'],
            'fen_before': t['fen_before'],
            'fen_after': t['fen_after'],
        })
    tactic_counter = Counter(t['tactic_name'] for t in tactics)
    return {
        'summary': {
            'games_scanned': len(processed_games),
            'tactics_found': len(tactics),
            'tactic_distribution': dict(tactic_counter),
        },
        'games': games_summary,
        'tactics': tactics_list,
    }


# ============================================================
# CLI命令实现
# ============================================================

def cmd_list(args):
    """列出PGN文件中的对局"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    # 打印表头
    print(f"{'#':<3} {'赛事':<20} {'白方':<20} {'黑方':<20} {'日期':<12} {'结果':<8} {'回合数':<6}")
    print("-" * 95)
    for i, game in enumerate(games):
        tags = game['tags']
        event = tags.get('Event', '?')[:18]
        white = tags.get('White', '?')[:18]
        black = tags.get('Black', '?')[:18]
        date = tags.get('Date', '?')[:10]
        result = tags.get('Result', '*')
        moves_count = len(game['moves_san'])
        print(f"{i+1:<3} {event:<20} {white:<20} {black:<20} {date:<12} {result:<8} {moves_count:<6}")
    print(f"\n共 {len(games)} 盘对局")
    return 0


def cmd_validate(args):
    """验证PGN走法合法性"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    # 如果指定了game参数，只验证指定对局
    game_indices = range(len(games))
    if args.game is not None:
        game_idx = max(0, min(args.game - 1, len(games) - 1))
        game_indices = [game_idx]
    total_errors = 0
    for i in game_indices:
        game = games[i]
        tags = game['tags']
        white = tags.get('White', '?')
        black = tags.get('Black', '?')
        print(f"\n=== 对局 {i+1}: {white} vs {black} ===")
        replayer = GameReplayer(game, start_fen=args.fen)
        moves, errors = replayer.replay()
        if errors:
            for err in errors:
                print(f"  ✗ 回合 {err['move_number']} ({err['color']}): {err['san']}")
                print(f"    原因: {err['reason']}")
                print(f"    FEN: {err['fen']}")
                total_errors += 1
        else:
            print(f"  ✓ 所有 {len(moves)} 步合法")
    print(f"\n总计: {total_errors} 个错误")
    return 0 if total_errors == 0 else 1


def cmd_board(args):
    """显示指定回合的棋盘"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    game_idx = max(0, min(args.game - 1, len(games) - 1))
    game = games[game_idx]
    replayer = GameReplayer(game)
    replayer.replay()
    move_num = max(0, args.move)
    if move_num > len(replayer.board_states) - 1:
        move_num = len(replayer.board_states) - 1
    board = replayer.get_board_at_move(move_num)
    tags = game['tags']
    print(f"对局 {args.game}: {tags.get('White', '?')} vs {tags.get('Black', '?')}")
    print(f"第 {move_num} 步后")
    print()
    print(board.to_ascii())
    print()
    print(f"FEN: {board.to_fen()}")
    if board.in_check():
        print(f"将军! ({'白方' if board.turn == 'w' else '黑方'}被将军)")
    return 0


def cmd_stats(args):
    """分析统计"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    total_games = len(games)
    white_wins = 0
    black_wins = 0
    draws = 0
    total_moves_white = 0
    total_moves_black = 0
    all_captures = 0
    all_checks = 0
    all_castles_k = 0
    all_castles_q = 0
    all_promotions = 0
    openings = Counter()
    player_wins = defaultdict(lambda: {'wins': 0, 'total': 0})

    for game in games:
        tags = game['tags']
        result = game.get('result', '*')
        white = tags.get('White', '?')
        black = tags.get('Black', '?')
        # 结果统计
        if result == '1-0':
            white_wins += 1
            player_wins[white]['wins'] += 1
        elif result == '0-1':
            black_wins += 1
            player_wins[black]['wins'] += 1
        elif result == '1/2-1/2':
            draws += 1
        # 玩家统计
        player_wins[white]['total'] += 1
        player_wins[black]['total'] += 1
        # 开局检测
        eco_code, eco_name = detect_opening(game['moves_san'])
        openings[f"{eco_code} {eco_name}"] += 1
        # 步数
        total_moves = len(game['moves_san'])
        total_moves_white += (total_moves + 1) // 2
        total_moves_black += total_moves // 2
        # 详细走法统计
        replayer = GameReplayer(game)
        replayer.replay()
        for m in replayer.move_results:
            if m['is_capture']:
                all_captures += 1
            if m['is_check']:
                all_checks += 1
            if m['is_castle_k']:
                all_castles_k += 1
            if m['is_castle_q']:
                all_castles_q += 1
            if m['is_promotion']:
                all_promotions += 1

    print("=" * 60)
    print("PGN对局统计分析")
    print("=" * 60)
    print(f"对局总数:           {total_games}")
    print(f"白方胜:             {white_wins} ({white_wins/total_games*100:.1f}%)")
    print(f"黑方胜:             {black_wins} ({black_wins/total_games*100:.1f}%)")
    print(f"和棋:               {draws} ({draws/total_games*100:.1f}%)")
    if total_games > 0:
        print(f"白方胜率:           {white_wins/total_games*100:.1f}%")
        print(f"黑方胜率:           {black_wins/total_games*100:.1f}%")
    print()
    print(f"平均白方每局步数:   {total_moves_white/total_games:.1f}")
    print(f"平均黑方每局步数:   {total_moves_black/total_games:.1f}")
    print(f"平均每局总步数:     {(total_moves_white+total_moves_black)/total_games:.1f}")
    print()
    print(f"总吃子次数:         {all_captures}")
    print(f"总将军次数:         {all_checks}")
    print(f"短易位次数:         {all_castles_k}")
    print(f"长易位次数:         {all_castles_q}")
    print(f"升变次数:           {all_promotions}")
    print()
    print("开局分布 (Top 10):")
    for opening, count in openings.most_common(10):
        print(f"  {opening:<30} {count} 局")
    return 0


def cmd_export_fen(args):
    """导出FEN"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    game_idx = max(0, min(args.game - 1, len(games) - 1))
    game = games[game_idx]
    replayer = GameReplayer(game)
    replayer.replay()
    move_num = max(0, args.move)
    if move_num > len(replayer.board_states) - 1:
        move_num = len(replayer.board_states) - 1
    fen = replayer.board_states[move_num]
    print(fen)
    if args.output:
        with open(args.output, 'w') as f:
            f.write(fen + '\n')
    return 0


def cmd_timeline(args):
    """生成Markdown时间线"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    output_lines = []
    # 如果指定了game参数，只处理指定对局
    game_indices = range(len(games))
    if args.game is not None:
        game_idx = max(0, min(args.game - 1, len(games) - 1))
        game_indices = [game_idx]
    for i in game_indices:
        game = games[i]
        tags = game['tags']
        white = tags.get('White', '?')
        black = tags.get('Black', '?')
        event = tags.get('Event', '?')
        date = tags.get('Date', '?')
        result = game.get('result', '*')
        output_lines.append(f"# 对局 {i+1}: {white} vs {black}")
        output_lines.append("")
        output_lines.append(f"- **赛事**: {event}")
        output_lines.append(f"- **日期**: {date}")
        output_lines.append(f"- **白方**: {white}")
        output_lines.append(f"- **黑方**: {black}")
        output_lines.append(f"- **结果**: {result}")
        output_lines.append("")
        output_lines.append("## 关键事件时间线")
        output_lines.append("")
        replayer = GameReplayer(game)
        replayer.replay()
        event_count = 0
        for m in replayer.move_results:
            events = []
            if m['is_capture']:
                cap = m['captured']
                if cap.upper() == 'Q':
                    events.append(f"**吃后** ({cap})")
                else:
                    events.append(f"吃子 ({cap})")
            if m['is_promotion']:
                events.append(f"**兵升变** → {m['promoted_to']}")
            if m['is_mate']:
                events.append("**将死！**")
            elif m['is_check']:
                events.append("将军")
            if m['is_castle_k']:
                events.append("短易位")
            if m['is_castle_q']:
                events.append("长易位")
            if events:
                move_label = f"{m['move_number']}. " if m['color'] == 'White' else f"{m['move_number']}... "
                output_lines.append(f"- 回合 {m['move_number']} ({m['color']}): `{move_label}{m['san']}` - {', '.join(events)}")
                event_count += 1
        if event_count == 0:
            output_lines.append("_无特殊事件_")
        output_lines.append("")
        # 结果事件
        if result != '*':
            result_str = {
                '1-0': '白方获胜',
                '0-1': '黑方获胜',
                '1/2-1/2': '和棋',
            }.get(result, result)
            output_lines.append(f"- **最终结果**: {result_str}")
            output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

    md_content = "\n".join(output_lines)
    print(md_content)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(md_content)
    return 0


def cmd_filter(args):
    """检索过滤"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    games = PGNParser.parse_file(args.file)
    if not games:
        print("未找到对局")
        return 0
    filtered = []
    for game in games:
        tags = game['tags']
        # 棋手过滤
        if args.player:
            white = tags.get('White', '').lower()
            black = tags.get('Black', '').lower()
            player = args.player.lower()
            if player not in white and player not in black:
                continue
        # 结果过滤
        if args.result:
            if game.get('result', '*') != args.result:
                continue
        # 日期范围
        if args.from_date or args.to_date:
            date_str = tags.get('Date', '')
            try:
                game_date = datetime.strptime(date_str, '%Y.%m.%d')
            except:
                try:
                    game_date = datetime.strptime(date_str, '%Y-%m-%d')
                except:
                    game_date = None
            if game_date:
                if args.from_date:
                    try:
                        from_dt = datetime.strptime(args.from_date, '%Y-%m-%d')
                        if game_date < from_dt:
                            continue
                    except:
                        pass
                if args.to_date:
                    try:
                        to_dt = datetime.strptime(args.to_date, '%Y-%m-%d')
                        if game_date > to_dt:
                            continue
                    except:
                        pass
        # 开局过滤
        if args.opening:
            eco_code, eco_name = detect_opening(game['moves_san'])
            opening_text = f"{eco_code} {eco_name}".lower()
            if args.opening.lower() not in opening_text:
                continue
        filtered.append(game)

    print(f"过滤结果: {len(filtered)} / {len(games)} 盘对局")
    # 导出PGN
    if args.output_pgn:
        with open(args.output_pgn, 'w', encoding='utf-8') as f:
            for game in filtered:
                for k, v in game['tags'].items():
                    f.write(f'[{k} "{v}"]\n')
                f.write('\n')
                moves = game['moves_san']
                line = ''
                for i, m in enumerate(moves):
                    if i % 2 == 0:
                        line += f"{i//2+1}. {m} "
                    else:
                        line += f"{m} "
                    if len(line) > 70:
                        f.write(line.strip() + '\n')
                        line = ''
                if line:
                    f.write(line.strip() + '\n')
                f.write(f"{game.get('result', '*')}\n\n")
        print(f"已导出PGN: {args.output_pgn}")
    # 导出JSON
    if args.output_json:
        json_data = []
        for game in filtered:
            json_data.append({
                'tags': game['tags'],
                'result': game.get('result', '*'),
                'moves': game['moves_san'],
                'total_moves': len(game['moves_san']),
            })
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"已导出JSON: {args.output_json}")
    return 0


def cmd_tactics(args):
    """战术主题识别与关键局面导出"""
    if not os.path.exists(args.file):
        print(f"错误：文件不存在: {args.file}")
        return 1
    tactics, processed_games = analyze_tactics_file(
        args.file,
        game_index=args.game,
        player_filter=args.player,
    )
    if len(tactics) == 0:
        print("未识别到任何战术主题")
        if args.output_md:
            md_content = tactics_to_markdown(tactics, processed_games)
            with open(args.output_md, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"已导出Markdown报告: {args.output_md}")
        if args.output_json:
            json_data = tactics_to_json(tactics, processed_games)
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"已导出JSON报告: {args.output_json}")
        return 0
    print(f"扫描完成: {len(processed_games)} 盘对局，识别到 {len(tactics)} 个战术主题")
    print()
    tactic_counter = Counter(t['tactic_name'] for t in tactics)
    print("战术类型分布:")
    for name, count in tactic_counter.most_common():
        print(f"  {name:<10} {count}")
    print()
    by_game = defaultdict(list)
    for t in tactics:
        by_game[t['game_index']].append(t)
    for gi in sorted(by_game.keys()):
        game_tactics = by_game[gi]
        sample = game_tactics[0]
        print(f"=== 对局 {gi}: {sample['white']} vs {sample['black']} ({len(game_tactics)} 个战术) ===")
        for t in game_tactics:
            move_label = f"{t['move_number']}. " if t['color'] == 'White' else f"{t['move_number']}... "
            print(f"  [{t['tactic_name']}] 回合 {t['move_number']} ({t['color']}): {move_label}{t['san']}")
            print(f"    原因: {t['reason']}")
            print(f"    FEN前: {t['fen_before']}")
            print(f"    FEN后: {t['fen_after']}")
            print()
    if args.output_md:
        md_content = tactics_to_markdown(tactics, processed_games)
        with open(args.output_md, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"已导出Markdown报告: {args.output_md}")
    if args.output_json:
        json_data = tactics_to_json(tactics, processed_games)
        with open(args.output_json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"已导出JSON报告: {args.output_json}")
    return 0


# ============================================================
# 主CLI入口
# ============================================================

def build_parser():
    parser = argparse.ArgumentParser(
        prog='pgnlab',
        description='国际象棋PGN解析和对局分析CLI工具',
    )
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # list
    p_list = subparsers.add_parser('list', help='列出对局信息')
    p_list.add_argument('file', help='PGN文件路径')
    p_list.set_defaults(func=cmd_list)

    # validate
    p_validate = subparsers.add_parser('validate', help='验证走法合法性')
    p_validate.add_argument('file', help='PGN文件路径')
    p_validate.add_argument('--game', type=int, default=None, help='指定对局编号(从1开始，不指定则验证所有对局)')
    p_validate.add_argument('--fen', default=None, help='起始FEN位置')
    p_validate.set_defaults(func=cmd_validate)

    # board
    p_board = subparsers.add_parser('board', help='显示棋盘')
    p_board.add_argument('file', help='PGN文件路径')
    p_board.add_argument('--game', type=int, default=1, help='对局编号(从1开始)')
    p_board.add_argument('--move', type=int, default=0, help='步数(0为初始局面)')
    p_board.set_defaults(func=cmd_board)

    # stats
    p_stats = subparsers.add_parser('stats', help='统计分析')
    p_stats.add_argument('file', help='PGN文件路径')
    p_stats.set_defaults(func=cmd_stats)

    # export-fen
    p_fen = subparsers.add_parser('export-fen', help='导出FEN')
    p_fen.add_argument('file', help='PGN文件路径')
    p_fen.add_argument('--game', type=int, default=1, help='对局编号')
    p_fen.add_argument('--move', type=int, default=0, help='步数')
    p_fen.add_argument('--output', '-o', help='输出文件')
    p_fen.set_defaults(func=cmd_export_fen)

    # timeline
    p_tl = subparsers.add_parser('timeline', help='生成Markdown时间线')
    p_tl.add_argument('file', help='PGN文件路径')
    p_tl.add_argument('--game', type=int, default=None, help='指定对局编号(从1开始，不指定则导出所有对局)')
    p_tl.add_argument('--output', '-o', help='输出Markdown文件')
    p_tl.set_defaults(func=cmd_timeline)

    # filter
    p_filter = subparsers.add_parser('filter', help='检索过滤对局')
    p_filter.add_argument('file', help='PGN文件路径')
    p_filter.add_argument('--player', help='棋手姓名(部分匹配)')
    p_filter.add_argument('--result', choices=['1-0', '0-1', '1/2-1/2', '*'], help='结果')
    p_filter.add_argument('--opening', help='开局名称(部分匹配)')
    p_filter.add_argument('--from-date', help='起始日期 YYYY-MM-DD')
    p_filter.add_argument('--to-date', help='结束日期 YYYY-MM-DD')
    p_filter.add_argument('--output-pgn', help='导出筛选后的PGN')
    p_filter.add_argument('--output-json', help='导出筛选后的JSON')
    p_filter.set_defaults(func=cmd_filter)

    # tactics
    p_tactics = subparsers.add_parser('tactics', help='战术主题识别与关键局面导出')
    p_tactics.add_argument('file', help='PGN文件路径')
    p_tactics.add_argument('--game', type=int, default=None, help='指定对局编号(从1开始，不指定则扫描所有对局)')
    p_tactics.add_argument('--player', help='按棋手姓名过滤(部分匹配)')
    p_tactics.add_argument('--output-md', help='导出Markdown报告')
    p_tactics.add_argument('--output-json', help='导出JSON报告')
    p_tactics.set_defaults(func=cmd_tactics)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
