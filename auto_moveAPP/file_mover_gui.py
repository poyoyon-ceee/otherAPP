#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダウンロードフォルダ自動振り分けアプリ（GUI版）
設定画面とスタートアップ設定機能付き
"""

import os
import json
import time
import shutil
import logging
import hashlib
import threading
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import pystray
from PIL import Image, ImageDraw

class FileAutoMover(FileSystemEventHandler):
    """ファイル自動移動ハンドラー"""
    
    def __init__(self, config_file="config.json", log_callback=None):
        self.config_file = config_file
        self.log_callback = log_callback
        self.config = self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # デフォルト設定を作成
                default_config = {
                    "watch_folder": os.path.expanduser("~/Downloads"),
                    "rules": [
                        {
                            "name": "kaunetファイル",
                            "pattern": ".*kaunet_.*",
                            "destination": "C:/LocalApp/kaunetAPP/DATA",
                            "action": "move"
                        },
                        {
                            "name": "PDFファイル",
                            "pattern": ".*\\.pdf$",
                            "destination": "Documents/PDF",
                            "action": "move"
                        },
                        {
                            "name": "画像ファイル",
                            "pattern": ".*\\.(jpg|jpeg|png|gif|bmp|webp)$",
                            "destination": "Pictures/Downloads",
                            "action": "move"
                        },
                        {
                            "name": "動画ファイル",
                            "pattern": ".*\\.(mp4|avi|mkv|mov|wmv|flv|webm)$",
                            "destination": "Videos/Downloads",
                            "action": "move"
                        },
                        {
                            "name": "音楽ファイル",
                            "pattern": ".*\\.(mp3|wav|flac|aac|ogg|m4a)$",
                            "destination": "Music/Downloads",
                            "action": "move"
                        },
                        {
                            "name": "実行ファイル",
                            "pattern": ".*\\.(exe|msi|app)$",
                            "destination": "Programs",
                            "action": "move"
                        },
                        {
                            "name": "圧縮ファイル",
                            "pattern": ".*\\.(zip|rar|7z|tar|gz)$",
                            "destination": "Downloads/Archives",
                            "action": "move"
                        },
                        {
                            "name": "ドキュメント",
                            "pattern": ".*\\.(doc|docx|txt|rtf|xls|xlsx|ppt|pptx)$",
                            "destination": "Documents/Downloads",
                            "action": "move"
                        },
                        {
                            "name": "その他のファイル",
                            "pattern": ".*",
                            "destination": "Downloads/Others",
                            "action": "move"
                        }
                    ],
                    "log_level": "INFO",
                    "delay_seconds": 3,
                    "create_directories": True,
                    "safe_move": {
                        "enabled": True,
                        "hash_check_threshold": 104857600,
                        "verify_integrity": True
                    }
                }
                self.save_config(default_config)
                return default_config
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
            return {}
    
    def save_config(self, config):
        """設定ファイルを保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def setup_logging(self):
        """ログ設定"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('file_mover.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def on_created(self, event):
        """ファイル作成時のイベント処理"""
        if not event.is_directory:
            time.sleep(self.config.get('delay_seconds', 2))
            self.process_file(event.src_path)
    
    def on_moved(self, event):
        """ファイル移動時のイベント処理"""
        if not event.is_directory:
            time.sleep(self.config.get('delay_seconds', 2))
            self.process_file(event.dest_path)
    
    def process_file(self, file_path):
        """ファイル処理メインロジック"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.warning(f"ファイルが存在しません: {file_path}")
                return
            
            file_name = file_path.name
            self.logger.info(f"処理開始: {file_name}")
            
            # ルールに基づいて振り分け
            for rule in self.config.get('rules', []):
                if self.match_rule(file_name, rule):
                    self.execute_rule(file_path, rule)
                    break
            else:
                self.logger.info(f"マッチするルールがありません: {file_name}")
                
        except Exception as e:
            self.logger.error(f"ファイル処理エラー: {e}")
    
    def match_rule(self, file_name, rule):
        """ルールにマッチするかチェック"""
        try:
            pattern = rule.get('pattern', '')
            if pattern:
                return re.match(pattern, file_name, re.IGNORECASE) is not None
        except Exception as e:
            self.logger.error(f"ルールマッチングエラー: {e}")
        return False
    
    def execute_rule(self, file_path, rule):
        """ルール実行"""
        try:
            destination = rule.get('destination', '')
            action = rule.get('action', 'move')
            
            if not destination:
                self.logger.warning("移動先が指定されていません")
                return
            
            # 移動先パスの構築
            if os.path.isabs(destination):
                dest_path = Path(destination)
            else:
                base_path = Path.home()
                dest_path = base_path / destination
            
            dest_file_path = dest_path / file_path.name
            
            # ディレクトリ作成
            if self.config.get('create_directories', True):
                dest_path.mkdir(parents=True, exist_ok=True)
            
            # ファイル移動/コピー
            if action == 'move':
                if dest_file_path.exists():
                    dest_file_path = self.get_unique_filename(dest_file_path)
                
                # 安全な移動を実行
                if self.safe_move(file_path, dest_file_path):
                    self.logger.info(f"安全移動完了: {file_path.name} -> {dest_path}")
                    if self.log_callback:
                        self.log_callback(f"移動完了: {file_path.name}")
                else:
                    self.logger.error(f"安全移動失敗: {file_path.name}")
                    if self.log_callback:
                        self.log_callback(f"移動失敗: {file_path.name}")
                
            elif action == 'copy':
                if dest_file_path.exists():
                    dest_file_path = self.get_unique_filename(dest_file_path)
                
                shutil.copy2(str(file_path), str(dest_file_path))
                self.logger.info(f"コピー完了: {file_path.name} -> {dest_path}")
                if self.log_callback:
                    self.log_callback(f"コピー完了: {file_path.name}")
                
        except Exception as e:
            self.logger.error(f"ルール実行エラー: {e}")
    
    def safe_move(self, src_path, dst_path):
        """安全な移動（コピー→整合性確認→元ファイル削除）"""
        try:
            src_path = Path(src_path)
            dst_path = Path(dst_path)
            
            # 1. ファイルサイズを取得
            src_size = src_path.stat().st_size
            
            # 2. コピー実行
            shutil.copy2(str(src_path), str(dst_path))
            
            # 3. ファイルサイズ確認
            dst_size = dst_path.stat().st_size
            if src_size != dst_size:
                self.logger.error(f"ファイルサイズ不一致: 元={src_size}, 先={dst_size}")
                dst_path.unlink()
                return False
            
            # 4. ファイルハッシュ確認（小さいファイルのみ）
            if src_size < 100 * 1024 * 1024:  # 100MB未満の場合のみハッシュ確認
                src_hash = self.calculate_file_hash(src_path)
                dst_hash = self.calculate_file_hash(dst_path)
                
                if src_hash != dst_hash:
                    self.logger.error(f"ファイルハッシュ不一致: {src_path.name}")
                    dst_path.unlink()
                    return False
            
            # 5. 元ファイル削除
            src_path.unlink()
            return True
            
        except Exception as e:
            self.logger.error(f"安全移動エラー: {e}")
            try:
                if dst_path.exists():
                    dst_path.unlink()
            except:
                pass
            return False
    
    def calculate_file_hash(self, file_path):
        """ファイルのハッシュ値を計算"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"ハッシュ計算エラー: {e}")
            return ""
    
    def get_unique_filename(self, file_path):
        """重複しないファイル名を生成"""
        base_path = file_path.parent
        name = file_path.stem
        suffix = file_path.suffix
        counter = 1
        
        while file_path.exists():
            new_name = f"{name}_{counter}{suffix}"
            file_path = base_path / new_name
            counter += 1
        
        return file_path

class FileMoverGUI:
    """メインGUIアプリケーション"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ダウンロードフォルダ自動振り分けアプリ")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # アプリケーション状態
        self.mover = None
        self.observer = None
        self.monitoring = False
        self.tray_icon = None
        self.minimize_to_tray = True
        
        # GUI構築
        self.create_widgets()
        
        # 設定読み込み
        self.load_settings()
        
        # システムトレイアイコン作成
        self.create_tray_icon()
        
    def create_widgets(self):
        """ウィジェット作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 設定ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="設定", command=self.open_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="スタートアップ設定", command=self.open_startup_settings).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="ログ表示", command=self.open_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="トレイに最小化", command=self.minimize_to_tray_window).pack(side=tk.LEFT, padx=(0, 5))
        
        # ステータス表示
        status_frame = ttk.LabelFrame(main_frame, text="ステータス", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="停止中")
        self.status_label.pack(side=tk.LEFT)
        
        # 制御ボタン
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="監視開始", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="監視停止", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # ログ表示エリア
        log_frame = ttk.LabelFrame(main_frame, text="ログ", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
    def load_settings(self):
        """設定読み込み"""
        try:
            self.mover = FileAutoMover(log_callback=self.log_callback)
            self.log_callback("設定を読み込みました")
        except Exception as e:
            messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {e}")
    
    def start_monitoring(self):
        """監視開始"""
        try:
            if not self.mover:
                messagebox.showerror("エラー", "設定が読み込まれていません")
                return
            
            watch_folder = self.mover.config.get('watch_folder', os.path.expanduser("~/Downloads"))
            
            if not os.path.exists(watch_folder):
                messagebox.showerror("エラー", f"監視フォルダが存在しません: {watch_folder}")
                return
            
            # オブザーバー設定
            self.observer = Observer()
            self.observer.schedule(self.mover, watch_folder, recursive=False)
            
            # 監視開始
            self.observer.start()
            self.monitoring = True
            
            # UI更新
            self.status_label.config(text=f"監視中: {watch_folder}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            self.log_callback(f"監視開始: {watch_folder}")
            
        except Exception as e:
            messagebox.showerror("エラー", f"監視開始に失敗しました: {e}")
    
    def stop_monitoring(self):
        """監視停止"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            self.monitoring = False
            
            # UI更新
            self.status_label.config(text="停止中")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            self.log_callback("監視停止")
            
        except Exception as e:
            messagebox.showerror("エラー", f"監視停止に失敗しました: {e}")
    
    def log_callback(self, message):
        """ログコールバック"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # ログが多すぎる場合は古いものを削除
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines)-100}.0")
    
    def open_settings(self):
        """設定画面を開く"""
        SettingsWindow(self.root, self.mover, self.log_callback)
    
    def open_startup_settings(self):
        """スタートアップ設定画面を開く"""
        StartupSettingsWindow(self.root)
    
    def open_log(self):
        """ログファイルを開く"""
        try:
            log_file = "file_mover.log"
            if os.path.exists(log_file):
                os.startfile(log_file)
            else:
                messagebox.showinfo("情報", "ログファイルが存在しません")
        except Exception as e:
            messagebox.showerror("エラー", f"ログファイルを開けませんでした: {e}")
    
    def run(self):
        """アプリケーション実行"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # スタートアップ時の動作確認
            if self.is_startup_launch():
                # スタートアップ起動の場合は最小化で起動
                self.root.withdraw()  # ウィンドウを隠す
                if self.tray_icon:
                    # 別スレッドでトレイアイコンを実行
                    import threading
                    tray_thread = threading.Thread(target=self.tray_icon.run_detached, daemon=True)
                    tray_thread.start()
                # 自動的に監視開始
                self.start_monitoring()
                # メインループを実行（トレイアイコン用）
                self.root.mainloop()
            else:
                # 通常起動の場合は通常表示
                self.root.mainloop()
        except Exception as e:
            messagebox.showerror("エラー", f"アプリケーションエラー: {e}")
    
    def is_startup_launch(self):
        """スタートアップ起動かどうかを判定"""
        try:
            # コマンドライン引数をチェック
            if len(sys.argv) > 1 and '--startup' in sys.argv:
                return True
            
            # または、スタートアップディレクトリから起動されているかチェック
            startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            current_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
            
            if current_dir.startswith(startup_dir):
                return True
                
            return False
        except:
            return False
    
    def create_tray_icon(self):
        """システムトレイアイコン作成"""
        try:
            # アイコン画像作成
            image = Image.new('RGB', (64, 64), color='blue')
            dc = ImageDraw.Draw(image)
            dc.text((10, 20), "FM", fill='white')
            
            # メニュー作成
            menu = pystray.Menu(
                pystray.MenuItem("表示", self.show_window),
                pystray.MenuItem("監視開始", self.start_monitoring_from_tray),
                pystray.MenuItem("監視停止", self.stop_monitoring_from_tray),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("終了", self.quit_application)
            )
            
            # トレイアイコン作成
            self.tray_icon = pystray.Icon(
                "FileMover", 
                image, 
                "ダウンロード自動振り分け", 
                menu,
                default_action=self.show_window
            )
            
        except Exception as e:
            print(f"トレイアイコン作成エラー: {e}")
            self.tray_icon = None
    
    def minimize_to_tray_window(self):
        """トレイに最小化"""
        if self.tray_icon:
            self.root.withdraw()
            if not self.tray_icon.visible:
                # 別スレッドでトレイアイコンを実行
                import threading
                tray_thread = threading.Thread(target=self.tray_icon.run_detached, daemon=True)
                tray_thread.start()
    
    def show_window(self, icon=None, item=None):
        """ウィンドウを表示"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def start_monitoring_from_tray(self, icon=None, item=None):
        """トレイから監視開始"""
        self.start_monitoring()
    
    def stop_monitoring_from_tray(self, icon=None, item=None):
        """トレイから監視停止"""
        self.stop_monitoring()
    
    def quit_application(self, icon=None, item=None):
        """アプリケーション終了"""
        try:
            # 監視停止
            if self.monitoring:
                self.stop_monitoring()
            
            # トレイアイコン停止
            if self.tray_icon:
                self.tray_icon.stop()
                self.tray_icon = None
            
            # ウィンドウ終了
            self.root.quit()
            self.root.destroy()
            
            # プロセス終了
            import os
            os._exit(0)
            
        except Exception as e:
            print(f"終了処理エラー: {e}")
            import os
            os._exit(0)
    
    def on_closing(self):
        """アプリケーション終了時"""
        if self.minimize_to_tray and self.tray_icon:
            # トレイに最小化
            self.minimize_to_tray_window()
        else:
            # 完全終了
            self.quit_application()

class SettingsWindow:
    """設定画面"""
    
    def __init__(self, parent, mover, log_callback):
        self.parent = parent
        self.mover = mover
        self.log_callback = log_callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("設定")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets()
        self.load_current_settings()
        
    def create_widgets(self):
        """ウィジェット作成"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 監視フォルダ設定
        folder_frame = ttk.LabelFrame(main_frame, text="監視フォルダ", padding="5")
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        folder_inner = ttk.Frame(folder_frame)
        folder_inner.pack(fill=tk.X)
        
        self.folder_var = tk.StringVar()
        ttk.Entry(folder_inner, textvariable=self.folder_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(folder_inner, text="参照", command=self.browse_folder).pack(side=tk.RIGHT)
        
        # ルール設定
        rules_frame = ttk.LabelFrame(main_frame, text="振り分けルール", padding="5")
        rules_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # ルール操作ボタン（上部に配置）
        rule_buttons = ttk.Frame(rules_frame)
        rule_buttons.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(rule_buttons, text="追加", command=self.add_rule).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(rule_buttons, text="編集", command=self.edit_rule).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(rule_buttons, text="削除", command=self.delete_rule).pack(side=tk.LEFT, padx=(0, 5))
        
        # ルール一覧
        tree_frame = ttk.Frame(rules_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.rules_tree = ttk.Treeview(tree_frame, columns=('pattern', 'destination', 'action'), show='tree headings')
        self.rules_tree.heading('#0', text='名前')
        self.rules_tree.heading('pattern', text='パターン')
        self.rules_tree.heading('destination', text='移動先')
        self.rules_tree.heading('action', text='アクション')
        
        # 列幅設定
        self.rules_tree.column('#0', width=150, minwidth=100)
        self.rules_tree.column('pattern', width=200, minwidth=150)
        self.rules_tree.column('destination', width=250, minwidth=200)
        self.rules_tree.column('action', width=80, minwidth=60)
        
        scrollbar_rules = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=scrollbar_rules.set)
        
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_rules.pack(side=tk.RIGHT, fill=tk.Y)
        
        # その他設定
        other_frame = ttk.LabelFrame(main_frame, text="その他設定", padding="5")
        other_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.delay_var = tk.IntVar()
        ttk.Label(other_frame, text="処理遅延(秒):").pack(side=tk.LEFT)
        ttk.Spinbox(other_frame, from_=1, to=10, textvariable=self.delay_var, width=5).pack(side=tk.LEFT, padx=(5, 10))
        
        self.create_dirs_var = tk.BooleanVar()
        ttk.Checkbutton(other_frame, text="ディレクトリ自動作成", variable=self.create_dirs_var).pack(side=tk.LEFT)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="保存", command=self.save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=self.window.destroy).pack(side=tk.RIGHT)
        
    def browse_folder(self):
        """フォルダ選択"""
        folder = filedialog.askdirectory(title="監視フォルダを選択")
        if folder:
            self.folder_var.set(folder)
    
    def load_current_settings(self):
        """現在の設定を読み込み"""
        try:
            if self.mover and self.mover.config:
                config = self.mover.config
                self.folder_var.set(config.get('watch_folder', ''))
                self.delay_var.set(config.get('delay_seconds', 3))
                self.create_dirs_var.set(config.get('create_directories', True))
                
                # ルール一覧を更新
                self.update_rules_list()
            else:
                # デフォルト設定を表示
                self.folder_var.set(os.path.expanduser("~/Downloads"))
                self.delay_var.set(3)
                self.create_dirs_var.set(True)
                self.update_rules_list()
        except Exception as e:
            messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {e}")
    
    def update_rules_list(self):
        """ルール一覧を更新"""
        # 既存のアイテムを削除
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
        
        # ルールを追加
        if self.mover and self.mover.config:
            for rule in self.mover.config.get('rules', []):
                self.rules_tree.insert('', tk.END, text=rule.get('name', ''),
                                     values=(rule.get('pattern', ''),
                                           rule.get('destination', ''),
                                           rule.get('action', '')))
    
    def add_rule(self):
        """ルール追加"""
        RuleEditWindow(self.window, None, self.add_rule_callback)
    
    def edit_rule(self):
        """ルール編集"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集するルールを選択してください")
            return
        
        item = self.rules_tree.item(selection[0])
        rule_data = {
            'name': item['text'],
            'pattern': item['values'][0],
            'destination': item['values'][1],
            'action': item['values'][2]
        }
        
        RuleEditWindow(self.window, rule_data, self.edit_rule_callback, selection[0])
    
    def delete_rule(self):
        """ルール削除"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除するルールを選択してください")
            return
        
        if messagebox.askyesno("確認", "選択したルールを削除しますか？"):
            self.rules_tree.delete(selection[0])
    
    def add_rule_callback(self, rule_data):
        """ルール追加コールバック"""
        try:
            self.rules_tree.insert('', tk.END, text=rule_data['name'],
                                 values=(rule_data['pattern'], rule_data['destination'], rule_data['action']))
            self.log_callback(f"ルール追加: {rule_data['name']}")
        except Exception as e:
            messagebox.showerror("エラー", f"ルール追加に失敗しました: {e}")
    
    def edit_rule_callback(self, rule_data, item_id):
        """ルール編集コールバック"""
        try:
            self.rules_tree.item(item_id, text=rule_data['name'],
                               values=(rule_data['pattern'], rule_data['destination'], rule_data['action']))
            self.log_callback(f"ルール編集: {rule_data['name']}")
        except Exception as e:
            messagebox.showerror("エラー", f"ルール編集に失敗しました: {e}")
    
    def save_settings(self):
        """設定保存"""
        try:
            # 設定を構築
            config = {
                'watch_folder': self.folder_var.get(),
                'delay_seconds': self.delay_var.get(),
                'create_directories': self.create_dirs_var.get(),
                'log_level': 'INFO',
                'safe_move': {
                    'enabled': True,
                    'hash_check_threshold': 104857600,
                    'verify_integrity': True
                }
            }
            
            # ルールを追加
            rules = []
            for item in self.rules_tree.get_children():
                item_data = self.rules_tree.item(item)
                rules.append({
                    'name': item_data['text'],
                    'pattern': item_data['values'][0],
                    'destination': item_data['values'][1],
                    'action': item_data['values'][2]
                })
            config['rules'] = rules
            
            # 設定を保存
            self.mover.config = config
            self.mover.save_config(config)
            
            messagebox.showinfo("成功", "設定を保存しました")
            self.log_callback("設定を保存しました")
            
        except Exception as e:
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")

