"""
System Diagnostics & Monitoring Tool - Part 2 (Tkinter)

Features included in this file:
 - CPU, RAM, Disk usage with ttk Progressbars and color-coded thresholds
 - Scrollable Treeview showing top processes (PID, Name, Memory%)
 - Adjustable refresh rate and Pause/Resume auto-refresh
 - Export sampled stats to CSV (logs)
 - Terminate selected process (with confirmation)

Dependencies:
 - psutil (pip install psutil)

Run:
    python system_monitor_part2.py

Notes:
 - This file is designed as a polished, ready-to-run Part 2.
 - Some progressbar color changes are platform-dependent; they work well on Windows and many Linux themes.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import datetime
import csv
import traceback


def bytes_to_human(n):
    """Return human friendly byte size."""
    symbols = ('B', 'KB', 'MB', 'GB', 'TB', 'PB')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i * 10)
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.2f %s' % (value, s)
    return '0 B'


class SystemMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Diagnostics & Monitoring Tool — Part 2")
        self.root.geometry("900x640")

        # Configuration / state
        self.refresh_rate_ms = tk.IntVar(value=2000)  # default 2000 ms
        self.auto_refresh = tk.BooleanVar(value=True)
        self.log = []  # list of dicts with timestamp, cpu, mem, disk
        self.alerts_shown = {"cpu": False, "mem": False, "disk": False}
        self.alert_thresholds = {"cpu": 85.0, "mem": 85.0, "disk": 95.0}

        # Styles
        self.style = ttk.Style(self.root)
        try:
            # keep a neutral theme so style changes are more predictable
            self.style.theme_use('default')
        except Exception:
            pass

        # Create UI
        self._create_top_metrics_frame()
        self._create_controls_frame()
        self._create_processes_frame()
        self._create_statusbar()

        # Start updates
        self.root.after(1000, self.update_stats)

    def _create_top_metrics_frame(self):
        frame = ttk.Frame(self.root, padding=(10, 8))
        frame.pack(side='top', fill='x')

        # CPU
        cpu_label = ttk.Label(frame, text="CPU Usage", font=(None, 11, 'bold'))
        cpu_label.grid(row=0, column=0, sticky='w')
        self.cpu_progress = ttk.Progressbar(frame, style='CPU.Horizontal.TProgressbar', orient='horizontal', length=480, mode='determinate')
        self.cpu_progress.grid(row=1, column=0, sticky='w', pady=(2, 8))
        self.cpu_value = ttk.Label(frame, text="0%", width=10)
        self.cpu_value.grid(row=1, column=1, sticky='w', padx=(8, 0))

        # RAM
        ram_label = ttk.Label(frame, text="RAM Usage", font=(None, 11, 'bold'))
        ram_label.grid(row=2, column=0, sticky='w')
        self.ram_progress = ttk.Progressbar(frame, style='RAM.Horizontal.TProgressbar', orient='horizontal', length=480, mode='determinate')
        self.ram_progress.grid(row=3, column=0, sticky='w', pady=(2, 8))
        self.ram_value = ttk.Label(frame, text="0%", width=30)
        self.ram_value.grid(row=3, column=1, sticky='w', padx=(8, 0))

        # Disk
        disk_label = ttk.Label(frame, text="Disk Usage (root partition)", font=(None, 11, 'bold'))
        disk_label.grid(row=4, column=0, sticky='w')
        self.disk_progress = ttk.Progressbar(frame, style='Disk.Horizontal.TProgressbar', orient='horizontal', length=480, mode='determinate')
        self.disk_progress.grid(row=5, column=0, sticky='w', pady=(2, 8))
        self.disk_value = ttk.Label(frame, text="0%", width=30)
        self.disk_value.grid(row=5, column=1, sticky='w', padx=(8, 0))

        # Provide a little spacing column expand
        frame.grid_columnconfigure(0, weight=1)

    def _create_controls_frame(self):
        frame = ttk.Frame(self.root, padding=(10, 6))
        frame.pack(side='top', fill='x')

        # Refresh rate control
        ttk.Label(frame, text="Refresh rate (ms):").grid(row=0, column=0, sticky='w')
        self.refresh_spin = ttk.Spinbox(frame, from_=500, to=10000, increment=250, textvariable=self.refresh_rate_ms, width=8)
        self.refresh_spin.grid(row=0, column=1, sticky='w', padx=(6, 14))

        # Auto-refresh toggle
        self.auto_cb = ttk.Checkbutton(frame, text="Auto-refresh", variable=self.auto_refresh)
        self.auto_cb.grid(row=0, column=2, sticky='w')

        # Immediate refresh
        refresh_btn = ttk.Button(frame, text="Refresh Now", command=self.update_stats_now)
        refresh_btn.grid(row=0, column=3, sticky='w', padx=(10, 6))

        # Export CSV
        export_btn = ttk.Button(frame, text="Export log to CSV", command=self.export_csv)
        export_btn.grid(row=0, column=4, sticky='w', padx=(6, 6))

        # Terminate process
        self.terminate_btn = ttk.Button(frame, text="Terminate Selected Process", command=self.terminate_selected_process)
        self.terminate_btn.grid(row=0, column=5, sticky='w', padx=(6, 6))
        self.terminate_btn.state(['disabled'])

        # Clear logs
        clear_btn = ttk.Button(frame, text="Clear Logs", command=self.clear_logs)
        clear_btn.grid(row=0, column=6, sticky='w', padx=(6, 6))

        frame.grid_columnconfigure(7, weight=1)

    def _create_processes_frame(self):
        frame = ttk.Frame(self.root, padding=(10, 6))
        frame.pack(side='top', fill='both', expand=True)

        title = ttk.Label(frame, text="Running Processes (top by memory %)", font=(None, 11, 'bold'))
        title.pack(side='top', anchor='w')

        columns = ('pid', 'name', 'mem')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('pid', text='PID')
        self.tree.heading('name', text='Name')
        self.tree.heading('mem', text='Memory %')
        self.tree.column('pid', width=70, anchor='center')
        self.tree.column('name', width=520, anchor='w')
        self.tree.column('mem', width=100, anchor='e')

        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)

        # bind selection and double-click
        self.tree.bind('<<TreeviewSelect>>', self._on_process_select)
        self.tree.bind('<Double-1>', self._on_process_double_click)

    def _create_statusbar(self):
        self.status = ttk.Label(self.root, text='Last updated: -', relief='sunken', anchor='w')
        self.status.pack(side='bottom', fill='x')

    def _set_progress_color(self, style_name, percent):
        # Choose a color based on percent
        if percent < 50:
            color = '#2ecc71'  # green
        elif percent < 80:
            color = '#f1c40f'  # yellow
        else:
            color = '#e74c3c'  # red
        try:
            self.style.configure(style_name, background=color)
        except Exception:
            # on some platforms this might not change; ignore
            pass

    def update_stats_now(self):
        # Force an immediate update once (does not affect auto_refresh)
        self.update_stats(force=True)

    def update_stats(self, force=False):
        # If auto-refresh is off and not forced, do nothing
        if not self.auto_refresh.get() and not force:
            return

        try:
            # --- System-wide metrics ---
            cpu = psutil.cpu_percent(interval=0.12)
            self.cpu_progress['value'] = cpu
            self.cpu_value.config(text=f"{cpu:.1f}%")
            self._set_progress_color('CPU.Horizontal.TProgressbar', cpu)

            mem = psutil.virtual_memory()
            mem_pct = mem.percent
            self.ram_progress['value'] = mem_pct
            used = bytes_to_human(mem.used)
            total = bytes_to_human(mem.total)
            self.ram_value.config(text=f"{mem_pct:.1f}%  ({used} / {total})")
            self._set_progress_color('RAM.Horizontal.TProgressbar', mem_pct)

            disk = psutil.disk_usage('/')
            disk_pct = disk.percent
            self.disk_progress['value'] = disk_pct
            self.disk_value.config(text=f"{disk_pct:.1f}%  ({bytes_to_human(disk.used)} / {bytes_to_human(disk.total)})")
            self._set_progress_color('Disk.Horizontal.TProgressbar', disk_pct)

            # --- Processes (top by memory%) ---
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    info = p.info
                    # normalize name
                    if not info.get('name'):
                        info['name'] = ''
                    procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            procs.sort(key=lambda x: x.get('memory_percent') or 0.0, reverse=True)

            # keep top N
            top_n = 30
            # update tree view
            self.tree.delete(*self.tree.get_children())
            for proc in procs[:top_n]:
                pid = proc.get('pid')
                name = proc.get('name') or ''
                mem_p = proc.get('memory_percent') or 0.0
                self.tree.insert('', 'end', values=(pid, name, f"{mem_p:.1f}"))

            # --- Logging ---
            ts = datetime.datetime.now().isoformat(timespec='seconds')
            self.log.append({'timestamp': ts, 'cpu': cpu, 'mem_pct': mem_pct, 'disk_pct': disk_pct})
            # limit log length to keep memory sane
            if len(self.log) > 5000:
                self.log = self.log[-5000:]

            # --- Alerts ---
            self._check_alerts(cpu, mem_pct, disk_pct)

            # --- Statusbar ---
            self.status.config(text=f'Last updated: {ts}   |  Samples logged: {len(self.log)}')

        except Exception as e:
            # show in statusbar and print stack for debugging
            self.status.config(text=f'Update error: {e}')
            traceback.print_exc()

        finally:
            # schedule next update if auto_refresh is on
            if self.auto_refresh.get() or force:
                try:
                    ms = max(200, int(self.refresh_rate_ms.get()))
                except Exception:
                    ms = 2000
                if self.auto_refresh.get():
                    self.root.after(ms, self.update_stats)

    def _check_alerts(self, cpu, mem, disk):
        # CPU
        if cpu >= self.alert_thresholds['cpu'] and not self.alerts_shown['cpu']:
            messagebox.showwarning('High CPU usage', f'CPU usage is high: {cpu:.1f}%')
            self.alerts_shown['cpu'] = True
        if cpu < (self.alert_thresholds['cpu'] - 5):
            self.alerts_shown['cpu'] = False

        # Memory
        if mem >= self.alert_thresholds['mem'] and not self.alerts_shown['mem']:
            messagebox.showwarning('High memory usage', f'Memory usage is high: {mem:.1f}%')
            self.alerts_shown['mem'] = True
        if mem < (self.alert_thresholds['mem'] - 5):
            self.alerts_shown['mem'] = False

        # Disk
        if disk >= self.alert_thresholds['disk'] and not self.alerts_shown['disk']:
            messagebox.showwarning('High disk usage', f'Disk usage is high: {disk:.1f}%')
            self.alerts_shown['disk'] = True
        if disk < (self.alert_thresholds['disk'] - 5):
            self.alerts_shown['disk'] = False

    def export_csv(self):
        if not self.log:
            messagebox.showinfo('No data', 'There are no logged samples to export yet.')
            return
        fn = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')], title='Save log as...')
        if not fn:
            return
        try:
            with open(fn, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'cpu', 'mem_pct', 'disk_pct'])
                writer.writeheader()
                for row in self.log:
                    writer.writerow(row)
            messagebox.showinfo('Export complete', f'Log exported to: {fn}')
        except Exception as e:
            messagebox.showerror('Export error', str(e))

    def clear_logs(self):
        if messagebox.askyesno('Clear logs', 'Are you sure you want to clear the collected samples?'):
            self.log = []
            self.status.config(text='Last updated: -   |  Samples logged: 0')

    def _on_process_select(self, event):
        sel = self.tree.selection()
        if sel:
            self.terminate_btn.state(['!disabled'])
        else:
            self.terminate_btn.state(['disabled'])

    def _on_process_double_click(self, event):
        # show details of selected process
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        pid = int(self.tree.item(item, 'values')[0])
        try:
            proc = psutil.Process(pid)
            info = {
                'pid': pid,
                'name': proc.name(),
                'exe': proc.exe() if proc.exe() else '',
                'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else '',
                'username': proc.username() if proc.username() else ''
            }
            details = '\n'.join(f"{k}: {v}" for k, v in info.items())
            messagebox.showinfo(f'Process {pid}', details)
        except Exception as e:
            messagebox.showerror('Error', f'Could not read process info: {e}')

    def terminate_selected_process(self):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        pid = int(self.tree.item(item, 'values')[0])
        if not messagebox.askyesno('Confirm terminate', f'Are you sure you want to terminate PID {pid}?'):
            return
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            messagebox.showinfo('Terminated', f'Process {pid} terminated successfully (or asked to terminate).')
            # refresh view immediately
            self.update_stats_now()
        except psutil.NoSuchProcess:
            messagebox.showinfo('Already gone', 'Process no longer exists.')
            self.update_stats_now()
        except psutil.AccessDenied:
            messagebox.showerror('Permission denied', 'Permission denied. Try running the app with elevated privileges.')
        except Exception as e:
            messagebox.showerror('Error', f'Could not terminate process: {e}')


if __name__ == '__main__':
    root = tk.Tk()
    app = SystemMonitorGUI(root)
    root.mainloop()
