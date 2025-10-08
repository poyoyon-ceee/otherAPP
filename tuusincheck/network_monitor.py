#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 11 Network Monitor App
Monitor network usage of applications during tethering every 3 minutes
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

class NetworkMonitor:
    def __init__(self):
        self.monitoring = False
        self.process_connections = {}
        self.previous_net_io = None
        self.connection_history = defaultdict(lambda: {'count': 0, 'first_seen': None, 'last_seen': None})
        self.monitor_thread = None
        self.update_interval = 180  # 3 minutes interval (seconds)
        self.total_bytes_sent = 0
        self.total_bytes_recv = 0
        
    def get_network_io(self):
        """Get system-wide network I/O statistics"""
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
            print(f"Network I/O error: {e}")
            return None
    
    def get_processes_with_connections(self):
        """Get all processes that have active network connections"""
        processes = {}
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pid = proc.info['pid']
                    name = proc.info['name']
                    
                    proc_obj = psutil.Process(pid)
                    
                    # Get network connections for this process
                    try:
                        connections = proc_obj.connections(kind='inet')
                        if connections:
                            # Count connection types
                            tcp_count = sum(1 for c in connections if c.type == 1)
                            udp_count = sum(1 for c in connections if c.type == 2)
                            
                            processes[pid] = {
                                'name': name,
                                'tcp_connections': tcp_count,
                                'udp_connections': udp_count,
                                'total_connections': len(connections),
                                'timestamp': datetime.now()
                            }
                            
                            # Update connection history
                            if self.connection_history[pid]['first_seen'] is None:
                                self.connection_history[pid]['first_seen'] = datetime.now()
                            self.connection_history[pid]['last_seen'] = datetime.now()
                            self.connection_history[pid]['count'] += len(connections)
                            
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        pass
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception as e:
            print(f"Process enumeration error: {e}")
            
        return processes
    
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
        self.previous_net_io = self.get_network_io()
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
        while self.monitoring:
            try:
                # Wait for the interval
                time.sleep(self.update_interval)
                
                # Get current network I/O
                current_net_io = self.get_network_io()
                
                if current_net_io and self.previous_net_io:
                    # Calculate difference
                    bytes_sent_diff = current_net_io['bytes_sent'] - self.previous_net_io['bytes_sent']
                    bytes_recv_diff = current_net_io['bytes_recv'] - self.previous_net_io['bytes_recv']
                    
                    # Update totals
                    self.total_bytes_sent += bytes_sent_diff
                    self.total_bytes_recv += bytes_recv_diff
                    
                    # Get processes with connections
                    processes = self.get_processes_with_connections()
                    
                    # Display results
                    self._display_results(bytes_sent_diff, bytes_recv_diff, processes)
                    
                    # Update previous data
                    self.previous_net_io = current_net_io
                    self.process_connections = processes
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _display_results(self, bytes_sent, bytes_recv, processes):
        """Display results"""
        print(f"\n=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Network Usage Report ===")
        print(f"Total Traffic (last 3 min): Sent: {self.format_bytes(bytes_sent)} | Recv: {self.format_bytes(bytes_recv)}")
        print(f"Cumulative Traffic: Sent: {self.format_bytes(self.total_bytes_sent)} | Recv: {self.format_bytes(self.total_bytes_recv)}")
        print(f"\nProcesses with active connections: {len(processes)}")
        
        if processes:
            # Sort by connection count
            sorted_procs = sorted(processes.items(), 
                                key=lambda x: x[1]['total_connections'], reverse=True)
            
            print("\nTop processes by connection count:")
            for i, (pid, data) in enumerate(sorted_procs[:20], 1):
                print(f"{i:>2}. PID: {pid:>6} | {data['name']:<25} | "
                      f"TCP: {data['tcp_connections']:>3} | UDP: {data['udp_connections']:>3} | "
                      f"Total: {data['total_connections']:>3}")
    
    def get_current_data(self):
        """Get current monitoring data"""
        return {
            'process_connections': self.process_connections,
            'total_sent': self.total_bytes_sent,
            'total_recv': self.total_bytes_recv,
            'connection_history': dict(self.connection_history)
        }
    
    def save_data_to_file(self, filename="network_usage.json"):
        """Save data to file"""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'total_bytes_sent': self.total_bytes_sent,
                'total_bytes_recv': self.total_bytes_recv,
                'processes': {str(k): {
                    'name': v['name'],
                    'tcp_connections': v['tcp_connections'],
                    'udp_connections': v['udp_connections'],
                    'total_connections': v['total_connections']
                } for k, v in self.process_connections.items()},
                'connection_history': {str(k): {
                    'count': v['count'],
                    'first_seen': v['first_seen'].isoformat() if v['first_seen'] else None,
                    'last_seen': v['last_seen'].isoformat() if v['last_seen'] else None
                } for k, v in self.connection_history.items()}
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            print(f"Data saved to {filename}")
            return True
            
        except Exception as e:
            print(f"Data save error: {e}")
            return False

