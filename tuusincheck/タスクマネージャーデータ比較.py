#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
タスクマネージャーデータ比較ツール
Network Monitorのデータとタスクマネージャーの履歴を比較分析
"""

import json
import os
from datetime import datetime, timedelta

def analyze_taskmanager_data():
    """タスクマネージャーのアプリ履歴の活用方法を説明"""
    print("=" * 80)
    print("タスクマネージャー「アプリの履歴」活用ガイド")
    print("=" * 80)
    print()
    
    print("【タスクマネージャーで確認できること】")
    print()
    print("1. 長期的な通信量傾向（過去30日間）")
    print("   → どのアプリが最も通信しているか")
    print("   → 月間の総通信量")
    print()
    
    print("2. CPU使用時間")
    print("   → バックグラウンドで動作しているアプリ")
    print("   → リソースを多く消費するアプリ")
    print()
    
    print("3. アプリの起動回数")
    print("   → よく使うアプリの特定")
    print()
    
    print("-" * 80)
    print("【Network Monitorで確認できること】")
    print()
    print("1. リアルタイムの通信量")
    print("   → 今、どのアプリが通信しているか")
    print("   → 3分間の通信量の変化")
    print()
    
    print("2. 接続先の詳細")
    print("   → 外部サーバーのIPアドレス")
    print("   → ポート番号（HTTP、HTTPS等）")
    print()
    
    print("3. プロセスごとの接続数")
    print("   → どのアプリが多くの接続を持っているか")
    print()
    
    print("=" * 80)
    print("【組み合わせた活用方法】")
    print("=" * 80)
    print()
    
    print("■ ステップ1: タスクマネージャーで長期傾向を確認")
    print("  1. タスクマネージャーを開く（Ctrl + Shift + Esc）")
    print("  2. 「アプリの履歴」タブを選択")
    print("  3. 「ネットワーク」列でソート")
    print("  4. 最も通信量が多いアプリを特定")
    print()
    
    print("■ ステップ2: Network Monitorでリアルタイム監視")
    print("  1. 特定したアプリが実行中に監視開始")
    print("  2. 3分間隔で通信量をチェック")
    print("  3. どのタイミングで通信が発生するか確認")
    print()
    
    print("■ ステップ3: 詳細調査ツールで原因究明")
    print("  1. 大容量通信が発生したら「大容量通信調査」を実行")
    print("  2. 接続先を確認")
    print("  3. 対策を実施")
    print()
    
    print("=" * 80)
    print("【実用例】")
    print("=" * 80)
    print()
    
    print("例1: Chromeの通信量が多い場合")
    print("  タスクマネージャー: 「過去30日間で500MB使用」")
    print("  → Network Monitor: 「現在、10個の接続あり」")
    print("  → Chrome通信調査: 「拡張機能が原因」")
    print("  → 対策: 不要な拡張機能を無効化")
    print()
    
    print("例2: OneDriveの通信量が多い場合")
    print("  タスクマネージャー: 「過去30日間で2GB使用」")
    print("  → Network Monitor: 「毎3分で50MB増加」")
    print("  → 長時間通信調査: 「大容量ファイルの同期中」")
    print("  → 対策: 同期を一時停止、または選択的同期に変更")
    print()
    
    print("例3: Steamの通信量が多い場合")
    print("  タスクマネージャー: 「過去30日間で10GB使用」")
    print("  → Network Monitor: 「午前3時に大容量通信」")
    print("  → 対策: 自動更新の時間帯を変更")
    print()
    
    print("=" * 80)
    print("【タスクマネージャーでのチェックポイント】")
    print("=" * 80)
    print()
    
    print("1. ネットワーク列を確認")
    print("   → 100MB以上のアプリに注目")
    print()
    
    print("2. CPU時間を確認")
    print("   → 長時間動作しているバックグラウンドアプリ")
    print()
    
    print("3. 定期的にデータを削除")
    print("   → 右クリック → 「使用履歴の削除」")
    print("   → 新しい期間のデータを測定")
    print()
    
    print("=" * 80)
    print("【推奨ワークフロー】")
    print("=" * 80)
    print()
    
    print("週次チェック:")
    print("  1. タスクマネージャーで週間の通信量を確認")
    print("  2. 異常に多いアプリがあれば、Network Monitorで詳細確認")
    print("  3. 必要に応じて設定を調整")
    print()
    
    print("テザリング使用時:")
    print("  1. Network Monitorを起動（システムトレイ版）")
    print("  2. リアルタイムで監視")
    print("  3. 大容量通信を即座に検出")
    print()
    
    print("月次レビュー:")
    print("  1. タスクマネージャーで月間の通信量を確認")
    print("  2. Network Monitorの保存データと比較")
    print("  3. 長期的な傾向を分析")
    print()

def show_taskmanager_tips():
    """タスクマネージャーの便利な使い方"""
    print("\n" + "=" * 80)
    print("【タスクマネージャーの便利な使い方】")
    print("=" * 80)
    print()
    
    print("■ アプリの履歴を開く方法:")
    print("  1. Ctrl + Shift + Esc でタスクマネージャーを開く")
    print("  2. 「アプリの履歴」タブをクリック")
    print("  3. 「ネットワーク」列をクリックしてソート")
    print()
    
    print("■ データの見方:")
    print("  ・CPU時間: アプリがCPUを使用した時間")
    print("  ・ネットワーク: データ通信量（MB単位）")
    print("  ・従量制課金接続: テザリング等での通信量")
    print()
    
    print("■ 履歴をリセットする:")
    print("  1. アプリを右クリック")
    print("  2. 「使用履歴の削除」を選択")
    print("  3. 新しい測定期間が開始")
    print()
    
    print("■ 注意点:")
    print("  ・Windowsアプリのみ表示（デスクトップアプリは含まれない場合あり）")
    print("  ・システムプロセスは表示されない")
    print("  ・正確な測定ではなく推定値")
    print()

def main():
    """メイン関数"""
    print("🔍 タスクマネージャーデータ比較・活用ガイド")
    print()
    
    analyze_taskmanager_data()
    show_taskmanager_tips()
    
    print("\n" + "=" * 80)
    print("ガイド表示完了")
    print()
    print("タスクマネージャーとNetwork Monitorを組み合わせて、")
    print("効果的な通信量管理を実現しましょう！")
    print("=" * 80)
    
    input("\nEnterキーを押して終了...")

if __name__ == "__main__":
    main()
