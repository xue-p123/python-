import sys
import socket
from optparse import OptionParser
from threading import Thread

# 修正1：函数名拼写修正 (open -> port_open)
def port_open(ip, port):
    s = socket.socket()
    try:
        s.connect((ip, port))  # 修正2：connect拼写修复
        return True
    except:
        return False  # 修正3：False拼写修复

# 修正4：统一扫描函数名
def port_scan(ip, port):
    if port_open(ip, port):
        print(f"{ip}:{port} [OPEN]")
    else:
        print(f"{ip}:{port} [CLOSED]")

# 修正5：参数命名避免与关键字冲突
def range_scan(ip, start_port, end_port):
    for port in range(start_port, end_port + 1):
        port_scan(ip, port)

def main():
    # 修正6：统一使用双引号
    usage = "用法: scan.py -i IP地址 -p 端口范围"
    parser = OptionParser(usage=usage)  # 修正7：变量名统一
    
    # 修正8：添加端口类型说明
    parser.add_option("-i", "--ip", dest="target_ip", help="目标IP地址")
    parser.add_option("-p", "--port", dest="ports", help="端口范围 (示例: 80,443 或 1-100 或 all)")
    
    # 修正9：正确解析参数
    (options, args) = parser.parse_args()
    
    if not options.target_ip or not options.ports:
        parser.error("必须提供IP地址和端口参数")
    
    ip = options.target_ip
    port_arg = options.ports.lower()
    default_ports = [21, 22, 23, 80, 443, 8080, 3306, 3389]
    
    # 修正10：重构端口处理逻辑
    if ',' in port_arg:
        ports = [int(p) for p in port_arg.split(',')]
        for port in ports:
            t = Thread(target=port_scan, args=(ip, port))
            t.start()
            
    elif '-' in port_arg:
        start, end = map(int, port_arg.split('-'))
        # 修正11：处理端口范围
        for port in range(start, end + 1):
            t = Thread(target=port_scan, args=(ip, port))
            t.start()
            
    elif port_arg == 'all':
        # 修正12：扫描所有端口 (1-65535)
        for port in range(1, 65536):
            t = Thread(target=port_scan, args=(ip, port))
            t.start()
            
    elif port_arg == 'default':
        for port in default_ports:
            t = Thread(target=port_scan, args=(ip, port))
            t.start()
    else:
        # 处理单个端口
        try:
            port = int(port_arg)
            port_scan(ip, port)
        except ValueError:
            parser.error("无效的端口格式")

if __name__ == '__main__':
    main()