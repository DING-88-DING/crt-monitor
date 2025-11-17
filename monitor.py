# -*- coding: utf-8 -*-
import json
import time
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header
import requests

# 配置文件路径
CONFIG_FILE = 'config.json'
# 已知子域名存储文件路径
KNOWN_SUBDOMAINS_FILE = 'known_subdomains.json'

def load_config():
    """加载配置文件"""
    if not os.path.exists(CONFIG_FILE):
        print(f"错误：配置文件 {CONFIG_FILE} 不存在。请根据说明创建并配置它。")
        sys.exit(1)
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_known_subdomains():
    """加载已知的子域名列表（字典格式：{domain: set(subdomains)}）"""
    if not os.path.exists(KNOWN_SUBDOMAINS_FILE) or os.path.getsize(KNOWN_SUBDOMAINS_FILE) == 0:
        return {} # 返回空字典
    with open(KNOWN_SUBDOMAINS_FILE, 'r', encoding='utf-8') as f:
        # 从JSON加载，并将列表转换为集合
        data = json.load(f)
        return {domain: set(subdomains) for domain, subdomains in data.items()}

def save_known_subdomains(known_subdomains_dict):
    """保存子域名列表（字典格式）到文件"""
    # 将集合转换为列表以便JSON序列化
    data = {domain: list(subdomains) for domain, subdomains in known_subdomains_dict.items()}
    with open(KNOWN_SUBDOMAINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_subdomains_from_crtsh(domain):
    """从 crt.sh 获取子域名列表"""
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()  # 如果请求失败则抛出异常
        
        # 解析JSON响应，并提取common_name和name_value
        subdomains = set()
        for entry in response.json():
            # crt.sh返回的name_value可能包含多个域名，需要分割
            names = entry.get('name_value', '').split('\n')
            for name in names:
                # 过滤掉包含通配符的域名和不属于目标域名的记录
                if '*' not in name and name.endswith(f".{domain}"):
                    subdomains.add(name.lower())
        return subdomains
    except requests.exceptions.RequestException as e:
        print(f"错误：请求 crt.sh 失败: {e}")
        return None
    except json.JSONDecodeError:
        print("错误：解析 crt.sh 的响应失败，可能服务暂时不可用。")
        return None

def send_email(subject, content, config):
    """发送邮件通知"""
    email_config = config['email_settings']
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = formataddr((Header('子域名监控服务', 'utf-8').encode(), email_config['sender_email']))
    msg['To'] = formataddr((Header('管理员', 'utf-8').encode(), email_config['receiver_email']))
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()  # 启用TLS加密
        server.login(email_config['sender_email'], email_config['sender_password'])
        server.sendmail(email_config['sender_email'], [email_config['receiver_email']], msg.as_string())
        server.quit()
        print("邮件通知已成功发送。")
    except Exception as e:
        print(f"错误：邮件发送失败: {e}")

def main():
    """主函数"""
    print("--- 子域名监控脚本启动 ---")
    config = load_config()
    domains_to_monitor = config['domains_to_monitor'] # 从配置中获取要监控的域名列表
    interval_seconds = config['monitoring_interval_hours'] * 3600

    while True:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始检查所有域名...")
        
        # 1. 加载所有已知的子域名（字典形式）
        all_known_subdomains = load_known_subdomains()
        
        new_subdomains_found_in_cycle = False # 标记本轮是否有新子域名发现

        for domain_to_monitor in domains_to_monitor:
            print(f"  - 正在检查域名: {domain_to_monitor}")
            
            # 获取该域名已知的子域名
            known_subdomains_for_this_domain = all_known_subdomains.get(domain_to_monitor, set())
            print(f"    已知的子域名数量 for {domain_to_monitor}: {len(known_subdomains_for_this_domain)}")

            # 2. 从crt.sh获取当前所有子域名
            current_subdomains = get_subdomains_from_crtsh(domain_to_monitor)
            
            if current_subdomains is None:
                print(f"    获取 {domain_to_monitor} 的子域名失败，跳过本次检查。")
                continue

            print(f"    本次获取到的子域名数量 for {domain_to_monitor}: {len(current_subdomains)}")

            # 3. 对比发现新增的子域名
            new_subdomains = current_subdomains - known_subdomains_for_this_domain

            # 4. 处理新增域名
            if new_subdomains:
                new_subdomains_found_in_cycle = True
                print(f"    发现 {len(new_subdomains)} 个新的子域名 for {domain_to_monitor}！")
                for subdomain in new_subdomains:
                    print(f"      - {subdomain}")
                
                # 发送邮件通知
                subject = f"发现新的子域名 for {domain_to_monitor}"
                content = f"你好，\n\n监控到域名 {domain_to_monitor} 新增了以下 {len(new_subdomains)} 个子域名：\n\n"
                content += "\n".join(sorted(list(new_subdomains)))
                send_email(subject, content, config)

                # 更新该域名的已知子域名列表
                known_subdomains_for_this_domain.update(new_subdomains)
                all_known_subdomains[domain_to_monitor] = known_subdomains_for_this_domain
                print(f"    本地的已知子域名列表已更新 for {domain_to_monitor}。")
            else:
                print(f"    未发现新的子域名 for {domain_to_monitor}。")
        
        # 在处理完所有域名后，统一保存更新后的所有已知子域名
        if new_subdomains_found_in_cycle:
            save_known_subdomains(all_known_subdomains)
            print("所有域名的已知子域名列表已保存。" )
        else:
            print("所有域名均未发现新的子域名，无需保存。" )

        # 5. 等待下一个周期
        print(f"本次所有域名检查完成，将在 {config['monitoring_interval_hours']} 小时后进行下一次检查。" )
        time.sleep(interval_seconds)

if __name__ == '__main__':
    main()