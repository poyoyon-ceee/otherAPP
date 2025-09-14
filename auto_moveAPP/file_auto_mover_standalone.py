#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ダウンロードフォルダ自動振り分けアプリ（スタンドアロン版）
設定ファイルをEXEに組み込んだ完全単体版
"""

import os
import json
import time
import shutil
import logging
import hashlib
import sys
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

class FileAutoMoverStandalone(FileSystemEventHandler):
    """ファイル自動移動ハンドラー（スタンドアロン版）"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
    def get_resource_path(self, relative_path):
        """PyInstallerでビルドされた場合のリソースパス取得"""
        try:
            # PyInstallerでビルドされた場合
            base_path = sys._MEIPASS
        except Exception:
            # 通常のPython実行の場合
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            # まず外部のconfig.jsonを確認
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 外部ファイルがない場合、組み込み設定を確認
            try:
                embedded_config_path = self.get_resource_path("config.json")
                if os.path.exists(embedded_config_path):
                    with open(embedded_config_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except:
                pass
            
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
                },
                "startup_options": {
                    "minimize_to_tray": True,
                    "auto_start": False,
                    "show_notifications": True
                }
            }
            
            # デフォルト設定を外部ファイルに保存
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
                # 絶対パスの場合
                dest_path = Path(destination)
            else:
                # 相対パスの場合（ホームディレクトリ基準）
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
                else:
                    self.logger.error(f"安全移動失敗: {file_path.name}")
                
            elif action == 'copy':
                if dest_file_path.exists():
                    dest_file_path = self.get_unique_filename(dest_file_path)
                
                shutil.copy2(str(file_path), str(dest_file_path))
                self.logger.info(f"コピー完了: {file_path.name} -> {dest_path}")
                
        except Exception as e:
            self.logger.error(f"ルール実行エラー: {e}")
    
    def safe_move(self, src_path, dst_path):
        """安全な移動（コピー→整合性確認→元ファイル削除）"""
        try:
            src_path = Path(src_path)
            dst_path = Path(dst_path)
            
            self.logger.info(f"安全移動開始: {src_path.name}")
            
            # 1. ファイルサイズを取得
            src_size = src_path.stat().st_size
            self.logger.debug(f"元ファイルサイズ: {src_size} bytes")
            
            # 2. コピー実行
            shutil.copy2(str(src_path), str(dst_path))
            self.logger.debug(f"コピー完了: {dst_path}")
            
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
                
                self.logger.debug(f"ハッシュ確認完了: {src_hash}")
            
            # 5. 元ファイル削除
            src_path.unlink()
            self.logger.info(f"元ファイル削除完了: {src_path.name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"安全移動エラー: {e}")
            # エラー時はコピー先を削除
            try:
                if dst_path.exists():
                    dst_path.unlink()
                    self.logger.info(f"エラー時のクリーンアップ完了: {dst_path.name}")
            except Exception as cleanup_error:
                self.logger.error(f"クリーンアップエラー: {cleanup_error}")
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

def main():
    """メイン関数"""
    print("ダウンロードフォルダ自動振り分けアプリ（スタンドアロン版）を開始します...")
    print("終了するには Ctrl+C を押してください")
    
    try:
        # ハンドラー作成
        event_handler = FileAutoMoverStandalone()
        
        # 監視対象フォルダ
        watch_folder = event_handler.config.get('watch_folder', os.path.expanduser("~/Downloads"))
        
        if not os.path.exists(watch_folder):
            print(f"エラー: 監視フォルダが存在しません: {watch_folder}")
            return
        
        print(f"監視フォルダ: {watch_folder}")
        
        # オブザーバー設定
        observer = Observer()
        observer.schedule(event_handler, watch_folder, recursive=False)
        
        # 監視開始
        observer.start()
        print("ファイル監視を開始しました...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n監視を停止しています...")
            observer.stop()
        
        observer.join()
        print("アプリケーションを終了しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
