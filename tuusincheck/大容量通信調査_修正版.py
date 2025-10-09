#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大容量通信調査ツール（修正版）
システム全体のネットワーク使用量から大容量通信を検出
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
        self.process_connections = {}
        self.network_history = []
        
    def get_active_processes_with_connections(self):
        """ネットワーク接続を持つプロセスを取得"""
        processes = {}
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                proc_obj = psutil.Process(pid)
                connections = proc_obj.connections(kind='inet')
                
                if connections:
                    external_connections = [c for c in connections 
                                          if c.raddr and c.status == psutil.CONN_ESTABLISHED]
                    
                    if external_connections:
                        processes[pid] = {
                            'name': name,
                            'total_connections': len(connections),
                            'external_connections': len(external_connections),
                            'connections': external_connections[:5]  # 最初の5個
                        }
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return processes
    
    def get_system_network_usage(self):
        """システム全体のネットワーク使用量を取得"""
        try:
            net_io = psutil.net_io_counters()
            return {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"ネットワーク統計取得エラー: {e}")
            return None
    
    def detect_high_volume_activity(self, duration_minutes=5):
        """高容量通信活動を検出"""
        print(f"=== 大容量通信調査開始 ===")
        print(f"検出対象: {self.threshold_mb}MB以上")
        print(f"監視時間: {duration_minutes}分")
        print(f"開始時刻: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 初期データ取得
        initial_net_io = self.get_system_network_usage()
        initial_processes = self.get_active_processes_with_connections()
        
        if not initial_net_io:
            print("❌ ネットワーク統計を取得できませんでした")
            return []
        
        print(f"初期状態:")
        print(f"  総送信: {initial_net_io['bytes_sent'] / (1024*1024):.2f} MB")
        print(f"  総受信: {initial_net_io['bytes_recv'] / (1024*1024):.2f} MB")
        print(f"  アクティブプロセス: {len(initial_processes)}個")
        print()
        
        # 監視期間中のデータ収集
        print("監視中... (プロセス情報を定期的に収集)")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            current_processes = self.get_active_processes_with_connections()
            
            # 新しいプロセスや接続数の変化を記録
            for pid, proc_info in current_processes.items():
                if pid not in self.process_connections:
                    self.process_connections[pid] = {
                        'name': proc_info['name'],
                        'first_seen': datetime.now(),
                        'max_connections': proc_info['total_connections'],
                        'connection_history': []
                    }
                
                # 接続数の変化を記録
                self.process_connections[pid]['connection_history'].append({
                    'timestamp': datetime.now(),
                    'total_connections': proc_info['total_connections'],
                    'external_connections': proc_info['external_connections']
                })
                
                # 最大接続数を更新
                if proc_info['total_connections'] > self.process_connections[pid]['max_connections']:
                    self.process_connections[pid]['max_connections'] = proc_info['total_connections']
            
            time.sleep(30)  # 30秒ごとにチェック
        
        # 最終データ取得
        final_net_io = self.get_system_network_usage()
        final_processes = self.get_active_processes_with_connections()
        
        if not final_net_io:
            print("❌ 最終ネットワーク統計を取得できませんでした")
            return []
        
        print(f"\n調査終了: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 差分計算
        bytes_sent_diff = final_net_io['bytes_sent'] - initial_net_io['bytes_sent']
        bytes_recv_diff = final_net_io['bytes_recv'] - initial_net_io['bytes_recv']
        total_bytes_diff = bytes_sent_diff + bytes_recv_diff
        
        print(f"監視期間中の通信量:")
        print(f"  送信増加: {bytes_sent_diff / (1024*1024):.2f} MB")
        print(f"  受信増加: {bytes_recv_diff / (1024*1024):.2f} MB")
        print(f"  合計増加: {total_bytes_diff / (1024*1024):.2f} MB")
        print()
        
        # 高容量通信の判定
        if total_bytes_diff >= self.threshold_bytes:
            print(f"🚨 {self.threshold_mb}MB以上の通信を検出しました！")
            print()
            
            # アクティブなプロセスを分析
            self.analyze_active_processes()
            
            return self.get_suspicious_processes()
        else:
            print(f"✅ {self.threshold_mb}MB以上の通信は検出されませんでした")
            print("   通常の使用範囲内です")
            return []
    
    def analyze_active_processes(self):
        """アクティブなプロセスを分析"""
        print("📊 アクティブなプロセスの分析:")
        print("-" * 60)
        
        # 接続数でソート
        sorted_processes = sorted(
            self.process_connections.items(),
            key=lambda x: x[1]['max_connections'],
            reverse=True
        )
        
        for i, (pid, proc_info) in enumerate(sorted_processes[:10], 1):
            name = proc_info['name']
            max_conn = proc_info['max_connections']
            
            print(f"{i}. {name} (PID: {pid})")
            print(f"   最大接続数: {max_conn}")
            
            # 接続履歴の分析
            if len(proc_info['connection_history']) > 1:
                first_conn = proc_info['connection_history'][0]['external_connections']
                last_conn = proc_info['connection_history'][-1]['external_connections']
                conn_change = last_conn - first_conn
                
                if conn_change > 0:
                    print(f"   接続増加: +{conn_change}")
                elif conn_change < 0:
                    print(f"   接続減少: {conn_change}")
                else:
                    print(f"   接続変化: なし")
            
            # 外部接続先を表示
            try:
                proc = psutil.Process(pid)
                connections = proc.connections(kind='inet')
                external_connections = [c for c in connections 
                                      if c.raddr and c.status == psutil.CONN_ESTABLISHED]
                
                if external_connections:
                    print("   主要な外部接続:")
                    for conn in external_connections[:3]:  # 最初の3個
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        service = self.get_service_name(remote_port)
                        print(f"     → {remote_ip}:{remote_port} ({service})")
                    
                    if len(external_connections) > 3:
                        print(f"     ... 他 {len(external_connections) - 3} 接続")
                
            except Exception as e:
                print(f"   接続情報取得エラー: {e}")
            
            print()
    
    def get_suspicious_processes(self):
        """疑わしいプロセスを特定"""
        suspicious = []
        
        for pid, proc_info in self.process_connections.items():
            name = proc_info['name'].lower()
            max_connections = proc_info['max_connections']
            
            # 疑わしい条件
            is_suspicious = (
                max_connections >= 10 or  # 10個以上の接続
                'chrome' in name or      # ブラウザ
                'steam' in name or       # Steam
                'onedrive' in name or    # クラウド同期
                'dropbox' in name or
                'spotify' in name or     # ストリーミング
                'youtube' in name or
                'netflix' in name
            )
            
            if is_suspicious:
                suspicious.append({
                    'pid': pid,
                    'name': proc_info['name'],
                    'max_connections': max_connections,
                    'reason': self.get_suspicion_reason(name, max_connections)
                })
        
        return suspicious
    
    def get_suspicion_reason(self, name, connections):
        """疑わしい理由を取得"""
        if connections >= 20:
            return "多数の接続"
        elif 'chrome' in name:
            return "ブラウザ（多数のタブ・拡張機能）"
        elif 'steam' in name:
            return "ゲームプラットフォーム"
        elif 'onedrive' in name or 'dropbox' in name:
            return "クラウド同期"
        elif 'spotify' in name or 'youtube' in name:
            return "ストリーミング"
        else:
            return "高接続数"
    
    def get_service_name(self, port):
        """ポート番号からサービス名を推測"""
        common_ports = {
            80: "HTTP", 443: "HTTPS", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
            21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
            110: "POP3", 143: "IMAP", 993: "IMAPS", 995: "POP3S",
            3389: "RDP", 5900: "VNC", 6881: "BitTorrent", 9090: "WebSocket",
        }
        return common_ports.get(port, "Unknown")
    
    def get_recommendations(self, suspicious_processes):
        """推奨対策を表示"""
        print("\n" + "=" * 80)
        print("📋 推奨対策")
        print("=" * 80)
        
        for proc in suspicious_processes:
            name = proc['name']
            connections = proc['max_connections']
            reason = proc['reason']
            
            print(f"\n【{name}】 (最大接続数: {connections})")
            print(f"  理由: {reason}")
            
            if 'chrome' in name.lower():
                print("  • ブラウザ関連:")
                print("    - 不要なタブを閉じる")
                print("    - 拡張機能を無効化")
                print("    - 自動再生を無効化")
                
            elif 'steam' in name.lower():
                print("  • Steam関連:")
                print("    - ゲームの自動更新を無効化")
                print("    - バックグラウンドでのダウンロードを停止")
                
            elif 'onedrive' in name.lower() or 'dropbox' in name.lower():
                print("  • クラウド同期関連:")
                print("    - 同期を一時停止")
                print("    - 大きなファイルの同期を確認")
                
            elif 'spotify' in name.lower() or 'youtube' in name.lower():
                print("  • ストリーミング関連:")
                print("    - 音質・画質設定を下げる")
                print("    - オフライン再生を有効化")
                
            else:
                print("  • 一般的な対策:")
                print("    - プロセスを終了")
                print("    - 設定で自動更新を無効化")

def main():
    """メイン関数"""
    print("🔍 大容量通信調査ツール（修正版）")
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
    suspicious_processes = detector.detect_high_volume_activity(duration)
    
    # 推奨対策を表示
    if suspicious_processes:
        detector.get_recommendations(suspicious_processes)
    
    print("\n" + "=" * 80)
    print("調査完了")
    input("Enterキーを押して終了...")

if __name__ == "__main__":
    main()

