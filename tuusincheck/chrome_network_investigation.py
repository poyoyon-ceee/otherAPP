#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Network Investigation Tool
詳細なChrome通信調査ツール
"""

import psutil
import subprocess
import json
from datetime import datetime

def get_chrome_processes():
    """Chromeプロセスを取得"""
    chrome_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    
                    # プロセスタイプを判定
                    process_type = "Unknown"
                    if '--type=renderer' in cmdline_str:
                        process_type = "Renderer (Tab)"
                    elif '--type=gpu-process' in cmdline_str:
                        process_type = "GPU Process"
                    elif '--type=utility' in cmdline_str:
                        process_type = "Utility Process"
                    elif '--type=zygote' in cmdline_str:
                        process_type = "Zygote Process"
                    elif '--type=broker' in cmdline_str:
                        process_type = "Broker Process"
                    elif '--type=crashpad-handler' in cmdline_str:
                        process_type = "Crash Handler"
                    elif '--type=network-service' in cmdline_str:
                        process_type = "Network Service"
                    elif '--type=storage-service' in cmdline_str:
                        process_type = "Storage Service"
                    elif '--type=audio-service' in cmdline_str:
                        process_type = "Audio Service"
                    elif '--type=ppapi' in cmdline_str:
                        process_type = "Plugin Process"
                    elif '--type=extension' in cmdline_str:
                        process_type = "Extension Process"
                    elif '--type=renderer' not in cmdline_str and '--type=' not in cmdline_str:
                        process_type = "Main Browser Process"
                    
                    chrome_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'type': process_type,
                        'cmdline': cmdline_str[:200] + '...' if len(cmdline_str) > 200 else cmdline_str
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return chrome_processes

def get_chrome_connections(pid):
    """特定のChromeプロセスの接続を取得"""
    try:
        proc = psutil.Process(pid)
        connections = proc.connections(kind='inet')
        
        connection_info = []
        for conn in connections:
            if conn.status == psutil.CONN_ESTABLISHED:
                local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
                remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
                
                connection_info.append({
                    'local': local_addr,
                    'remote': remote_addr,
                    'status': conn.status,
                    'family': conn.family.name
                })
        
        return connection_info
    except Exception as e:
        return [{'error': str(e)}]

def investigate_chrome_network():
    """Chromeのネットワーク使用状況を詳細調査"""
    print("=" * 80)
    print("Chrome Network Investigation Report")
    print("=" * 80)
    print(f"調査時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Chromeプロセスを取得
    chrome_processes = get_chrome_processes()
    
    if not chrome_processes:
        print("Chromeプロセスが見つかりませんでした。")
        return
    
    print(f"発見されたChromeプロセス数: {len(chrome_processes)}")
    print()
    
    # プロセスごとの詳細情報
    for i, proc in enumerate(chrome_processes, 1):
        print(f"【プロセス {i}】")
        print(f"  PID: {proc['pid']}")
        print(f"  名前: {proc['name']}")
        print(f"  タイプ: {proc['type']}")
        print()
        
        # 接続情報を取得
        connections = get_chrome_connections(proc['pid'])
        
        if connections and 'error' not in connections[0]:
            print(f"  アクティブ接続数: {len(connections)}")
            
            # リモート接続を表示（外部通信）
            remote_connections = [c for c in connections if c['remote'] != 'N/A']
            if remote_connections:
                print("  外部接続:")
                for conn in remote_connections[:10]:  # 最大10個表示
                    print(f"    → {conn['remote']} ({conn['family']})")
                
                if len(remote_connections) > 10:
                    print(f"    ... 他 {len(remote_connections) - 10} 接続")
            else:
                print("  外部接続: なし")
        else:
            print(f"  接続情報: 取得できませんでした")
        
        print("-" * 60)
    
    # 推奨対策
    print("\n【推奨対策】")
    print("1. Chrome拡張機能の確認:")
    print("   chrome://extensions/ で不要な拡張機能を無効化")
    print()
    print("2. Chrome設定の調整:")
    print("   chrome://settings/ で以下を確認:")
    print("   - セーフブラウジング設定")
    print("   - 使用統計の送信設定")
    print("   - バックグラウンド処理の設定")
    print()
    print("3. ローカルHTMLの確認:")
    print("   開発者ツール(F12) → Network タブで")
    print("   外部リソースの読み込みを確認")
    print()
    print("4. Chromeの再起動:")
    print("   すべてのChromeウィンドウを閉じて再起動")

def main():
    """メイン関数"""
    try:
        investigate_chrome_network()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
    
    input("\nEnterキーを押して終了...")

if __name__ == "__main__":
    main()

