#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
長時間通信調査ツール
より長い時間で監視して大容量通信を検出
"""

import psutil
import time
import json
from datetime import datetime, timedelta
from collections import defaultdict

class LongTermNetworkDetector:
    def __init__(self, threshold_mb=50):
        self.threshold_mb = threshold_mb
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.network_history = []
        self.process_history = defaultdict(list)
        
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
    
    def get_active_processes(self):
        """アクティブなプロセスを取得"""
        processes = {}
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                proc_obj = psutil.Process(pid)
                connections = proc_obj.net_connections(kind='inet')
                
                if connections:
                    external_connections = [c for c in connections 
                                          if c.raddr and c.status == psutil.CONN_ESTABLISHED]
                    
                    if external_connections:
                        processes[pid] = {
                            'name': name,
                            'total_connections': len(connections),
                            'external_connections': len(external_connections)
                        }
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return processes
    
    def monitor_long_term(self, duration_minutes=30):
        """長時間監視"""
        print(f"=== 長時間通信調査開始 ===")
        print(f"検出対象: {self.threshold_mb}MB以上")
        print(f"監視時間: {duration_minutes}分")
        print(f"開始時刻: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # 初期データ取得
        initial_net_io = self.get_system_network_usage()
        if not initial_net_io:
            print("❌ ネットワーク統計を取得できませんでした")
            return
        
        print(f"初期状態:")
        print(f"  総送信: {initial_net_io['bytes_sent'] / (1024*1024):.2f} MB")
        print(f"  総受信: {initial_net_io['bytes_recv'] / (1024*1024):.2f} MB")
        print()
        
        # 監視ループ
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        last_net_io = initial_net_io
        
        print("監視中... (5分ごとに進捗を表示)")
        
        while datetime.now() < end_time:
            current_time = datetime.now()
            elapsed_minutes = int((current_time - start_time).total_seconds() / 60)
            remaining_minutes = duration_minutes - elapsed_minutes
            
            # 現在のネットワーク使用量を取得
            current_net_io = self.get_system_network_usage()
            if current_net_io:
                # 5分間の増加量を計算
                sent_diff = current_net_io['bytes_sent'] - last_net_io['bytes_sent']
                recv_diff = current_net_io['bytes_recv'] - last_net_io['bytes_recv']
                total_diff = sent_diff + recv_diff
                
                # 履歴に記録
                self.network_history.append({
                    'timestamp': current_time,
                    'bytes_sent': sent_diff,
                    'bytes_recv': recv_diff,
                    'total_bytes': total_diff,
                    'elapsed_minutes': elapsed_minutes
                })
                
                # 進捗表示（5分ごと）
                if elapsed_minutes % 5 == 0 and elapsed_minutes > 0:
                    print(f"  {elapsed_minutes:2d}分経過: "
                          f"送信+{sent_diff/(1024*1024):.1f}MB "
                          f"受信+{recv_diff/(1024*1024):.1f}MB "
                          f"合計+{total_diff/(1024*1024):.1f}MB")
                    
                    # 大容量通信をチェック
                    if total_diff >= self.threshold_bytes:
                        print(f"🚨 {self.threshold_mb}MB以上の通信を検出！")
                        self.analyze_peak_activity(current_net_io)
                
                last_net_io = current_net_io
            
            # プロセス情報も定期的に収集
            if elapsed_minutes % 10 == 0:  # 10分ごと
                processes = self.get_active_processes()
                self.process_history[elapsed_minutes] = processes
            
            time.sleep(60)  # 1分ごとにチェック
        
        # 最終結果
        final_net_io = self.get_system_network_usage()
        if final_net_io:
            total_sent = final_net_io['bytes_sent'] - initial_net_io['bytes_sent']
            total_recv = final_net_io['bytes_recv'] - initial_net_io['bytes_recv']
            total_all = total_sent + total_recv
            
            print(f"\n調査終了: {datetime.now().strftime('%H:%M:%S')}")
            print(f"総監視時間: {duration_minutes}分")
            print(f"総通信量:")
            print(f"  送信: {total_sent / (1024*1024):.2f} MB")
            print(f"  受信: {total_recv / (1024*1024):.2f} MB")
            print(f"  合計: {total_all / (1024*1024):.2f} MB")
            print(f"  平均: {total_all / (1024*1024) / duration_minutes:.2f} MB/分")
            
            if total_all >= self.threshold_bytes:
                print(f"\n🚨 {self.threshold_mb}MB以上の通信を検出しました！")
                self.analyze_results()
            else:
                print(f"\n✅ {self.threshold_mb}MB以上の通信は検出されませんでした")
    
    def analyze_peak_activity(self, net_io):
        """ピーク時の活動を分析"""
        print("📊 ピーク時のプロセス分析:")
        processes = self.get_active_processes()
        
        # 接続数でソート
        sorted_processes = sorted(
            processes.items(),
            key=lambda x: x[1]['external_connections'],
            reverse=True
        )
        
        for i, (pid, proc_info) in enumerate(sorted_processes[:5], 1):
            name = proc_info['name']
            external_conn = proc_info['external_connections']
            total_conn = proc_info['total_connections']
            
            print(f"  {i}. {name} (PID: {pid})")
            print(f"     外部接続: {external_conn} / 総接続: {total_conn}")
    
    def analyze_results(self):
        """結果を分析"""
        print("\n📈 詳細分析:")
        
        # 最も通信量が多かった5分間を特定
        peak_periods = sorted(
            self.network_history,
            key=lambda x: x['total_bytes'],
            reverse=True
        )[:3]
        
        print("最も通信量が多かった期間:")
        for i, period in enumerate(peak_periods, 1):
            minutes = period['elapsed_minutes']
            total_mb = period['total_bytes'] / (1024*1024)
            print(f"  {i}. {minutes}分目: {total_mb:.1f}MB")
        
        # 時間帯別の平均通信量
        print("\n時間帯別平均通信量:")
        for period in self.network_history:
            if period['elapsed_minutes'] % 10 == 0:  # 10分ごと
                avg_mb = period['total_bytes'] / (1024*1024)
                print(f"  {period['elapsed_minutes']:2d}分目: {avg_mb:.1f}MB")

def main():
    """メイン関数"""
    print("🔍 長時間通信調査ツール")
    print("=" * 50)
    print()
    
    # 検出閾値を設定
    threshold = input("検出閾値(MB) [デフォルト: 50]: ").strip()
    if not threshold:
        threshold = 50
    else:
        try:
            threshold = int(threshold)
        except ValueError:
            threshold = 50
    
    # 監視時間を設定
    duration = input("監視時間(分) [デフォルト: 30]: ").strip()
    if not duration:
        duration = 30
    else:
        try:
            duration = int(duration)
        except ValueError:
            duration = 30
    
    print()
    
    # 調査実行
    detector = LongTermNetworkDetector(threshold)
    detector.monitor_long_term(duration)
    
    print("\n" + "=" * 80)
    print("調査完了")
    input("Enterキーを押して終了...")

if __name__ == "__main__":
    main()