class NetworkMonitorGUI:
    def __init__(self):
        self.monitor = NetworkMonitor()
        self.root = tk.Tk()
        self.root.title("Tethering Network Monitor")
        self.root.geometry("1100x700")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Tethering Network Monitor", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(main_frame, 
                              text="Monitors network activity every 3 minutes and displays processes with active connections",
                              font=("Arial", 9))
        info_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=4, pady=(0, 10))
        
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
        self.clear_button.grid(row=0, column=3)
        
        # Status and stats frame
        stats_frame = ttk.LabelFrame(main_frame, text="Network Statistics", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=4, pady=(0, 10), sticky=(tk.W, tk.E))
        
        self.status_label = ttk.Label(stats_frame, text="Monitoring Stopped", 
                                     foreground="red", font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, columnspan=2, pady=(0, 5))
        
        self.total_sent_label = ttk.Label(stats_frame, text="Total Sent: 0 B")
        self.total_sent_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 20))
        
        self.total_recv_label = ttk.Label(stats_frame, text="Total Received: 0 B")
        self.total_recv_label.grid(row=1, column=1, sticky=tk.W)
        
        self.process_count_label = ttk.Label(stats_frame, text="Active Processes: 0")
        self.process_count_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        self.last_update_label = ttk.Label(stats_frame, text="Last Update: Never")
        self.last_update_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # Results display Treeview
        tree_frame = ttk.LabelFrame(main_frame, text="Processes with Network Connections", padding="5")
        tree_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        columns = ('PID', 'App Name', 'TCP Connections', 'UDP Connections', 'Total Connections', 'Last Seen')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
        
        # Column settings
        self.tree.heading('PID', text='PID')
        self.tree.heading('App Name', text='App Name')
        self.tree.heading('TCP Connections', text='TCP Connections')
        self.tree.heading('UDP Connections', text='UDP Connections')
        self.tree.heading('Total Connections', text='Total Connections')
        self.tree.heading('Last Seen', text='Last Seen')
        
        # Column widths
        self.tree.column('PID', width=80)
        self.tree.column('App Name', width=250)
        self.tree.column('TCP Connections', width=130)
        self.tree.column('UDP Connections', width=130)
        self.tree.column('Total Connections', width=140)
        self.tree.column('Last Seen', width=150)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Update timer
        self.update_timer()
        
    def start_monitoring(self):
        """Start monitoring"""
        try:
            self.monitor.start_monitoring()
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Monitoring... (updates every 3 minutes)", foreground="green")
            messagebox.showinfo("Started", "Network monitoring started. Data will be updated every 3 minutes.")
        except Exception as e:
            messagebox.showerror("Error", f"Start monitoring error: {e}")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        try:
            self.monitor.stop_monitoring()
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Monitoring Stopped", foreground="red")
        except Exception as e:
            messagebox.showerror("Error", f"Stop monitoring error: {e}")
    
    def save_data(self):
        """Save data"""
        try:
            filename = f"network_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            if self.monitor.save_data_to_file(filename):
                messagebox.showinfo("Save Complete", f"Data saved to {filename}")
            else:
                messagebox.showerror("Error", "Failed to save data")
        except Exception as e:
            messagebox.showerror("Error", f"Save error: {e}")
    
    def clear_data(self):
        """Clear data"""
        if messagebox.askyesno("Confirm", "Clear all data?"):
            self.monitor.process_connections.clear()
            self.monitor.connection_history.clear()
            self.monitor.total_bytes_sent = 0
            self.monitor.total_bytes_recv = 0
            self.update_display()
            messagebox.showinfo("Complete", "Data cleared")
    
    def update_display(self):
        """Update display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get current data
        data = self.monitor.get_current_data()
        
        # Update statistics
        self.total_sent_label.config(text=f"Total Sent: {self.monitor.format_bytes(data['total_sent'])}")
        self.total_recv_label.config(text=f"Total Received: {self.monitor.format_bytes(data['total_recv'])}")
        self.process_count_label.config(text=f"Active Processes: {len(data['process_connections'])}")
        self.last_update_label.config(text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        # Display processes
        if data['process_connections']:
            # Sort by total connections
            sorted_procs = sorted(data['process_connections'].items(), 
                                key=lambda x: x[1]['total_connections'], reverse=True)
            
            for pid, proc_data in sorted_procs:
                # Get process name
                try:
                    proc = psutil.Process(int(pid))
                    name = proc.name()
                except:
                    name = proc_data.get('name', 'Unknown')
                
                self.tree.insert('', 'end', values=(
                    pid,
                    name,
                    proc_data['tcp_connections'],
                    proc_data['udp_connections'],
                    proc_data['total_connections'],
                    proc_data['timestamp'].strftime('%H:%M:%S')
                ))
    
    def update_timer(self):
        """Update display periodically"""
        self.update_display()
        self.root.after(5000, self.update_timer)  # Update every 5 seconds
    
    def run(self):
        """Run app"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.monitor.stop_monitoring()
            sys.exit(0)
    
    def on_closing(self):
        """Handle window closing"""
        if self.monitor.monitoring:
            if messagebox.askokcancel("Quit", "Monitoring is active. Do you want to stop and quit?"):
                self.monitor.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """Main function"""
    print("Starting Tethering Network Monitor App...")
    print("This app monitors network activity every 3 minutes")
    print("and displays processes with active network connections.")
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
    app = NetworkMonitorGUI()
    app.run()

if __name__ == "__main__":
    main()