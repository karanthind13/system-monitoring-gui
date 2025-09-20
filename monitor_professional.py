import tkinter as tk
from tkinter import ttk, messagebox
import psutil, GPUtil, datetime, csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ProfessionalSystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("System Diagnostics & Monitoring Tool - Professional")
        self.root.geometry("1000x650")
        self.running = True
        self.logging = False
        self.log_file = None
        self.cpu_history, self.ram_history, self.disk_history = [], [], []

        # --- Create Tabs ---
        self.tab_control = ttk.Notebook(root)
        self.overview_tab = ttk.Frame(self.tab_control)
        self.process_tab = ttk.Frame(self.tab_control)
        self.chart_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.overview_tab, text='Overview')
        self.tab_control.add(self.process_tab, text='Processes')
        self.tab_control.add(self.chart_tab, text='Charts')
        self.tab_control.pack(expand=1, fill='both')

        # --- Overview Tab ---
        self.create_overview_tab()
        self.create_process_tab()
        self.create_chart_tab()

        # --- Start updates ---
        self.update_stats()

    def create_overview_tab(self):
        # CPU
        tk.Label(self.overview_tab, text="CPU Usage", font=("Arial",12,"bold")).pack(pady=5)
        self.cpu_bar = ttk.Progressbar(self.overview_tab,length=500,maximum=100)
        self.cpu_bar.pack()

        # RAM
        tk.Label(self.overview_tab, text="RAM Usage", font=("Arial",12,"bold")).pack(pady=5)
        self.ram_bar = ttk.Progressbar(self.overview_tab,length=500,maximum=100)
        self.ram_bar.pack()

        # Disk
        tk.Label(self.overview_tab, text="Disk Usage", font=("Arial",12,"bold")).pack(pady=5)
        self.disk_bar = ttk.Progressbar(self.overview_tab,length=500,maximum=100)
        self.disk_bar.pack()

        # Network
        tk.Label(self.overview_tab, text="Network Usage (KB/s)", font=("Arial",12,"bold")).pack(pady=5)
        self.network_label = tk.Label(self.overview_tab, text="Up: 0  Down: 0", font=("Arial",10))
        self.network_label.pack(pady=2)

        # Battery
        tk.Label(self.overview_tab, text="Battery", font=("Arial",12,"bold")).pack(pady=5)
        self.battery_label = tk.Label(self.overview_tab, text="Battery info not available", font=("Arial",10))
        self.battery_label.pack(pady=2)

        # Buttons
        self.btn_frame = tk.Frame(self.overview_tab)
        self.btn_frame.pack(pady=15)
        self.log_btn = tk.Button(self.btn_frame, text="Start Logging", command=self.toggle_logging, width=15)
        self.log_btn.grid(row=0,column=0,padx=10)
        self.quit_btn = tk.Button(self.btn_frame, text="Exit", command=self.quit_app, width=15)
        self.quit_btn.grid(row=0,column=1,padx=10)

    def create_process_tab(self):
        # Table for top processes
        columns = ("PID","Name","CPU %","Memory %")
        self.tree = ttk.Treeview(self.process_tab, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col,width=120)
        self.tree.pack(expand=True, fill='both', pady=10)

    def create_chart_tab(self):
        fig = Figure(figsize=(8,3), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_title("CPU, RAM, Disk Usage History")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Usage %")
        self.cpu_line, = self.ax.plot([], [], "g-", label="CPU")
        self.ram_line, = self.ax.plot([], [], "b-", label="RAM")
        self.disk_line, = self.ax.plot([], [], "r-", label="Disk")
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_tab)
        self.canvas.get_tk_widget().pack(expand=True, fill='both', pady=10)

    def update_stats(self):
        if not self.running:
            return

        # System metrics
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        net_io = psutil.net_io_counters()
        up_speed = net_io.bytes_sent / 1024
        down_speed = net_io.bytes_recv / 1024

        # Update progress bars
        self.cpu_bar["value"] = cpu
        self.ram_bar["value"] = ram
        self.disk_bar["value"] = disk

        # Network label
        self.network_label.config(text=f"Up: {int(up_speed)} KB/s  Down: {int(down_speed)} KB/s")

        # Battery
        if hasattr(psutil, "sensors_battery"):
            bat = psutil.sensors_battery()
            if bat:
                status = "Charging" if bat.power_plugged else "Not Charging"
                self.battery_label.config(text=f"{bat.percent}% - {status}")
            else:
                self.battery_label.config(text="Battery info not available")

        # Alerts
        if cpu>85: messagebox.showwarning("High CPU Usage",f"CPU usage is at {cpu}%!")
        if ram>90: messagebox.showwarning("High Memory Usage",f"Memory usage is at {ram}%!")

        # Logging
        if self.logging:
            self.write_log(cpu, ram, disk, up_speed, down_speed, bat.percent if bat else "N/A")

        # Update CPU/RAM/Disk history
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        self.disk_history.append(disk)
        if len(self.cpu_history)>30:
            self.cpu_history.pop(0); self.ram_history.pop(0); self.disk_history.pop(0)

        self.cpu_line.set_xdata(range(len(self.cpu_history)))
        self.cpu_line.set_ydata(self.cpu_history)
        self.ram_line.set_xdata(range(len(self.ram_history)))
        self.ram_line.set_ydata(self.ram_history)
        self.disk_line.set_xdata(range(len(self.disk_history)))
        self.disk_line.set_ydata(self.disk_history)
        self.ax.set_xlim(0,max(30,len(self.cpu_history)))
        self.ax.set_ylim(0,100)
        self.canvas.draw()

        # Update process table
        for i in self.tree.get_children():
            self.tree.delete(i)
        for proc in psutil.process_iter(['pid','name','cpu_percent','memory_percent']):
            self.tree.insert('',tk.END,values=(proc.info['pid'],proc.info['name'],proc.info['cpu_percent'],round(proc.info['memory_percent'],2)))

        self.root.after(1000,self.update_stats)

    def toggle_logging(self):
        if not self.logging:
            self.log_file = open("system_log_professional.csv","a",newline="")
            self.csv_writer = csv.writer(self.log_file)
            self.csv_writer.writerow(["Timestamp","CPU %","RAM %","Disk %","Upload KB/s","Download KB/s","Battery %"])
            self.logging = True
            self.log_btn.config(text="Stop Logging")
        else:
            self.logging = False
            if self.log_file: self.log_file.close()
            self.log_btn.config(text="Start Logging")

    def write_log(self,cpu,ram,disk,up,down,battery):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.csv_writer.writerow([timestamp,cpu,ram,disk,int(up),int(down),battery])

    def quit_app(self):
        self.running=False
        if self.logging and self.log_file: self.log_file.close()
        self.root.destroy()

if __name__=="__main__":
    root = tk.Tk()
    app = ProfessionalSystemMonitor(root)
    root.mainloop()
