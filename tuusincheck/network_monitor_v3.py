#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Network Monitor App V3
システムトレイアイコン対応版
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
try:
    from PIL import Image, ImageDraw
    import pystray
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False
    print("警告: pystrayがインストールされていません。システムトレイ機能は利用できません。")
    print("インストール: pip install pystray pillow")

# network_monitor_v2.pyからクラスをインポート
import importlib.util
spec = importlib.util.spec_from_file_location("network_monitor_v2", "network_monitor_v2.py")
network_monitor_v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network_monitor_v2)

NetworkMonitorV2 = network_monitor_v2.NetworkMonitorV2

class NetworkMonitorGUIWithTray:
    def __init__(self, silent_mode=False, start_minimized=False):
        self.monitor = NetworkMonitorV2()
        self.root = tk.Tk()
        self.root.title("Tethering Network Monitor V3")
        self.root.geometry("1200x750")
        self.silent_mode = silent_mode
        self.is_minimized = False
        self.tray_icon = None
        self.start_minimized = start_minimized
        
        # Prevent window from flashing
        self.root.attributes('-topmost', False)
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.root.bind('<Unmap>', self.on_minimize)
        self.root.bind('<Map>', self.on_restore)
        
        # Setup UI
        self.setup_ui()
        
        # Setup system tray icon
        if HAS_PYSTRAY:
            self.setup_tray_icon()
        
        # Start minimized if requested
        if start_minimized:
            self.root.after(100, self.hide_window)
    
    def setup_ui(self):
        """Setup UI - network_monitor_v2と同じ"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Tethering Network Monitor V3", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 5))
        
        # Info label
        self.info_label = ttk.Label(main_frame, 
                              text="Monitors network usage per application at selected intervals (System tray support)",
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
        self.silent_check = ttk.Checkbutton(button_frame, text="Silent Mode", 
                                           variable=self.silent_var)
        self.silent_check.grid(row=0, column=4, padx=(0, 10))
        
        # Hide to tray button
        if HAS_PYSTRAY:
            self.hide_button = ttk.Button(button_frame, text="Hide to Tray", 
                                         command=self.hide_window)
            self.hide_button.grid(row=0, column=5)
        
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
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=18)
        
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
                              text="Tip: Click 'Hide to Tray' or close window to minimize to system tray",
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
        image = self.create_icon_image()
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window, default=True),
            pystray.MenuItem("Hide Window", self.hide_window),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Start Monitoring", self.start_monitoring),
            pystray.MenuItem("Stop Monitoring", self.stop_monitoring),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        # Create tray icon
        self.tray_icon = pystray.Icon("network_monitor", image, "Network Monitor", menu)
        
        # Run tray icon in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def create_icon_image(self):
        """Create icon image"""
        # Create a simple icon
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='white')
        dc = ImageDraw.Draw(image)
        
        # Draw network icon (simple graph)
        dc.rectangle([10, 10, 54, 54], outline='blue', width=3)
        dc.line([20, 40, 30, 25, 40, 35, 50, 20], fill='green', width=3)
        
        return image
    
    def hide_window(self):
        """Hide window to system tray"""
        if HAS_PYSTRAY:
            self.root.withdraw()
            self.is_minimized = True
        else:
            self.root.iconify()
            self.is_minimized = True
    
    def show_window(self, icon=None, item=None):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_minimized = False
    
    def on_minimize(self, event):
        """Handle minimize event"""
        if event.widget == self.root:
            self.is_minimized = True
    
    def on_restore(self, event):
        """Handle restore event"""
        if event.widget == self.root:
            self.is_minimized = False
    
    def on_interval_change(self):
        """Handle interval change"""
        if self.monitor.monitoring:
            if not self.silent_var.get():
                messagebox.showwarning("Warning", 
                                     "Please stop monitoring before changing the interval.")
            return
        
        interval = int(self.interval_var.get())
        self.monitor.set_update_interval(interval)
        
        interval_text = {
            30: "30 seconds", 60: "1 minute",
            180: "3 minutes", 300: "5 minutes"
        }.get(interval, f"{interval} seconds")
        
        self.info_label.config(
            text=f"Monitors network usage per application every {interval_text} (System tray support)"
        )
    
    def start_monitoring(self, icon=None, item=None):
        """Start monitoring"""
        try:
            interval = int(self.interval_var.get())
            self.monitor.set_update_interval(interval)
            self.monitor.start_monitoring()
            
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            
            interval_text = {
                30: "30 seconds", 60: "1 minute",
                180: "3 minutes", 300: "5 minutes"
            }.get(interval, f"{interval} seconds")
            
            self.status_label.config(text=f"Monitoring... (every {interval_text})", foreground="green")
            
            if not self.silent_var.get() and not self.is_minimized:
                messagebox.showinfo("Started", 
                                  f"Network monitoring started.\nInterval: {interval_text}")
        except Exception as e:
            messagebox.showerror("Error", f"Start error: {e}")
    
    def stop_monitoring(self, icon=None, item=None):
        """Stop monitoring"""
        try:
            self.monitor.stop_monitoring()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Monitoring Stopped", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", f"Stop error: {e}")
    
    def save_data(self):
        """Save data"""
        try:
            filename = f"network_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if self.monitor.save_data_to_file(filename):
                if not self.silent_var.get():
                    messagebox.showinfo("Saved", f"Data saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Save error: {e}")
    
    def clear_data(self):
        """Clear data"""
        if messagebox.askyesno("Confirm", "Clear all data?"):
            self.monitor.process_data.clear()
            self.update_display()
            if not self.silent_var.get():
                messagebox.showinfo("Complete", "Data cleared")
    
    def update_display(self):
        """Update display"""
        if self.is_minimized:
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        data = self.monitor.get_current_data()
        
        self.process_count_label.config(text=f"Active Processes: {len(data)}")
        
        if self.monitor.last_measurement_time:
            self.last_update_label.config(
                text=f"Last Measurement: {self.monitor.last_measurement_time.strftime('%H:%M:%S')}"
            )
        
        if data:
            sorted_data = sorted(data.items(), 
                               key=lambda x: x[1]['bytes_sent'] + x[1]['bytes_recv'], 
                               reverse=True)
            
            for rank, (pid, proc_data) in enumerate(sorted_data, 1):
                total_bytes = proc_data['bytes_sent'] + proc_data['bytes_recv']
                
                if total_bytes > 0:
                    try:
                        proc = psutil.Process(int(pid))
                        name = proc.name()
                    except:
                        name = proc_data.get('name', 'Unknown')
                    
                    last_update = proc_data['last_update'].strftime('%H:%M:%S') if proc_data['last_update'] else 'Never'
                    
                    self.tree.insert('', 'end', values=(
                        rank, pid, name,
                        self.monitor.format_bytes(proc_data['bytes_sent']),
                        self.monitor.format_bytes(proc_data['bytes_recv']),
                        self.monitor.format_bytes(total_bytes),
                        proc_data.get('last_connections', 0),
                        last_update
                    ))
    
    def update_timer(self):
        """Update display periodically"""
        if not self.is_minimized:
            self.update_display()
        self.root.after(5000, self.update_timer)
    
    def quit_app(self, icon=None, item=None):
        """Quit application"""
        self.monitor.stop_monitoring()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def run(self):
        """Run app"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Monitor V3 with System Tray')
    parser.add_argument('--silent', action='store_true', help='Silent mode')
    parser.add_argument('--minimized', action='store_true', help='Start minimized')
    args = parser.parse_args()
    
    print("Starting Network Monitor V3 (System Tray Support)...")
    
    if not HAS_PYSTRAY:
        print("\n警告: システムトレイ機能を使用するには、以下をインストールしてください:")
        print("  pip install pystray pillow")
        print()
    
    app = NetworkMonitorGUIWithTray(silent_mode=args.silent, start_minimized=args.minimized)
    app.run()

if __name__ == "__main__":
    main()
