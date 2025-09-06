import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import socket
import sys
from datetime import datetime

class FirewallSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("小型防火墙系统 v1.0")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        # 初始化防火墙规则
        self.rules = [
            {"id": 1, "action": "允许", "protocol": "TCP", "src_ip": "192.168.1.0/24", "dst_port": "80,443", "enabled": True},
            {"id": 2, "action": "阻止", "protocol": "TCP", "src_ip": "10.0.0.5", "dst_port": "22", "enabled": True},
            {"id": 3, "action": "阻止", "protocol": "UDP", "src_ip": "any", "dst_port": "53", "enabled": False},
            {"id": 4, "action": "允许", "protocol": "ICMP", "src_ip": "any", "dst_port": "any", "enabled": True},
            {"id": 5, "action": "阻止", "protocol": "TCP", "src_ip": "any", "dst_port": "135-139", "enabled": True}
        ]
        
        # 初始化流量日志
        self.traffic_log = []
        self.log_lock = threading.Lock()
        self.running = True
        
        # 创建界面
        self.create_widgets()
        
        # 启动流量生成线程
        self.start_traffic_generator()
    
    def create_widgets(self):
        # 创建选项卡控件 - 标签页容器
        tab_control = ttk.Notebook(self.root)
        
        # 创建第一个标签页：规则管理
        rules_tab = ttk.Frame(tab_control)
        tab_control.add(rules_tab, text='规则管理')
        self.create_rules_tab(rules_tab)
        
        # 创建第二个标签页：流量监控
        traffic_tab = ttk.Frame(tab_control)
        tab_control.add(traffic_tab, text='流量监控')
        self.create_traffic_tab(traffic_tab)
        
        # 创建第三个标签页：防火墙状态
        status_tab = ttk.Frame(tab_control)
        tab_control.add(status_tab, text='防火墙状态')
        self.create_status_tab(status_tab)
        
        # 将选项卡控件放置在窗口中
        tab_control.pack(expand=1, fill="both", padx=10, pady=10)
        
        # 添加控制按钮
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(control_frame, text="启动防火墙", command=self.start_firewall, 
                 bg="#4CAF50", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
        tk.Button(control_frame, text="停止防火墙", command=self.stop_firewall, 
                 bg="#F44336", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
        tk.Button(control_frame, text="清除日志", command=self.clear_log, 
                 bg="#2196F3", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
        tk.Button(control_frame, text="添加测试规则", command=self.add_test_rule, 
                 bg="#FF9800", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
    
    def create_rules_tab(self, parent):
        # 规则列表标题
        header_frame = tk.Frame(parent)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        headers = ["ID", "启用", "动作", "协议", "源IP/掩码", "目标端口", "操作"]
        for i, header in enumerate(headers):
            tk.Label(header_frame, text=header, width=10, font=("Arial", 10, "bold"), 
                    borderwidth=1, relief="solid").grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        
        # 规则列表
        self.rule_tree = ttk.Treeview(parent, columns=("id", "enabled", "action", "protocol", "src_ip", "dst_port"), show="headings")
        self.rule_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.rule_tree.heading("id", text="ID")
        self.rule_tree.heading("enabled", text="启用")
        self.rule_tree.heading("action", text="动作")
        self.rule_tree.heading("protocol", text="协议")
        self.rule_tree.heading("src_ip", text="源IP/掩码")
        self.rule_tree.heading("dst_port", text="目标端口")
        
        self.rule_tree.column("id", width=50, anchor="center")
        self.rule_tree.column("enabled", width=50, anchor="center")
        self.rule_tree.column("action", width=60, anchor="center")
        self.rule_tree.column("protocol", width=60, anchor="center")
        self.rule_tree.column("src_ip", width=150, anchor="center")
        self.rule_tree.column("dst_port", width=100, anchor="center")
        
        # 添加规则按钮
        button_frame = tk.Frame(parent)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Button(button_frame, text="添加规则", command=self.add_rule, 
                 bg="#2196F3", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
        tk.Button(button_frame, text="删除规则", command=self.delete_rule, 
                 bg="#F44336", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
        tk.Button(button_frame, text="启用/禁用", command=self.toggle_rule, 
                 bg="#FF9800", fg="white", font=("Arial", 10)).pack(side="left", padx=5)
        
        # 初始加载规则
        self.load_rules()
    
    def load_rules(self):
        # 清除现有规则显示
        for item in self.rule_tree.get_children():
            self.rule_tree.delete(item)
        
        # 添加规则到Treeview
        for rule in self.rules:
            enabled = "是" if rule["enabled"] else "否"
            action_color = "#4CAF50" if rule["action"] == "允许" else "#F44336"
            self.rule_tree.insert("", "end", values=(
                rule["id"],
                enabled,
                rule["action"],
                rule["protocol"],
                rule["src_ip"],
                rule["dst_port"]
            ), tags=(action_color,))
        
        self.rule_tree.tag_configure("#4CAF50", background="#E8F5E9")
        self.rule_tree.tag_configure("#F44336", background="#FFEBEE")
    
    def add_rule(self):
        # 在实际应用中，这里应该有一个弹窗用于输入新规则
        new_id = max(r["id"] for r in self.rules) + 1 if self.rules else 1
        new_rule = {
            "id": new_id,
            "action": random.choice(["允许", "阻止"]),
            "protocol": random.choice(["TCP", "UDP", "ICMP"]),
            "src_ip": f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "dst_port": ",".join(str(random.randint(1, 65535)) for _ in range(random.randint(1, 3))),
            "enabled": True
        }
        self.rules.append(new_rule)
        self.load_rules()
        self.traffic_log.append(f"添加规则: ID={new_id}, {new_rule['action']} {new_rule['protocol']} from {new_rule['src_ip']} to {new_rule['dst_port']}")
    
    def add_test_rule(self):
        new_id = max(r["id"] for r in self.rules) + 1 if self.rules else 1
        new_rule = {
            "id": new_id,
            "action": "允许",
            "protocol": "TCP",
            "src_ip": "192.168.1.0/24",
            "dst_port": "8080",
            "enabled": True
        }
        self.rules.append(new_rule)
        self.load_rules()
        self.traffic_log.append(f"添加测试规则: ID={new_id}, {new_rule['action']} {new_rule['protocol']} from {new_rule['src_ip']} to {new_rule['dst_port']}")
    
    def delete_rule(self):
        selected = self.rule_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一条规则")
            return
        
        item = selected[0]
        values = self.rule_tree.item(item, "values")
        rule_id = int(values[0])
        
        # 查找并删除规则
        for i, rule in enumerate(self.rules):
            if rule["id"] == rule_id:
                del self.rules[i]
                self.traffic_log.append(f"删除规则: ID={rule_id}")
                self.load_rules()
                return
    
    def toggle_rule(self):
        selected = self.rule_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一条规则")
            return
        
        item = selected[0]
        values = self.rule_tree.item(item, "values")
        rule_id = int(values[0])
        
        # 切换规则状态
        for rule in self.rules:
            if rule["id"] == rule_id:
                rule["enabled"] = not rule["enabled"]
                self.traffic_log.append(f"{'启用' if rule['enabled'] else '禁用'}规则: ID={rule_id}")
                self.load_rules()
                return
    
    def create_traffic_tab(self, parent):
        # 流量日志标题
        header_frame = tk.Frame(parent)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        headers = ["时间", "方向", "源IP", "目标IP", "协议", "端口", "动作", "结果"]
        for i, header in enumerate(headers):
            tk.Label(header_frame, text=header, width=10, font=("Arial", 10, "bold"), 
                    borderwidth=1, relief="solid").grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        
        # 流量日志
        self.traffic_tree = ttk.Treeview(parent, columns=("time", "direction", "src_ip", "dst_ip", "protocol", "port", "action", "result"), show="headings")
        self.traffic_tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.traffic_tree.heading("time", text="时间")
        self.traffic_tree.heading("direction", text="方向")
        self.traffic_tree.heading("src_ip", text="源IP")
        self.traffic_tree.heading("dst_ip", text="目标IP")
        self.traffic_tree.heading("protocol", text="协议")
        self.traffic_tree.heading("port", text="端口")
        self.traffic_tree.heading("action", text="动作")
        self.traffic_tree.heading("result", text="结果")
        
        # 设置列宽度
        self.traffic_tree.column("time", width=80)
        self.traffic_tree.column("direction", width=50)
        self.traffic_tree.column("src_ip", width=120)
        self.traffic_tree.column("dst_ip", width=120)
        self.traffic_tree.column("protocol", width=60)
        self.traffic_tree.column("port", width=60)
        self.traffic_tree.column("action", width=90)
        self.traffic_tree.column("result", width=60)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.traffic_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.traffic_tree.configure(yscrollcommand=scrollbar.set)
        
        # 自动刷新日志的定时器
        self.update_traffic_display()
    
    def create_status_tab(self, parent):
        status_frame = tk.Frame(parent, bg="white", bd=2, relief="groove")
        status_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 状态标题
        title_frame = tk.Frame(status_frame, bg="#3F51B5")
        title_frame.pack(fill="x")
        tk.Label(title_frame, text="防火墙状态", fg="white", bg="#3F51B5", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        # 状态指标
        metrics_frame = tk.Frame(status_frame, bg="white")
        metrics_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建状态指标
        status_metrics = [
            ("状态", "运行中", "#4CAF50"),
            ("活动规则", f"{len([r for r in self.rules if r['enabled']])} 条", None),
            ("拦截包数", "142", "#F44336"),
            ("允许包数", "286", "#4CAF50"),
            ("TCP连接", "89", "#2196F3"),
            ("UDP流", "34", "#2196F3"),
            ("内存占用", "32.5 MB", "#FF9800"),
            ("CPU使用率", "12.3%", "#FF9800")
        ]
        
        rows, cols = 2, 4
        for i, (label, value, color) in enumerate(status_metrics):
            row, col = divmod(i, cols)
            metric_frame = tk.Frame(metrics_frame, bg="white")
            metric_frame.grid(row=row, column=col, padx=20, pady=20, sticky="nsew")
            
            tk.Label(metric_frame, text=label, bg="white", font=("Arial", 10)).pack()
            tk.Label(metric_frame, text=value, bg="white", font=("Arial", 14, "bold"), 
                    fg=color if color else "black").pack(pady=5)
        
        # 系统信息
        info_frame = tk.Frame(status_frame, bg="#F5F5F5", bd=1, relief="groove")
        info_frame.pack(fill="x", padx=20, pady=20)
        
        tk.Label(info_frame, text="系统信息", bg="#F5F5F5", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # 获取本机IP
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except:
            ip = "127.0.0.1"
        
        info_labels = [
            f"主机名: {hostname}",
            f"IP地址: {ip}",
            f"平台: {sys.platform}",
            f"Python版本: {sys.version.split()[0]}"
        ]
        
        for info in info_labels:
            tk.Label(info_frame, text=info, bg="#F5F5F5", anchor="w", justify="left").pack(fill="x", padx=20, pady=2)
    
    def start_traffic_generator(self):
        def traffic_thread():
            protocols = ["TCP", "UDP", "ICMP"]
            directions = ["IN", "OUT"]
            actions = ["连接尝试", "数据传输", "端口扫描", "ICMP回显请求"]
            
            while self.running:
                time.sleep(random.uniform(0.1, 1.0))
                
                direction = random.choice(directions)
                protocol = random.choice(protocols)
                port = random.randint(1, 65535)
                action = random.choice(actions)
                
                if direction == "IN":
                    src_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                    dst_ip = "192.168.1.100"
                else:
                    src_ip = "192.168.1.100"
                    dst_ip = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                
                # 模拟应用规则
                allow = random.random() < 0.7  # 70% 允许
                result = "允许" if allow else "拦截"
                
                with self.log_lock:
                    log_entry = {
                        "time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        "direction": direction,
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "protocol": protocol,
                        "port": port,
                        "action": action,
                        "result": result
                    }
                    self.traffic_log.append(log_entry)
        
        threading.Thread(target=traffic_thread, daemon=True).start()
    
    def update_traffic_display(self):
        with self.log_lock:
            # 只显示最新的100条日志
            display_log = self.traffic_log[-100:]
        
        # 清除现有日志显示
        for item in self.traffic_tree.get_children():
            self.traffic_tree.delete(item)
        
        # 添加日志到Treeview
        for entry in display_log:
            if isinstance(entry, dict):  # 流量日志
                color = "#4CAF50" if entry["result"] == "允许" else "#F44336"
                self.traffic_tree.insert("", "end", values=(
                    entry["time"],
                    entry["direction"],
                    entry["src_ip"],
                    entry["dst_ip"],
                    entry["protocol"],
                    entry["port"],
                    entry["action"],
                    entry["result"]
                ), tags=(color,))
            else:  # 系统日志（文本）
                self.traffic_tree.insert("", "end", values=("", "", "", "", "", "", "", entry), tags=("#FF9800",))
        
        self.traffic_tree.tag_configure("#4CAF50", foreground="#4CAF50")
        self.traffic_tree.tag_configure("#F44336", foreground="#F44336")
        self.traffic_tree.tag_configure("#FF9800", foreground="#FF9800")
        
        # 每500毫秒更新一次
        if self.running:
            self.root.after(500, self.update_traffic_display)
    
    def start_firewall(self):
        self.running = True
        self.traffic_log.append("防火墙已启动")
    
    def stop_firewall(self):
        self.running = False
        self.traffic_log.append("防火墙已停止")
    
    def clear_log(self):
        with self.log_lock:
            self.traffic_log.clear()
        self.traffic_log.append("日志已清除")

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = FirewallSimulator(root)
    root.mainloop()