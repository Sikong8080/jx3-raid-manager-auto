import calendar
from datetime import timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime as dt
import json

import sys
import tkinter.font as tkFont
import platform
import locale
import re
import threading
import time

import os
import sys

os.environ['MPLBACKEND'] = 'Agg'

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.backends.backend_agg
    import matplotlib.backends.backend_tkagg
    import matplotlib.figure
    import matplotlib.pyplot as plt
    plt.switch_backend('Agg')
except ImportError as e:
    print(f"Matplotlib 导入警告: {e}")

import calendar
from datetime import timedelta

SCALE_FACTOR = 1

try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    import mplcursors 
    matplotlib.use('TkAgg')
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_app_data_path():
    if platform.system() == "Windows":
        app_data = os.getenv('APPDATA')
        app_dir = os.path.join(app_data, "JX3DungeonTracker")
    elif platform.system() == "Darwin":
        app_dir = os.path.expanduser("~/Library/Application Support/JX3DungeonTracker")
    else:
        app_dir = os.path.expanduser("~/.jx3dungeontracker")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

def get_current_time():
    try:
        now = dt.datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")
    except:
        now = dt.datetime.utcnow()
        return now.strftime("%Y-%m-%d %H:%M:%S")

class DatabaseManager:
    def __init__(self, db_path):
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON")
        self.initialize_tables()
        self.load_preset_dungeons()
        self.upgrade_database()

    def initialize_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dungeons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                special_drops TEXT,
                is_public INTEGER DEFAULT 0
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dungeon_id INTEGER NOT NULL,
                trash_gold INTEGER DEFAULT 0,
                iron_gold INTEGER DEFAULT 0,
                other_gold INTEGER DEFAULT 0,
                special_auctions TEXT,
                total_gold INTEGER DEFAULT 0,
                black_owner TEXT,
                worker TEXT,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                team_type TEXT,
                lie_down_count INTEGER DEFAULT 0,
                fine_gold INTEGER DEFAULT 0,
                subsidy_gold INTEGER DEFAULT 0,
                personal_gold INTEGER DEFAULT 0,
                note TEXT DEFAULT '',
                is_new INTEGER DEFAULT 0,
                scattered_consumption INTEGER DEFAULT 0,
                iron_consumption INTEGER DEFAULT 0,
                special_consumption INTEGER DEFAULT 0,
                other_consumption INTEGER DEFAULT 0,
                total_consumption INTEGER DEFAULT 0,
                FOREIGN KEY (dungeon_id) REFERENCES dungeons (id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS column_widths (
                tree_name TEXT PRIMARY KEY,
                widths TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS window_state (
                width INTEGER,
                height INTEGER,
                maximized INTEGER DEFAULT 0,
                x INTEGER,
                y INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pane_positions (
                pane_name TEXT PRIMARY KEY,
                position INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL UNIQUE,
                remark TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS filled_uids (
                uid TEXT PRIMARY KEY,
                fill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def upgrade_database(self):
        try:
            self.cursor.execute("PRAGMA table_info(dungeons)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'is_public' not in columns:
                self.cursor.execute("ALTER TABLE dungeons ADD COLUMN is_public INTEGER DEFAULT 0")
            
            self.cursor.execute("PRAGMA table_info(records)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'is_new' not in columns:
                self.cursor.execute("ALTER TABLE records ADD COLUMN is_new INTEGER DEFAULT 0")
            consumption_columns = [
                'scattered_consumption', 
                'iron_consumption', 
                'special_consumption', 
                'other_consumption', 
                'total_consumption'
            ]
            for col in consumption_columns:
                if col not in columns:
                    self.cursor.execute(f"ALTER TABLE records ADD COLUMN {col} INTEGER DEFAULT 0")
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='window_state'")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    CREATE TABLE window_state (
                        width INTEGER,
                        height INTEGER,
                        maximized INTEGER DEFAULT 0,
                        x INTEGER,
                        y INTEGER
                    )
                ''')
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pane_positions'")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    CREATE TABLE pane_positions (
                        pane_name TEXT PRIMARY KEY,
                        position INTEGER
                    )
                ''')
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_files'")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    CREATE TABLE analysis_files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL UNIQUE,
                        remark TEXT
                    )
                ''')
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='filled_uids'")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    CREATE TABLE filled_uids (
                        uid TEXT PRIMARY KEY,
                        fill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='column_widths'")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    CREATE TABLE column_widths (
                        tree_name TEXT PRIMARY KEY,
                        widths TEXT
                    )
                ''')
            
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dungeons'")
            if not self.cursor.fetchone():
                self.cursor.execute('''
                    CREATE TABLE dungeons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        special_drops TEXT,
                        is_public INTEGER DEFAULT 0
                    )
                ''')
            
            self.conn.commit()
        except Exception as e:
            import traceback
            traceback.print_exc()

    def load_preset_dungeons(self):
        # 首先添加公共预设（置顶）
        public_dungeon = ("公共预设", "《寸险律·残卷》,《纵横之剑·阖》,《纵横之剑·捭》,《蜀山剑诀·秘卷》,《圣灵心法·秘卷》,《月朔实录·残卷》,《易筋经·秘卷》,《惊羽诀·秘卷》,《离经易道·秘卷》,《纯阳别册·残卷》,《气经·残卷》,《冰心诀·秘卷》", 1)
        self.cursor.execute('''
            INSERT OR IGNORE INTO dungeons (name, special_drops, is_public) 
            VALUES (?, ?, ?)
        ''', public_dungeon)
        
        # 然后添加其他预设副本
        dungeons = [
            ("狼牙堡·狼神殿", "阿豪（宠物）,遗忘的书函（外观）,醉月玄晶（95级）", 0),
            ("敖龙岛", "赤纹野正宗（腰部挂件）,隐狐匿踪（特殊面部）,木木（宠物）,星云踏月骓（普通坐骑）,归墟玄晶（100级）", 0),
            ("范阳夜变", "簪花空竹（腰部挂件）,弃身·肆（特殊腰部）,幽明录（宠物）,润州绣舞筵（家具）,聆音（特殊腰部）,夜泊蝶影（披风）,归墟玄晶（100级）", 0),
            ("达摩洞", "活色生香（腰部挂件）,冰蚕龙渡（腰部挂件）,猿神发带（头饰）,漫漫香罗（奇趣坐骑）,阿修罗像（家具）,天乙玄晶（110级）", 0),
            ("白帝江关", "鲤跃龙门（背部挂件）,血佑铃（腰部挂件）,御马踏金·头饰（马具）,御马踏金·鞍饰（马具）,御马踏金·足饰（马具）,御马踏金（马具）,飞毛将军（普通坐骑）,阔豪（脚印）,天乙玄晶（110级）", 0),
            ("雷域大泽", "大眼崽（宠物）,灵虫石像（家具）,脊骨王座（家具）,掠影无迹（背部挂件）,荒原切（腰部挂件）,游空竹翼（背部挂件）,天乙玄晶（110级）", 0),
            ("河阳之战", "爆炸（头顶表情）,北拒风狼（家具）,百战同心（家具）,云鹤报捷（玩具）,玄域辟甲·头饰（马具）,玄域辟甲·鞍饰（马具）,玄域辟甲·足饰（马具）,玄域辟甲（马具）,扇风耳（宠物）,墨言（特殊背部）,天乙玄晶（110级）", 0),
            ("西津渡", "卯金修德（背部挂件）,相思尽（腰部挂件）,比翼剪（背部挂件）,静子（宠物）,泽心龙头像（家具）,焚金阙（外观）,赤发狻猊（头饰）,太一玄晶（120级）", 0),
            ("武狱黑牢", "驭己刃（腰部挂件）,象心灵犀（玩具）,心定（头饰）,幽兰引芳（脚印）,武氏挂旗（家具）,白鬼血泣（披风）,太一玄晶（120级）", 0),
            ("九老洞", "武圣（背部挂件）,不渡（特殊腰部）,灵龟·卜逆（奇趣坐骑）,朱雀·灼（家具）,青龙·木（家具）,麒麟·祝瑞（宠物）,幻月（特殊腰部）,太一玄晶（120级）", 0),
            ("冷龙峰", "涉海翎（帽子）,透骨香（腰部挂件）,转珠天轮（玩具）,鸷（宠物）,炽芒·邪锋（特殊腰部）,祆教神鸟像（家具）,太一玄晶（120级）", 0)
        ]
        self.cursor.executemany('''
            INSERT OR IGNORE INTO dungeons (name, special_drops, is_public) 
            VALUES (?, ?, ?)
        ''', dungeons)
        self.conn.commit()

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def execute_update(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def close(self):
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn:
                self.conn.commit()
                self.conn.close()
        except Exception:
            pass
        finally:
            self.cursor = None
            self.conn = None

    def get_pane_position(self, pane_name):
        result = self.execute_query("SELECT position FROM pane_positions WHERE pane_name = ?", (pane_name,))
        return result[0][0] if result else None

    def save_pane_position(self, pane_name, position):
        self.execute_update('''
            INSERT OR REPLACE INTO pane_positions (pane_name, position) 
            VALUES (?, ?)
        ''', (pane_name, position))

    def dungeon_exists(self, dungeon_name):
        result = self.execute_query("SELECT COUNT(*) FROM dungeons WHERE name = ?", (dungeon_name,))
        return result[0][0] > 0

class SpecialItemsTree:
    def __init__(self, parent):
        self.parent = parent
        self.tree = ttk.Treeview(parent, columns=("item", "price"), show="headings", 
                                height=int(3*SCALE_FACTOR), selectmode="browse")
        self.tree.heading("item", text="物品", anchor="center")
        self.tree.heading("price", text="金额", anchor="center")
        self.tree.column("item", width=int(120*SCALE_FACTOR), anchor=tk.CENTER)
        self.tree.column("price", width=int(60*SCALE_FACTOR), anchor=tk.CENTER)
        style = ttk.Style()
        style.configure("Special.Treeview", font=("PingFang SC", int(9*SCALE_FACTOR)), 
                       rowheight=int(24*SCALE_FACTOR))
        self.tree.configure(style="Special.Treeview")
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.setup_context_menu()

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="删除选中项", command=self.delete_selected_items)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def delete_selected_items(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            self.tree.delete(item)

    def clear(self):
        self.tree.delete(*self.tree.get_children())

    def add_item(self, item, price):
        self.tree.insert("", "end", values=(item, price))

    def get_items(self):
        items = []
        for child in self.tree.get_children():
            values = self.tree.item(child, 'values')
            items.append({"item": values[0], "price": values[1]})
        return items

    def calculate_total(self):
        total = 0
        for child in self.tree.get_children():
            values = self.tree.item(child, 'values')
            try:
                total += int(values[1])
            except ValueError:
                pass
        return total

class GoldCalculator:
    @staticmethod
    def safe_int(value):
        try:
            return int(value) if value != "" else 0
        except ValueError:
            return 0

    @classmethod
    def calculate_total(cls, trash, iron, other, special):
        return cls.safe_int(trash) + cls.safe_int(iron) + cls.safe_int(other) + cls.safe_int(special)

class DBAnalyzer:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app
        self.db_folders = {}
        self.analysis_results = []
        self.filled_uids = set()
        self.optimize_patterns()
        self.batch_size = 5000
        self.max_file_size_mb = 100
        self.setup_ui()
        self.load_folder_list()
        self.load_filled_uids()

    def optimize_patterns(self):
        self.patterns = {
            'start': re.compile(r'^你悄悄地对\[[^\]]+\]说：开始自动记录\[(.*?)\]$'),
            'end': re.compile(r'^你悄悄地对\[[^\]]+\]说：结束自动记录\[(.*?)\]$'),
            'team_info': re.compile(
                r'\[房间\]\[([^\]]+)\]：拍团目前总收入为：(\d+)金，'
                r'补贴总费用：(\d+)金，\s*实际可用分配金额：(\d+)金，'
                r'\s*分配人数：(\d+)，\s*每人底薪：(\d+)金'
            ),
            'personal_salary_named': re.compile(r'text="(\d+)"[^>]*name="Text_(GoldB|Gold|Silver|Copper)"'),
            'penalty': re.compile(r'\[房间\]\[([^\]]+)\]：.*?向团队里追加了\[(\d+金砖(?:\d+金)?|\d+金)\]'),
            'item_purchase': re.compile(r'\[房间\]\[([^\]]+)\]：\[([^\]]+)\]花费\[(.*?)\]购买了\[(.*?)\]'),
            'gold_amount': re.compile(r'(\d+)金砖|(\d+)金')
        }
        self.fixed_rules = {
            "scattered_keywords": ["五行石", "五彩石", "上品茶饼", "猫眼石", "玛瑙"],
            "iron_keywords": ["陨铁"]
        }
        self.gkp_patterns = [
            re.compile(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})_(\d+人)(普通|英雄|挑战)?(.*?)\.gkp\.jx3dat'),
            re.compile(r'(\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})_(.*?)\.gkp\.jx3dat')
        ]

    def scan_gkp_files(self, folder_path):
        gkp_data = []
        gkp_folder = os.path.join(folder_path, "userdata", "gkp")
        if not os.path.exists(gkp_folder):
            return gkp_data
        try:
            for file_name in os.listdir(gkp_folder):
                if file_name.endswith('.gkp.jx3dat'):
                    file_path = os.path.join(gkp_folder, file_name)
                    if os.path.isfile(file_path):
                        gkp_info = None
                        for pattern in self.gkp_patterns:
                            match = pattern.search(file_name)
                            if match:
                                if len(match.groups()) == 4:
                                    start_time_str = match.group(1)
                                    team_type = match.group(2)
                                    difficulty = match.group(3) or "普通"
                                    dungeon_name = match.group(4).strip()
                                else:
                                    start_time_str = match.group(1)
                                    dungeon_name = match.group(2).strip()
                                    team_type = "十人本"
                                    difficulty = ""
                                start_time = dt.datetime.strptime(start_time_str, '%Y-%m-%d-%H-%M-%S')
                                end_time = dt.datetime.fromtimestamp(os.path.getmtime(file_path))
                                gkp_info = {
                                    'start_time': start_time,
                                    'end_time': end_time,
                                    'team_type': team_type,
                                    'difficulty': difficulty,
                                    'dungeon_name': dungeon_name,
                                    'file_name': file_name
                                }
                                break
                        if gkp_info:
                            gkp_data.append(gkp_info)
            gkp_data.sort(key=lambda x: x['start_time'])
        except Exception as e:
            pass
        return gkp_data

    def match_chatlog_with_gkp(self, chatlog_records, gkp_data):
        matched_segments = []
        for gkp in gkp_data:
            start_time = gkp['start_time']
            end_time = gkp['end_time']
            segment_records = []
            for i, (time_ts, text, msg) in enumerate(chatlog_records):
                record_time = dt.datetime.fromtimestamp(time_ts)
                if start_time <= record_time <= end_time:
                    segment_records.append((i, time_ts, text, msg))
            if segment_records:
                start_idx = segment_records[0][0]
                end_idx = segment_records[-1][0]
                start_time_ts = segment_records[0][1]
                end_time_ts = segment_records[-1][1]
                matched_segments.append({
                    'start_idx': start_idx,
                    'end_idx': end_idx,
                    'start_time': start_time_ts,
                    'end_time': end_time_ts,
                    'gkp_info': gkp,
                    'records': [r[2:] for r in segment_records]
                })
        return matched_segments

    def analyze_db_file_with_gkp(self, db_file, folder_path, remark):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT time, text, msg FROM chatlog ORDER BY time")
            all_records = cursor.fetchall()
            conn.close()
            if not all_records:
                return [self.create_empty_result(os.path.basename(db_file), remark)]
            gkp_data = self.scan_gkp_files(folder_path)
            all_results = []
            if gkp_data:
                matched_segments = self.match_chatlog_with_gkp(all_records, gkp_data)
                for segment in matched_segments:
                    result = self.analyze_single_record_segment_with_gkp(
                        segment, remark, os.path.basename(db_file)
                    )
                    if result:
                        all_results.append(result)
            chatlog_results = self.analyze_records_optimized(all_records, remark, os.path.basename(db_file))
            existing_uids = {r["uid"] for r in all_results}
            for result in chatlog_results:
                if result["uid"] not in existing_uids:
                    all_results.append(result)
            if not all_results:
                all_results.append(self.create_empty_result(os.path.basename(db_file), remark))
            return all_results
        except Exception as e:
            return [self.create_empty_result(os.path.basename(db_file), remark)]

    def analyze_single_record_segment_with_gkp(self, segment, remark, filename):
        gkp_info = segment['gkp_info']
        team_type = gkp_info['team_type']
        dungeon_name = gkp_info['dungeon_name']
        difficulty = gkp_info['difficulty']
        if team_type == "未知":
            team_type = "十人本"
        elif "10" in team_type:
            team_type = "十人本"
        elif "25" in team_type:
            team_type = "二十五人本"
        analysis_data = {
            "dungeon_name": dungeon_name,
            "team_type": team_type,
            "difficulty_note": difficulty,
            "black_person": "",
            "personal_salaries": [],
            "team_total_salary": 0,
            "subsidy_total": 0,
            "actual_distributable": 0,
            "distribution_count": 0,
            "base_salary": 0,
            "penalty_total": 0,
            "lie_count": 0,
            "scattered_total": 0,
            "iron_total": 0,
            "other_total": 0,
            "special_total": 0,
            "special_items": [],
            "scattered_consumption": 0,
            "iron_consumption": 0,
            "special_consumption": 0,
            "other_consumption": 0,
            "total_consumption": 0,
            "worker": remark,
            "record_index": 0,
            "priority3_leaders": {},
            "priority2_leaders": {},
            "priority1_leaders": {}
        }
        # 获取当前副本和公共预设的特殊物品
        current_dungeon_special_items = self.get_special_items_for_dungeon(dungeon_name)
        public_special_items = self.get_public_special_items()
        all_special_items = current_dungeon_special_items + public_special_items
        for text, msg in segment['records']:
            self.analyze_single_line_with_consumption(text, msg, analysis_data, all_special_items, remark)
        analysis_data["lie_count"] = self.calculate_lie_count(
            analysis_data["team_type"], 
            analysis_data["distribution_count"]
        )
        analysis_data["total_consumption"] = (
            analysis_data["scattered_consumption"] + 
            analysis_data["iron_consumption"] + 
            analysis_data["special_consumption"] + 
            analysis_data["other_consumption"]
        )
        return self.calculate_final_result_with_gkp(analysis_data, segment, remark, filename, gkp_info)

    def determine_black_person(self, analysis_data):
        black_person = ""

        if "priority3_leaders" in analysis_data and analysis_data["priority3_leaders"]:
            earliest_index = float('inf')
            earliest_leader = ""
            for leader, info in analysis_data["priority3_leaders"].items():
                if info["index"] < earliest_index:
                    earliest_index = info["index"]
                    earliest_leader = leader
            return earliest_leader

        if "priority2_leaders" in analysis_data and analysis_data["priority2_leaders"]:
            earliest_index = float('inf')
            earliest_leader = ""
            for leader, info in analysis_data["priority2_leaders"].items():
                if info["index"] < earliest_index:
                    earliest_index = info["index"]
                    earliest_leader = leader
            return earliest_leader
        
        if "priority1_leaders" in analysis_data and analysis_data["priority1_leaders"]:
            earliest_index = float('inf')
            earliest_leader = ""
            for leader, info in analysis_data["priority1_leaders"].items():
                if info["index"] < earliest_index:
                    earliest_index = info["index"]
                    earliest_leader = leader
            return earliest_leader
        
        return black_person

    def calculate_final_result_with_gkp(self, analysis_data, segment, remark, filename, gkp_info):
        black_person = self.determine_black_person(analysis_data)

        if not black_person and analysis_data.get("black_person"):
            black_person = analysis_data["black_person"]

        personal_salary = max(analysis_data["personal_salaries"]) if analysis_data["personal_salaries"] else 0
        note_parts = []

        if analysis_data.get("difficulty_note") and analysis_data["difficulty_note"]:
            note_parts.append(analysis_data["difficulty_note"])

        if personal_salary == 10:
            personal_salary = 0
            note_parts.append("躺拍")
            if analysis_data["penalty_total"] > 0:
                note_parts.append(f"抵消{analysis_data['penalty_total']}金")
        
        note = "，".join(note_parts)

        subsidy = 0
        if personal_salary > 0:
            if personal_salary > analysis_data["base_salary"]:
                subsidy = personal_salary - analysis_data["base_salary"]

        start_time_str = dt.datetime.fromtimestamp(segment['start_time']).strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = dt.datetime.fromtimestamp(segment['end_time']).strftime('%Y-%m-%d %H:%M:%S')

        analysis_result = {
            "filename": filename,
            "remark": remark,
            "start_time": start_time_str,
            "end_time": end_time_str,
            "dungeon_name": analysis_data["dungeon_name"],
            "black_person": black_person,
            "worker": remark,
            "team_total_salary": analysis_data["team_total_salary"],
            "personal_salary": personal_salary,
            "subsidy": subsidy,
            "penalty_total": analysis_data["penalty_total"],
            "scattered_total": analysis_data["scattered_total"],
            "iron_total": analysis_data["iron_total"],
            "other_total": analysis_data["other_total"],
            "special_total": analysis_data["special_total"],
            "special_items": analysis_data["special_items"],
            "team_type": analysis_data["team_type"],
            "lie_count": analysis_data["lie_count"],
            "note": note,
            "scattered_consumption": analysis_data["scattered_consumption"],
            "iron_consumption": analysis_data["iron_consumption"],
            "special_consumption": analysis_data["special_consumption"],
            "other_consumption": analysis_data["other_consumption"],
            "total_consumption": analysis_data["total_consumption"],
            "gkp_file": gkp_info['file_name']
        }

        analysis_result["uid"] = self.generate_uid(analysis_result)
        return analysis_result

    def setup_ui(self):
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=int(10*SCALE_FACTOR), pady=int(10*SCALE_FACTOR))
        file_frame = ttk.LabelFrame(main_frame, text="数据库文件夹列表", padding=int(8*SCALE_FACTOR))
        file_frame.pack(fill=tk.X, pady=(0, int(10*SCALE_FACTOR)))
        tree_container = ttk.Frame(file_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, pady=(0, int(5*SCALE_FACTOR)))
        columns = ("folder", "remark")
        self.file_treeview = ttk.Treeview(tree_container, columns=columns, show="headings", height=6)
        self.file_treeview.heading("folder", text="文件夹路径", anchor="center")
        self.file_treeview.heading("remark", text="打工仔", anchor="center")
        self.file_treeview.column("folder", width=int(400*SCALE_FACTOR), anchor=tk.CENTER)
        self.file_treeview.column("remark", width=int(150*SCALE_FACTOR), anchor=tk.CENTER)
        file_vsb = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.file_treeview.yview)
        file_hsb = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=self.file_treeview.xview)
        self.file_treeview.configure(yscrollcommand=file_vsb.set, xscrollcommand=file_hsb.set)
        self.file_treeview.grid(row=0, column=0, sticky="nsew")
        file_vsb.grid(row=0, column=1, sticky="ns")
        file_hsb.grid(row=1, column=0, sticky="ew")
        tree_container.columnconfigure(0, weight=1)
        tree_container.rowconfigure(0, weight=1)
        self.file_treeview.bind('<<TreeviewSelect>>', self.on_treeview_select)
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        ttk.Button(btn_frame, text="添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(btn_frame, text="移除文件夹", command=self.remove_folder).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(btn_frame, text="清空列表", command=self.clear_folders).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(btn_frame, text="保存列表", command=self.save_folder_list).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        remark_frame = ttk.Frame(file_frame)
        remark_frame.pack(fill=tk.X)
        ttk.Label(remark_frame, text="路径备注:").pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        self.remark_entry = ttk.Entry(remark_frame, width=int(30*SCALE_FACTOR))
        self.remark_entry.pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(remark_frame, text="修改选中路径备注", command=self.edit_selected_remark).pack(side=tk.LEFT)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, int(10*SCALE_FACTOR)))
        ttk.Button(control_frame, text="开始分析", command=self.start_analysis).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(control_frame, text="填充到表单", command=self.fill_form).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        self.progress_frame = ttk.LabelFrame(main_frame, text="分析进度", padding=int(8*SCALE_FACTOR))
        self.progress_frame.pack(fill=tk.X, pady=(0, int(10*SCALE_FACTOR)))
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        self.status_var = tk.StringVar(value="准备就绪")
        self.status_label = ttk.Label(self.progress_frame, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X)
        result_frame = ttk.LabelFrame(main_frame, text="分析结果", padding=int(8*SCALE_FACTOR))
        result_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("uid", "start_time", "end_time", "dungeon_name", "black_person", "worker", 
                "team_total", "personal", "consumption", "subsidy", "penalty", "scattered", "iron", "other", "special", 
                "team_type", "lie_count", "note")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15, selectmode="browse")
        column_config = [
            ("uid", "UID", 80),
            ("start_time", "开始时间", 120),
            ("end_time", "结束时间", 120),
            ("dungeon_name", "副本名", 100),
            ("black_person", "团长", 80),
            ("worker", "打工仔", 80),
            ("team_total", "团队总收入", 100),
            ("personal", "个人收入", 80),
            ("consumption", "个人消费", 80),
            ("subsidy", "补贴", 60),
            ("penalty", "罚款", 60),
            ("scattered", "散件金额", 80),
            ("iron", "小铁金额", 80),
            ("other", "其他金额", 80),
            ("special", "特殊金额", 80),
            ("team_type", "团队类型", 80),
            ("lie_count", "躺拍人数", 80),
            ("note", "备注", 100)
        ]
        for col_id, heading, width in column_config:
            self.result_tree.heading(col_id, text=heading, anchor="center")
            self.result_tree.column(col_id, width=int(width*SCALE_FACTOR), anchor=tk.CENTER)
        vsb = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.result_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

    def update_progress(self, value, status=""):
        try:
            self.progress_var.set(value)
            if status:
                self.status_var.set(status)
            self.parent.update_idletasks()
        except Exception as e:
            pass

    def scan_folder_for_db_files(self, folder_path):
        db_files = []
        try:
            if not os.path.exists(folder_path):
                return []
            for file in os.listdir(folder_path):
                if file.endswith('.db'):
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path):
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        max_size = self.max_file_size_mb
                        if file_size_mb <= max_size:
                            db_files.append(file_path)
        except Exception as e:
            pass
        return db_files

    def analyze_db_file_optimized(self, db_file, remark):
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            total_records = cursor.execute("SELECT COUNT(*) FROM chatlog").fetchone()[0]
            if total_records == 0:
                conn.close()
                return []
            all_records = []
            batch_size = self.batch_size
            for offset in range(0, total_records, batch_size):
                cursor.execute(
                    "SELECT time, text, msg FROM chatlog ORDER BY time LIMIT ? OFFSET ?", 
                    (batch_size, offset)
                )
                batch_records = cursor.fetchall()
                all_records.extend(batch_records)
                progress = min(50, (offset + len(batch_records)) / total_records * 50)
                self.update_progress(progress, f"读取数据: {os.path.basename(db_file)}")
            conn.close()
            self.update_progress(60, f"分析记录: {os.path.basename(db_file)}")
            analysis_results = self.analyze_records_optimized(all_records, remark, os.path.basename(db_file))
            self.update_progress(100, f"完成分析: {os.path.basename(db_file)}")
            return analysis_results
        except Exception as e:
            return [self.create_empty_result(os.path.basename(db_file), remark)]

    def analyze_records_optimized(self, records, remark, filename):
        start_positions = []
        end_positions = []
        for i, (time, text, msg) in enumerate(records):
            start_match = self.patterns['start'].search(text)
            if start_match:
                dungeon_info = start_match.group(1)
                start_positions.append((i, time, text, dungeon_info))
            end_match = self.patterns['end'].search(text)
            if end_match:
                dungeon_info = end_match.group(1)
                end_positions.append((i, time, text, dungeon_info))
        if not start_positions or not end_positions:
            return [self.create_empty_result(filename, remark)]
        start_positions.sort(key=lambda x: x[1])
        end_positions.sort(key=lambda x: x[1])
        matched_pairs = self.match_record_pairs(start_positions, end_positions)
        all_results = []
        for start_idx, end_idx, start_time, end_time, start_text, end_text, dungeon_info in matched_pairs:
            result = self.analyze_single_record_segment_optimized(
                records, start_idx, end_idx, remark, filename, dungeon_info
            )
            if result:
                all_results.append(result)
        if not all_results:
            all_results.append(self.create_empty_result(filename, remark))
        return all_results

    def match_record_pairs(self, start_positions, end_positions):
        matched_pairs = []
        used_starts = set()
        used_ends = set()
        for start_idx, start_time, start_text, start_dungeon_info in start_positions:
            if start_idx in used_starts:
                continue
            possible_ends = [
                (idx, t, txt, dungeon_info) for idx, t, txt, dungeon_info in end_positions 
                if idx > start_idx and idx not in used_ends and dungeon_info == start_dungeon_info
            ]
            if possible_ends:
                end_idx, end_time, end_text, end_dungeon_info = min(possible_ends, key=lambda x: x[0])
                matched_pairs.append((start_idx, end_idx, start_time, end_time, start_text, end_text, start_dungeon_info))
                used_starts.add(start_idx)
                used_ends.add(end_idx)
        return matched_pairs

    def process_item_purchase_with_consumption(self, item_match, analysis_data, special_items_list, current_worker):
        room_name = item_match.group(1)
        buyer = item_match.group(2)
        gold_text = item_match.group(3)
        item_name = item_match.group(4)
        item_price = self.parse_gold_amount(gold_text)
        is_worker_purchase = (buyer == current_worker)
        is_special = False
        special_item_name = ""
        for special_item in special_items_list:
            if self.is_special_item_match(item_name, special_item):
                is_special = True
                special_item_name = special_item
                break
        if is_special:
            analysis_data["special_total"] += item_price
            analysis_data["special_items"].append({
                "item": special_item_name,
                "price": item_price,
                "original_name": item_name,
                "buyer": buyer
            })
            if is_worker_purchase:
                analysis_data["special_consumption"] += item_price
        else:
            is_potential_special = self.is_potential_special_item(item_name)
            if is_potential_special:
                return
            is_scattered = any(keyword in item_name for keyword in self.fixed_rules["scattered_keywords"])
            is_iron = any(keyword in item_name for keyword in self.fixed_rules["iron_keywords"])
            if is_worker_purchase:
                if is_scattered:
                    analysis_data["scattered_total"] += item_price
                    analysis_data["scattered_consumption"] += item_price
                elif is_iron:
                    analysis_data["iron_total"] += item_price
                    analysis_data["iron_consumption"] += item_price
                else:
                    analysis_data["other_total"] += item_price
                    analysis_data["other_consumption"] += item_price
            else:
                if is_scattered:
                    analysis_data["scattered_total"] += item_price
                elif is_iron:
                    analysis_data["iron_total"] += item_price
                else:
                    analysis_data["other_total"] += item_price

    def analyze_single_line_with_consumption(self, text, msg, analysis_data, special_items_list, current_worker):
        if "record_index" not in analysis_data:
            analysis_data["record_index"] = 0
        else:
            analysis_data["record_index"] += 1
        
        current_index = analysis_data["record_index"]
        
        if "【团队倒计时】战斗开始！" in text and text.startswith("[团队]"):
            team_start_match = re.search(r'^\[团队\]\[([^\]]+)\].*', text)
            if team_start_match:
                team_leader = team_start_match.group(1)
                
                if "priority3_leaders" not in analysis_data:
                    analysis_data["priority3_leaders"] = {}
                
                if team_leader not in analysis_data["priority3_leaders"]:
                    analysis_data["priority3_leaders"][team_leader] = {
                        "index": current_index,
                        "time": analysis_data.get("record_index", 0)
                    }
        
        if "拍团目前总收入为" in text and text.startswith("[房间]"):
            room_match = re.search(r'^\[房间\]\[([^\]]+)\].*', text)
            if room_match:
                room_leader = room_match.group(1)
                
                if "priority2_leaders" not in analysis_data:
                    analysis_data["priority2_leaders"] = {}
                
                if room_leader not in analysis_data["priority2_leaders"]:
                    analysis_data["priority2_leaders"][room_leader] = {
                        "index": current_index,
                        "time": analysis_data.get("record_index", 0)
                    }

                team_match = self.patterns['team_info'].search(text)
                if team_match:
                    analysis_data.update({
                        "team_total_salary": int(team_match.group(2)),
                        "subsidy_total": int(team_match.group(3)),
                        "actual_distributable": int(team_match.group(4)),
                        "distribution_count": int(team_match.group(5)),
                        "base_salary": int(team_match.group(6))
                    })
        
        elif text.startswith("[房间]") and "拍团目前总收入为" not in text and "将[" in text and "以[" in text and "记录给了[" in text:
            priority1_match = re.search(r'^\[房间\]\[([^\]]+)\].*', text)
            if priority1_match:
                room_leader = priority1_match.group(1)
                
                if "priority1_leaders" not in analysis_data:
                    analysis_data["priority1_leaders"] = {}
                
                if room_leader not in analysis_data["priority1_leaders"]:
                    analysis_data["priority1_leaders"][room_leader] = {
                        "index": current_index,
                        "time": analysis_data.get("record_index", 0)
                    }

        item_match = self.patterns['item_purchase'].search(text)
        if item_match:
            self.process_item_purchase_with_consumption(item_match, analysis_data, special_items_list, current_worker)

        if msg and "你获得：" in msg and ("Text_Gold" in msg or "Text_GoldB" in msg):
            cleaned_msg = re.sub(r'\s+', '', msg)
            matches = self.patterns['personal_salary_named'].findall(cleaned_msg)
            
            if matches:
                gold_bricks = 0
                gold = 0
                silver = 0
                copper = 0
                
                for num, coin_type in matches:
                    try:
                        value = int(num)
                        if coin_type == "GoldB":
                            gold_bricks = value
                        elif coin_type == "Gold":
                            gold = value
                        elif coin_type == "Silver":
                            silver = value
                        elif coin_type == "Copper":
                            copper = value
                    except ValueError:
                        continue

                total_copper = (gold_bricks * 10000 * 10000) + (gold * 10000) + (silver * 100) + copper
                
                if total_copper > 0:
                    salary_amount = round(total_copper / 10000)
                    analysis_data["personal_salaries"].append(salary_amount)

        penalty_match = self.patterns['penalty'].search(text)
        if penalty_match:
            penalty_player = penalty_match.group(1)
            gold_text = penalty_match.group(2)
            penalty_amount = self.parse_gold_amount(gold_text)
            
            analysis_data["other_total"] += penalty_amount
            
            if penalty_player == current_worker:
                analysis_data["penalty_total"] += penalty_amount

    def analyze_single_record_segment_optimized(self, records, start_idx, end_idx, remark, filename, dungeon_info):
        team_type, dungeon_name, difficulty_note = self.parse_dungeon_info(dungeon_info)
        analysis_data = {
            "dungeon_name": dungeon_name,
            "team_type": team_type,
            "difficulty_note": difficulty_note,
            "black_person": "",
            "personal_salaries": [],
            "team_total_salary": 0,
            "subsidy_total": 0,
            "actual_distributable": 0,
            "distribution_count": 0,
            "base_salary": 0,
            "penalty_total": 0,
            "lie_count": 0,
            "scattered_total": 0,
            "iron_total": 0,
            "other_total": 0,
            "special_total": 0,
            "special_items": [],
            "scattered_consumption": 0,
            "iron_consumption": 0,
            "special_consumption": 0,
            "other_consumption": 0,
            "total_consumption": 0,
            "worker": remark,
            "record_index": 0,
            "priority3_leaders": {},
            "priority2_leaders": {},
            "priority1_leaders": {}
        }
        # 获取当前副本和公共预设的特殊物品
        current_dungeon_special_items = self.get_special_items_for_dungeon(dungeon_name)
        public_special_items = self.get_public_special_items()
        all_special_items = current_dungeon_special_items + public_special_items
        for i in range(start_idx, end_idx + 1):
            time, text, msg = records[i]
            self.analyze_single_line_with_consumption(text, msg, analysis_data, all_special_items, remark)
        analysis_data["lie_count"] = self.calculate_lie_count(
            analysis_data["team_type"], 
            analysis_data["distribution_count"]
        )
        analysis_data["total_consumption"] = (
            analysis_data["scattered_consumption"] + 
            analysis_data["iron_consumption"] + 
            analysis_data["special_consumption"] + 
            analysis_data["other_consumption"]
        )
        return self.calculate_final_result(analysis_data, records, start_idx, end_idx, remark, filename)

    def calculate_lie_count(self, team_type, distribution_count):
        if not distribution_count or distribution_count <= 0:
            return 0
        if team_type == "十人本":
            total_players = 10
        elif team_type == "二十五人本":
            total_players = 25
        else:
            return 0
        lie_count = total_players - distribution_count
        return max(0, lie_count)

    def parse_dungeon_info(self, dungeon_info):
        team_type = "未知"
        dungeon_name = "未知副本"
        difficulty_note = ""
        try:
            if "10人" in dungeon_info:
                team_type = "十人本"
                clean_info = dungeon_info.replace("10人", "")
            elif "25人" in dungeon_info:
                team_type = "二十五人本"
                clean_info = dungeon_info.replace("25人", "")
            else:
                clean_info = dungeon_info
            difficulty_patterns = ["普通", "英雄", "挑战", "简单", "困难"]
            found_difficulty = ""
            for pattern in difficulty_patterns:
                if pattern in clean_info:
                    found_difficulty = pattern
                    clean_info = clean_info.replace(pattern, "")
                    break
            if team_type == "二十五人本" and found_difficulty in ["普通", "英雄"]:
                difficulty_note = found_difficulty
            raw_dungeon_name = clean_info.strip()
            dungeon_name = self.find_matching_dungeon(raw_dungeon_name)
        except Exception as e:
            if "10人" in dungeon_info:
                team_type = "十人本"
            elif "25人" in dungeon_info:
                team_type = "二十五人本"
            dungeon_name = self.find_matching_dungeon(dungeon_info)
        return team_type, dungeon_name, difficulty_note

    def find_matching_dungeon(self, raw_dungeon_name):
        dungeons = self.load_all_dungeons()
        for dungeon in dungeons:
            if dungeon in raw_dungeon_name:
                return dungeon
        for dungeon in dungeons:
            if raw_dungeon_name in dungeon:
                return dungeon
        return "未知副本"

    def load_all_dungeons(self):
        if hasattr(self, '_cached_dungeons'):
            return self._cached_dungeons
        try:
            result = self.main_app.db.execute_query("SELECT name FROM dungeons ORDER BY is_public DESC, name")
            self._cached_dungeons = [row[0] for row in result]
            return self._cached_dungeons
        except Exception as e:
            return []

    def get_special_items_for_dungeon(self, dungeon_name):
        try:
            result = self.main_app.db.execute_query(
                "SELECT special_drops FROM dungeons WHERE name = ?", 
                (dungeon_name,)
            )
            if result and result[0][0]:
                items = [item.strip() for item in result[0][0].split(',')]
                return items
            else:
                return []
        except Exception as e:
            return []

    def get_public_special_items(self):
        try:
            result = self.main_app.db.execute_query(
                "SELECT special_drops FROM dungeons WHERE is_public = 1"
            )
            if result and result[0][0]:
                items = [item.strip() for item in result[0][0].split(',')]
                return items
            else:
                return []
        except Exception as e:
            return []

    def calculate_final_result(self, analysis_data, records, start_idx, end_idx, remark, filename):
        black_person = self.determine_black_person(analysis_data)

        if not black_person and analysis_data.get("black_person"):
            black_person = analysis_data["black_person"]

        personal_salary = max(analysis_data["personal_salaries"]) if analysis_data["personal_salaries"] else 0
        note_parts = []

        if analysis_data.get("difficulty_note"):
            note_parts.append(analysis_data["difficulty_note"])

        if personal_salary == 10:
            personal_salary = 0
            note_parts.append("躺拍")
            if analysis_data["penalty_total"] > 0:
                note_parts.append(f"抵消{analysis_data['penalty_total']}金")
        
        note = "，".join(note_parts)

        subsidy = 0
        if personal_salary > 0:
            if personal_salary > analysis_data["base_salary"]:
                subsidy = personal_salary - analysis_data["base_salary"]

        start_time_str = dt.datetime.fromtimestamp(records[start_idx][0]).strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = dt.datetime.fromtimestamp(records[end_idx][0]).strftime('%Y-%m-%d %H:%M:%S')

        analysis_result = {
            "filename": filename,
            "remark": remark,
            "start_time": start_time_str,
            "end_time": end_time_str,
            "dungeon_name": analysis_data["dungeon_name"],
            "black_person": black_person,
            "worker": remark,
            "team_total_salary": analysis_data["team_total_salary"],
            "personal_salary": personal_salary,
            "subsidy": subsidy,
            "penalty_total": analysis_data["penalty_total"],
            "scattered_total": analysis_data["scattered_total"],
            "iron_total": analysis_data["iron_total"],
            "other_total": analysis_data["other_total"],
            "special_total": analysis_data["special_total"],
            "special_items": analysis_data["special_items"],
            "team_type": analysis_data["team_type"],
            "lie_count": analysis_data["lie_count"],
            "note": note,
            "scattered_consumption": analysis_data["scattered_consumption"],
            "iron_consumption": analysis_data["iron_consumption"],
            "special_consumption": analysis_data["special_consumption"],
            "other_consumption": analysis_data["other_consumption"],
            "total_consumption": analysis_data["total_consumption"]
        }

        analysis_result["uid"] = self.generate_uid(analysis_result)
        return analysis_result

    def generate_uid(self, analysis_result):
        import hashlib
        key_string = (
            f"{analysis_result['start_time']}|"
            f"{analysis_result['end_time']}|"
            f"{analysis_result['dungeon_name']}|"
            f"{analysis_result['black_person']}|"
            f"{analysis_result['worker']}|"
            f"{analysis_result['team_total_salary']}|"
            f"{analysis_result['personal_salary']}|"
            f"{analysis_result['scattered_total']}|"
            f"{analysis_result['iron_total']}|"
            f"{analysis_result['other_total']}|"
            f"{analysis_result['special_total']}|"
            f"{analysis_result['note']}"
        )
        hash_object = hashlib.md5(key_string.encode('utf-8'))
        return hash_object.hexdigest()[:8]

    def load_filled_uids(self):
        try:
            result = self.main_app.db.execute_query("SELECT uid FROM filled_uids")
            if result:
                self.filled_uids = {row[0] for row in result}
        except Exception as e:
            self.create_filled_uids_table()

    def create_filled_uids_table(self):
        try:
            self.main_app.db.execute_update('''
                CREATE TABLE IF NOT EXISTS filled_uids (
                    uid TEXT PRIMARY KEY,
                    fill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        except Exception as e:
            pass

    def save_filled_uid(self, uid):
        try:
            self.main_app.db.execute_update(
                "INSERT OR IGNORE INTO filled_uids (uid) VALUES (?)",
                (uid,)
            )
            self.filled_uids.add(uid)
        except Exception as e:
            pass

    def load_folder_list(self):
        try:
            self.db_folders = {}
            result = self.main_app.db.execute_query("SELECT file_path, remark FROM analysis_files ORDER BY file_path")
            if not result:
                return
            folder_data = {}
            for file_path, remark in result:
                if remark.startswith("FOLDER:"):
                    folder_path = file_path
                    actual_remark = remark.replace("FOLDER:", "")
                    folder_data[folder_path] = {
                        'remark': actual_remark,
                        'files': []
                    }
            for file_path, remark in result:
                if remark.startswith("FILE:"):
                    try:
                        parts = remark.split(":", 2)
                        if len(parts) >= 3:
                            actual_remark = parts[1]
                            folder_path = parts[2]
                            if folder_path in folder_data:
                                folder_data[folder_path]['files'].append(file_path)
                    except Exception as e:
                        pass
            for folder_path, data in folder_data.items():
                if data['files']:
                    self.db_folders[folder_path] = (data['remark'], data['files'])
            self.refresh_treeview()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.db_folders = {}

    def save_folder_list(self):
        try:
            self.main_app.db.execute_update("DELETE FROM analysis_files")
            for folder_path, (remark, file_list) in self.db_folders.items():
                self.main_app.db.execute_update(
                    "INSERT INTO analysis_files (file_path, remark) VALUES (?, ?)",
                    (folder_path, f"FOLDER:{remark}")
                )
                for file_path in file_list:
                    self.main_app.db.execute_update(
                        "INSERT INTO analysis_files (file_path, remark) VALUES (?, ?)",
                        (file_path, f"FILE:{remark}")
                    )
            messagebox.showinfo("成功", "文件夹列表已保存到数据库")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件夹列表失败: {str(e)}")

    def refresh_treeview(self):
        for item in self.file_treeview.get_children():
            self.file_treeview.delete(item)
        for folder_path, (remark, file_list) in self.db_folders.items():
            self.file_treeview.insert("", "end", values=(
                folder_path,
                remark
            ))

    def on_treeview_select(self, event):
        selection = self.file_treeview.selection()
        if selection:
            item = selection[0]
            values = self.file_treeview.item(item, "values")
            if values:
                self.remark_entry.delete(0, tk.END)
                self.remark_entry.insert(0, values[1])

    def add_folder(self):
        folder_path = filedialog.askdirectory(
            title="选择剑网3数据文件夹"
        )
        if not folder_path:
            return
        if folder_path in self.db_folders:
            messagebox.showwarning("警告", "该文件夹已添加")
            return
        userdata_path = os.path.join(folder_path, "userdata")
        chat_log_path = os.path.join(userdata_path, "chat_log")
        if not os.path.exists(userdata_path) or not os.path.exists(chat_log_path):
            messagebox.showwarning("警告", "该文件夹不包含正确的userdata/chat_log结构")
            return
        db_files = self.scan_folder_for_db_files(chat_log_path)
        if not db_files:
            messagebox.showwarning("警告", "该文件夹的chat_log中没有找到.db文件")
            return
        worker_name = os.path.basename(folder_path)
        self.db_folders[folder_path] = (worker_name, db_files)
        self.refresh_treeview()
        self.remark_entry.delete(0, tk.END)
        self.remark_entry.insert(0, worker_name)
        self.save_folder_list_silent()
        messagebox.showinfo("成功", f"已添加文件夹，找到 {len(db_files)} 个.db文件，打工仔: {worker_name}")

    def remove_folder(self):
        selection = self.file_treeview.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件夹")
            return
        item = selection[0]
        values = self.file_treeview.item(item, 'values')
        if not values:
            return
        folder_path = values[0]
        if folder_path in self.db_folders:
            del self.db_folders[folder_path]
            self.refresh_treeview()
            self.save_folder_list_silent()
            messagebox.showinfo("成功", "文件夹已移除")
        else:
            messagebox.showwarning("警告", "找不到要移除的文件夹")

    def clear_folders(self):
        if not self.db_folders:
            return
        if messagebox.askyesno("确认", "确定要清空所有文件夹吗？"):
            self.db_folders = {}
            self.refresh_treeview()
            self.save_folder_list_silent()
            messagebox.showinfo("成功", "已清空所有文件夹")

    def edit_selected_remark(self):
        selection = self.file_treeview.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个文件夹")
            return
        item = selection[0]
        values = self.file_treeview.item(item, 'values')
        if not values:
            return
        folder_path = values[0]
        if folder_path not in self.db_folders:
            return
        new_remark = self.remark_entry.get().strip()
        if not new_remark:
            messagebox.showwarning("警告", "请输入打工仔备注")
            return
        current_remark, file_list = self.db_folders[folder_path]
        if new_remark != current_remark:
            self.db_folders[folder_path] = (new_remark, file_list)
            self.refresh_treeview()
            children = self.file_treeview.get_children()
            for child in children:
                if self.file_treeview.item(child, 'values')[0] == folder_path:
                    self.file_treeview.selection_set(child)
                    break
            self.save_folder_list_silent()
            messagebox.showinfo("成功", "备注修改成功")

    def save_folder_list_silent(self):
        try:
            self.main_app.db.execute_update("DELETE FROM analysis_files")
            for folder_path, (remark, file_list) in self.db_folders.items():
                self.main_app.db.execute_update(
                    "INSERT OR REPLACE INTO analysis_files (file_path, remark) VALUES (?, ?)",
                    (folder_path, f"FOLDER:{remark}")
                )
                for file_path in file_list:
                    self.main_app.db.execute_update(
                        "INSERT OR REPLACE INTO analysis_files (file_path, remark) VALUES (?, ?)",
                        (file_path, f"FILE:{remark}:{folder_path}")
                    )
        except Exception as e:
            import traceback
            traceback.print_exc()

    def create_empty_result(self, filename, remark):
        return {
            "filename": filename,
            "remark": remark,
            "start_time": "未找到",
            "end_time": "未找到",
            "dungeon_name": "未知副本",
            "black_person": "",
            "worker": remark,
            "team_total_salary": 0,
            "personal_salary": 0,
            "subsidy": 0,
            "penalty_total": 0,
            "scattered_total": 0,
            "iron_total": 0,
            "other_total": 0,
            "special_total": 0,
            "special_items": [],
            "team_type": "未知",
            "lie_count": 0,
            "note": "",
            "scattered_consumption": 0,
            "iron_consumption": 0,
            "special_consumption": 0,
            "other_consumption": 0,
            "total_consumption": 0,
            "uid": "empty"
        }

    def add_result_to_tree(self, result):
        consumption_total = (
            result.get("scattered_consumption", 0) + 
            result.get("iron_consumption", 0) + 
            result.get("special_consumption", 0) + 
            result.get("other_consumption", 0)
        )
        self.result_tree.insert("", "end", values=(
            result["uid"],
            result["start_time"],
            result["end_time"],
            result["dungeon_name"],
            result["black_person"],
            result["worker"],
            f"{result['team_total_salary']}金",
            f"{result['personal_salary']}金",
            f"{consumption_total}金",
            f"{result['subsidy']}金",
            f"{result['penalty_total']}金",
            f"{result['scattered_total']}金",
            f"{result['iron_total']}金",
            f"{result['other_total']}金",
            f"{result['special_total']}金",
            result["team_type"],
            result["lie_count"],
            result["note"]
        ))

    def start_analysis(self):
        if not self.db_folders:
            messagebox.showwarning("警告", "请先添加包含.db文件的文件夹")
            return
        self.update_progress(0, "开始扫描文件夹...")
        updated_folders = {}
        total_files = 0
        for folder_path, (remark, old_file_list) in self.db_folders.items():
            self.update_progress(10, f"扫描文件夹: {os.path.basename(folder_path)}")
            chat_log_path = os.path.join(folder_path, "userdata", "chat_log")
            new_file_list = self.scan_folder_for_db_files(chat_log_path)
            updated_folders[folder_path] = (remark, new_file_list)
            total_files += len(new_file_list)
        self.db_folders = updated_folders
        self.save_folder_list_silent()
        if total_files == 0:
            messagebox.showwarning("警告", "所有文件夹中都没有找到.db文件")
            self.update_progress(0, "没有找到.db文件")
            return
        self.update_progress(60, "开始分析所有.db文件")
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.analysis_results = []
        success_count = 0
        duplicate_count = 0
        seen_uids = set()
        processed_files = 0
        for folder_path, (remark, file_list) in self.db_folders.items():
            for db_file in file_list:
                try:
                    processed_files += 1
                    progress = 10 + (processed_files / total_files) * 80
                    self.update_progress(
                        progress, 
                        f"分析进度: {processed_files}/{total_files} - {os.path.basename(db_file)}"
                    )
                    results = self.analyze_db_file_with_gkp(db_file, folder_path, remark)
                    if results:
                        for result in results:
                            uid = result["uid"]
                            if uid in seen_uids or uid in self.filled_uids:
                                duplicate_count += 1
                                continue
                            self.analysis_results.append(result)
                            self.add_result_to_tree(result)
                            seen_uids.add(uid)
                            success_count += 1
                except Exception as e:
                    pass
        if success_count > 0:
            messagebox.showinfo("完成", f"分析完成！成功分析{success_count}个记录段")
        else:
            messagebox.showwarning("警告", "没有成功分析任何记录段")
        self.update_progress(0, "分析完成")

    def fill_form(self):
        selected = self.result_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一条分析结果")
            return
        item = selected[0]
        values = self.result_tree.item(item, 'values')
        uid = values[0]
        result = next((r for r in self.analysis_results if r.get('uid') == uid), None)
        if not result:
            messagebox.showerror("错误", "找不到对应的分析结果")
            return
        try:
            self.main_app.analysis_time = result.get("end_time", "")
            self.main_app.dungeon_var.set(result.get("dungeon_name", ""))
            self.update_special_items_combo_immediately(result.get("dungeon_name", ""))
            self.main_app.trash_gold_var.set(str(result.get("scattered_total", 0)))
            self.main_app.iron_gold_var.set(str(result.get("iron_total", 0)))
            self.main_app.other_gold_var.set(str(result.get("other_total", 0)))
            self.main_app.total_gold_var.set(str(result.get("team_total_salary", 0)))
            self.main_app.personal_gold_var.set(str(result.get("personal_salary", 0)))
            self.main_app.subsidy_gold_var.set(str(result.get("subsidy", 0)))
            self.main_app.fine_gold_var.set(str(result.get("penalty_total", 0)))
            self.main_app.team_type_var.set(result.get("team_type", ""))
            self.main_app.lie_down_var.set(str(result.get("lie_count", 0)))
            self.main_app.black_owner_var.set(result.get("black_person", ""))
            self.main_app.worker_var.set(result.get("worker", ""))
            self.main_app.note_var.set(result.get("note", ""))
            scattered_consumption = result.get("scattered_consumption", 0)
            iron_consumption = result.get("iron_consumption", 0)
            special_consumption = result.get("special_consumption", 0)
            other_consumption = result.get("other_consumption", 0)
            total_consumption = result.get("total_consumption", 0)
            self.main_app.scattered_consumption_var.set(str(scattered_consumption))
            self.main_app.iron_consumption_var.set(str(iron_consumption))
            self.main_app.special_consumption_var.set(str(special_consumption))
            self.main_app.other_consumption_var.set(str(other_consumption))
            self.main_app.total_consumption_var.set(str(total_consumption))
            self.main_app.special_tree.clear()
            for item_data in result.get("special_items", []):
                self.main_app.special_tree.add_item(item_data.get("item", ""), item_data.get("price", 0))
            special_total = sum(item_data.get("price", 0) for item_data in result.get("special_items", []))
            self.main_app.special_total_var.set(str(special_total))
            self.save_filled_uid(uid)
            self.result_tree.delete(item)
            self.analysis_results = [r for r in self.analysis_results if r.get('uid') != uid]
            messagebox.showinfo("成功", "分析结果已填充到表单，该记录已从列表中移除")
        except Exception as e:
            messagebox.showerror("错误", f"填充表单时出错: {str(e)}")

    def update_special_items_combo_immediately(self, dungeon_name):
        if not dungeon_name:
            return
        try:
            # 获取当前副本的特殊掉落
            result = self.main_app.db.execute_query(
                "SELECT special_drops FROM dungeons WHERE name = ?", 
                (dungeon_name,)
            )
            current_dungeon_items = []
            if result and result[0][0]:
                current_dungeon_items = [item.strip() for item in result[0][0].split(',')]
            
            # 获取公共预设的特殊掉落
            public_result = self.main_app.db.execute_query(
                "SELECT special_drops FROM dungeons WHERE is_public = 1"
            )
            public_items = []
            if public_result and public_result[0][0]:
                public_items = [item.strip() for item in public_result[0][0].split(',')]
            
            # 合并特殊掉落
            all_items = current_dungeon_items + public_items
            
            if hasattr(self.main_app, 'special_item_combo') and self.main_app.special_item_combo:
                self.main_app.special_item_combo['values'] = all_items
                self.main_app.special_item_var.set("")
        except Exception as e:
            pass

    def is_special_item_match(self, item_name, special_item):
        clean_special = re.sub(r'（.*?）', '', special_item).strip()
        return clean_special in item_name

    def parse_gold_amount(self, gold_text):
        total = 0
        brick_match = re.search(r'(\d+)金砖', gold_text)
        if brick_match:
            total += int(brick_match.group(1)) * 10000
        gold_match = re.search(r'(\d+)金(?!砖)', gold_text)
        if gold_match:
            total += int(gold_match.group(1))
        return total

    def is_potential_special_item(self, item_name):
        all_special_items = self.load_special_items()
        for special_item in all_special_items:
            if self.is_special_item_match(item_name, special_item):
                return True
        return False

    def load_special_items(self):
        special_items = []
        try:
            # 获取所有副本的特殊掉落
            result = self.main_app.db.execute_query("SELECT special_drops FROM dungeons")
            for row in result:
                if row[0]:
                    items = [item.strip() for item in row[0].split(',')]
                    special_items.extend(items)
        except Exception as e:
            pass
        return special_items

class WeeklyRecordManager:
    def __init__(self, db):
        self.db = db
    
    def get_weekly_start_date(self, team_type):
        now = dt.datetime.now()
        
        if team_type == "二十五人本":
            # 每周一07:00重置
            last_monday = now - timedelta(days=now.weekday())
            if now.hour < 7:
                last_monday -= timedelta(days=7)
            last_monday = last_monday.replace(hour=7, minute=0, second=0, microsecond=0)
            return last_monday
        
        elif team_type == "十人本":
            # 周一07:00 与 周五07:00 双重置
            # 本周一 07:00
            monday = now - timedelta(days=now.weekday())
            monday_7 = monday.replace(hour=7, minute=0, second=0, microsecond=0)
            # 本周五 07:00
            friday_7 = (monday + timedelta(days=4)).replace(hour=7, minute=0, second=0, microsecond=0)

            # 如果当前时间 < 本周一07:00 → 属于“上周五07:00 ~ 本周一06:59”周期，起始时间为上周五07:00
            if now < monday_7:
                last_friday = monday - timedelta(days=3)  # 上周五
                return last_friday.replace(hour=7, minute=0, second=0, microsecond=0)
            # 如果当前时间 < 本周五07:00 → 属于“本周一07:00 ~ 本周五06:59”周期，起始时间为本周一07:00
            elif now < friday_7:
                return monday_7
            # 否则（当前时间 ≥ 本周五07:00）→ 属于“本周五07:00 ~ 下周一06:59”周期，起始时间为本周五07:00
            else:
                return friday_7
        
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def get_weekly_records(self, worker_name=None):
        # 分别获取25人本和10人本周期起始时间
        start_25 = self.get_weekly_start_date("二十五人本")
        start_10 = self.get_weekly_start_date("十人本")
        
        conditions = []
        params = []
        
        # 添加时间过滤条件：记录必须在对应团队类型的周期内
        conditions.append(
            "((r.team_type = '二十五人本' AND r.time >= ?) OR (r.team_type = '十人本' AND r.time >= ?))"
        )
        params.extend([start_25.strftime('%Y-%m-%d %H:%M:%S'), start_10.strftime('%Y-%m-%d %H:%M:%S')])
        
        if worker_name:
            conditions.append("r.worker = ?")
            params.append(worker_name)
        
        where_clause = " AND ".join(conditions)
        query = f'''
            SELECT r.worker, 
                COALESCE(d.name, '未知副本') as dungeon_name, 
                r.note,
                r.time,
                r.team_type
            FROM records r
            LEFT JOIN dungeons d ON r.dungeon_id = d.id
            WHERE {where_clause}
            ORDER BY r.worker COLLATE NOCASE, 
                    CASE WHEN r.team_type = '十人本' THEN 1 
                         WHEN r.team_type = '二十五人本' THEN 2 
                         ELSE 3 END,
                    r.time
        '''
        
        records = self.db.execute_query(query, params)
        return [
            {
                'worker': row[0],
                'dungeon': row[1],
                'note': row[2] or "",
                'time': row[3],
                'team_type': row[4]
            }
            for row in records
        ]
    
    def get_weekly_period_text(self):
        now = dt.datetime.now()
        
        # ----- 二十五人本周期
        start_25 = self.get_weekly_start_date("二十五人本")
        end_25 = start_25 + timedelta(days=7, seconds=-1)
        period_25 = f"{start_25.strftime('%Y-%m-%d %H:%M')} 至 {end_25.strftime('%Y-%m-%d %H:%M')}"
        
        # ----- 十人本周期（根据当前时间自动判断区间）-----
        start_10 = self.get_weekly_start_date("十人本")
        if start_10.weekday() == 0:
            end_10 = start_10 + timedelta(days=4, hours=0, minutes=0, seconds=-1)
        else:
            end_10 = start_10 + timedelta(days=3, hours=0, minutes=0, seconds=-1)
        period_10 = f"{start_10.strftime('%Y-%m-%d %H:%M')} 至 {end_10.strftime('%Y-%m-%d %H:%M')}"
        
        return f"25人周期: {period_25} | 10人周期: {period_10}"

def load_weekly_data(self):
    for item in self.weekly_tree.get_children():
        self.weekly_tree.delete(item)
    
    weekly_manager = WeeklyRecordManager(self.db)
    self.weekly_period_var.set(weekly_manager.get_weekly_period_text())
    
    # 获取当前周期内的记录
    records = weekly_manager.get_weekly_records(
        self.weekly_worker_var.get() if self.weekly_worker_var.get() else None
    )
    
    if not records:
        return
    
    # 插入数据 - 注意：数据库查询已经按照正确的顺序排序了
    for record in records:
        self.weekly_tree.insert("", "end", values=(
            record['time'],  # 结束时间
            record['worker'] or "",  # 打工仔
            record['team_type'],  # 团队类型
            record['dungeon'],  # 副本
            record['note']  # 备注
        ))

class JX3DungeonTracker:
    def __init__(self, root):
        self.is_closing = False
        self.root = root
        self.root.title("JX3DungeonTracker - 剑网3副本记录工具")
        self.root.attributes('-topmost', True)
        self.initialize_all_attributes()
        self.analysis_time = None
        self.root.withdraw()
        self.show_splash_screen()
        try:
            locale.setlocale(locale.LC_TIME, '')
        except:
            pass
        app_data_dir = get_app_data_path()
        db_path = os.path.join(app_data_dir, 'jx3_dungeon.db')
        os.makedirs(app_data_dir, exist_ok=True)
        try:
            self.db_initialized = False
            self.db_error = None
            self.init_db_in_background(db_path)
        except Exception as e:
            self.hide_splash_screen()
            messagebox.showerror("数据库错误", f"无法初始化数据库: {str(e)}")
            self.root.destroy()
            return
        self.clear_new_record_highlights_on_startup()
        self.setup_basic_ui()
        self.wait_for_db_init()
        if self.db_error:
            self.hide_splash_screen()
            messagebox.showerror("数据库错误", f"数据库初始化失败: {self.db_error}")
            self.root.destroy()
            return
        self.optimized_ui_setup()
        self.after_ids = []
        self.new_record_ids = set()
        self.cached_dungeons = None
        self.cached_owners = None
        self.cached_workers = None
        self._save_scheduled = None
        self._pane_save_scheduled = None
        self._charts_preloaded = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.schedule_time_update()
        self.setup_pane_events()
        self.setup_window_tracking()
        self.root.after(100, self.restore_window_state)
        self.root.after(100, self.initialize_stats_tab_chart)
        self.selected_worker = None
        # === 修改点 1：添加实例变量记录搜索时选中的副本 ===
        self.current_search_dungeon = None

    def initialize_all_attributes(self):
        self.record_tree = None
        self.worker_stats_tree = None
        self.dungeon_tree = None
        self.weekly_tree = None
        self.record_pane = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.db_analyzer = None
        self.trash_gold_entry = None
        self.iron_gold_entry = None
        self.other_gold_entry = None
        self.subsidy_gold_entry = None
        self.fine_gold_entry = None
        self.scattered_consumption_entry = None
        self.iron_consumption_entry = None
        self.special_consumption_entry = None
        self.other_consumption_entry = None
        self.total_consumption_entry = None
        self.lie_down_entry = None
        self.total_gold_entry = None
        self.personal_gold_entry = None
        self.note_entry = None
        self.dungeon_combo = None
        self.special_item_combo = None
        self.special_price_entry = None
        self.team_type_combo = None
        self.black_owner_combo = None
        self.worker_combo = None
        self.search_owner_combo = None
        self.search_worker_combo = None
        self.search_dungeon_combo = None
        self.search_item_combo = None
        self.search_team_type_combo = None
        self.start_date_entry = None
        self.end_date_entry = None
        self.weekly_worker_combo = None
        self.add_btn = None
        self.edit_btn = None
        self.update_btn = None
        self.special_tree = None
        self.current_edit_id = None
        self.after_ids = []
        self.new_record_ids = set()
        self.cached_dungeons = None
        self.cached_owners = None
        self.cached_workers = None
        self.db_initialized = False
        self.db_error = None
        self._save_scheduled = None
        self._pane_save_scheduled = None

    def show_splash_screen(self):
        self.splash = tk.Toplevel(self.root)
        self.splash.title("正在启动...")
        self.splash.geometry("400x250")
        self.splash.configure(bg='#f0f0f0')
        self.splash.overrideredirect(True)
        self.splash.attributes('-topmost', True)
        screen_width = self.splash.winfo_screenwidth()
        screen_height = self.splash.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        self.splash.geometry(f"400x250+{x}+{y}")
        ttk.Label(self.splash, text="JX3DungeonTracker", 
                 font=("PingFang SC", 18, "bold"), background='#f0f0f0').pack(pady=20)
        ttk.Label(self.splash, text="剑网3副本记录工具", 
                 font=("PingFang SC", 12), background='#f0f0f0').pack()
        self.splash_status = ttk.Label(self.splash, text="正在初始化...", 
                                  font=("PingFang SC", 10), background='#f0f0f0')
        self.splash_status.pack(pady=(10, 5))
        self.splash_progress = ttk.Progressbar(self.splash, mode='determinate', length=300)
        self.splash_progress.pack(pady=10)
        self.progress_steps = [
            "初始化数据库...",
            "构建用户界面...", 
            "加载副本数据...",
            "加载历史记录...",
            "准备就绪..."
        ]
        self.current_step = 0
        self.update_splash_progress()
        self.splash.update()
        self.root.update()

    def update_splash_progress(self, step=None):
        if step is not None:
            self.current_step = step
        total_steps = len(self.progress_steps)
        progress_value = (self.current_step / total_steps) * 100
        if self.current_step < total_steps:
            self.splash_status.config(text=self.progress_steps[self.current_step])
            self.splash_progress['value'] = progress_value
            self.current_step += 1
        self.splash.update()

    def hide_splash_screen(self):
        if hasattr(self, 'splash') and self.splash:
            self.splash.destroy()
            self.splash = None
        self.root.deiconify()
        self.root.attributes('-topmost', False)

    def init_db_in_background(self, db_path):
        def init_db():
            try:
                time.sleep(1)
                if not self.is_closing:
                    self.db = DatabaseManager(db_path)
                    self.db_initialized = True
                    if not self.is_closing:
                        self.root.after(500, self.stage_2_data_loading)
            except Exception as e:
                if not self.is_closing:
                    self.db_error = str(e)
        
        if not self.is_closing:
            self.db_thread = threading.Thread(target=init_db, daemon=True)
            self.db_thread.start()

    def stage_2_data_loading(self):
        if not self.db_initialized:
            self.root.after(500, self.stage_2_data_loading)
            return
        self.update_splash_progress(1)
        self.load_dungeon_options()
        self.load_black_owner_options()
        self.root.after(800, self.stage_3_data_loading)

    def stage_3_data_loading(self):
        try:
            self.update_splash_progress(2)
            self.load_recent_records(50)
            self.root.after(800, self.stage_4_data_loading)
        except Exception as e:
            self.root.after(800, self.stage_4_data_loading)

    def stage_4_data_loading(self):
        try:
            self.update_splash_progress(3)
            self.update_stats()
            threading.Thread(target=self.load_remaining_records_background, daemon=True).start()
            self.root.after(500, self.final_loading_stage)
        except Exception as e:
            self.root.after(500, self.final_loading_stage)

    def final_loading_stage(self):
        try:
            self.update_splash_progress(4)
            self.root.after(500, self.hide_splash_screen)
        except Exception as e:
            self.hide_splash_screen()

    def wait_for_db_init(self):
        max_wait_time = 15
        start_time = time.time()
        def update_splash_status(status):
            if hasattr(self, 'splash') and self.splash:
                for widget in self.splash.winfo_children():
                    if isinstance(widget, ttk.Label) and "正在初始化" in widget.cget("text"):
                        widget.config(text=status)
                        break
        while not self.db_initialized and not self.db_error:
            elapsed = time.time() - start_time
            if elapsed > max_wait_time:
                self.db_error = "数据库初始化超时"
                break
            if elapsed < 2:
                update_splash_status("正在初始化数据库...")
            elif elapsed < 5:
                update_splash_status("正在加载预设数据...")
            elif elapsed < 8:
                update_splash_status("正在准备界面组件...")
            else:
                update_splash_status("正在完成初始化，请稍候...")
            self.splash.update()
            time.sleep(0.1)

    def setup_basic_ui(self):
        self.setup_window()
        self.setup_variables()
        self.setup_styles()
        self.create_main_ui()

    def setup_window(self):
        width, height = int(1700*SCALE_FACTOR), int(1000*SCALE_FACTOR)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg="#f5f5f7")
        self.root.minsize(int(1024*SCALE_FACTOR), int(600*SCALE_FACTOR))

    def setup_variables(self):
        self.trash_gold_var = tk.StringVar(value="")
        self.iron_gold_var = tk.StringVar(value="")
        self.other_gold_var = tk.StringVar(value="")
        self.fine_gold_var = tk.StringVar(value="")
        self.subsidy_gold_var = tk.StringVar(value="")
        self.lie_down_var = tk.StringVar(value="")
        self.team_type_var = tk.StringVar(value="十人本")
        self.total_gold_var = tk.StringVar(value="")
        self.personal_gold_var = tk.StringVar(value="")
        self.special_total_var = tk.StringVar(value="")
        self.note_var = tk.StringVar(value="")
        self.start_date_var = tk.StringVar(value="")
        self.end_date_var = tk.StringVar(value="")
        self.time_var = tk.StringVar(value=get_current_time())
        self.dungeon_var = tk.StringVar()
        self.special_item_var = tk.StringVar()
        self.special_price_var = tk.StringVar()
        self.black_owner_var = tk.StringVar()
        self.worker_var = tk.StringVar()
        self.search_dungeon_var = tk.StringVar()
        self.search_item_var = tk.StringVar()
        self.search_owner_var = tk.StringVar()
        self.search_worker_var = tk.StringVar()
        self.search_team_type_var = tk.StringVar()
        self.preset_drops_var = tk.StringVar()
        self.preset_name_var = tk.StringVar()
        self.weekly_worker_var = tk.StringVar()
        self.weekly_period_var = tk.StringVar()
        self.scattered_consumption_var = tk.StringVar(value="")
        self.iron_consumption_var = tk.StringVar(value="")
        self.special_consumption_var = tk.StringVar(value="")
        self.other_consumption_var = tk.StringVar(value="")
        self.total_consumption_var = tk.StringVar(value="")

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#f5f5f7", foreground="#333")
        self.style.configure("TFrame", background="#f5f5f7")
        self.style.configure("TLabel", background="#f5f5f7", font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.style.configure("TButton",
                            font=("PingFang SC", int(10*SCALE_FACTOR)),
                            padding=int(6*SCALE_FACTOR),
                            background="#e6e6e6")
        self.style.map("TButton", background=[("active", "#d6d6d6")])
        self.style.configure("Treeview", font=("PingFang SC", int(9*SCALE_FACTOR)), rowheight=int(24*SCALE_FACTOR))
        self.style.configure("Treeview.Heading", font=("PingFang SC", int(10*SCALE_FACTOR)), anchor="center")
        self.style.configure("TNotebook", background="#f5f5f7", borderwidth=0)
        self.style.configure("TNotebook.Tab", font=("PingFang SC", int(10*SCALE_FACTOR)), padding=[int(10*SCALE_FACTOR), int(4*SCALE_FACTOR)])
        self.style.configure("TCombobox", font=("PingFang SC", int(10*SCALE_FACTOR)), padding=int(4*SCALE_FACTOR))
        self.style.configure("TEntry", font=("PingFang SC", int(10*SCALE_FACTOR)), padding=int(4*SCALE_FACTOR))
        self.style.configure("TLabelFrame", font=("PingFang SC", int(10*SCALE_FACTOR)), padding=int(8*SCALE_FACTOR), labelanchor="n")
        self.style.configure("NewRecord.Treeview", background="#e6f7ff")
        self.root.option_add("*TCombobox*Listbox*Font", ("PingFang SC", int(10*SCALE_FACTOR)))

    def create_main_ui(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=int(10*SCALE_FACTOR), pady=int(10*SCALE_FACTOR))
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, int(8*SCALE_FACTOR)))
        title_frame.columnconfigure(0, weight=1)
        title_frame.columnconfigure(1, weight=0)
        ttk.Label(title_frame, text="JX3DungeonTracker - 剑网3副本记录工具", 
                 font=("PingFang SC", int(16*SCALE_FACTOR), "bold"), anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=int(10*SCALE_FACTOR))
        ttk.Label(title_frame, textvariable=self.time_var, 
                 font=("PingFang SC", int(12*SCALE_FACTOR)), anchor="e"
        ).grid(row=0, column=1, sticky="e")
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=int(5*SCALE_FACTOR), pady=int(5*SCALE_FACTOR))
        self.record_frame = ttk.Frame(self.notebook)
        self.stats_frame = ttk.Frame(self.notebook)
        self.preset_frame = ttk.Frame(self.notebook)
        self.weekly_frame = ttk.Frame(self.notebook)
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="数据总览")
        self.notebook.add(self.record_frame, text="副本记录")
        self.notebook.add(self.preset_frame, text="副本预设")
        self.notebook.add(self.weekly_frame, text="秘境记录")
        self.notebook.add(self.analysis_frame, text="拍团分析")
        loading_label = ttk.Label(self.record_frame, text="正在加载数据，请稍候...", 
                                 font=("PingFang SC", 12))
        loading_label.pack(expand=True)

    def optimized_ui_setup(self):
        for widget in self.record_frame.winfo_children():
            widget.destroy()
        self.create_record_tab(self.record_frame)
        self.create_stats_tab(self.stats_frame)
        self.create_preset_tab(self.preset_frame)
        self.create_weekly_tab(self.weekly_frame)
        self.create_analysis_tab(self.analysis_frame)
        self.notebook.select(0)
        self.setup_events()
        self.root.after(100, self.load_critical_data)
        self.root.after(500, self.load_secondary_data)
        self.root.after(1000, self.load_background_data)

    def load_critical_data(self):
        try:
            self.load_dungeon_options()
            self.load_black_owner_options()
            self.load_worker_options()
            self.load_recent_records(20)
            self.root.update_idletasks()
        except Exception as e:
            pass

    def load_secondary_data(self):
        try:
            self.update_stats()
            self.load_weekly_worker_options()
            self.safe_load_column_widths()
            self.root.update_idletasks()
        except Exception as e:
            pass

    def load_background_data(self):
        try:
            threading.Thread(target=self.load_remaining_data, daemon=True).start()
        except Exception as e:
            pass

    def load_remaining_data(self):
        try:
            self.load_remaining_records_background()
            self.load_weekly_data()
            self.load_dungeon_presets()
        except Exception as e:
            pass

    def create_record_tab(self, parent):
        try:
            pane = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
            pane.pack(fill=tk.BOTH, expand=True, padx=int(5*SCALE_FACTOR), pady=int(5*SCALE_FACTOR))
            form_frame = ttk.LabelFrame(pane, text="副本记录管理", padding=int(8*SCALE_FACTOR), width=int(350*SCALE_FACTOR))
            self.build_record_form(form_frame)
            list_frame = ttk.LabelFrame(pane, text="副本记录列表", padding=int(8*SCALE_FACTOR))
            self.build_record_list(list_frame)
            pane.add(form_frame, weight=1)
            pane.add(list_frame, weight=2)
            self.record_pane = pane
            self.record_pane_name = "record_pane"
            self.restore_pane_position(self.record_pane, self.record_pane_name)
        except Exception as e:
            pass

    def build_record_form(self, parent):
        dungeon_row = ttk.Frame(parent)
        dungeon_row.pack(fill=tk.X, pady=int(3*SCALE_FACTOR))
        ttk.Label(dungeon_row, text="副本名称:").pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        self.dungeon_combo = ttk.Combobox(dungeon_row, textvariable=self.dungeon_var, 
                                         width=int(25*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.dungeon_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        special_frame = ttk.LabelFrame(parent, text="特殊掉落", padding=int(6*SCALE_FACTOR))
        special_frame.pack(fill=tk.BOTH, pady=(0, int(5*SCALE_FACTOR)), expand=True)
        tree_frame = ttk.Frame(special_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=int(3*SCALE_FACTOR))
        self.special_tree = SpecialItemsTree(tree_frame)
        add_special_frame = ttk.Frame(special_frame)
        add_special_frame.pack(fill=tk.X, pady=(int(8*SCALE_FACTOR), 0))
        ttk.Label(add_special_frame, text="物品:").grid(row=0, column=0, padx=(0, int(5*SCALE_FACTOR)), sticky="w")
        self.special_item_combo = ttk.Combobox(add_special_frame, textvariable=self.special_item_var, 
                                              width=int(22*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.special_item_combo.grid(row=0, column=1, padx=(0, int(5*SCALE_FACTOR)), sticky="ew")
        ttk.Label(add_special_frame, text="金额:").grid(row=0, column=2, padx=(int(5*SCALE_FACTOR), int(5*SCALE_FACTOR)), sticky="w")
        self.special_price_entry = ttk.Entry(add_special_frame, textvariable=self.special_price_var, 
                                            width=int(7*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.special_price_entry.grid(row=0, column=3, padx=(0, int(5*SCALE_FACTOR)), sticky="w")
        ttk.Button(add_special_frame, text="添加", width=int(6*SCALE_FACTOR), command=self.add_special_item
        ).grid(row=0, column=4, padx=(int(5*SCALE_FACTOR), 0))
        add_special_frame.columnconfigure(1, weight=1)
        team_frame = ttk.LabelFrame(parent, text="团队项目", padding=int(6*SCALE_FACTOR))
        team_frame.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        self.build_team_fields(team_frame)
        personal_frame = ttk.LabelFrame(parent, text="个人项目", padding=int(6*SCALE_FACTOR))
        personal_frame.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        self.build_personal_fields(personal_frame)
        info_frame = ttk.LabelFrame(parent, text="团队信息", padding=int(6*SCALE_FACTOR))
        info_frame.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        self.build_info_fields(info_frame)
        gold_frame = ttk.LabelFrame(parent, text="工资信息", padding=int(6*SCALE_FACTOR))
        gold_frame.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        self.build_gold_fields(gold_frame)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=int(5*SCALE_FACTOR))
        self.build_form_buttons(btn_frame)

    def build_team_fields(self, parent):
        ttk.Label(parent, text="散件金额:").grid(row=0, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.trash_gold_entry = ttk.Entry(parent, textvariable=self.trash_gold_var, 
                                         width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.trash_gold_entry.grid(row=0, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="小铁金额:").grid(row=0, column=2, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.iron_gold_entry = ttk.Entry(parent, textvariable=self.iron_gold_var, 
                                        width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.iron_gold_entry.grid(row=0, column=3, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="特殊金额:").grid(row=1, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, textvariable=self.special_total_var, width=int(10*SCALE_FACTOR), 
                 font=("PingFang SC", int(10*SCALE_FACTOR))
        ).grid(row=1, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="其他金额:").grid(row=1, column=2, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.other_gold_entry = ttk.Entry(parent, textvariable=self.other_gold_var, 
                                         width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.other_gold_entry.grid(row=1, column=3, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)

    def build_personal_fields(self, parent):
        ttk.Label(parent, text="补贴金额:").grid(row=0, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.subsidy_gold_entry = ttk.Entry(parent, textvariable=self.subsidy_gold_var, 
                                        width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.subsidy_gold_entry.grid(row=0, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="罚款金额:").grid(row=0, column=2, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.fine_gold_entry = ttk.Entry(parent, textvariable=self.fine_gold_var, 
                                        width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.fine_gold_entry.grid(row=0, column=3, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="散件消费:").grid(row=1, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.scattered_consumption_entry = ttk.Entry(parent, textvariable=self.scattered_consumption_var, 
                                                width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.scattered_consumption_entry.grid(row=1, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="小铁消费:").grid(row=1, column=2, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.iron_consumption_entry = ttk.Entry(parent, textvariable=self.iron_consumption_var, 
                                            width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.iron_consumption_entry.grid(row=1, column=3, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="特殊消费:").grid(row=2, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.special_consumption_entry = ttk.Entry(parent, textvariable=self.special_consumption_var, 
                                                width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.special_consumption_entry.grid(row=2, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="其他消费:").grid(row=2, column=2, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.other_consumption_entry = ttk.Entry(parent, textvariable=self.other_consumption_var, 
                                            width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.other_consumption_entry.grid(row=2, column=3, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="总消费:").grid(row=3, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.total_consumption_entry = ttk.Entry(parent, textvariable=self.total_consumption_var, 
                                            width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.total_consumption_entry.grid(row=3, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)

    def build_info_fields(self, parent):
        ttk.Label(parent, text="团队类型:").grid(row=0, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.team_type_combo = ttk.Combobox(parent, textvariable=self.team_type_var, 
                                           values=["十人本", "二十五人本"], width=int(10*SCALE_FACTOR), 
                                           state="readonly", font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.team_type_combo.grid(row=0, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.team_type_combo.current(0)
        ttk.Label(parent, text="躺拍人数:").grid(row=0, column=2, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.lie_down_entry = ttk.Entry(parent, textvariable=self.lie_down_var, 
                                       width=int(6*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.lie_down_entry.grid(row=0, column=3, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="团长:").grid(row=1, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.black_owner_combo = ttk.Combobox(parent, textvariable=self.black_owner_var, 
                                             width=int(20*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.black_owner_combo.grid(row=1, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W, columnspan=3)
        ttk.Label(parent, text="打工仔:").grid(row=2, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.worker_combo = ttk.Combobox(parent, textvariable=self.worker_var, 
                                        width=int(20*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.worker_combo.grid(row=2, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W, columnspan=3)
        ttk.Label(parent, text="备注:").grid(row=3, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.note_entry = ttk.Entry(parent, textvariable=self.note_var, 
                                   width=int(30*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.note_entry.grid(row=3, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W, columnspan=3)

    def build_gold_fields(self, parent):
        ttk.Label(parent, text="团队总收入:").grid(row=0, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.total_gold_entry = ttk.Entry(parent, textvariable=self.total_gold_var, 
                                        width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.total_gold_entry.grid(row=0, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        ttk.Label(parent, text="个人收入:").grid(row=1, column=0, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)
        self.personal_gold_entry = ttk.Entry(parent, textvariable=self.personal_gold_var, 
                                            width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.personal_gold_entry.grid(row=1, column=1, padx=int(3*SCALE_FACTOR), pady=int(2*SCALE_FACTOR), sticky=tk.W)

    def build_form_buttons(self, parent):
        self.add_btn = ttk.Button(parent, text="保存记录", command=self.validate_and_save, width=int(10*SCALE_FACTOR))
        self.edit_btn = ttk.Button(parent, text="编辑记录", command=self.edit_record, width=int(10*SCALE_FACTOR))
        self.update_btn = ttk.Button(parent, text="更新记录", command=self.update_record, 
                                   state=tk.DISABLED, width=int(10*SCALE_FACTOR))
        clear_btn = ttk.Button(parent, text="清空表单", command=self.clear_form, width=int(10*SCALE_FACTOR))
        self.add_btn.grid(row=0, column=0, padx=int(2*SCALE_FACTOR), sticky="ew")
        self.edit_btn.grid(row=0, column=1, padx=int(2*SCALE_FACTOR), sticky="ew")
        self.update_btn.grid(row=0, column=2, padx=int(2*SCALE_FACTOR), sticky="ew")
        clear_btn.grid(row=0, column=3, padx=int(2*SCALE_FACTOR), sticky="ew")
        for i in range(4):
            parent.columnconfigure(i, weight=1)

    def build_record_list(self, parent):
        search_frame = ttk.Frame(parent)
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, int(5*SCALE_FACTOR)))
        self.build_search_controls(search_frame)
        tree_frame = ttk.Frame(parent)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        columns = ("row_num", "dungeon", "time", "team_type", "lie_down", "total", "personal", "consumption", "black_owner", "worker", "note")
        self.record_tree = ttk.Treeview(parent, columns=columns, show="headings", 
                                    selectmode="extended", height=int(10*SCALE_FACTOR))
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.record_tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.record_tree.xview)
        self.record_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.record_tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        self.setup_tree_columns()
        self.setup_column_resizing(self.record_tree)
        self.setup_context_menu()
        self.record_tree.tag_configure('new_record', background='#e6f7ff')

    def build_search_controls(self, parent):
        search_row1 = ttk.Frame(parent)
        search_row1.pack(fill=tk.X, pady=int(2*SCALE_FACTOR))
        ttk.Label(search_row1, text="团长:").pack(side=tk.LEFT, padx=(0, int(3*SCALE_FACTOR)))
        self.search_owner_combo = ttk.Combobox(search_row1, textvariable=self.search_owner_var, 
                                            width=int(15*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.search_owner_combo.pack(side=tk.LEFT, padx=(0, int(8*SCALE_FACTOR)))
        ttk.Label(search_row1, text="打工仔:").pack(side=tk.LEFT, padx=(int(5*SCALE_FACTOR), int(5*SCALE_FACTOR)))
        self.search_worker_combo = ttk.Combobox(search_row1, textvariable=self.search_worker_var, 
                                            width=int(15*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.search_worker_combo.pack(side=tk.LEFT, padx=(0, int(8*SCALE_FACTOR)))
        search_row2 = ttk.Frame(parent)
        search_row2.pack(fill=tk.X, pady=int(2*SCALE_FACTOR))
        ttk.Label(search_row2, text="副本:").pack(side=tk.LEFT, padx=(0, int(3*SCALE_FACTOR)))
        self.search_dungeon_combo = ttk.Combobox(search_row2, textvariable=self.search_dungeon_var, 
                                                width=int(15*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.search_dungeon_combo.pack(side=tk.LEFT, padx=(0, int(8*SCALE_FACTOR)))
        ttk.Label(search_row2, text="特殊掉落:").pack(side=tk.LEFT, padx=(0, int(3*SCALE_FACTOR)))
        self.search_item_combo = ttk.Combobox(search_row2, textvariable=self.search_item_var, 
                                            width=int(15*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.search_item_combo.pack(side=tk.LEFT, padx=(0, int(8*SCALE_FACTOR)))
        # === 修改点 2：为特殊掉落下拉框绑定实时过滤事件，并设置初始值 ===
        self.search_item_combo['values'] = self.get_all_special_items()
        self.search_item_combo.bind('<KeyRelease>', self.update_search_item_combo)
        self.search_item_combo['postcommand'] = self.update_search_item_combo
        # ==============================================================
        search_row3 = ttk.Frame(parent)
        search_row3.pack(fill=tk.X, pady=int(2*SCALE_FACTOR))
        ttk.Label(search_row3, text="开始时间:").pack(side=tk.LEFT, padx=(0, int(3*SCALE_FACTOR)))
        self.start_date_entry = ttk.Entry(search_row3, textvariable=self.start_date_var, 
                                        width=int(12*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.start_date_entry.pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Label(search_row3, text="结束时间:").pack(side=tk.LEFT, padx=(0, int(3*SCALE_FACTOR)))
        self.end_date_entry = ttk.Entry(search_row3, textvariable=self.end_date_var, 
                                    width=int(12*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.end_date_entry.pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Label(search_row3, text="团队类型:").pack(side=tk.LEFT, padx=(0, int(3*SCALE_FACTOR)))
        self.search_team_type_combo = ttk.Combobox(search_row3, textvariable=self.search_team_type_var, 
                                                values=["", "十人本", "二十五人本"], 
                                                width=int(10*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.search_team_type_combo.pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        search_row4 = ttk.Frame(parent)
        search_row4.pack(fill=tk.X, pady=int(2*SCALE_FACTOR))
        left_btn_frame = ttk.Frame(search_row4)
        left_btn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(left_btn_frame, text="查询", command=self.search_records, width=int(10*SCALE_FACTOR)
        ).pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(left_btn_frame, text="重置", command=self.reset_search, width=int(10*SCALE_FACTOR)
        ).pack(side=tk.LEFT, padx=int(5*SCALE_FACTOR))
        ttk.Button(left_btn_frame, text="修复数据库", command=self.repair_database, width=int(10*SCALE_FACTOR)
        ).pack(side=tk.LEFT, padx=int(5*SCALE_FACTOR))
        right_btn_frame = ttk.Frame(search_row4)
        right_btn_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        ttk.Button(right_btn_frame, text="导入数据", command=self.import_data, width=int(10*SCALE_FACTOR)
        ).pack(side=tk.RIGHT, padx=(0, int(5*SCALE_FACTOR)))
        ttk.Button(right_btn_frame, text="导出数据", command=self.export_data, width=int(10*SCALE_FACTOR)
        ).pack(side=tk.RIGHT, padx=(0, int(5*SCALE_FACTOR)))

    def setup_tree_columns(self):
        columns = [
            ("row_num", "序号", int(35*SCALE_FACTOR)),
            ("dungeon", "副本名称", int(100*SCALE_FACTOR)),
            ("time", "时间", int(100*SCALE_FACTOR)),
            ("team_type", "团队类型", int(70*SCALE_FACTOR)),
            ("lie_down", "躺拍人数", int(70*SCALE_FACTOR)),
            ("total", "团队总收入", int(100*SCALE_FACTOR)),
            ("personal", "个人收入", int(100*SCALE_FACTOR)),
            ("consumption", "个人消费", int(100*SCALE_FACTOR)),
            ("black_owner", "团长", int(70*SCALE_FACTOR)),
            ("worker", "打工仔", int(70*SCALE_FACTOR)),
            ("note", "备注", int(100*SCALE_FACTOR))
        ]
        for col_id, heading, width in columns:
            self.record_tree.heading(col_id, text=heading, anchor="center")
            self.record_tree.column(col_id, width=width, anchor=tk.CENTER, stretch=(col_id == "note"))

    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="删除记录", command=self.delete_selected_records)
        self.record_tree.bind("<Button-3>", self.show_record_context_menu)

    def create_stats_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=int(10*SCALE_FACTOR), pady=int(10*SCALE_FACTOR))
        if not MATPLOTLIB_AVAILABLE:
            self.show_matplotlib_error(main_frame)
            return
        pane = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)
        left_frame = ttk.Frame(pane)
        left_frame.pack(fill=tk.BOTH, expand=True)
        self.build_stats_cards(left_frame)
        right_frame = ttk.Frame(pane)
        right_frame.pack(fill=tk.BOTH, expand=True)
        self.build_chart_area(right_frame)
        self.build_worker_stats(right_frame)
        pane.add(left_frame, weight=1)
        pane.add(right_frame, weight=2)
        self.setup_global_click_handler()

    def initialize_stats_tab_chart(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        try:
            total_records = self.db.execute_query("SELECT COUNT(*) FROM records")[0][0]
            if total_records == 0:
                if hasattr(self, 'ax') and self.ax:
                    self.ax.clear()
                    self.ax.text(0.5, 0.5, '暂无数据\n请先添加副本记录', 
                                ha='center', va='center', 
                                transform=self.ax.transAxes, fontsize=12, color='gray')
                    self.ax.set_xticks([])
                    self.ax.set_yticks([])
                    self.ax.set_frame_on(False)
                    self.ax.set_title('')
                    if hasattr(self, 'canvas') and self.canvas:
                        self.canvas.draw()
                return
            self.prepare_chart_data()
            self.update_chart()
        except Exception as e:
            pass

    def show_matplotlib_error(self, parent):
        error_frame = ttk.Frame(parent)
        error_frame.pack(fill=tk.BOTH, expand=True, pady=int(20*SCALE_FACTOR))
        ttk.Label(error_frame, 
                text="需要安装matplotlib、numpy和mplcursors库才能显示统计图表\n请运行: pip install matplotlib numpy mplcursors", 
                foreground="red", font=("PingFang SC", int(10*SCALE_FACTOR)), 
                anchor="center", justify="center"
        ).pack(fill=tk.BOTH, expand=True)

    def build_stats_cards(self, parent):
        self.total_records_var = tk.StringVar(value="0")
        self.team_total_gold_var = tk.StringVar(value="0")
        self.team_max_gold_var = tk.StringVar(value="0")
        self.personal_total_gold_var = tk.StringVar(value="0")
        self.personal_max_gold_var = tk.StringVar(value="0")
        self.personal_total_consumption_var = tk.StringVar(value="0")
        self.personal_max_consumption_var = tk.StringVar(value="0")
        self.personal_total_income_var = tk.StringVar(value="0")
        self.personal_max_income_var = tk.StringVar(value="0")
        cards = [
            ("总记录数", self.total_records_var),
            ("团队总收入", self.team_total_gold_var),
            ("团队最高收入", self.team_max_gold_var),
            ("个人总收入", self.personal_total_gold_var),
            ("个人最高收入", self.personal_max_gold_var),
            ("个人总消费", self.personal_total_consumption_var),
            ("个人最高消费", self.personal_max_consumption_var),
            ("个人总净收入", self.personal_total_income_var),
            ("个人最高净收入", self.personal_max_income_var)
        ]
        for title, var in cards:
            card = ttk.LabelFrame(parent, text=title, padding=(int(10*SCALE_FACTOR), int(8*SCALE_FACTOR)))
            card.pack(fill=tk.X, pady=int(5*SCALE_FACTOR))
            ttk.Label(card, textvariable=var, font=("PingFang SC", int(14*SCALE_FACTOR), "bold"), anchor="center"
            ).pack(fill=tk.BOTH, expand=True)

    def build_chart_area(self, parent):
        chart_frame = ttk.LabelFrame(parent, text="", padding=(int(8*SCALE_FACTOR), int(6*SCALE_FACTOR)))
        chart_frame.pack(fill=tk.BOTH, expand=True)
        if MATPLOTLIB_AVAILABLE:
            try:
                plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                self.fig, self.ax = plt.subplots(figsize=(10, 5), dpi=100)
                self.fig.patch.set_facecolor('#f5f5f7')
                self.ax.set_facecolor('#f5f5f7')
                total_records = self.db.execute_query("SELECT COUNT(*) FROM records")[0][0]
                if total_records == 0:
                    self.ax.text(0.5, 0.5, '暂无数据\n请先添加副本记录', 
                                ha='center', va='center', 
                                transform=self.ax.transAxes, fontsize=12, color='gray')
                    self.ax.set_xticks([])
                    self.ax.set_yticks([])
                    self.ax.set_frame_on(False)
                else:
                    self.ax.text(0.5, 0.5, '正在加载图表数据...', 
                                ha='center', va='center', 
                                transform=self.ax.transAxes, fontsize=12, color='gray')
                    self.ax.set_xticks([])
                    self.ax.set_yticks([])
                    self.ax.set_frame_on(False)
                self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
                self.canvas_widget = self.canvas.get_tk_widget()
                self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
                self.fig.tight_layout()
                self.canvas.draw()
            except Exception as e:
                self.show_matplotlib_error(chart_frame)
        else:
            self.show_matplotlib_error(chart_frame)

    def create_preset_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=int(5*SCALE_FACTOR), pady=int(5*SCALE_FACTOR))
        list_frame = ttk.LabelFrame(main_frame, text="副本列表", padding=int(8*SCALE_FACTOR))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, int(5*SCALE_FACTOR)))
        self.build_dungeon_list(list_frame)
        form_frame = ttk.LabelFrame(main_frame, text="副本详情", padding=int(8*SCALE_FACTOR))
        form_frame.pack(fill=tk.X, pady=(0, int(5*SCALE_FACTOR)))
        self.build_dungeon_form(form_frame)
        form_frame.configure(height=int(200*SCALE_FACTOR))

    def build_dungeon_list(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, int(8*SCALE_FACTOR)))
        self.dungeon_tree = ttk.Treeview(tree_frame, columns=("name", "drops"), show="headings", height=int(22*SCALE_FACTOR))
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.dungeon_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.dungeon_tree.xview)
        self.dungeon_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.dungeon_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        columns = [
            ("name", "副本名称", int(120*SCALE_FACTOR)),
            ("drops", "特殊掉落", int(150*SCALE_FACTOR))
        ]
        for col_id, heading, width in columns:
            self.dungeon_tree.heading(col_id, text=heading, anchor="center")
            self.dungeon_tree.column(col_id, width=width, anchor=tk.CENTER)
        self.setup_column_resizing(self.dungeon_tree)
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(0, 0))
        buttons = [
            ("编辑副本", self.edit_dungeon),
            ("更新副本", self.update_dungeon),
            ("删除副本", self.delete_dungeon)
        ]
        for i, (text, command) in enumerate(buttons):
            btn = ttk.Button(btn_frame, text=text, command=command, width=int(10*SCALE_FACTOR))
            btn.pack(side=tk.LEFT, padx=int(2*SCALE_FACTOR), fill=tk.X, expand=True)
            if text == "更新副本":
                self.preset_update_btn = btn
                self.preset_update_btn.configure(state=tk.DISABLED)

    def build_dungeon_form(self, parent):
        parent.grid_columnconfigure(1, weight=1)
        name_row = ttk.Frame(parent)
        name_row.grid(row=0, column=0, columnspan=3, sticky="ew", pady=int(5*SCALE_FACTOR))
        name_row.columnconfigure(1, weight=1)
        ttk.Label(name_row, text="副本名称:").grid(row=0, column=0, padx=int(4*SCALE_FACTOR), sticky=tk.W)
        self.preset_name_entry = ttk.Entry(name_row, textvariable=self.preset_name_var, 
                                          width=int(15*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.preset_name_entry.grid(row=0, column=1, padx=int(4*SCALE_FACTOR), sticky=tk.W)
        btn_frame = ttk.Frame(name_row)
        btn_frame.grid(row=0, column=2, padx=int(4*SCALE_FACTOR), sticky=tk.E)
        ttk.Button(btn_frame, text="新建", width=int(8*SCALE_FACTOR), command=self.create_dungeon
        ).pack(side=tk.LEFT, padx=int(2*SCALE_FACTOR))
        ttk.Button(btn_frame, text="清空", width=int(8*SCALE_FACTOR), command=self.clear_preset_form
        ).pack(side=tk.LEFT, padx=int(2*SCALE_FACTOR))
        ttk.Label(parent, text="特殊掉落:").grid(row=1, column=0, padx=int(4*SCALE_FACTOR), pady=int(5*SCALE_FACTOR), sticky=tk.W)
        self.preset_drops_entry = ttk.Entry(parent, textvariable=self.preset_drops_var, 
                                           width=int(180*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.preset_drops_entry.grid(row=1, column=1, padx=int(4*SCALE_FACTOR), pady=int(5*SCALE_FACTOR), sticky=tk.W, columnspan=2)
        batch_frame = ttk.LabelFrame(parent, text="批量添加特殊掉落", padding=int(6*SCALE_FACTOR))
        batch_frame.grid(row=2, column=0, columnspan=3, padx=int(4*SCALE_FACTOR), pady=int(5*SCALE_FACTOR), sticky=tk.W+tk.E)
        batch_frame.columnconfigure(0, weight=1)
        ttk.Label(batch_frame, text="输入多个物品，用逗号或方括号分隔:").pack(side=tk.TOP, anchor=tk.W, pady=(0, int(4*SCALE_FACTOR)))
        input_frame = ttk.Frame(batch_frame)
        input_frame.pack(fill=tk.X, pady=int(2*SCALE_FACTOR))
        self.batch_items_var = tk.StringVar()
        batch_entry = ttk.Entry(input_frame, textvariable=self.batch_items_var, font=("PingFang SC", int(10*SCALE_FACTOR)))
        batch_entry.pack(side=tk.LEFT, padx=(0, int(8*SCALE_FACTOR)), fill=tk.X, expand=True)
        ttk.Button(input_frame, text="添加", command=self.batch_add_items, width=int(8*SCALE_FACTOR)
        ).pack(side=tk.LEFT)

    def create_dungeon(self):
        name = self.preset_name_var.get().strip()
        drops = self.preset_drops_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "副本名称不能为空")
            return
        
        if self.db.dungeon_exists(name):
            messagebox.showwarning("警告", f"副本 '{name}' 已存在，无法创建同名副本")
            return
        
        try:
            self.db.execute_update('''
                INSERT INTO dungeons (name, special_drops, is_public)
                VALUES (?, ?, 0)
            ''', (name, drops))
            messagebox.showinfo("成功", "副本新建成功")
            self.clear_preset_form()
            self.load_dungeon_presets()
            self.load_dungeon_options()
        except Exception as e:
            messagebox.showerror("错误", f"新建副本失败: {str(e)}")

    def create_weekly_tab(self, parent):
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=int(10*SCALE_FACTOR), pady=int(10*SCALE_FACTOR))
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, int(10*SCALE_FACTOR)))
        ttk.Label(control_frame, text="选择打工仔:").pack(side=tk.LEFT, padx=(0, int(5*SCALE_FACTOR)))
        self.weekly_worker_combo = ttk.Combobox(control_frame, textvariable=self.weekly_worker_var, 
                                            width=int(20*SCALE_FACTOR), font=("PingFang SC", int(10*SCALE_FACTOR)))
        self.weekly_worker_combo.pack(side=tk.LEFT, padx=(0, int(15*SCALE_FACTOR)))
        self.weekly_worker_combo.bind("<<ComboboxSelected>>", self.on_weekly_worker_select)
        ttk.Label(control_frame, text="(留空显示全部记录)", 
                font=("PingFang SC", int(9*SCALE_FACTOR)), foreground="gray").pack(side=tk.LEFT, padx=(0, int(15*SCALE_FACTOR)))
        ttk.Label(control_frame, textvariable=self.weekly_period_var, 
                font=("PingFang SC", int(10*SCALE_FACTOR), "bold")).pack(side=tk.LEFT)
        ttk.Button(control_frame, text="刷新数据", command=self.load_weekly_data
                ).pack(side=tk.RIGHT, padx=(int(5*SCALE_FACTOR), 0))
        tree_frame = ttk.LabelFrame(main_frame, text="本周秘境记录", padding=int(8*SCALE_FACTOR))
        tree_frame.pack(fill=tk.BOTH, expand=True)
        columns = ("end_time", "worker", "team_type", "dungeon", "note")
        self.weekly_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                    height=int(15*SCALE_FACTOR), selectmode="browse")
        column_config = [
            ("end_time", "结束时间", int(150*SCALE_FACTOR)),
            ("worker", "打工仔", int(120*SCALE_FACTOR)),
            ("team_type", "团队类型", int(80*SCALE_FACTOR)),
            ("dungeon", "副本", int(150*SCALE_FACTOR)),
            ("note", "备注", int(150*SCALE_FACTOR))
        ]
        for col_id, heading, width in column_config:
            self.weekly_tree.heading(col_id, text=heading, anchor="center")
            self.weekly_tree.column(col_id, width=width, anchor=tk.CENTER, stretch=(col_id == "note"))
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.weekly_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.weekly_tree.xview)
        self.weekly_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.weekly_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self.setup_column_resizing(self.weekly_tree)

    def create_analysis_tab(self, parent):
        self.db_analyzer = DBAnalyzer(parent, self)

    def setup_events(self):
        self.scattered_consumption_var.trace_add("write", self.update_total_consumption)
        self.iron_consumption_var.trace_add("write", self.update_total_consumption)
        self.special_consumption_var.trace_add("write", self.update_total_consumption)
        self.other_consumption_var.trace_add("write", self.update_total_consumption)
        reg = self.root.register(self.validate_numeric_input)
        vcmd = (reg, '%P')
        for entry in [self.trash_gold_entry, self.iron_gold_entry, self.other_gold_entry, 
                    self.fine_gold_entry, self.subsidy_gold_entry, self.lie_down_entry, 
                    self.total_gold_entry, self.personal_gold_entry, self.scattered_consumption_entry, 
                    self.iron_consumption_entry, self.special_consumption_entry, 
                    self.other_consumption_entry]:
            if entry:
                entry.config(validate="key", validatecommand=vcmd)
        if hasattr(self, 'notebook'):
            self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        if hasattr(self, 'dungeon_combo') and self.dungeon_combo:
            self.dungeon_combo.bind("<<ComboboxSelected>>", self.on_dungeon_select)
        if hasattr(self, 'search_dungeon_combo') and self.search_dungeon_combo:
            self.search_dungeon_combo.bind("<<ComboboxSelected>>", self.on_search_dungeon_select)
        if hasattr(self, 'record_tree') and self.record_tree:
            self.record_tree.bind('<ButtonRelease-1>', self.on_record_click)
        self.root.after(2000, self.safe_load_column_widths)
        self.root.after(1000, self.update_time)

    def setup_global_click_handler(self):
        def on_global_click(event):
            current_tab = self.get_current_tab()
            if current_tab != "数据总览":
                return
            clicked_in_tree = False
            if hasattr(self, 'worker_stats_tree') and self.worker_stats_tree:
                tree_bbox = (
                    self.worker_stats_tree.winfo_rootx(),
                    self.worker_stats_tree.winfo_rooty(),
                    self.worker_stats_tree.winfo_rootx() + self.worker_stats_tree.winfo_width(),
                    self.worker_stats_tree.winfo_rooty() + self.worker_stats_tree.winfo_height()
                )
                if (tree_bbox[0] <= event.x_root <= tree_bbox[2] and 
                    tree_bbox[1] <= event.y_root <= tree_bbox[3]):
                    clicked_in_tree = True
            if not clicked_in_tree:
                if hasattr(self, 'worker_stats_tree') and self.worker_stats_tree:
                    self.worker_stats_tree.selection_remove(self.worker_stats_tree.selection())
                self.selected_worker = None
                self.selected_team_type = None
                self.remove_detail_rows()
                self.update_chart()
        self.root.bind('<Button-1>', on_global_click)

    def on_tab_changed(self, event):
        try:
            current_tab = self.notebook.tab(self.notebook.select(), "text")
            if current_tab == "数据总览":
                self.update_stats()
                self.update_worker_stats()
                self.update_chart()
            elif current_tab == "秘境记录":
                self.load_weekly_data()
        except Exception as e:
            pass

    def get_current_tab(self):
        try:
            def find_notebook(widget):
                if isinstance(widget, ttk.Notebook):
                    return widget
                for child in widget.winfo_children():
                    result = find_notebook(child)
                    if result:
                        return result
                return None
            notebook = find_notebook(self.root)
            if notebook:
                current_index = notebook.index(notebook.select())
                tab_text = notebook.tab(current_index, "text")
                return tab_text
        except Exception as e:
            pass
        return "未知"

    def safe_load_column_widths(self):
        try:
            self.load_column_widths()
        except AttributeError:
            self.root.after(1000, self.safe_load_column_widths)

    def load_column_widths(self):
        trees = []
        if hasattr(self, 'record_tree') and self.record_tree and self.record_tree.winfo_exists():
            trees.append((self.record_tree, "record_tree"))
        if hasattr(self, 'worker_stats_tree') and self.worker_stats_tree and self.worker_stats_tree.winfo_exists():
            trees.append((self.worker_stats_tree, "worker_stats_tree"))
        if hasattr(self, 'dungeon_tree') and self.dungeon_tree and self.dungeon_tree.winfo_exists():
            trees.append((self.dungeon_tree, "dungeon_tree"))
        if hasattr(self, 'weekly_tree') and self.weekly_tree and self.weekly_tree.winfo_exists():
            trees.append((self.weekly_tree, "weekly_tree"))
        for tree, tree_name in trees:
            try:
                result = self.db.execute_query("SELECT widths FROM column_widths WHERE tree_name = ?", (tree_name,))
                if result and result[0][0]:
                    widths = json.loads(result[0][0])
                    for col, width in widths.items():
                        if col in tree["columns"]:
                            tree.column(col, width=width)
            except Exception as e:
                pass

    def save_column_widths(self):
        trees = []
        if hasattr(self, 'record_tree') and self.record_tree and self.record_tree.winfo_exists():
            trees.append((self.record_tree, "record_tree"))
        if hasattr(self, 'worker_stats_tree') and self.worker_stats_tree and self.worker_stats_tree.winfo_exists():
            trees.append((self.worker_stats_tree, "worker_stats_tree"))
        if hasattr(self, 'dungeon_tree') and self.dungeon_tree and self.dungeon_tree.winfo_exists():
            trees.append((self.dungeon_tree, "dungeon_tree"))
        if hasattr(self, 'weekly_tree') and self.weekly_tree and self.weekly_tree.winfo_exists():
            trees.append((self.weekly_tree, "weekly_tree"))
        for tree, tree_name in trees:
            try:
                widths = {col: tree.column(col, "width") for col in tree["columns"]}
                self.db.execute_update('''
                    INSERT OR REPLACE INTO column_widths (tree_name, widths)
                    VALUES (?, ?)
                ''', (tree_name, json.dumps(widths)))
            except Exception as e:
                pass

    def auto_resize_column(self, tree, column_id):
        font = tkFont.Font(family="PingFang SC", size=int(10*SCALE_FACTOR))
        heading_text = tree.heading(column_id)["text"]
        max_width = font.measure(heading_text) + int(20*SCALE_FACTOR)
        for item in tree.get_children():
            cell_value = tree.set(item, column_id)
            if cell_value:
                cell_width = font.measure(cell_value) + int(20*SCALE_FACTOR)
                if cell_width > max_width:
                    max_width = cell_width
        tree.column(column_id, width=max_width)

    def setup_column_resizing(self, tree):
        columns = tree["columns"]
        for col in columns:
            tree.heading(col, command=lambda c=col: self.auto_resize_column(tree, c))

    def on_record_click(self, event):
        item = self.record_tree.identify('item', event.x, event.y)
        if not item:
            return
        selected = self.record_tree.selection()
        if len(selected) == 1 and item in selected:
            self.fill_form_from_record(item)

    def fill_form_from_record(self, item):
        values = self.record_tree.item(item, 'values')
        if not values:
            return
        dungeon_name = values[1]
        time_str = values[2]
        record = self.db.execute_query('''
            SELECT r.id, d.name, r.trash_gold, r.iron_gold, r.other_gold, r.special_auctions, 
                r.total_gold, r.black_owner, r.worker, r.time, r.team_type, r.lie_down_count, 
                r.fine_gold, r.subsidy_gold, r.personal_gold, r.note,
                r.scattered_consumption, r.iron_consumption, r.special_consumption, r.other_consumption, r.total_consumption
            FROM records r
            JOIN dungeons d ON r.dungeon_id = d.id
            WHERE d.name = ? AND r.time LIKE ?
        ''', (dungeon_name, f"{time_str}%"))
        if not record:
            return
        r = record[0]
        record_id = r[0]
        if record_id in self.new_record_ids:
            self.db.execute_update("UPDATE records SET is_new = 0 WHERE id = ?", (record_id,))
            self.new_record_ids.discard(record_id)
            self.record_tree.item(item, tags=())
        self.dungeon_var.set(r[1])
        self.trash_gold_var.set(str(r[2]))
        self.iron_gold_var.set(str(r[3]))
        self.other_gold_var.set(str(r[4]))
        self.total_gold_var.set(str(r[6]))
        self.black_owner_var.set(r[7] or "")
        self.worker_var.set(r[8] or "")
        self.team_type_var.set(r[10])
        self.lie_down_var.set(str(r[11]))
        self.fine_gold_var.set(str(r[12]))
        self.subsidy_gold_var.set(str(r[13]))
        self.personal_gold_var.set(str(r[14]))
        self.note_var.set(r[15] or "")
        self.scattered_consumption_var.set(str(r[16]))
        self.iron_consumption_var.set(str(r[17]))
        self.special_consumption_var.set(str(r[18]))
        self.other_consumption_var.set(str(r[19]))
        self.total_consumption_var.set(str(r[20]))
        self.special_tree.clear()
        special_auctions = json.loads(r[5]) if r[5] else []
        for item_data in special_auctions:
            self.special_tree.add_item(item_data['item'], item_data['price'])
        self.special_total_var.set(str(self.special_tree.calculate_total()))
        self.add_btn.configure(state=tk.NORMAL)
        self.edit_btn.configure(state=tk.NORMAL)
        self.update_btn.configure(state=tk.DISABLED)
        if hasattr(self, 'current_edit_id'):
            del self.current_edit_id
        self.update_special_items_combo()

    def update_special_items_combo(self):
        selected_dungeon = self.dungeon_var.get()
        if not selected_dungeon:
            return
        try:
            result = self.db.execute_query("SELECT special_drops FROM dungeons WHERE name=?", (selected_dungeon,))
            current_dungeon_items = []
            if result and result[0][0]:
                current_dungeon_items = [item.strip() for item in result[0][0].split(',')]
            public_result = self.db.execute_query("SELECT special_drops FROM dungeons WHERE is_public = 1")
            public_items = []
            if public_result and public_result[0][0]:
                public_items = [item.strip() for item in public_result[0][0].split(',')]
            all_items = current_dungeon_items + public_items
            if hasattr(self, 'special_item_combo') and self.special_item_combo:
                self.special_item_combo['values'] = all_items
                self.special_item_var.set("")
        except Exception as e:
            pass

    def load_dungeon_options(self):
        try:
            self.cached_dungeons = [row[0] for row in self.db.execute_query(
                "SELECT name FROM dungeons WHERE is_public = 0 ORDER BY name"
            )]
        except Exception as e:
            self.cached_dungeons = []
        if hasattr(self, 'dungeon_combo') and self.dungeon_combo:
            self.dungeon_combo['values'] = self.cached_dungeons
        if hasattr(self, 'search_dungeon_combo') and self.search_dungeon_combo:
            self.search_dungeon_combo['values'] = self.cached_dungeons

    def get_all_special_items(self):
        items = set()
        for row in self.db.execute_query("SELECT special_drops FROM dungeons"):
            if row[0]:
                for item in row[0].split(','):
                    items.add(item.strip())
        return list(items)

    def load_recent_records(self, limit=50):
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        records = self.db.execute_query('''
            SELECT r.id, 
                COALESCE(d.name, '未知副本') as dungeon_name, 
                strftime('%Y-%m-%d %H:%M', r.time), 
                r.team_type, r.lie_down_count, r.total_gold, 
                r.personal_gold, r.black_owner, r.worker, r.note, r.is_new,
                r.total_consumption
            FROM records r
            LEFT JOIN dungeons d ON r.dungeon_id = d.id
            ORDER BY r.time DESC
            LIMIT ?
        ''', (limit,))
        total_records = len(records)
        row_num = total_records
        for row in records:
            note = row[9] or ""
            if len(note) > 30:
                note = note[:30] + "..."
            tags = ()
            if row[10] == 1:
                tags = ("new_record",)
            self.record_tree.insert("", "end", values=(
                row_num, row[1], row[2], row[3], row[4], 
                f"{row[5]:,}", f"{row[6]:,}", f"{row[11]:,}",
                row[7], row[8], note
            ), tags=tags)
            row_num -= 1
        self.clear_new_record_highlights_after_load()

    def load_remaining_records_background(self):
        try:
            remaining_records = self.db.execute_query('''
                SELECT r.id, 
                    COALESCE(d.name, '未知副本') as dungeon_name, 
                    strftime('%Y-%m-%d %H:%M', r.time), 
                    r.team_type, r.lie_down_count, r.total_gold, 
                    r.personal_gold, r.black_owner, r.worker, r.note, r.is_new,
                    r.total_consumption
                FROM records r
                LEFT JOIN dungeons d ON r.dungeon_id = d.id
                WHERE r.id NOT IN (
                    SELECT id FROM records ORDER BY time DESC LIMIT 50
                )
                ORDER BY r.time DESC
            ''')
            self.root.after(0, self.append_records_batch, remaining_records)
        except Exception as e:
            pass

    def append_records_batch(self, records):
        if not records:
            return
        batch_size = 20
        current_batch = records[:batch_size]
        remaining_records = records[batch_size:]
        start_index = len(self.record_tree.get_children())
        for row in current_batch:
            note = row[9] or ""
            if len(note) > 30:
                note = note[:30] + "..."
            tags = ()
            if row[10] == 1:
                tags = ("new_record",)
                self.new_record_ids.add(row[0])
            self.record_tree.insert("", "end", values=(
                start_index + 1, row[1], row[2], row[3], row[4], 
                f"{row[5]:,}", f"{row[6]:,}", f"{row[11]:,}",
                row[7], row[8], note
            ), tags=tags)
            start_index += 1
        if remaining_records:
            self.root.after(500, self.append_records_batch, remaining_records)

    def clear_new_record_highlights(self):
        self.db.execute_update("UPDATE records SET is_new = 0 WHERE is_new = 1")
        for item in self.record_tree.get_children():
            self.record_tree.item(item, tags=())

    def clear_new_record_highlights_on_startup(self):
        try:
            if hasattr(self, 'db') and self.db:
                self.db.execute_update("UPDATE records SET is_new = 0 WHERE is_new = 1")
        except Exception as e:
            pass

    def clear_new_record_highlights_after_load(self):
        try:
            if hasattr(self, 'db') and self.db:
                self.db.execute_update("UPDATE records SET is_new = 0 WHERE is_new = 1")
                if hasattr(self, 'new_record_ids'):
                    self.new_record_ids.clear()
        except Exception as e:
            pass

    def load_dungeon_presets(self):
        self.dungeon_tree.delete(*self.dungeon_tree.get_children())
        for row in self.db.execute_query("SELECT name, special_drops, is_public FROM dungeons ORDER BY is_public DESC, name"):
            self.dungeon_tree.insert("", "end", values=(row[0], row[1]))

    # === 修改点 3：更新 on_search_dungeon_select 方法，记录选中的副本 ===
    def on_search_dungeon_select(self, event=None):
        selected = self.search_dungeon_var.get()
        self.current_search_dungeon = selected if selected else None
        if selected:
            result = self.db.execute_query("SELECT special_drops FROM dungeons WHERE name=?", (selected,))
            if result and result[0][0]:
                drops = [item.strip() for item in result[0][0].split(',')]
            else:
                drops = []
            self.search_item_combo['values'] = drops
        else:
            self.search_item_combo['values'] = self.get_all_special_items()
        self.search_item_var.set("")
    # ================================================================

    def update_time(self):
        try:
            if not self.root.winfo_exists() or self.is_closing:
                return
            self.time_var.set(get_current_time())
            after_id = self.root.after(1000, self.update_time)
            self.after_ids.append(after_id)
        except Exception:
            pass

    def schedule_time_update(self):
        if hasattr(self, 'time_var'):
            self.root.after(1000, self.update_time)

    def setup_pane_events(self):
        if hasattr(self, 'record_pane'):
            def save_pane_position(event=None):
                if hasattr(self, '_pane_save_scheduled') and self._pane_save_scheduled is not None:
                    try:
                        self.root.after_cancel(self._pane_save_scheduled)
                    except (ValueError, tk.TclError):
                        pass
                    self._pane_save_scheduled = None
                self._pane_save_scheduled = self.root.after(500, self.save_pane_positions)
            self.record_pane.bind("<ButtonRelease-1>", save_pane_position)

    def save_pane_positions(self):
        try:
            self._pane_save_scheduled = None
            if hasattr(self, 'record_pane') and self.record_pane:
                try:
                    sash_count = self.record_pane.panes()
                    if sash_count and len(sash_count) > 0:
                        try:
                            pos = self.record_pane.sashpos(0)
                            if pos is not None:
                                pos = int(pos)
                                self.db.save_pane_position(self.record_pane_name, pos)
                        except Exception as e1:
                            try:
                                geometry = self.record_pane.winfo_geometry()
                                if geometry:
                                    width = self.record_pane.winfo_width()
                                    if width > 0:
                                        pos = int(width * 0.3)
                                        self.db.save_pane_position(self.record_pane_name, pos)
                            except Exception as e2:
                                pass
                except Exception as e:
                    pass
        except Exception as e:
            import traceback
            traceback.print_exc()

    def restore_pane_position(self, pane, pane_name):
        try:
            pos = self.db.get_pane_position(pane_name)
            if pos is not None:
                if isinstance(pos, (int, float)):
                    pos = int(pos)
                    try:
                        pane.sashpos(0, pos)
                    except Exception as e1:
                        try:
                            pane.sash_place(0, pos, 0)
                        except Exception as e2:
                            pass
        except Exception as e:
            import traceback
            traceback.print_exc()

    def setup_window_tracking(self):
        def save_window_state(event=None):
            if hasattr(self, '_save_scheduled') and self._save_scheduled is not None:
                try:
                    self.root.after_cancel(self._save_scheduled)
                except (ValueError, tk.TclError):
                    pass
                self._save_scheduled = None
            self._save_scheduled = self.root.after(500, self.save_window_state_to_db)
        self.root.bind('<Configure>', save_window_state)

    def save_window_state_to_db(self):
        try:
            self._save_scheduled = None
            if not hasattr(self, 'root') or not self.root.winfo_exists():
                return
            if self.root.state() == 'normal':
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                maximized = 0
            else:
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                maximized = 1
            self.db.execute_update('''
                DELETE FROM window_state
            ''')
            self.db.execute_update('''
                INSERT INTO window_state (width, height, maximized, x, y)
                VALUES (?, ?, ?, ?, ?)
            ''', (width, height, maximized, x, y))
        except Exception as e:
            pass

    def restore_window_state(self):
        try:
            result = self.db.execute_query("SELECT width, height, maximized, x, y FROM window_state")
            if result:
                width, height, maximized, x, y = result[0]
                if width > 0 and height > 0:
                    if maximized:
                        self.root.geometry(f"{width}x{height}+{x}+{y}")
                    else:
                        self.root.geometry(f"{width}x{height}+{x}+{y}")
        except Exception as e:
            pass

    def load_black_owner_options(self):
        try:
            self.cached_owners = None
            self.cached_owners = sorted(list(set(
                row[0] for row in self.db.execute_query(
                    "SELECT DISTINCT black_owner FROM records WHERE black_owner IS NOT NULL AND black_owner != ''"
                )
            )))
        except Exception as e:
            self.cached_owners = []
        if hasattr(self, 'black_owner_combo') and self.black_owner_combo:
            self.black_owner_combo['values'] = self.cached_owners
        if hasattr(self, 'search_owner_combo') and self.search_owner_combo:
            self.search_owner_combo['values'] = self.cached_owners

    def load_worker_options(self):
        try:
            self.cached_workers = None
            self.cached_workers = sorted(list(set(
                row[0] for row in self.db.execute_query(
                    "SELECT DISTINCT worker FROM records WHERE worker IS NOT NULL AND worker != ''"
                )
            )))
        except Exception as e:
            self.cached_workers = []
        if hasattr(self, 'worker_combo') and self.worker_combo:
            self.worker_combo['values'] = self.cached_workers
        if hasattr(self, 'search_worker_combo') and self.search_worker_combo:
            self.search_worker_combo['values'] = self.cached_workers
        if hasattr(self, 'weekly_worker_combo') and self.weekly_worker_combo:
            self.weekly_worker_combo['values'] = [''] + self.cached_workers

    def load_weekly_worker_options(self):
        try:
            workers = sorted(list(set(
                row[0] for row in self.db.execute_query(
                    "SELECT DISTINCT worker FROM records WHERE worker IS NOT NULL AND worker != ''"
                )
            )))
            if hasattr(self, 'weekly_worker_combo') and self.weekly_worker_combo:
                self.weekly_worker_combo['values'] = [''] + workers
                self.weekly_worker_combo.set('')
        except Exception as e:
            pass

    def update_total_consumption(self, *args):
        try:
            scattered = int(self.scattered_consumption_var.get() or 0)
            iron = int(self.iron_consumption_var.get() or 0)
            special = int(self.special_consumption_var.get() or 0)
            other = int(self.other_consumption_var.get() or 0)
            total = scattered + iron + special + other
            self.total_consumption_var.set(str(total))
        except ValueError:
            self.total_consumption_var.set("0")

    def add_special_item(self):
        item = self.special_item_var.get().strip()
        price_str = self.special_price_var.get().strip()
        if not item or not price_str:
            messagebox.showwarning("警告", "请填写物品名称和价格")
            return
        try:
            price = int(price_str)
            if price < 0:
                raise ValueError("价格不能为负数")
        except ValueError:
            messagebox.showwarning("警告", "价格必须是有效的非负整数")
            return
        self.special_tree.add_item(item, price)
        self.special_item_var.set("")
        self.special_price_var.set("")
        self.special_total_var.set(str(self.special_tree.calculate_total()))

    def on_dungeon_select(self, event):
        selected_dungeon = self.dungeon_var.get()
        if selected_dungeon:
            self.update_special_items_combo()

    def update_special_items_combo_immediately(self, dungeon_name):
        if not dungeon_name:
            return
        try:
            result = self.db.execute_query("SELECT special_drops FROM dungeons WHERE name = ?", (dungeon_name,))
            current_dungeon_items = []
            if result and result[0][0]:
                current_dungeon_items = [item.strip() for item in result[0][0].split(',')]
            public_result = self.db.execute_query("SELECT special_drops FROM dungeons WHERE is_public = 1")
            public_items = []
            if public_result and public_result[0][0]:
                public_items = [item.strip() for item in public_result[0][0].split(',')]
            all_items = current_dungeon_items + public_items
            if hasattr(self, 'special_item_combo') and self.special_item_combo:
                self.special_item_combo['values'] = all_items
                self.special_item_var.set("")
        except Exception as e:
            pass

    def validate_numeric_input(self, value):
        if value == "":
            return True
        try:
            if value.isdigit():
                return True
            return False
        except ValueError:
            return False

    def validate_and_save(self):
        if not self.dungeon_var.get():
            messagebox.showwarning("警告", "请选择副本")
            return
        if not self.trash_gold_var.get():
            self.trash_gold_var.set("0")
        if not self.iron_gold_var.get():
            self.iron_gold_var.set("0")
        if not self.other_gold_var.get():
            self.other_gold_var.set("0")
        if not self.special_total_var.get():
            self.special_total_var.set("0")
        if not self.fine_gold_var.get():
            self.fine_gold_var.set("0")
        if not self.subsidy_gold_var.get():
            self.subsidy_gold_var.set("0")
        if not self.lie_down_var.get():
            self.lie_down_var.set("0")
        if not self.total_gold_var.get():
            self.total_gold_var.set("0")
        if not self.personal_gold_var.get():
            self.personal_gold_var.set("0")
        if not self.scattered_consumption_var.get():
            self.scattered_consumption_var.set("0")
        if not self.iron_consumption_var.get():
            self.iron_consumption_var.set("0")
        if not self.special_consumption_var.get():
            self.special_consumption_var.set("0")
        if not self.other_consumption_var.get():
            self.other_consumption_var.set("0")
        if not self.total_consumption_var.get():
            self.total_consumption_var.set("0")
        self.save_record()

    def save_record(self):
        try:
            special_items = self.special_tree.get_items()
            special_auctions_json = json.dumps(special_items, ensure_ascii=False)
            special_total = self.special_tree.calculate_total()
            total_gold = GoldCalculator.calculate_total(
                self.trash_gold_var.get(),
                self.iron_gold_var.get(),
                self.other_gold_var.get(),
                str(special_total)
            )
            self.total_gold_var.set(str(total_gold))
            result = self.db.execute_query("SELECT id FROM dungeons WHERE name=?", (self.dungeon_var.get(),))
            if not result:
                messagebox.showerror("错误", "找不到对应的副本")
                return
            dungeon_id = result[0][0]
            if hasattr(self, 'analysis_time') and self.analysis_time and self.analysis_time != "未找到":
                current_time = self.analysis_time
                self.analysis_time = None
            else:
                current_time = get_current_time()
            self.db.execute_update('''
                INSERT INTO records (
                    dungeon_id, trash_gold, iron_gold, other_gold, special_auctions, total_gold,
                    black_owner, worker, time, team_type, lie_down_count, fine_gold, subsidy_gold,
                    personal_gold, note, is_new,
                    scattered_consumption, iron_consumption, special_consumption, other_consumption, total_consumption
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dungeon_id,
                int(self.trash_gold_var.get()),
                int(self.iron_gold_var.get()),
                int(self.other_gold_var.get()),
                special_auctions_json,
                total_gold,
                self.black_owner_var.get(),
                self.worker_var.get(),
                current_time,
                self.team_type_var.get(),
                int(self.lie_down_var.get()),
                int(self.fine_gold_var.get()),
                int(self.subsidy_gold_var.get()),
                int(self.personal_gold_var.get()),
                self.note_var.get(),
                1,
                int(self.scattered_consumption_var.get()),
                int(self.iron_consumption_var.get()),
                int(self.special_consumption_var.get()),
                int(self.other_consumption_var.get()),
                int(self.total_consumption_var.get())
            ))
            last_id = self.db.cursor.lastrowid
            self.new_record_ids.add(last_id)
            messagebox.showinfo("成功", "记录保存成功")
            self.clear_form()
            self.load_recent_records(50)
            self.update_stats()
            self.load_black_owner_options()
            self.load_worker_options()
            self.update_worker_stats()
            self.update_chart()
        except Exception as e:
            messagebox.showerror("错误", f"保存记录失败: {str(e)}")

    def edit_record(self):
        selected = self.record_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要编辑的记录")
            return
        item = selected[0]
        values = self.record_tree.item(item, 'values')
        if not values:
            return
        dungeon_name = values[1]
        time_str = values[2]
        result = self.db.execute_query('''
            SELECT r.id, d.name, r.trash_gold, r.iron_gold, r.other_gold, r.special_auctions, 
                r.total_gold, r.black_owner, r.worker, r.time, r.team_type, r.lie_down_count, 
                r.fine_gold, r.subsidy_gold, r.personal_gold, r.note,
                r.scattered_consumption, r.iron_consumption, r.special_consumption, r.other_consumption, r.total_consumption
            FROM records r
            JOIN dungeons d ON r.dungeon_id = d.id
            WHERE d.name = ? AND r.time LIKE ?
        ''', (dungeon_name, f"{time_str}%"))
        if not result:
            messagebox.showerror("错误", "找不到对应的记录")
            return
        r = result[0]
        self.current_edit_id = r[0]
        self.dungeon_var.set(r[1])
        self.trash_gold_var.set(str(r[2]))
        self.iron_gold_var.set(str(r[3]))
        self.other_gold_var.set(str(r[4]))
        self.total_gold_var.set(str(r[6]))
        self.black_owner_var.set(r[7] or "")
        self.worker_var.set(r[8] or "")
        self.team_type_var.set(r[10])
        self.lie_down_var.set(str(r[11]))
        self.fine_gold_var.set(str(r[12]))
        self.subsidy_gold_var.set(str(r[13]))
        self.personal_gold_var.set(str(r[14]))
        self.note_var.set(r[15] or "")
        self.scattered_consumption_var.set(str(r[16]))
        self.iron_consumption_var.set(str(r[17]))
        self.special_consumption_var.set(str(r[18]))
        self.other_consumption_var.set(str(r[19]))
        self.total_consumption_var.set(str(r[20]))
        self.special_tree.clear()
        special_auctions = json.loads(r[5]) if r[5] else []
        for item_data in special_auctions:
            self.special_tree.add_item(item_data['item'], item_data['price'])
        self.special_total_var.set(str(self.special_tree.calculate_total()))
        self.add_btn.configure(state=tk.DISABLED)
        self.edit_btn.configure(state=tk.DISABLED)
        self.update_btn.configure(state=tk.NORMAL)
        self.update_special_items_combo()

    def update_record(self):
        if not hasattr(self, 'current_edit_id'):
            messagebox.showwarning("警告", "没有正在编辑的记录")
            return
        try:
            special_items = self.special_tree.get_items()
            special_auctions_json = json.dumps(special_items, ensure_ascii=False)
            special_total = self.special_tree.calculate_total()
            total_gold = GoldCalculator.calculate_total(
                self.trash_gold_var.get(),
                self.iron_gold_var.get(),
                self.other_gold_var.get(),
                str(special_total)
            )
            self.total_gold_var.set(str(total_gold))
            result = self.db.execute_query("SELECT id FROM dungeons WHERE name=?", (self.dungeon_var.get(),))
            if not result:
                messagebox.showerror("错误", "找不到对应的副本")
                return
            dungeon_id = result[0][0]
            self.db.execute_update('''
                UPDATE records SET
                    dungeon_id=?, trash_gold=?, iron_gold=?, other_gold=?, special_auctions=?, total_gold=?,
                    black_owner=?, worker=?, team_type=?, lie_down_count=?, fine_gold=?, subsidy_gold=?,
                    personal_gold=?, note=?,
                    scattered_consumption=?, iron_consumption=?, special_consumption=?, other_consumption=?, total_consumption=?
                WHERE id=?
            ''', (
                dungeon_id,
                int(self.trash_gold_var.get()),
                int(self.iron_gold_var.get()),
                int(self.other_gold_var.get()),
                special_auctions_json,
                total_gold,
                self.black_owner_var.get(),
                self.worker_var.get(),
                self.team_type_var.get(),
                int(self.lie_down_var.get()),
                int(self.fine_gold_var.get()),
                int(self.subsidy_gold_var.get()),
                int(self.personal_gold_var.get()),
                self.note_var.get(),
                int(self.scattered_consumption_var.get()),
                int(self.iron_consumption_var.get()),
                int(self.special_consumption_var.get()),
                int(self.other_consumption_var.get()),
                int(self.total_consumption_var.get()),
                self.current_edit_id
            ))
            messagebox.showinfo("成功", "记录更新成功")
            self.clear_form()
            self.load_recent_records(50)
            self.update_stats()
            self.load_black_owner_options()
            self.load_worker_options()
            self.update_worker_stats()
            self.update_chart()
        except Exception as e:
            messagebox.showerror("错误", f"更新记录失败: {str(e)}")

    def clear_form(self):
        self.dungeon_var.set("")
        self.trash_gold_var.set("")
        self.iron_gold_var.set("")
        self.other_gold_var.set("")
        self.special_total_var.set("")
        self.fine_gold_var.set("")
        self.subsidy_gold_var.set("")
        self.lie_down_var.set("")
        self.team_type_var.set("十人本")
        self.total_gold_var.set("")
        self.personal_gold_var.set("")
        self.black_owner_var.set("")
        self.worker_var.set("")
        self.note_var.set("")
        self.scattered_consumption_var.set("")
        self.iron_consumption_var.set("")
        self.special_consumption_var.set("")
        self.other_consumption_var.set("")
        self.total_consumption_var.set("")
        self.special_tree.clear()
        if hasattr(self, 'special_item_combo') and self.special_item_combo:
            self.special_item_combo['values'] = []
            self.special_item_var.set("")
        self.special_price_var.set("")
        self.add_btn.configure(state=tk.NORMAL)
        self.edit_btn.configure(state=tk.NORMAL)
        self.update_btn.configure(state=tk.DISABLED)
        if hasattr(self, 'analysis_time'):
            self.analysis_time = None
        if hasattr(self, 'current_edit_id'):
            del self.current_edit_id

    def delete_selected_records(self):
        selected = self.record_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的记录")
            return
        if messagebox.askyesno("确认删除", f"确定要删除这 {len(selected)} 条记录吗？"):
            for item in selected:
                values = self.record_tree.item(item, 'values')
                if values:
                    dungeon_name = values[1]
                    time_str = values[2]
                    self.db.execute_update('''
                        DELETE FROM records 
                        WHERE id IN (
                            SELECT r.id FROM records r
                            JOIN dungeons d ON r.dungeon_id = d.id
                            WHERE d.name = ? AND r.time LIKE ?
                        )
                    ''', (dungeon_name, f"{time_str}%"))
            messagebox.showinfo("成功", "记录删除成功")
            self.load_recent_records(50)
            self.update_stats()
            self.load_black_owner_options()
            self.load_worker_options()
            self.update_worker_stats()
            self.update_chart()

    def show_record_context_menu(self, event):
        item = self.record_tree.identify_row(event.y)
        if item:
            self.record_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def search_records(self):
        conditions = []
        params = []
        if self.search_dungeon_var.get():
            conditions.append("d.name = ?")
            params.append(self.search_dungeon_var.get())
        if self.search_item_var.get():
            conditions.append("r.special_auctions LIKE ?")
            params.append(f'%"{self.search_item_var.get()}"%')
        if self.search_owner_var.get():
            conditions.append("r.black_owner = ?")
            params.append(self.search_owner_var.get())
        if self.search_worker_var.get():
            conditions.append("r.worker = ?")
            params.append(self.search_worker_var.get())
        if self.search_team_type_var.get():
            conditions.append("r.team_type = ?")
            params.append(self.search_team_type_var.get())
        if self.start_date_var.get():
            conditions.append("r.time >= ?")
            params.append(self.start_date_var.get())
        if self.end_date_var.get():
            conditions.append("r.time <= ?")
            params.append(self.end_date_var.get())
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f'''
            SELECT r.id, 
                COALESCE(d.name, '未知副本') as dungeon_name, 
                strftime('%Y-%m-%d %H:%M', r.time), 
                r.team_type, r.lie_down_count, r.total_gold, 
                r.personal_gold, r.black_owner, r.worker, r.note, r.is_new,
                r.total_consumption
            FROM records r
            LEFT JOIN dungeons d ON r.dungeon_id = d.id
            WHERE {where_clause}
            ORDER BY r.time DESC
        '''
        records = self.db.execute_query(query, params)
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        row_num = len(records)
        for row in records:
            note = row[9] or ""
            if len(note) > 30:
                note = note[:30] + "..."
            tags = ()
            if row[10] == 1:
                tags = ("new_record",)
            self.record_tree.insert("", "end", values=(
                row_num, row[1], row[2], row[3], row[4], 
                f"{row[5]:,}", f"{row[6]:,}", f"{row[11]:,}",
                row[7], row[8], note
            ), tags=tags)
            row_num -= 1

    # === 修改点 4：添加实时过滤方法 ===
    def update_search_item_combo(self, event=None):
        """根据当前输入和选中的副本动态更新特殊掉落下拉列表"""
        current_text = self.search_item_var.get().strip()
        if current_text:
            all_items = self.get_all_special_items()
            filtered = [item for item in all_items if current_text in item]
            self.search_item_combo['values'] = filtered
        else:
            if self.current_search_dungeon:
                result = self.db.execute_query("SELECT special_drops FROM dungeons WHERE name=?", (self.current_search_dungeon,))
                if result and result[0][0]:
                    drops = [item.strip() for item in result[0][0].split(',')]
                else:
                    drops = []
                self.search_item_combo['values'] = drops
            else:
                self.search_item_combo['values'] = self.get_all_special_items()
    # =================================

    # === 修改点 5：修改 reset_search 方法，重置变量并恢复下拉列表 ===
    def reset_search(self):
        self.search_dungeon_var.set("")
        self.search_item_var.set("")
        self.search_owner_var.set("")
        self.search_worker_var.set("")
        self.search_team_type_var.set("")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.current_search_dungeon = None
        self.search_item_combo['values'] = self.get_all_special_items()
        self.load_recent_records(50)
    # ==============================================================

    def export_data(self):
        export_type_window = tk.Toplevel(self.root)
        export_type_window.title("选择导出类型")
        export_type_window.geometry("300x150")
        export_type_window.transient(self.root)
        export_type_window.grab_set()
        
        ttk.Label(export_type_window, text="请选择要导出的数据类型", 
                 font=("PingFang SC", 12)).pack(pady=20)
        
        def export_selected_type(export_type):
            export_type_window.destroy()
            self._export_data(export_type)
        
        btn_frame = ttk.Frame(export_type_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="副本记录", 
                  command=lambda: export_selected_type("records"),
                  width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="副本预设", 
                  command=lambda: export_selected_type("presets"),
                  width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="全部", 
                  command=lambda: export_selected_type("all"),
                  width=10).pack(side=tk.LEFT, padx=5)

    def _export_data(self, export_type):
        file_path = filedialog.asksaveasfilename(
            title="导出数据",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            records_data = []
            dungeons_data = []
            
            if export_type in ["records", "all"]:
                records = self.db.execute_query('''
                    SELECT r.id, d.name, r.trash_gold, r.iron_gold, r.other_gold, r.special_auctions, 
                        r.total_gold, r.black_owner, r.worker, r.time, r.team_type, r.lie_down_count, 
                        r.fine_gold, r.subsidy_gold, r.personal_gold, r.note,
                        r.scattered_consumption, r.iron_consumption, r.special_consumption, r.other_consumption, r.total_consumption
                    FROM records r
                    JOIN dungeons d ON r.dungeon_id = d.id
                    ORDER BY r.time
                ''')
                for row in records:
                    records_data.append({
                        "dungeon_name": row[1],
                        "trash_gold": row[2],
                        "iron_gold": row[3],
                        "other_gold": row[4],
                        "special_auctions": json.loads(row[5]) if row[5] else [],
                        "total_gold": row[6],
                        "black_owner": row[7],
                        "worker": row[8],
                        "time": row[9],
                        "team_type": row[10],
                        "lie_down_count": row[11],
                        "fine_gold": row[12],
                        "subsidy_gold": row[13],
                        "personal_gold": row[14],
                        "note": row[15],
                        "scattered_consumption": row[16],
                        "iron_consumption": row[17],
                        "special_consumption": row[18],
                        "other_consumption": row[19],
                        "total_consumption": row[20]
                    })
            
            if export_type in ["presets", "all"]:
                dungeons = self.db.execute_query("SELECT name, special_drops, is_public FROM dungeons")
                for row in dungeons:
                    dungeons_data.append({
                        "name": row[0],
                        "special_drops": row[1],
                        "is_public": row[2]
                    })
            
            data = {
                "metadata": {
                    "export_time": get_current_time(),
                    "version": "1.0",
                    "export_type": export_type,
                    "record_count": len(records_data),
                    "dungeon_count": len(dungeons_data)
                }
            }
            
            if export_type in ["records", "all"]:
                data["records"] = records_data
            if export_type in ["presets", "all"]:
                data["dungeons"] = dungeons_data
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", f"数据已导出到 {file_path}\n导出类型: {export_type}")
        except Exception as e:
            messagebox.showerror("错误", f"导出数据失败: {str(e)}")

    def import_data(self):
        file_path = filedialog.askopenfilename(
            title="导入数据",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_dungeons = 0
            imported_records = 0
            skipped_dungeons = 0
            skipped_records = 0
            
            export_type = data.get("metadata", {}).get("export_type", "all")
            
            if export_type in ["presets", "all"] and "dungeons" in data:
                for dungeon in data["dungeons"]:
                    existing = self.db.execute_query(
                        "SELECT name FROM dungeons WHERE name = ?", 
                        (dungeon["name"],)
                    )
                    if not existing:
                        self.db.execute_update('''
                            INSERT INTO dungeons (name, special_drops, is_public)
                            VALUES (?, ?, ?)
                        ''', (dungeon["name"], dungeon["special_drops"], dungeon.get("is_public", 0)))
                        imported_dungeons += 1
                    else:
                        skipped_dungeons += 1
            
            if export_type in ["records", "all"] and "records" in data:
                for record in data["records"]:
                    result = self.db.execute_query(
                        "SELECT id FROM dungeons WHERE name = ?", 
                        (record["dungeon_name"],)
                    )
                    if not result:
                        skipped_records += 1
                        continue
                    dungeon_id = result[0][0]
                    existing_record = self.db.execute_query('''
                        SELECT id FROM records 
                        WHERE dungeon_id = ? AND time = ? AND worker = ?
                    ''', (dungeon_id, record["time"], record["worker"]))
                    if not existing_record:
                        self.db.execute_update('''
                            INSERT INTO records (
                                dungeon_id, trash_gold, iron_gold, other_gold, special_auctions, total_gold,
                                black_owner, worker, time, team_type, lie_down_count, fine_gold, subsidy_gold,
                                personal_gold, note,
                                scattered_consumption, iron_consumption, special_consumption, other_consumption, total_consumption
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            dungeon_id,
                            record["trash_gold"],
                            record["iron_gold"],
                            record["other_gold"],
                            json.dumps(record["special_auctions"], ensure_ascii=False),
                            record["total_gold"],
                            record["black_owner"],
                            record["worker"],
                            record["time"],
                            record["team_type"],
                            record["lie_down_count"],
                            record["fine_gold"],
                            record["subsidy_gold"],
                            record["personal_gold"],
                            record["note"],
                            record.get("scattered_consumption", 0),
                            record.get("iron_consumption", 0),
                            record.get("special_consumption", 0),
                            record.get("other_consumption", 0),
                            record.get("total_consumption", 0)
                        ))
                        imported_records += 1
                    else:
                        skipped_records += 1
            
            result_message = f"导入完成！\n\n"
            if export_type in ["presets", "all"]:
                result_message += f"副本预设: 新增 {imported_dungeons} 个，跳过 {skipped_dungeons} 个（已存在）\n"
            if export_type in ["records", "all"]:
                result_message += f"副本记录: 新增 {imported_records} 条，跳过 {skipped_records} 条（已存在或副本不存在）"
            
            messagebox.showinfo("导入结果", result_message)
            self.load_recent_records(50)
            self.load_dungeon_presets()
            self.load_dungeon_options()
            self.load_black_owner_options()
            self.load_worker_options()
            self.update_stats()
            self.update_worker_stats()
            self.update_chart()
        except Exception as e:
            messagebox.showerror("错误", f"导入数据失败: {str(e)}")

    def repair_database(self):
        try:
            self.db.execute_update("VACUUM")
            self.db.execute_update("REINDEX")
            messagebox.showinfo("成功", "数据库修复完成")
        except Exception as e:
            messagebox.showerror("错误", f"数据库修复失败: {str(e)}")

    def format_currency(self, amount):
        try:
            amount = int(amount)
            if amount == 0:
                return "0金"
            units = [
                (100000000, "亿金"),
                (10000, "万金"),
                (1, "金")
            ]
            for divisor, unit in units:
                if amount >= divisor:
                    value = amount / divisor
                    if value == int(value):
                        return f"{int(value)}{unit}"
                    else:
                        return f"{value:.2f}{unit}"
            return f"{amount}金"
        except (ValueError, TypeError):
            return "0金"

    def update_stats(self):
        try:
            total_records = self.db.execute_query("SELECT COUNT(*) FROM records")[0][0]
            self.total_records_var.set(f"{total_records:,}")
            team_total_result = self.db.execute_query("SELECT SUM(total_gold) FROM records")
            team_total = team_total_result[0][0] or 0
            self.team_total_gold_var.set(self.format_currency(team_total))
            team_max_result = self.db.execute_query("SELECT MAX(total_gold) FROM records")
            team_max = team_max_result[0][0] or 0
            self.team_max_gold_var.set(self.format_currency(team_max))
            personal_total = self.db.execute_query("SELECT SUM(personal_gold) FROM records")[0][0] or 0
            self.personal_total_gold_var.set(self.format_currency(personal_total))
            personal_max = self.db.execute_query("SELECT MAX(personal_gold) FROM records")[0][0] or 0
            self.personal_max_gold_var.set(self.format_currency(personal_max))
            consumption_total = self.db.execute_query("SELECT SUM(total_consumption) FROM records")[0][0] or 0
            self.personal_total_consumption_var.set(self.format_currency(consumption_total))
            consumption_max = self.db.execute_query("SELECT MAX(total_consumption) FROM records")[0][0] or 0
            self.personal_max_consumption_var.set(self.format_currency(consumption_max))
            net_total = personal_total - consumption_total
            self.personal_total_income_var.set(self.format_currency(net_total))
            max_net_result = self.db.execute_query('''
                SELECT MAX(personal_gold - total_consumption) 
                FROM records 
                WHERE personal_gold - total_consumption IS NOT NULL
            ''')
            max_net = max_net_result[0][0] or 0
            self.personal_max_income_var.set(self.format_currency(max_net))
        except Exception as e:
            self.total_records_var.set("0")
            self.team_total_gold_var.set("0金")
            self.team_max_gold_var.set("0金")
            self.personal_total_gold_var.set("0金")
            self.personal_max_gold_var.set("0金")
            self.personal_total_consumption_var.set("0金")
            self.personal_max_consumption_var.set("0金")
            self.personal_total_income_var.set("0金")
            self.personal_max_income_var.set("0金")

    def build_worker_stats(self, parent):
        stats_frame = ttk.LabelFrame(parent, text="打工仔统计", padding=(int(8*SCALE_FACTOR), int(6*SCALE_FACTOR)))
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=(int(10*SCALE_FACTOR), 0))
        columns = ("worker", "team_type", "count", "total_income", "avg_income", "max_income", 
                "total_consumption", "avg_consumption", "max_consumption", "net_income")
        self.worker_stats_tree = ttk.Treeview(stats_frame, columns=columns, show="headings", height=int(8*SCALE_FACTOR))
        vsb = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.worker_stats_tree.yview)
        hsb = ttk.Scrollbar(stats_frame, orient=tk.HORIZONTAL, command=self.worker_stats_tree.xview)
        self.worker_stats_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.worker_stats_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(0, weight=1)
        column_config = [
            ("worker", "打工仔", int(100*SCALE_FACTOR)),
            ("team_type", "团队类型", int(80*SCALE_FACTOR)),
            ("count", "记录数", int(80*SCALE_FACTOR)),
            ("total_income", "总收入", int(100*SCALE_FACTOR)),
            ("avg_income", "平均收入", int(100*SCALE_FACTOR)),
            ("max_income", "最高收入", int(100*SCALE_FACTOR)),
            ("total_consumption", "总消费", int(100*SCALE_FACTOR)),
            ("avg_consumption", "平均消费", int(100*SCALE_FACTOR)),
            ("max_consumption", "最高消费", int(100*SCALE_FACTOR)),
            ("net_income", "净收入", int(100*SCALE_FACTOR))
        ]
        for col_id, heading, width in column_config:
            self.worker_stats_tree.heading(col_id, text=heading, anchor="center")
            self.worker_stats_tree.column(col_id, width=width, anchor=tk.CENTER)
        self.setup_column_resizing(self.worker_stats_tree)
        self.update_worker_stats()
        self.worker_stats_tree.bind('<<TreeviewSelect>>', self.on_worker_stats_select)

    def update_worker_stats(self):
        for item in self.worker_stats_tree.get_children():
            self.worker_stats_tree.delete(item)
        try:
            stats = self.db.execute_query('''
                SELECT 
                    worker,
                    COUNT(*) as count,
                    COALESCE(SUM(personal_gold), 0) as total_income,
                    COALESCE(AVG(personal_gold), 0) as avg_income,
                    COALESCE(MAX(personal_gold), 0) as max_income,
                    COALESCE(SUM(total_consumption), 0) as total_consumption,
                    COALESCE(AVG(total_consumption), 0) as avg_consumption,
                    COALESCE(MAX(total_consumption), 0) as max_consumption,
                    COALESCE(SUM(personal_gold), 0) - COALESCE(SUM(total_consumption), 0) as net_income
                FROM records 
                WHERE worker IS NOT NULL AND worker != ''
                GROUP BY worker
                ORDER BY worker
            ''')
            for row in stats:
                worker = row[0] or "未知"
                count = int(row[1] or 0)
                total_income = int(row[2] or 0)
                avg_income = float(row[3] or 0)
                max_income = int(row[4] or 0)
                total_consumption = int(row[5] or 0)
                avg_consumption = float(row[6] or 0)
                max_consumption = int(row[7] or 0)
                net_income = int(row[8] or 0)
                tags = ("total_row",)
                self.worker_stats_tree.insert("", "end", values=(
                    worker,
                    "总计",
                    f"{count:,}",
                    self.format_currency(total_income),
                    self.format_currency(int(avg_income)),
                    self.format_currency(max_income),
                    self.format_currency(total_consumption),
                    self.format_currency(int(avg_consumption)),
                    self.format_currency(max_consumption),
                    self.format_currency(net_income)
                ), tags=tags)
            self.worker_stats_tree.tag_configure('total_row', background='#e6f3ff', font=('PingFang SC', int(9*SCALE_FACTOR), 'bold'))
        except Exception as e:
            pass

    def on_worker_stats_select(self, event):
        selected = self.worker_stats_tree.selection()
        if selected:
            item = selected[0]
            values = self.worker_stats_tree.item(item, 'values')
            if values:
                worker_name = values[0]
                team_type = values[1]
                if team_type == "总计":
                    self.remove_detail_rows()
                    self.insert_detail_rows(worker_name, item)
                    self.selected_worker = worker_name
                    self.selected_team_type = None
                    self.update_chart_for_worker(worker_name)
                else:
                    self.selected_worker = worker_name
                    self.selected_team_type = team_type
                    self.update_chart_for_worker(worker_name, team_type)
        else:
            self.remove_detail_rows()
            self.selected_worker = None
            self.selected_team_type = None
            self.update_chart()

    def remove_detail_rows(self):
        items_to_remove = []
        for item in self.worker_stats_tree.get_children():
            values = self.worker_stats_tree.item(item, 'values')
            if values and values[1] != "总计":
                items_to_remove.append(item)
        for item in items_to_remove:
            self.worker_stats_tree.delete(item)

    def insert_detail_rows(self, worker_name, parent_item):
        try:
            detail_stats = self.db.execute_query('''
                SELECT 
                    team_type,
                    COUNT(*) as count,
                    COALESCE(SUM(personal_gold), 0) as total_income,
                    COALESCE(AVG(personal_gold), 0) as avg_income,
                    COALESCE(MAX(personal_gold), 0) as max_income,
                    COALESCE(SUM(total_consumption), 0) as total_consumption,
                    COALESCE(AVG(total_consumption), 0) as avg_consumption,
                    COALESCE(MAX(total_consumption), 0) as max_consumption,
                    COALESCE(SUM(personal_gold), 0) - COALESCE(SUM(total_consumption), 0) as net_income
                FROM records 
                WHERE worker = ? AND worker IS NOT NULL AND worker != ''
                GROUP BY team_type
                ORDER BY team_type DESC
            ''', (worker_name,))
            parent_index = self.worker_stats_tree.index(parent_item)
            for i, row in enumerate(detail_stats):
                team_type = row[0] or "未知"
                count = int(row[1] or 0)
                total_income = int(row[2] or 0)
                avg_income = float(row[3] or 0)
                max_income = int(row[4] or 0)
                total_consumption = int(row[5] or 0)
                avg_consumption = float(row[6] or 0)
                max_consumption = int(row[7] or 0)
                net_income = int(row[8] or 0)
                insert_index = parent_index + 1 + i
                self.worker_stats_tree.insert("", insert_index, values=(
                    worker_name,
                    team_type,
                    f"{count:,}",
                    self.format_currency(total_income),
                    self.format_currency(int(avg_income)),
                    self.format_currency(max_income),
                    self.format_currency(total_consumption),
                    self.format_currency(int(avg_consumption)),
                    self.format_currency(max_consumption),
                    self.format_currency(net_income)
                ), tags=("detail_row",))
            self.worker_stats_tree.tag_configure('detail_row', background='#f9f9f9')
        except Exception as e:
            pass

    def update_chart_for_worker(self, worker_name, team_type=None):
        if not MATPLOTLIB_AVAILABLE:
            return
        try:
            if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                try:
                    self.overview_text_obj.remove()
                except:
                    pass
                self.overview_text_obj = None
            if hasattr(self, '_hover_connection'):
                try:
                    self.fig.canvas.mpl_disconnect(self._hover_connection)
                except:
                    pass
            if hasattr(self, '_leave_connection'):
                try:
                    self.fig.canvas.mpl_disconnect(self._leave_connection)
                except:
                    pass
            self.ax.clear()
            self.fig.patch.set_facecolor('#0f0f23')
            self.ax.set_facecolor('#0f0f23')
            today = dt.date.today()
            weeks_data = []
            week_labels = []
            query_conditions = "worker = ?"
            query_params = [worker_name]
            if team_type:
                query_conditions += " AND team_type = ?"
                query_params.append(team_type)
            for i in range(30):
                current_week_monday = today - timedelta(days=today.weekday())
                target_week_monday = current_week_monday - timedelta(weeks=(29-i))
                start_date = target_week_monday
                query = f'''
                    SELECT 
                        COALESCE(SUM(total_gold), 0) as weekly_team_total,
                        COALESCE(SUM(personal_gold), 0) as weekly_personal_total,
                        COALESCE(SUM(total_consumption), 0) as weekly_consumption
                    FROM records 
                    WHERE date(time) BETWEEN ? AND ? AND {query_conditions}
                '''
                week_params = [start_date.strftime('%Y-%m-%d'), (start_date + timedelta(days=6)).strftime('%Y-%m-%d')] + query_params
                week_records = self.db.execute_query(query, week_params)
                if week_records:
                    team_total = week_records[0][0] or 0
                    personal_total = week_records[0][1] or 0
                    consumption = week_records[0][2] or 0
                else:
                    team_total = 0
                    personal_total = 0
                    consumption = 0
                weeks_data.append({
                    'team_total': team_total,
                    'personal_total': personal_total,
                    'consumption': consumption
                })
                if i % 4 == 0 or i == 29:
                    week_label = f"{start_date.month:02d}/{start_date.day:02d}"
                else:
                    week_label = ""
                week_labels.append(week_label)
            team_totals = [data['team_total'] for data in weeks_data]
            personal_totals = [data['personal_total'] for data in weeks_data]
            consumptions = [data['consumption'] for data in weeks_data]
            total_team = sum(team_totals)
            total_personal = sum(personal_totals)
            total_consumption = sum(consumptions)
            avg_team = total_team / 30 if total_team > 0 else 0
            avg_personal = total_personal / 30 if total_personal > 0 else 0
            avg_consumption = total_consumption / 30 if total_consumption > 0 else 0
            if team_type:
                chart_title = f'最近30周收入趋势 - {worker_name} ({team_type})'
            else:
                chart_title = f'最近30周收入趋势 - {worker_name}'
            if sum(team_totals) == 0 and sum(personal_totals) == 0 and sum(consumptions) == 0:
                self.ax.text(0.5, 0.5, f'打工仔 {worker_name} 最近30周暂无数据', 
                            ha='center', va='center', 
                            transform=self.ax.transAxes, fontsize=12, color='white')
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.ax.set_frame_on(False)
                self.ax.set_title(chart_title, color='white', fontsize=13, fontweight='bold', pad=20)
                self.canvas.draw()
                return
            x = np.arange(len(week_labels))
            colors = ['#ff4d4d', '#4dff4d', '#4d4dff']
            line1 = self.ax.plot(x, team_totals, linewidth=3, color=colors[0], alpha=0.9, 
                                label='团队收入', marker='o', markersize=4, 
                                markerfacecolor='white', markeredgecolor=colors[0])[0]
            line2 = self.ax.plot(x, personal_totals, linewidth=3, color=colors[1], alpha=0.9, 
                                label='个人收入', marker='s', markersize=4, 
                                markerfacecolor='white', markeredgecolor=colors[1])[0]
            line3 = self.ax.plot(x, consumptions, linewidth=3, color=colors[2], alpha=0.9, 
                                label='个人消费', marker='^', markersize=4, 
                                markerfacecolor='white', markeredgecolor=colors[2])[0]
            self.ax.fill_between(x, team_totals, alpha=0.2, color=colors[0])
            self.ax.fill_between(x, personal_totals, alpha=0.2, color=colors[1])
            self.ax.fill_between(x, consumptions, alpha=0.2, color=colors[2])
            self.ax.spines['bottom'].set_color('#00ffcc')
            self.ax.spines['top'].set_color('#00ffcc') 
            self.ax.spines['right'].set_color('#00ffcc')
            self.ax.spines['left'].set_color('#00ffcc')
            self.ax.tick_params(axis='x', colors='white', labelsize=8)
            self.ax.tick_params(axis='y', colors='white', labelsize=8)
            self.ax.set_xlabel('周期 (周)', fontsize=10, color='white', fontweight='bold')
            self.ax.set_ylabel('金额 (金)', fontsize=10, color='white', fontweight='bold')
            self.ax.set_title(chart_title, fontsize=13, color='white', fontweight='bold', pad=20)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(week_labels)
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
            self.ax.grid(True, alpha=0.2, color='white')
            all_values = team_totals + personal_totals + consumptions
            if all_values:
                min_value = min(all_values)
                max_value = max(all_values)
                value_range = max_value - min_value
                if value_range == 0:
                    if max_value == 0:
                        y_min, y_max = -1, 1
                    else:
                        y_min = min_value - abs(min_value) * 0.2
                        y_max = max_value + abs(max_value) * 0.2
                else:
                    margin = value_range * 0.2
                    y_min = min_value - margin
                    y_max = max_value + margin
            else:
                y_min, y_max = -1, 1
            self.ax.set_ylim(y_min, y_max)
            if y_min <= 0 <= y_max:
                self.ax.axhline(y=0, color='white', linestyle='--', alpha=0.5, linewidth=1)
            from matplotlib.patches import FancyBboxPatch
            rect = FancyBboxPatch((0, 0), 1, 1, 
                                boxstyle="round,pad=0.02", 
                                linewidth=2, 
                                edgecolor='#00ffcc', 
                                facecolor='none',
                                alpha=0.7,
                                transform=self.ax.transAxes)
            self.ax.add_patch(rect)
            self.fig.tight_layout()
            plt.subplots_adjust(bottom=0.2, top=0.85, left=0.1, right=0.9)
            self.current_annotation = None
            self.current_period = None
            if team_type:
                overview_text = f"{worker_name} ({team_type}) - 30周总览: 团队{self.format_currency(total_team)} | 个人{self.format_currency(total_personal)} | 消费{self.format_currency(total_consumption)} | 平均: 团队{self.format_currency(avg_team)}/周 | 个人{self.format_currency(avg_personal)}/周 | 消费{self.format_currency(avg_consumption)}/周"
            else:
                overview_text = f"{worker_name} - 30周总览: 团队{self.format_currency(total_team)} | 个人{self.format_currency(total_personal)} | 消费{self.format_currency(total_consumption)} | 平均: 团队{self.format_currency(avg_team)}/周 | 个人{self.format_currency(avg_personal)}/周 | 消费{self.format_currency(avg_consumption)}/周"
            self.overview_text_obj = self.fig.text(
                0.1, 0.05,
                overview_text,
                bbox=dict(
                    facecolor='#1a1a2e', 
                    edgecolor='#00ffcc',
                    linewidth=1.5,
                    boxstyle='round,pad=0.5',
                    alpha=0.9
                ),
                fontsize=10,
                color='white',
                ha='left',
                va='bottom',
                transform=self.fig.transFigure
            )
            legend = self.ax.legend(
                loc='upper right',
                bbox_to_anchor=(0.98, 1.0),
                ncol=3,
                frameon=True,
                facecolor='#0f0f23', 
                edgecolor='#00ffcc',
                fontsize=10,
                labelcolor='white'
            )
            legend.get_frame().set_alpha(0.8)
            def on_hover(event):
                if event.inaxes != self.ax:
                    if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                        self.overview_text_obj.set_text(overview_text)
                        self.canvas.draw_idle()
                    return
                x_data = event.xdata
                y_data = event.ydata
                if x_data is None or y_data is None:
                    if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                        self.overview_text_obj.set_text(overview_text)
                        self.canvas.draw_idle()
                    return
                closest_period = int(round(x_data))
                if closest_period < 0 or closest_period >= len(week_labels):
                    if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                        self.overview_text_obj.set_text(overview_text)
                        self.canvas.draw_idle()
                    return
                week_label = week_labels[closest_period] if week_labels[closest_period] else f"第{closest_period+1}周"
                team_total = team_totals[closest_period]
                personal_total = personal_totals[closest_period]
                consumption = consumptions[closest_period]
                if team_type:
                    detail_text = f"{worker_name} ({team_type}) - 第{closest_period+1}周({week_label}): 团队{self.format_currency(team_total)} | 个人{self.format_currency(personal_total)} | 消费{self.format_currency(consumption)}"
                else:
                    detail_text = f"{worker_name} - 第{closest_period+1}周({week_label}): 团队{self.format_currency(team_total)} | 个人{self.format_currency(personal_total)} | 消费{self.format_currency(consumption)}"
                if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                    self.overview_text_obj.set_text(detail_text)
                    self.canvas.draw_idle()
            def on_leave(event):
                if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                    self.overview_text_obj.set_text(overview_text)
                    self.canvas.draw_idle()
            self._hover_connection = self.fig.canvas.mpl_connect('motion_notify_event', on_hover)
            self._leave_connection = self.fig.canvas.mpl_connect('axes_leave_event', on_leave)
            self.canvas.draw()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.ax.clear()
            self.ax.text(0.5, 0.5, '图表加载失败\n请检查数据完整性', 
                        ha='center', va='center', 
                        transform=self.ax.transAxes, fontsize=12, color='white')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_frame_on(False)
            if team_type:
                chart_title = f'最近30周收入趋势 - {worker_name} ({team_type})'
            else:
                chart_title = f'最近30周收入趋势 - {worker_name}'
            self.ax.set_title(chart_title, color='white')
            self.canvas.draw()

    def prepare_chart_data(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        try:
            self.weekly_data = {}
            self.worker_weekly_data = {}
        except Exception as e:
            self.weekly_data = {}
            self.worker_weekly_data = {}

    def update_chart(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        try:
            if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                try:
                    self.overview_text_obj.remove()
                except:
                    pass
                self.overview_text_obj = None
            total_records = self.db.execute_query("SELECT COUNT(*) FROM records")[0][0]
            if total_records == 0:
                if hasattr(self, 'ax') and self.ax:
                    self.ax.clear()
                    self.ax.text(0.5, 0.5, '暂无数据\n请先添加副本记录', 
                                ha='center', va='center', 
                                transform=self.ax.transAxes, fontsize=12, color='gray')
                    self.ax.set_xticks([])
                    self.ax.set_yticks([])
                    self.ax.set_frame_on(False)
                    self.ax.set_title('')
                    if hasattr(self, 'canvas') and self.canvas:
                        self.canvas.draw()
                return
            if hasattr(self, 'selected_worker') and self.selected_worker:
                self.update_chart_for_worker(self.selected_worker)
            else:
                self.plot_all_workers_chart()
        except Exception as e:
            if hasattr(self, 'ax') and self.ax:
                self.ax.clear()
                self.ax.text(0.5, 0.5, '图表更新失败', 
                            ha='center', va='center', 
                            transform=self.ax.transAxes, fontsize=12, color='gray')
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.ax.set_frame_on(False)
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.draw()

    def plot_all_workers_chart(self):
        if not MATPLOTLIB_AVAILABLE:
            return
        try:
            if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                try:
                    self.overview_text_obj.remove()
                except:
                    pass
                self.overview_text_obj = None
            if hasattr(self, '_hover_connection'):
                try:
                    self.fig.canvas.mpl_disconnect(self._hover_connection)
                except:
                    pass
            if hasattr(self, '_leave_connection'):
                try:
                    self.fig.canvas.mpl_disconnect(self._leave_connection)
                except:
                    pass
            self.ax.clear()
            self.fig.patch.set_facecolor('#0f0f23')
            self.ax.set_facecolor('#0f0f23')
            today = dt.date.today()
            weeks_data = []
            week_labels = []
            for i in range(30):
                current_week_monday = today - timedelta(days=today.weekday())
                target_week_monday = current_week_monday - timedelta(weeks=(29-i))
                start_date = target_week_monday
                week_records = self.db.execute_query('''
                    SELECT 
                        COALESCE(SUM(total_gold), 0) as weekly_team_total,
                        COALESCE(SUM(personal_gold), 0) as weekly_personal_total,
                        COALESCE(SUM(total_consumption), 0) as weekly_consumption
                    FROM records 
                    WHERE date(time) BETWEEN ? AND ?
                ''', (start_date.strftime('%Y-%m-%d'), (start_date + timedelta(days=6)).strftime('%Y-%m-%d')))
                if week_records:
                    team_total = week_records[0][0] or 0
                    personal_total = week_records[0][1] or 0
                    consumption = week_records[0][2] or 0
                else:
                    team_total = 0
                    personal_total = 0
                    consumption = 0
                weeks_data.append({
                    'team_total': team_total,
                    'personal_total': personal_total,
                    'consumption': consumption
                })
                if i % 4 == 0 or i == 29:
                    week_label = f"{start_date.month:02d}/{start_date.day:02d}"
                else:
                    week_label = ""
                week_labels.append(week_label)
            team_totals = [data['team_total'] for data in weeks_data]
            personal_totals = [data['personal_total'] for data in weeks_data]
            consumptions = [data['consumption'] for data in weeks_data]
            total_team = sum(team_totals)
            total_personal = sum(personal_totals)
            total_consumption = sum(consumptions)
            avg_team = total_team / 30 if total_team > 0 else 0
            avg_personal = total_personal / 30 if total_personal > 0 else 0
            avg_consumption = total_consumption / 30 if total_consumption > 0 else 0
            if sum(team_totals) == 0 and sum(personal_totals) == 0 and sum(consumptions) == 0:
                self.ax.text(0.5, 0.5, '最近30周暂无数据\n请先添加副本记录', 
                            ha='center', va='center', 
                            transform=self.ax.transAxes, fontsize=12, color='white')
                self.ax.set_xticks([])
                self.ax.set_yticks([])
                self.ax.set_frame_on(False)
                self.ax.set_title('最近30周收入趋势 - 总览', color='white', fontsize=13, fontweight='bold', pad=20)
                self.canvas.draw()
                return
            x = np.arange(len(week_labels))
            colors = ['#ff4d4d', '#4dff4d', '#4d4dff']
            line1 = self.ax.plot(x, team_totals, linewidth=3, color=colors[0], alpha=0.9, 
                                label='团队收入', marker='o', markersize=4, 
                                markerfacecolor='white', markeredgecolor=colors[0])[0]
            line2 = self.ax.plot(x, personal_totals, linewidth=3, color=colors[1], alpha=0.9, 
                                label='个人收入', marker='s', markersize=4, 
                                markerfacecolor='white', markeredgecolor=colors[1])[0]
            line3 = self.ax.plot(x, consumptions, linewidth=3, color=colors[2], alpha=0.9, 
                                label='个人消费', marker='^', markersize=4, 
                                markerfacecolor='white', markeredgecolor=colors[2])[0]
            self.ax.fill_between(x, team_totals, alpha=0.2, color=colors[0])
            self.ax.fill_between(x, personal_totals, alpha=0.2, color=colors[1])
            self.ax.fill_between(x, consumptions, alpha=0.2, color=colors[2])
            self.ax.spines['bottom'].set_color('#00ffcc')
            self.ax.spines['top'].set_color('#00ffcc') 
            self.ax.spines['right'].set_color('#00ffcc')
            self.ax.spines['left'].set_color('#00ffcc')
            self.ax.tick_params(axis='x', colors='white', labelsize=8)
            self.ax.tick_params(axis='y', colors='white', labelsize=8)
            self.ax.set_xlabel('周期 (周)', fontsize=10, color='white', fontweight='bold')
            self.ax.set_ylabel('金额 (金)', fontsize=10, color='white', fontweight='bold')
            self.ax.set_title('最近30周收入趋势 - 总览', fontsize=13, color='white', fontweight='bold', pad=20)
            self.ax.set_xticks(x)
            self.ax.set_xticklabels(week_labels)
            self.ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'))
            self.ax.grid(True, alpha=0.2, color='white')
            all_values = team_totals + personal_totals + consumptions
            if all_values:
                min_value = min(all_values)
                max_value = max(all_values)
                value_range = max_value - min_value
                if value_range == 0:
                    if max_value == 0:
                        y_min, y_max = -1, 1
                    else:
                        y_min = min_value - abs(min_value) * 0.2
                        y_max = max_value + abs(max_value) * 0.2
                else:
                    margin = value_range * 0.2
                    y_min = min_value - margin
                    y_max = max_value + margin
            else:
                y_min, y_max = -1, 1
            self.ax.set_ylim(y_min, y_max)
            if y_min <= 0 <= y_max:
                self.ax.axhline(y=0, color='white', linestyle='--', alpha=0.5, linewidth=1)
            from matplotlib.patches import FancyBboxPatch
            rect = FancyBboxPatch((0, 0), 1, 1, 
                                boxstyle="round,pad=0.02", 
                                linewidth=2, 
                                edgecolor='#00ffcc', 
                                facecolor='none',
                                alpha=0.7,
                                transform=self.ax.transAxes)
            self.ax.add_patch(rect)
            self.fig.tight_layout()
            plt.subplots_adjust(bottom=0.2, top=0.85, left=0.1, right=0.9)
            self.current_annotation = None
            self.current_period = None
            overview_text = f"30周总览: 团队{self.format_currency(total_team)} | 个人{self.format_currency(total_personal)} | 消费{self.format_currency(total_consumption)} | 平均: 团队{self.format_currency(avg_team)}/周 | 个人{self.format_currency(avg_personal)}/周 | 消费{self.format_currency(avg_consumption)}/周"
            self.overview_text_obj = self.fig.text(
                0.1, 0.05,
                overview_text,
                bbox=dict(
                    facecolor='#1a1a2e', 
                    edgecolor='#00ffcc',
                    linewidth=1.5,
                    boxstyle='round,pad=0.5',
                    alpha=0.9
                ),
                fontsize=10,
                color='white',
                ha='left',
                va='bottom',
                transform=self.fig.transFigure
            )
            legend = self.ax.legend(
                loc='upper right',
                bbox_to_anchor=(0.98, 1.0),
                ncol=3,
                frameon=True,
                facecolor='#0f0f23', 
                edgecolor='#00ffcc',
                fontsize=10,
                labelcolor='white'
            )
            legend.get_frame().set_alpha(0.8)
            def on_hover(event):
                if event.inaxes != self.ax:
                    if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                        self.overview_text_obj.set_text(overview_text)
                        self.canvas.draw_idle()
                    return
                x_data = event.xdata
                y_data = event.ydata
                if x_data is None or y_data is None:
                    if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                        self.overview_text_obj.set_text(overview_text)
                        self.canvas.draw_idle()
                    return
                closest_period = int(round(x_data))
                if closest_period < 0 or closest_period >= len(week_labels):
                    if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                        self.overview_text_obj.set_text(overview_text)
                        self.canvas.draw_idle()
                    return
                week_label = week_labels[closest_period] if week_labels[closest_period] else f"第{closest_period+1}周"
                team_total = team_totals[closest_period]
                personal_total = personal_totals[closest_period]
                consumption = consumptions[closest_period]
                net_income = personal_total - consumption
                detail_text = f"第{closest_period+1}周({week_label}): 团队{self.format_currency(team_total)} | 个人{self.format_currency(personal_total)} | 消费{self.format_currency(consumption)} | 净收入{self.format_currency(net_income)}"
                if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                    self.overview_text_obj.set_text(detail_text)
                    self.canvas.draw_idle()
            def on_leave(event):
                if hasattr(self, 'overview_text_obj') and self.overview_text_obj:
                    self.overview_text_obj.set_text(overview_text)
                    self.canvas.draw_idle()
            self._hover_connection = self.fig.canvas.mpl_connect('motion_notify_event', on_hover)
            self._leave_connection = self.fig.canvas.mpl_connect('axes_leave_event', on_leave)
            self.canvas.draw()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.ax.clear()
            self.ax.text(0.5, 0.5, '图表加载失败\n请检查数据完整性', 
                        ha='center', va='center', 
                        transform=self.ax.transAxes, fontsize=12, color='white')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_frame_on(False)
            self.ax.set_title('最近30周收入趋势 - 总览', color='white')
            self.canvas.draw()

    def load_weekly_data(self):
        for item in self.weekly_tree.get_children():
            self.weekly_tree.delete(item)
        weekly_manager = WeeklyRecordManager(self.db)
        self.weekly_period_var.set(weekly_manager.get_weekly_period_text())
        records = weekly_manager.get_weekly_records(self.weekly_worker_var.get() if self.weekly_worker_var.get() else None)
        for record in records:
            self.weekly_tree.insert("", "end", values=(
                record['time'],
                record['worker'],
                record['team_type'],
                record['dungeon'],
                record['note']
            ))

    def on_weekly_worker_select(self, event=None):
        self.load_weekly_data()

    def batch_add_items(self):
        items_text = self.batch_items_var.get().strip()
        if not items_text:
            messagebox.showwarning("警告", "请输入要添加的物品")
            return
        
        cleaned_text = items_text.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
        
        items = []
        if ',' in cleaned_text:
            items = [item.strip() for item in cleaned_text.split(',') if item.strip()]
        else:
            items = [cleaned_text]
        
        current_drops = self.preset_drops_var.get()
        if current_drops:
            new_items = current_drops.split(',')
            new_items.extend(items)
            unique_items = []
            seen = set()
            for item in new_items:
                item = item.strip()
                if item and item not in seen:
                    seen.add(item)
                    unique_items.append(item)
            self.preset_drops_var.set(','.join(unique_items))
        else:
            self.preset_drops_var.set(','.join(items))
        
        self.batch_items_var.set("")
        messagebox.showinfo("成功", f"已添加 {len(items)} 个物品")

    def edit_dungeon(self):
        selected = self.dungeon_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要编辑的副本")
            return
        item = selected[0]
        values = self.dungeon_tree.item(item, 'values')
        self.preset_name_var.set(values[0])
        self.preset_drops_var.set(values[1])
        self.current_edit_dungeon_name = values[0]
        self.preset_update_btn.configure(state=tk.NORMAL)

    def update_dungeon(self):
        if not hasattr(self, 'current_edit_dungeon_name'):
            messagebox.showwarning("警告", "没有正在编辑的副本")
            return
        name = self.preset_name_var.get().strip()
        drops = self.preset_drops_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "副本名称不能为空")
            return
        try:
            if name != self.current_edit_dungeon_name:
                existing = self.db.execute_query("SELECT name FROM dungeons WHERE name = ?", (name,))
                if existing:
                    messagebox.showwarning("警告", f"副本 '{name}' 已存在，无法重命名为此名称")
                    return
            
            self.db.execute_update('''
                UPDATE dungeons SET name = ?, special_drops = ?
                WHERE name = ?
            ''', (name, drops, self.current_edit_dungeon_name))
            messagebox.showinfo("成功", "副本更新成功")
            self.clear_preset_form()
            self.load_dungeon_presets()
            self.load_dungeon_options()
        except Exception as e:
            messagebox.showerror("错误", f"更新副本失败: {str(e)}")

    def delete_dungeon(self):
        selected = self.dungeon_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的副本")
            return
        item = selected[0]
        values = self.dungeon_tree.item(item, 'values')
        dungeon_name = values[0]
        
        result = self.db.execute_query('''
            SELECT COUNT(*) FROM records r
            JOIN dungeons d ON r.dungeon_id = d.id
            WHERE d.name = ?
        ''', (dungeon_name,))
        
        if result and result[0][0] > 0:
            if messagebox.askyesno("确认删除", 
                    f"副本 '{dungeon_name}' 有 {result[0][0]} 条相关记录，删除副本会同时删除这些记录。\n确定要删除吗？"):
                self.db.execute_update("DELETE FROM records WHERE dungeon_id = (SELECT id FROM dungeons WHERE name = ?)", (dungeon_name,))
                self.db.execute_update("DELETE FROM dungeons WHERE name = ?", (dungeon_name,))
                messagebox.showinfo("成功", "副本及相关记录已删除")
                self.load_dungeon_presets()
                self.load_dungeon_options()
                self.load_recent_records(50)
                self.update_stats()
                self.update_worker_stats()
                self.update_chart()
        else:
            if messagebox.askyesno("确认删除", f"确定要删除副本 '{dungeon_name}' 吗？"):
                self.db.execute_update("DELETE FROM dungeons WHERE name = ?", (dungeon_name,))
                messagebox.showinfo("成功", "副本已删除")
                self.load_dungeon_presets()
                self.load_dungeon_options()

    def clear_preset_form(self):
        self.preset_name_var.set("")
        self.preset_drops_var.set("")
        self.batch_items_var.set("")
        self.preset_update_btn.configure(state=tk.DISABLED)
        if hasattr(self, 'current_edit_dungeon_name'):
            del self.current_edit_dungeon_name

    def on_close(self):
        self.is_closing = True
        
        for after_id in self.after_ids:
            try:
                self.root.after_cancel(after_id)
            except (ValueError, tk.TclError):
                pass
        self.after_ids.clear()
        
        if self._save_scheduled:
            try:
                self.root.after_cancel(self._save_scheduled)
            except (ValueError, tk.TclError):
                pass
            self._save_scheduled = None
            
        if self._pane_save_scheduled:
            try:
                self.root.after_cancel(self._pane_save_scheduled)
            except (ValueError, tk.TclError):
                pass
            self._pane_save_scheduled = None
        
        try:
            self.save_column_widths()
            self.save_window_state_to_db()
            self.save_pane_positions()
        except Exception:
            pass
        
        if MATPLOTLIB_AVAILABLE:
            try:
                if hasattr(self, 'fig') and self.fig:
                    plt.close(self.fig)
                if hasattr(self, 'canvas') and self.canvas:
                    self.canvas.get_tk_widget().destroy()
            except Exception:
                pass
        
        for child in self.root.winfo_children():
            try:
                child.destroy()
            except Exception:
                pass
        
        if hasattr(self, 'db') and self.db:
            try:
                self.db.close()
            except Exception:
                pass
        
        try:
            self.root.quit()
        except Exception:
            pass
            
        import os
        import signal
        os.kill(os.getpid(), signal.SIGTERM)

def main():
    root = tk.Tk()
    app = JX3DungeonTracker(root)
    root.mainloop()

if __name__ == "__main__":
    main()