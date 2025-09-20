import customtkinter as ctk
import psutil, GPUtil, datetime, csv
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

class ProfessionalSystemMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("System Diagnostics & Monitoring Tool - Professional")
        self.root.geometry("1000x650")

        # CustomTkinter settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.running = True
        self.logging = False
        self.log_file = None
        self.cpu_history, self.ram_history, self.disk_history = [], [], []

        # --- Tabs ---
        self.tabview = ctk.CTkTabview(root, width=980, height=600)
        self.overview_tab = self.tabview.add("Overview")
        self.process_tab = self.tabview.add("Processes")
        self.chart_tab = self.tabview.add("Charts")
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        # --- Overview Tab ---
        self.create_overview_tab()

        # --- Process Tab ---
        self.create_process_tab()

        # --- Chart Tab ---
        self.create_chart_tab()

        # --- Start updates ---
        self.update_stats()

    # ----------------- Overview Tab -----------------
    def create_overview_tab(self):
        # Using card style frames for metrics
        self.cards_frame = ctk.CTkFrame(self.overview_tab)
        self.cards_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # CPU Card
        self.cpu_card = ctk.CTkFrame(self.cards_frame)
        self.cpu_card.pack(pady=10, fill="x")
        ctk.CTkLabel(self.cpu_card, text="CPU Usage", font=("Arial", 14, "bold")).pack(pady=(5,2))
        self.cpu_bar = ctk.CTkProgressBar(self.cpu_card)
        self.cpu_bar.pack(padx=10, pady=5, fill="x")

        # RAM Card
        self.ram_card = ctk.CTkFrame(self.cards_frame)
        self.ram_card.pack(pady=10, fill="x")
        ctk.CTkLabel(self.ram_card, text="RAM Usage", font=("Arial", 14, "bold")).pack(pady=(5,2))
        self.ram_bar = ctk.CTkProgressBar(self.ram_card)
        self.ram_bar.pack(padx=10, pady=5, fill="x")

        # Disk Card
        self.disk_card = ctk.CTkFrame(self.cards_frame)
        self.disk_card.pack(pady=10, fill="x")
        ctk.CTkLabel(self.disk_card, text="Disk Usage", font=("Arial", 14, "bold")).pack(pady=(5,2))
        self.disk_bar = ctk.CTkProgressBar(self.disk_card)
        self.disk_bar.pack(padx=10, pady=5, fill="x")

        # Network Card
        self.network_card = ctk.CTkFrame(self.cards_frame)
        self.network_card.pack(pady=10, fill="x")
        ctk.CTkLabel(self.network_card, text="Network Usage (KB/s)", font=("Arial", 14, "bold")).pack(pady=(5,2))
        self.network_label = ctk.CTkLabel(self.network_card, text="Up: 0  Down: 0", font=("Arial", 12))
        self.network_label.pack(pady=5)

        # Battery Card
        self.battery_card = ctk.CTkFrame(self.cards_frame)
        self.battery_card.pack(pady=10, fill="x")
        ctk.CTkLabel(self.battery_card, text="Battery", font=("Arial", 14, "bold")).pack(pady=(5,2))
        self.battery_label = ctk.CTkLabel(self.battery_card, text="Battery info not available", font=("Arial", 12))
        self.battery_label.pack(pady=5)

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.cards_frame)
        self.btn_frame.pack(pady=15)
        self.log_btn = ctk.CTkButton(self.btn_frame, text="Start Logging", width=150, command=self.toggle_logging)
        self.log_btn.grid(row=0,column=0,padx=10)
        self.quit_btn = ctk.CTkButton(self.btn_frame, text="Exit", width=150, fg_color="#FF4500", hover_color="#B22222", command=self.quit_app)
        self.quit_btn.grid(row=0,column=1,padx=10)

    # ----------------- Process Tab -----------------
    def create_process_tab(self):
        columns = ("PID","Name","CPU %","Memory %")
        self.tree_frame = ctk.CTkFrame(self.process_tab)
        self.tree_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.treeview = ttk.Treeview(self.tree_frame, columns=columns, show='headings')
        for col in columns:
            self.treeview.heading(col, text=col)
            self.treeview.column(col, width=120)
        self.treeview.pack(expand=True, fill='both')

    # ----------------- Chart Tab -----------------
    def create_chart_tab(self):
        fig = Figure(figsize=(8,3), dpi=100)
        self.ax = fig.add_subplot(111)
        self.ax.set_facecolor("#2B2B2B")
        self.ax.figure.set_facecolor("#2B2B2B")
        self.ax.tick_params(colors="white")
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.set_title("CPU, RAM, Disk Usage History", color="white")
        self.ax.set_xlabel("Time (s)", color="white")
        self.ax.set_ylabel("Usage %", color="white")
        self.cpu_line, = self.ax.plot([], [], "lime", label="CPU")
        self.ram_line, = self.ax.plot([], [], "cyan", label="RAM")
        self.disk_line, = self.ax.plot([], [], "magenta", label="Disk")
        self.ax.legend(facecolor="#444444", labelcolor="white")

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_tab)
        self.canvas.get_tk_widget().pack(expand=True, fill='both', pady=10)

    # ----------------- Update Stats -----------------
    def update_stats(self):
        if not self.running:
            return

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        net_io = psutil.net_io_counters()
        up_speed = net_io.bytes_sent / 1024
        down_speed = net_io.bytes_recv / 1024

        # Update bars
        self.cpu_bar.set(cpu / 100)
        self.ram_bar.set(ram / 100)
        self.disk_bar.set(disk / 100)

        # Update network label
        self.network_label.configure(text=f"Up: {int(up_speed)} KB/s  Down: {int(down_speed)} KB/s")

        # Battery info
        if hasattr(psutil, "sensors_battery"):
            bat = psutil.sensors_battery()
            if bat:
                status = "Charging" if bat.power_plugged else "Not Charging"
                self.battery_label.configure(text=f"{bat.percent}% - {status}")
            else:
                self.battery_label.configure(text="Battery info not available")

        # Alerts
        if cpu>85: ctk.CTkMessagebox.show_warning("High CPU Usage",f"CPU usage is at {cpu}%!")
        if ram>90: ctk.CTkMessagebox.show_warning("High Memory Usage",f"Memory usage is at {ram}%!")

        # Logging
        if self.logging:
            self.write_log(cpu, ram, disk, up_speed, down_speed, bat.percent if bat else "N/A")

        # Update history
        self.cpu_history.append(cpu)
        self.ram_history.append(ram)
        self.disk_history.append(disk)
        if len(self.cpu_history)>30:
            self.cpu_history.pop(0)
            self.ram_history.pop(0)
            self.disk_history.pop(0)

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
        for i in self.treeview.get_children():
            self.treeview.delete(i)
        for proc in psutil.process_iter(['pid','name','cpu_percent','memory_percent']):
            self.treeview.insert('',tk.END,values=(proc.info['pid'],proc.info['name'],proc.info['cpu_percent'],round(proc.info['memory_percent'],2)))

        self.root.after(1000,self.update_stats)

    # ----------------- Logging -----------------
    def toggle_logging(self):
        if not self.logging:
            self.log_file = open("system_log_customtkinter.csv","a",newline="")
            self.csv_writer = csv.writer(self.log_file)
            self.csv_writer.writerow(["Timestamp","CPU %","RAM %","Disk %","Upload KB/s","Download KB/s","Battery %"])
            self.logging = True
            self.log_btn.configure(text="Stop Logging")
        else:
            self.logging = False
            if self.log_file: self.log_file.close()
            self.log_btn.configure(text="Start Logging")

    def write_log(self,cpu,ram,disk,up,down,battery):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.csv_writer.writerow([timestamp,cpu,ram,disk,int(up),int(down),battery])

    def quit_app(self):
        self.running=False
        if self.logging and self.log_file: self.log_file.close()
        self.root.destroy()


if __name__=="__main__":
    root = ctk.CTk()
    app = ProfessionalSystemMonitor(root)
    root.mainloop()
