#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Network Monitor App V2
Monitor network usage per application during tethering every 3 minutes
Uses Windows Performance Counters for per-process network statistics
"""

import psutil
import time
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import subprocess

# Windows用の定数（コンソールウィンドウを非表示にするため）
if not hasattr(subprocess, 'CREATE_NO_WINDOW'):
    subprocess.CREATE_NO_WINDOW = 0x08000000

# システムトレイ用ライブラリ
try:
    from PIL import Image, ImageDraw
    import pystray
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False
    print("警告: pystray/Pillowがインストールされていません。システムトレイ機能は無効です。")
    print("インストール: pip install pystray Pillow")

class NetworkMonitorV2:
    def __init__(self, update_interval=180):
        self.monitoring = False
        self.process_data = defaultdict(lambda: {'bytes_sent': 0, 'bytes_recv': 0, 'last_update': None})
        self.previous_connections = {}
        self.connection_bytes = {}
        self.monitor_thread = None
        self.update_interval = update_interval  # Monitoring interval (seconds)
        self.last_measurement_time = None
    
    def set_update_interval(self, interval):
        """Set monitoring interval in seconds"""
        self.update_interval = interval
        print(f"Monitoring interval set to {interval} seconds")
        
    def get_network_connections_with_stats(self):
        """Get network connections with statistics using netstat"""
        connections_by_pid = defaultdict(lambda: {'sent': 0, 'recv': 0, 'connections': []})
        
        try:
            # Use netstat to get connection statistics
            # This is more reliable on Windows
            # CREATE_NO_WINDOW flag to prevent console window from appearing
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            
            result = subprocess.run(
                ['netstat', '-ano', '-p', 'TCP'],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            lines = result.stdout.strip().split('\n')
            
            for line in lines[4:]:  # Skip header lines
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        pid = int(parts[-1])
                        proto = parts[0]
                        local_addr = parts[1]
                        foreign_addr = parts[2]
                        state = parts[3] if len(parts) > 3 else ''
                        
                        if state == 'ESTABLISHED':
                            connections_by_pid[pid]['connections'].append({
                                'proto': proto,
                                'local': local_addr,
                                'foreign': foreign_addr,
                                'state': state
                            })
                    except (ValueError, IndexError):
                        continue
            
            # Also get UDP connections
            result_udp = subprocess.run(
                ['netstat', '-ano', '-p', 'UDP'],
                capture_output=True,
                text=True,
                timeout=10,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            lines_udp = result_udp.stdout.strip().split('\n')
            
            for line in lines_udp[4:]:  # Skip header lines
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        pid = int(parts[-1])
                        proto = parts[0]
                        local_addr = parts[1]
                        
                        connections_by_pid[pid]['connections'].append({
                            'proto': proto,
                            'local': local_addr,
                            'foreign': '*:*',
                            'state': 'LISTENING'
                        })
                    except (ValueError, IndexError):
                        continue
                        
        except Exception as e:
            print(f"Netstat error: {e}")
        
        return connections_by_pid
    
    def estimate_bandwidth_by_connections(self, total_sent, total_recv, connections_by_pid):
        """Estimate bandwidth per process based on connection count (approximation)"""
        process_stats = {}
        
        # Get total connection count
        total_connections = sum(len(data['connections']) for data in connections_by_pid.values())
        
        if total_connections == 0:
            return process_stats
        
        # Distribute bandwidth proportionally to connection count
        # This is an approximation, not exact measurement
        for pid, conn_data in connections_by_pid.items():
            if len(conn_data['connections']) > 0:
                try:
                    proc = psutil.Process(pid)
                    name = proc.name()
                    
                    # Weight by connection count
                    weight = len(conn_data['connections']) / total_connections
                    
                    estimated_sent = int(total_sent * weight)
                    estimated_recv = int(total_recv * weight)
                    
                    process_stats[pid] = {
                        'name': name,
                        'bytes_sent': estimated_sent,
                        'bytes_recv': estimated_recv,
                        'total_bytes': estimated_sent + estimated_recv,
                        'connection_count': len(conn_data['connections']),
                        'connections': conn_data['connections'][:5],  # First 5 connections
                        'timestamp': datetime.now()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        
        return process_stats
    
    def format_bytes(self, bytes_value):
        """Convert bytes to human readable format"""
        if bytes_value == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def start_monitoring(self):
        """Start monitoring"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.last_measurement_time = datetime.now()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Network monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Network monitoring stopped")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        # Get initial network I/O
        prev_net_io = psutil.net_io_counters()
        
        while self.monitoring:
            try:
                # Wait for the interval
                time.sleep(self.update_interval)
                
                # Get current network I/O
                current_net_io = psutil.net_io_counters()
                
                # Calculate difference
                bytes_sent = current_net_io.bytes_sent - prev_net_io.bytes_sent
                bytes_recv = current_net_io.bytes_recv - prev_net_io.bytes_recv
                
                # Get connections
                connections_by_pid = self.get_network_connections_with_stats()
                
                # Estimate bandwidth per process
                process_stats = self.estimate_bandwidth_by_connections(bytes_sent, bytes_recv, connections_by_pid)
                
                # Update cumulative data
                for pid, stats in process_stats.items():
                    self.process_data[pid]['bytes_sent'] += stats['bytes_sent']
                    self.process_data[pid]['bytes_recv'] += stats['bytes_recv']
                    self.process_data[pid]['last_update'] = datetime.now()
                    self.process_data[pid]['name'] = stats['name']
                    self.process_data[pid]['last_connections'] = stats.get('connection_count', 0)
                
                # Display results
                self._display_results(bytes_sent, bytes_recv, process_stats)
                
                # Update previous data
                prev_net_io = current_net_io
                self.last_measurement_time = datetime.now()
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait 1 minute on error
    
    def _display_results(self, total_sent, total_recv, process_stats):
        """Display results"""
        print(f"\n{'='*80}")
        print(f"Network Usage Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        print(f"Total Traffic (last 3 min): Sent: {self.format_bytes(total_sent)} | Recv: {self.format_bytes(total_recv)}")
        print(f"\nEstimated Per-Process Usage (based on connection count):")
        print(f"{'-'*80}")
        
        if process_stats:
            # Sort by total bytes
            sorted_stats = sorted(process_stats.items(), 
                                key=lambda x: x[1]['total_bytes'], reverse=True)
            
            for i, (pid, data) in enumerate(sorted_stats[:20], 1):
                print(f"{i:>2}. PID: {pid:>6} | {data['name']:<25}")
                print(f"    Sent: {self.format_bytes(data['bytes_sent']):>12} | "
                      f"Recv: {self.format_bytes(data['bytes_recv']):>12} | "
                      f"Connections: {data['connection_count']:>3}")
        else:
            print("No active network connections detected")
    
    def get_current_data(self):
        """Get current monitoring data"""
        return dict(self.process_data)
    
    def save_data_to_file(self, filename="network_usage.json"):
        """Save data to file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'processes': {}
            }
            
            for pid, proc_data in self.process_data.items():
                data['processes'][str(pid)] = {
                    'name': proc_data.get('name', 'Unknown'),
                    'bytes_sent': proc_data['bytes_sent'],
                    'bytes_recv': proc_data['bytes_recv'],
                    'total_bytes': proc_data['bytes_sent'] + proc_data['bytes_recv'],
                    'last_update': proc_data['last_update'].isoformat() if proc_data['last_update'] else None,
                    'last_connections': proc_data.get('last_connections', 0)
                }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"Data saved to {filename}")
            return True
            
        except Exception as e:
            print(f"Data save error: {e}")
            return False

class NetworkMonitorGUI:
    def __init__(self, silent_mode=False):
        self.monitor = NetworkMonitorV2()
        self.root = tk.Tk()
        self.root.title("Tethering Network Monitor V2")
        self.root.geometry("1200x750")
        self.silent_mode = silent_mode  # Silent mode suppresses popups
        self.is_minimized = False  # Track minimized state
        self.tray_icon = None  # System tray icon
        
        # Prevent window from flashing when minimized
        self.root.attributes('-topmost', False)
        
        # Windows specific: Force taskbar icon to persist
        try:
            import ctypes
            # Set proper window style to ensure taskbar icon persists
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            
            # Wait for window to be created
            self.root.update_idletasks()
            
            # Get window handle
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if not hwnd:
                hwnd = self.root.winfo_id()
            
            if hwnd:
                # Ensure window appears in taskbar
                current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | WS_EX_APPWINDOW)
                
                # Force window to show in taskbar
                ctypes.windll.user32.ShowWindow(hwnd, 5)  # SW_SHOW
        except Exception as e:
            print(f"Taskbar icon setup warning: {e}")
        
        # Setup system tray icon
        if HAS_PYSTRAY:
            self.setup_tray_icon()
        
        # Bind minimize/restore events
        self.root.bind('<Unmap>', self.on_minimize)
        self.root.bind('<Map>', self.on_restore)
        
        # Override window close to minimize to tray instead
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Override iconify to minimize to tray
        self.original_iconify = self.root.iconify
        self.root.iconify = self.custom_iconify
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Tethering Network Monitor V2", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 5))
        
        # Info label
        self.info_label = ttk.Label(main_frame, 
                              text="Monitors network usage per application at selected intervals (estimated based on connection count)",
                              font=("Arial", 9), foreground="blue")
        self.info_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))
        
        # Interval selection frame
        interval_frame = ttk.LabelFrame(main_frame, text="Monitoring Interval", padding="10")
        interval_frame.grid(row=2, column=0, columnspan=4, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(interval_frame, text="Select interval:").grid(row=0, column=0, padx=(0, 10))
        
        self.interval_var = tk.StringVar(value="180")
        
        intervals = [
            ("30 seconds (Real-time)", "30"),
            ("1 minute (Recommended)", "60"),
            ("3 minutes (Balanced)", "180"),
            ("5 minutes (Light)", "300")
        ]
        
        for i, (text, value) in enumerate(intervals):
            rb = ttk.Radiobutton(interval_frame, text=text, variable=self.interval_var, 
                                value=value, command=self.on_interval_change)
            rb.grid(row=0, column=i+1, padx=5)
        
        # Load info
        load_info_label = ttk.Label(interval_frame, 
                                    text="⚡30s: High precision | ⭐1min: Best balance | 🔋3-5min: Low CPU usage",
                                    font=("Arial", 8), foreground="gray")
        load_info_label.grid(row=1, column=0, columnspan=5, pady=(5, 0))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=4, pady=(0, 10))
        
        self.start_button = ttk.Button(button_frame, text="Start Monitoring", 
                                      command=self.start_monitoring)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_frame, text="Stop Monitoring", 
                                     command=self.stop_monitoring, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.save_button = ttk.Button(button_frame, text="Save Data", 
                                     command=self.save_data)
        self.save_button.grid(row=0, column=2, padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, text="Clear Data", 
                                     command=self.clear_data)
        self.clear_button.grid(row=0, column=3, padx=(0, 10))
        
        # Silent mode toggle
        self.silent_var = tk.BooleanVar(value=self.silent_mode)
        self.silent_check = ttk.Checkbutton(button_frame, text="Silent Mode (No popups)", 
                                           variable=self.silent_var)
        self.silent_check.grid(row=0, column=4)
        
        # Status and stats frame
        stats_frame = ttk.LabelFrame(main_frame, text="Network Statistics", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=4, pady=(0, 10), sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(stats_frame, text="Monitoring Stopped", 
                                     foreground="red", font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))
        
        self.process_count_label = ttk.Label(stats_frame, text="Active Processes: 0")
        self.process_count_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 20))
        
        self.last_update_label = ttk.Label(stats_frame, text="Last Measurement: Never")
        self.last_update_label.grid(row=1, column=1, sticky=tk.W)
        
        # Results display Treeview
        tree_frame = ttk.LabelFrame(main_frame, text="Per-Application Network Usage (Cumulative)", padding="5")
        tree_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        columns = ('Rank', 'PID', 'App Name', 'Sent', 'Received', 'Total', 'Connections', 'Last Update')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=22)
        
        # Column settings
        self.tree.heading('Rank', text='#')
        self.tree.heading('PID', text='PID')
        self.tree.heading('App Name', text='App Name')
        self.tree.heading('Sent', text='Sent')
        self.tree.heading('Received', text='Received')
        self.tree.heading('Total', text='Total')
        self.tree.heading('Connections', text='Connections')
        self.tree.heading('Last Update', text='Last Update')
        
        # Column widths
        self.tree.column('Rank', width=40)
        self.tree.column('PID', width=70)
        self.tree.column('App Name', width=250)
        self.tree.column('Sent', width=120)
        self.tree.column('Received', width=120)
        self.tree.column('Total', width=120)
        self.tree.column('Connections', width=100)
        self.tree.column('Last Update', width=150)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Note label
        note_label = ttk.Label(main_frame, 
                              text="Note: Per-app usage is estimated based on connection count. For exact measurements, use tools like GlassWire or Wireshark.",
                              font=("Arial", 8), foreground="gray")
        note_label.grid(row=6, column=0, columnspan=4, pady=(5, 0))
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Update timer
        self.update_timer()
    
    def setup_tray_icon(self):
        """Setup system tray icon"""
        if not HAS_PYSTRAY:
            return
        
        # Create icon image
        image = self.create_tray_icon_image()
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("表示", self.show_window, default=True),
            pystray.MenuItem("最小化", self.hide_to_tray),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("監視開始", self.start_monitoring_from_tray),
            pystray.MenuItem("監視停止", self.stop_monitoring_from_tray),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("終了", self.quit_app)
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon("network_monitor", image, "通信量監視", menu)
        
        # Run tray icon in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def create_tray_icon_image(self):
        """Create system tray icon image"""
        # Create a simple icon
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='white')
        dc = ImageDraw.Draw(image)
        
        # Draw network icon
        dc.rectangle([10, 10, 54, 54], outline='blue', width=3)
        dc.line([20, 40, 30, 25, 40, 35, 50, 20], fill='green', width=3)
        
        return image
    
    def show_window(self, icon=None, item=None):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.is_minimized = False
    
    def hide_to_tray(self, icon=None, item=None):
        """Hide window to system tray"""
        if HAS_PYSTRAY:
            self.root.withdraw()
            self.is_minimized = True
        else:
            self.root.iconify()
            self.is_minimized = True
    
    def start_monitoring_from_tray(self, icon=None, item=None):
        """Start monitoring from tray menu"""
        if not self.monitor.monitoring:
            self.root.after(0, lambda: self.start_button.invoke())
    
    def stop_monitoring_from_tray(self, icon=None, item=None):
        """Stop monitoring from tray menu"""
        if self.monitor.monitoring:
            self.root.after(0, lambda: self.stop_button.invoke())
    
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        self.monitor.stop_monitoring()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def custom_iconify(self):
        """Custom iconify - minimize to system tray"""
        self.is_minimized = True
        if HAS_PYSTRAY:
            # Minimize to tray instead of taskbar
            self.hide_to_tray()
        else:
            # Fallback to normal minimize
            self.original_iconify()
    
    def on_minimize(self, event):
        """Handle minimize event"""
        if event.widget == self.root:
            self.is_minimized = True
            # When minimized, hide to tray if available
            if HAS_PYSTRAY:
                self.root.after(100, self.hide_to_tray)
    
    def on_restore(self, event):
        """Handle restore event"""
        if event.widget == self.root:
            self.is_minimized = False
    
    def on_closing(self):
        """Handle window close button - minimize to tray instead of closing"""
        if HAS_PYSTRAY:
            # Minimize to tray instead of closing
            if not self.silent_var.get():
                result = messagebox.askyesnocancel(
                    "最小化", 
                    "システムトレイに最小化しますか？\n\n"
                    "はい: トレイに最小化\n"
                    "いいえ: アプリを終了\n"
                    "キャンセル: 何もしない"
                )
                if result is True:  # Yes - minimize to tray
                    self.hide_to_tray()
                elif result is False:  # No - quit
                    if self.monitor.monitoring:
                        self.monitor.stop_monitoring()
                    self.quit_app()
                # None (Cancel) - do nothing
            else:
                # Silent mode - always minimize to tray
                self.hide_to_tray()
        else:
            # No tray support - ask to quit
            if self.monitor.monitoring:
                if messagebox.askokcancel("終了", "監視中です。終了しますか？"):
                    self.monitor.stop_monitoring()
                    self.root.quit()
                    self.root.destroy()
            else:
                self.root.quit()
                self.root.destroy()
    
    def on_interval_change(self):
        """Handle interval change"""
        if self.monitor.monitoring:
            messagebox.showwarning("Warning", 
                                 "Please stop monitoring before changing the interval.\n"
                                 "The new interval will be applied when you restart monitoring.")
            return
        
        interval = int(self.interval_var.get())
        self.monitor.set_update_interval(interval)
        
        # Update info label
        interval_text = {
            30: "30 seconds",
            60: "1 minute",
            180: "3 minutes",
            300: "5 minutes"
        }.get(interval, f"{interval} seconds")
        
        self.info_label.config(
            text=f"Monitors network usage per application every {interval_text} (estimated based on connection count)"
        )
        
    def start_monitoring(self):
        """Start monitoring"""
        try:
            # Set the interval before starting
            interval = int(self.interval_var.get())
            self.monitor.set_update_interval(interval)
            
            self.monitor.start_monitoring()
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            # Disable interval selection during monitoring
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.LabelFrame) and "Monitoring Interval" in str(subchild):
                            for rb in subchild.winfo_children():
                                if isinstance(rb, ttk.Radiobutton):
                                    rb.config(state="disabled")
            
            interval_text = {
                30: "30 seconds",
                60: "1 minute",
                180: "3 minutes",
                300: "5 minutes"
            }.get(interval, f"{interval} seconds")
            
            self.status_label.config(text=f"Monitoring... (updates every {interval_text})", foreground="green")
            
            # Show popup only if not in silent mode
            if not self.silent_var.get():
                messagebox.showinfo("Started", 
                                  f"Network monitoring started.\n\n"
                                  f"Monitoring interval: {interval_text}\n"
                                  f"Per-app usage is estimated based on connection count.\n"
                                  f"First measurement will appear in {interval_text}.")
        except Exception as e:
            messagebox.showerror("Error", f"Start monitoring error: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            self.monitor.stop_monitoring()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            
            # Re-enable interval selection
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ttk.LabelFrame) and "Monitoring Interval" in str(subchild):
                            for rb in subchild.winfo_children():
                                if isinstance(rb, ttk.Radiobutton):
                                    rb.config(state="normal")
            
            self.status_label.config(text="Monitoring Stopped", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", f"Stop monitoring error: {e}")
    
    def save_data(self):
        """Save data"""
        try:
            filename = f"network_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if self.monitor.save_data_to_file(filename):
                if not self.silent_var.get():
                    messagebox.showinfo("Save Complete", f"Data saved to {filename}")
            else:
                messagebox.showerror("Error", "Failed to save data")
        except Exception as e:
            messagebox.showerror("Error", f"Save error: {e}")
    
    def clear_data(self):
        """Clear data"""
        if messagebox.askyesno("Confirm", "Clear all cumulative data?"):
            self.monitor.process_data.clear()
            self.update_display()
            if not self.silent_var.get():
                messagebox.showinfo("Complete", "Data cleared")
    
    def update_display(self):
        """Update display"""
        # Skip update if minimized to prevent focus stealing
        if self.is_minimized:
            return
        
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get current data
        data = self.monitor.get_current_data()
        
        # Update statistics
        self.process_count_label.config(text=f"Active Processes: {len(data)}")
        
        if self.monitor.last_measurement_time:
            self.last_update_label.config(
                text=f"Last Measurement: {self.monitor.last_measurement_time.strftime('%H:%M:%S')}"
            )
        
        # Display processes
        if data:
            # Sort by total bytes
            sorted_data = sorted(data.items(), 
                               key=lambda x: x[1]['bytes_sent'] + x[1]['bytes_recv'], 
                               reverse=True)
            
            for rank, (pid, proc_data) in enumerate(sorted_data, 1):
                total_bytes = proc_data['bytes_sent'] + proc_data['bytes_recv']
                
                if total_bytes > 0:
                    # Get process name
                    try:
                        proc = psutil.Process(int(pid))
                        name = proc.name()
                    except:
                        name = proc_data.get('name', 'Unknown')
                    
                    last_update = proc_data['last_update'].strftime('%H:%M:%S') if proc_data['last_update'] else 'Never'
                    
                    self.tree.insert('', 'end', values=(
                        rank,
                        pid,
                        name,
                        self.monitor.format_bytes(proc_data['bytes_sent']),
                        self.monitor.format_bytes(proc_data['bytes_recv']),
                        self.monitor.format_bytes(total_bytes),
                        proc_data.get('last_connections', 0),
                        last_update
                    ))
    
    def update_timer(self):
        """Update display periodically"""
        # Only update display if not minimized
        if not self.is_minimized:
            self.update_display()
        self.root.after(5000, self.update_timer)  # Update every 5 seconds
    
    def prevent_focus_stealing(self):
        """Prevent window from stealing focus on Windows"""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Get window handle
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if hwnd:
                # Set window style to prevent activation
                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                
                current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, current_style | WS_EX_NOACTIVATE)
        except Exception as e:
            print(f"Focus prevention setup failed (non-critical): {e}")
    
    def run(self):
        """Run app"""
        try:
            # Prevent focus stealing after window is created
            self.root.after(500, self.prevent_focus_stealing)
            
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()
            sys.exit(0)

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Tethering Network Monitor App V2')
    parser.add_argument('--silent', action='store_true', 
                       help='Start in silent mode (no popup messages)')
    parser.add_argument('--minimized', action='store_true',
                       help='Start minimized to taskbar')
    args = parser.parse_args()
    
    print("Starting Tethering Network Monitor App V2...")
    print("This app monitors network usage per application")
    print("Per-app usage is ESTIMATED based on connection count.")
    
    if args.silent:
        print("Silent mode: Popup messages disabled")
    
    print()
    
    # Check admin privileges
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Warning: Running with admin privileges is recommended")
            print("Some processes may not be accessible without admin rights.")
            print()
    except:
        pass
    
    # Start GUI app
    app = NetworkMonitorGUI(silent_mode=args.silent)
    
    # Start minimized if requested
    if args.minimized:
        app.root.iconify()
    
    app.run()

if __name__ == "__main__":
    main()
