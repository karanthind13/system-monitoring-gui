import psutil
import datetime

class SystemMonitor:
    def get_cpu_usage(self, interval=0.1):
        return psutil.cpu_percent(interval=interval)

    def get_memory_usage(self):
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent
        }

    def get_disk_usage(self):
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }

    def list_processes(self, top_n=10, sort_by="cpu"):
        processes = []
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # sort processes by cpu or memory
        key = 'cpu_percent' if sort_by == 'cpu' else 'memory_percent'
        processes = sorted(processes, key=lambda p: p.get(key, 0), reverse=True)
        return processes[:top_n]

    def snapshot(self, top_n=10):
        return {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "cpu": self.get_cpu_usage(),
            "memory": self.get_memory_usage(),
            "disk": self.get_disk_usage(),
            "processes": self.list_processes(top_n)
        }

# Helper function to convert bytes to human-readable format
def human(n):
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"

# Pretty print the snapshot
if __name__ == "__main__":
    monitor = SystemMonitor()
    snap = monitor.snapshot(top_n=5)

    print("\n=== System Diagnostics Snapshot ===")
    print("Timestamp:", snap["timestamp"])

    # CPU
    print("\n-- CPU --")
    print(f"Total CPU Usage: {snap['cpu']}%")

    # Memory
    mem = snap['memory']
    print("\n-- Memory --")
    print(f"Total: {human(mem['total'])}, Used: {human(mem['used'])}, Available: {human(mem['available'])}, Usage: {mem['percent']}%")

    # Disk
    disk = snap['disk']
    print("\n-- Disk --")
    print(f"Total: {human(disk['total'])}, Used: {human(disk['used'])}, Free: {human(disk['free'])}, Usage: {disk['percent']}%")

    # Top processes
    print("\n-- Top Processes (by CPU) --")
    for i, p in enumerate(snap['processes'], start=1):
        print(f"{i}. PID {p['pid']}, {p['name']} — CPU: {p['cpu_percent']:.1f}%  MEM: {p['memory_percent']:.2f}%")
    print("\n=== End of Snapshot ===\n")