class RuleEditWindow:
    """ルール編集画面"""
    
    def __init__(self, parent, rule_data, callback, item_id=None):
        self.parent = parent
        self.rule_data = rule_data
        self.callback = callback
        self.item_id = item_id
        
        self.window = tk.Toplevel(parent)
        self.window.title("ルール編集" if rule_data else "ルール追加")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets()
        if rule_data:
            self.load_rule_data()
        
    def create_widgets(self):
        """ウィジェット作成"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ルール名
        ttk.Label(main_frame, text="ルール名:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # パターン
        ttk.Label(main_frame, text="パターン:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.pattern_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.pattern_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 移動先
        ttk.Label(main_frame, text="移動先:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.destination_var = tk.StringVar()
        dest_frame = ttk.Frame(main_frame)
        dest_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        ttk.Entry(dest_frame, textvariable=self.destination_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(dest_frame, text="参照", command=self.browse_destination).pack(side=tk.RIGHT)
        
        # アクション
        ttk.Label(main_frame, text="アクション:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        self.action_var = tk.StringVar()
        action_combo = ttk.Combobox(main_frame, textvariable=self.action_var, values=['move', 'copy'], state='readonly')
        action_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 説明
        ttk.Label(main_frame, text="説明:", font=('', 8)).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        ttk.Label(main_frame, text="パターンは正規表現で指定します。例: .*\\.pdf$", font=('', 8)).grid(row=5, column=0, columnspan=2, sticky=tk.W)
        ttk.Label(main_frame, text="移動先は絶対パスまたはホームディレクトリからの相対パス", font=('', 8)).grid(row=6, column=0, columnspan=2, sticky=tk.W)
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=(20, 0))
        
        ttk.Button(button_frame, text="OK", command=self.save_rule).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="キャンセル", command=self.window.destroy).pack(side=tk.RIGHT)
        
        main_frame.columnconfigure(1, weight=1)
        
    def browse_destination(self):
        """移動先フォルダ選択"""
        folder = filedialog.askdirectory(title="移動先フォルダを選択")
        if folder:
            self.destination_var.set(folder)
    
    def load_rule_data(self):
        """ルールデータを読み込み"""
        if self.rule_data:
            self.name_var.set(self.rule_data.get('name', ''))
            self.pattern_var.set(self.rule_data.get('pattern', ''))
            self.destination_var.set(self.rule_data.get('destination', ''))
            self.action_var.set(self.rule_data.get('action', 'move'))
    
    def save_rule(self):
        """ルール保存"""
        try:
            rule_data = {
                'name': self.name_var.get(),
                'pattern': self.pattern_var.get(),
                'destination': self.destination_var.get(),
                'action': self.action_var.get()
            }
            
            # バリデーション
            if not rule_data['name']:
                messagebox.showerror("エラー", "ルール名を入力してください")
                return
            
            if not rule_data['pattern']:
                messagebox.showerror("エラー", "パターンを入力してください")
                return
            
            if not rule_data['destination']:
                messagebox.showerror("エラー", "移動先を入力してください")
                return
            
            self.callback(rule_data, self.item_id)
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("エラー", f"ルールの保存に失敗しました: {e}")

class StartupSettingsWindow:
    """スタートアップ設定画面"""
    
    def __init__(self, parent):
        self.parent = parent
        
        self.window = tk.Toplevel(parent)
        self.window.title("スタートアップ設定")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.create_widgets()
        self.check_startup_status()
        
    def create_widgets(self):
        """ウィジェット作成"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 説明
        ttk.Label(main_frame, text="PC起動時に自動的にアプリを開始する設定を行います。", wraplength=350).pack(pady=(0, 20))
        
        # 現在の状態
        status_frame = ttk.LabelFrame(main_frame, text="現在の状態", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.status_label = ttk.Label(status_frame, text="確認中...")
        self.status_label.pack()
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.register_button = ttk.Button(button_frame, text="スタートアップ登録", command=self.register_startup)
        self.register_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.unregister_button = ttk.Button(button_frame, text="スタートアップ解除", command=self.unregister_startup)
        self.unregister_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="閉じる", command=self.window.destroy).pack(side=tk.RIGHT)
        
    def check_startup_status(self):
        """スタートアップ状態確認"""
        try:
            startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_dir, 'ダウンロード自動振り分け.lnk')
            
            if os.path.exists(shortcut_path):
                self.status_label.config(text="スタートアップに登録済み")
                self.register_button.config(state=tk.DISABLED)
                self.unregister_button.config(state=tk.NORMAL)
            else:
                self.status_label.config(text="スタートアップに未登録")
                self.register_button.config(state=tk.NORMAL)
                self.unregister_button.config(state=tk.DISABLED)
                
        except Exception as e:
            self.status_label.config(text=f"確認エラー: {e}")
    
    def register_startup(self):
        """スタートアップ登録"""
        try:
            # 現在の実行ファイルのパスを取得
            if getattr(sys, 'frozen', False):
                # PyInstallerでビルドされた場合
                exe_path = sys.executable
            else:
                # 通常のPython実行の場合
                exe_path = os.path.join(os.path.dirname(__file__), 'file_mover_gui.py')
            
            # スタートアップディレクトリ
            startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_dir, 'ダウンロード自動振り分け.lnk')
            
            # PowerShellを使用してショートカット作成（最小化で起動）
            ps_command = f'''
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{exe_path}"
            $Shortcut.Arguments = "--startup"
            $Shortcut.WorkingDirectory = "{os.path.dirname(exe_path)}"
            $Shortcut.Description = "ダウンロードフォルダ自動振り分けアプリ（最小化起動）"
            $Shortcut.WindowStyle = 7
            $Shortcut.Save()
            '''
            
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                messagebox.showinfo("成功", "スタートアップ登録が完了しました")
                self.check_startup_status()
            else:
                messagebox.showerror("エラー", f"スタートアップ登録に失敗しました: {result.stderr}")
                
        except Exception as e:
            messagebox.showerror("エラー", f"スタートアップ登録に失敗しました: {e}")
    
    def unregister_startup(self):
        """スタートアップ解除"""
        try:
            startup_dir = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
            shortcut_path = os.path.join(startup_dir, 'ダウンロード自動振り分け.lnk')
            
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
                messagebox.showinfo("成功", "スタートアップ登録を解除しました")
                self.check_startup_status()
            else:
                messagebox.showinfo("情報", "スタートアップ登録が見つかりませんでした")
                
        except Exception as e:
            messagebox.showerror("エラー", f"スタートアップ解除に失敗しました: {e}")

def main():
    """メイン関数"""
    try:
        app = FileMoverGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("エラー", f"アプリケーションの起動に失敗しました: {e}")

if __name__ == "__main__":
    main()
