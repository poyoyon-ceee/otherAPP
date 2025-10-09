#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大容量通信調査ツール
100MB級の通信を特定する
"""

import psutil
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

class HighVolumeNetworkDetector:
    def __init__(self, threshold_mb=10):
        self.threshold_mb = threshold_mb
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.process_data = {}
        self.previous_data = {}
        
    def get_process_io_counters(self):
        """プロセスのI/Oカウンターを取得"""
        current_data = {}
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                proc_obj = psutil.Process(pid)
                io_counters = proc_obj.io_counters()
                
                if io_counters:
                    current_data[pid] = {
                        'name': name,
                        'bytes_sent': io_counters.bytes_sent if hasattr(io_counters, 'bytes_sent') else 0,
                        'bytes_recv': io_counters.bytes_recv if hasattr(io_counters, 'bytes_recv') else 0,
                        'timestamp': datetime.now()
                    }
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return current_data
    
    def detect_high_volume_processes(self, duration_minutes=5):
        """高容量通信プロセスを検出"""
        print(f"=== 大容量通信調査開始 ===")
        print(f"検出対象: {self.threshold_mb}MB以上")
        print(f"監視時間: {duration_minutes}分")
        print(f"開始時刻: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 初期データ取得
        self.previous_data = self.get_process_io_counters()
        time.sleep(duration_minutes * 60)  # 指定時間待機
        current_data = self.get_process_io_counters()
        
        print(f"調査終了: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 差分計算
        high_volume_processes = []
        
        for pid, current in current_data.items():
            if pid in self.previous_data:
                prev = self.previous_data[pid]
                
                bytes_sent_diff = max(0, current['bytes_sent'] - prev['bytes_sent'])
                bytes_recv_diff = max(0, current['bytes_recv'] - prev['bytes_recv'])
                total_bytes = bytes_sent_diff + bytes_recv_diff
                
                if total_bytes >= self.threshold_bytes:
                    high_volume_processes.append({
                        'pid': pid,
                        'name': current['name'],
                        'bytes_sent': bytes_sent_diff,
                        'bytes_recv': bytes_recv_diff,
                        'total_bytes': total_bytes,
                        'mb_sent': bytes_sent_diff / (1024 * 1024),
                        'mb_recv': bytes_recv_diff / (1024 * 1024),
                        'mb_total': total_bytes / (1024 * 1024)
                    })
        
        # 結果表示
        if high_volume_processes:
            high_volume_processes.sort(key=lambda x: x['total_bytes'], reverse=True)
            
            print("🚨 大容量通信を検出したプロセス:")
            print("-" * 80)
            
            for i, proc in enumerate(high_volume_processes, 1):
                print(f"{i}. {proc['name']} (PID: {proc['pid']})")
                print(f"   送信: {proc['mb_sent']:.2f} MB")
                print(f"   受信: {proc['mb_recv']:.2f} MB")
                print(f"   合計: {proc['mb_total']:.2f} MB")
                
                # プロセスの詳細情報
                self.analyze_process(proc['pid'], proc['name'])
                print()
        else:
            print(f"✅ {self.threshold_mb}MB以上の通信は検出されませんでした")
            print("   通常の使用範囲内です")
        
        return high_volume_processes
    
    def analyze_process(self, pid, name):
        """プロセスの詳細分析"""
        try:
            proc = psutil.Process(pid)
            
            # 接続情報
            connections = proc.connections(kind='inet')
            external_connections = [c for c in connections if c.raddr and c.status == psutil.CONN_ESTABLISHED]
            
            print(f"   接続数: {len(connections)} (外部: {len(external_connections)})")
            
            # 主要な外部接続を表示
            if external_connections:
                print("   主要な外部接続:")
                for conn in external_connections[:5]:  # 最大5個
                    remote_ip = conn.raddr.ip
                    remote_port = conn.raddr.port
                    
                    # ポートからサービスを推測
                    service = self.get_service_name(remote_port)
                    print(f"     → {remote_ip}:{remote_port} ({service})")
                
                if len(external_connections) > 5:
                    print(f"     ... 他 {len(external_connections) - 5} 接続")
            
            # プロセスのコマンドライン
            try:
                cmdline = proc.cmdline()
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    if len(cmdline_str) > 100:
                        cmdline_str = cmdline_str[:100] + '...'
                    print(f"   コマンド: {cmdline_str}")
            except:
                pass
                
        except Exception as e:
            print(f"   詳細情報取得エラー: {e}")
    
    def get_service_name(self, port):
        """ポート番号からサービス名を推測"""
        common_ports = {
            80: "HTTP",
            443: "HTTPS",
            8080: "HTTP-Alt",
            8443: "HTTPS-Alt",
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            110: "POP3",
            143: "IMAP",
            993: "IMAPS",
            995: "POP3S",
            3389: "RDP",
            5900: "VNC",
            6881: "BitTorrent",
            9090: "WebSocket",
        }
        return common_ports.get(port, "Unknown")
    
    def get_recommendations(self, high_volume_processes):
        """推奨対策を表示"""
        print("\n" + "=" * 80)
        print("📋 推奨対策")
        print("=" * 80)
        
        for proc in high_volume_processes:
            name = proc['name'].lower()
            mb_total = proc['mb_total']
            
            print(f"\n【{proc['name']}】 ({mb_total:.1f}MB)")
            
            if 'chrome' in name or 'msedge' in name:
                print("  • ブラウザ関連:")
                print("    - タブを閉じる（不要なタブを確認）")
                print("    - 拡張機能を無効化")
                print("    - 自動再生を無効化")
                print("    - バックグラウンド処理を無効化")
                
            elif 'steam' in name:
                print("  • Steam関連:")
                print("    - ゲームの自動更新を無効化")
                print("    - バックグラウンドでのダウンロードを停止")
                
            elif 'windows' in name or 'svchost' in name:
                print("  • Windows関連:")
                print("    - Windows Updateを一時停止")
                print("    - 自動メンテナンスを無効化")
                
            elif 'onedrive' in name or 'dropbox' in name:
                print("  • クラウド同期関連:")
                print("    - 同期を一時停止")
                print("    - 大きなファイルの同期を確認")
                
            elif 'spotify' in name or 'youtube' in name:
                print("  • ストリーミング関連:")
                print("    - 音質・画質設定を下げる")
                print("    - オフライン再生を有効化")
                
            else:
                print("  • 一般的な対策:")
                print("    - プロセスを終了")
                print("    - 設定で自動更新を無効化")
                print("    - バックグラウンド処理を停止")

def main():
    """メイン関数"""
    print("🔍 大容量通信調査ツール")
    print("=" * 50)
    print()
    
    # 検出閾値を設定（デフォルト10MB）
    threshold = input("検出閾値(MB) [デフォルト: 10]: ").strip()
    if not threshold:
        threshold = 10
    else:
        try:
            threshold = int(threshold)
        except ValueError:
            threshold = 10
    
    # 監視時間を設定（デフォルト5分）
    duration = input("監視時間(分) [デフォルト: 5]: ").strip()
    if not duration:
        duration = 5
    else:
        try:
            duration = int(duration)
        except ValueError:
            duration = 5
    
    print()
    
    # 調査実行
    detector = HighVolumeNetworkDetector(threshold)
    high_volume_processes = detector.detect_high_volume_processes(duration)
    
    # 推奨対策を表示
    if high_volume_processes:
        detector.get_recommendations(high_volume_processes)
    
    print("\n" + "=" * 80)
    print("調査完了")
    input("Enterキーを押して終了...")

if __name__ == "__main__":
    main()
