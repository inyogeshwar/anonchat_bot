#!/usr/bin/env python3
"""
Simple monitoring script for the Anonymous Chat Bot
"""

import time
import psutil
import requests
from datetime import datetime

class BotMonitor:
    def __init__(self):
        self.start_time = time.time()

    def get_system_stats(self):
        """Get basic system statistics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3)
        }

    def get_uptime(self):
        """Get bot uptime"""
        uptime_seconds = time.time() - self.start_time
        uptime_minutes = uptime_seconds / 60
        uptime_hours = uptime_minutes / 60

        return {
            'seconds': uptime_seconds,
            'minutes': uptime_minutes,
            'hours': uptime_hours
        }

    def print_status(self):
        """Print current status"""
        stats = self.get_system_stats()
        uptime = self.get_uptime()

        print(f"\n{'='*50}")
        print(f"Bot Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        print(f"🕐 Uptime: {uptime['hours']:.2f} hours")
        print(f"🖥️  CPU Usage: {stats['cpu_percent']:.1f}%")
        print(f"🧠 Memory Usage: {stats['memory_percent']:.1f}% ({stats['memory_used_gb']:.2f}/{stats['memory_total_gb']:.2f} GB)")
        print(f"💾 Disk Usage: {stats['disk_percent']:.1f}% (Free: {stats['disk_free_gb']:.2f} GB)")
        print(f"{'='*50}")

    def start_monitoring(self, interval=300):  # 5 minutes
        """Start monitoring loop"""
        print("🔍 Starting bot monitoring...")
        print(f"📊 Reporting every {interval} seconds")

        while True:
            try:
                self.print_status()
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Error in monitoring: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    monitor = BotMonitor()
    monitor.start_monitoring()
