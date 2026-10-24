import socket
import psutil

def str2bool(string):
    return string.lower() in ('yes', 'true', '1')

def get_host_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def kill_process_tree(pid):
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    for child in children:
        child.terminate()  # 发送终止信号给子进程
    psutil.wait_procs(children, timeout=5)  # 等待子进程结束
    parent.terminate()  # 发送终止信号给父进程
