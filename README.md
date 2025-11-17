# Subdomain Watcher - 子域名监控工具

一个轻量、自动化的Python脚本，用于监控指定域名下的新增子域名，并通过邮件实时通知您。

## ✨ 主要功能 (Features)

- **多域名支持**: 可在配置文件中添加任意多个主域名进行同时监控。
- **自动化发现**: 定期通过 `crt.sh` 公开的证书透明度日志，自动发现新出现的子域名。
- **增量监控**: 只在发现新的、从未记录过的子域名时触发通知，避免重复打扰。
- **邮件实时提醒**: 一旦发现新域名，立即将详细列表发送到您指定的邮箱。
- **灵活配置**: 所有参数（监控域名、检查周期、邮箱设置）均在 `config.json` 中统一管理，无需改动代码。
- **后台持续运行**: 脚本启动后可作为后台服务，根据设定的时间间隔持续执行。

## 🚀 工作原理 (How It Works)

脚本的自动化流程如下：

1.  **加载配置**: 启动时读取 `config.json` 文件获取所有设置。
2.  **加载历史记录**: 读取 `known_subdomains.json` 文件，将已发现的子域名加载到内存中。
3.  **循环监控**:
    - **查询新域名**: 针对每个要监控的域名，请求 `crt.sh` 的API，获取当前全量子域名列表。
    - **比较差异**: 将API返回的列表与内存中的历史记录进行对比。
    - **发现新域名**: 如果出现差异（即发现了新域名），则触发通知。
    - **发送邮件**: 将新增的子域名列表通过邮件发送给管理员。
    - **更新记录**: 将新发现的子域名追加到 `known_subdomains.json` 文件中，完成本地记录的更新。
4.  **定时等待**: 完成一轮检查后，脚本会暂停运行，等待预设的时间（例如2小时）后，再次开始下一轮检查。

## 🛠️ 如何使用 (How to Use)

### 步骤 1: 安装依赖

首先，请确保您的电脑已经安装了 Python。然后，在命令行中进入项目文件夹，运行以下命令来安装必需的库：

```bash
pip install -r requirements.txt
```

### 步骤 2: 修改配置文件

这是最关键的一步。请打开 `config.json` 文件，并根据您的实际情况修改：

- `domains_to_monitor`: 您想要监控的主域名列表。
  - 示例: `["example.com", "another-domain.org"]`
- `monitoring_interval_hours`: 每次检查的间隔时间，以小时为单位。
  - 示例: `2` (表示每2小时检查一次)
- `email_settings`: 邮件通知相关的设置。
    - `smtp_server`: 发件邮箱的SMTP服务器地址。
      - 常见地址: QQ邮箱是 `smtp.qq.com`, 163邮箱是 `smtp.163.com`, Gmail是 `smtp.gmail.com`。
    - `smtp_port`: SMTP服务器的端口。
      - 推荐使用 `587` (TLS加密)，备选 `465` (SSL加密)。
    - `sender_email`: 您用来发送通知邮件的邮箱地址。
    - `sender_password`: **极其重要！** 这里填写的**不是邮箱的登录密码**，而是邮箱服务商提供的**“授权码”**或“应用专用密码”。您需要登录邮箱网页版，在“设置” -> “账户” -> “POP3/IMAP/SMTP”等相关页面中开启服务并生成它。
    - `receiver_email`: 您用来接收提醒邮件的地址。

**一个配置示例 (以QQ邮箱为例):**
```json
{
  "domains_to_monitor": ["initia.xyz"],
  "monitoring_interval_hours": 2,
  "email_settings": {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "sender_email": "your_sender@qq.com",
    "sender_password": "这里填写你的QQ邮箱授权码",
    "receiver_email": "your_receiver@example.com"
  }
}
```

### 步骤 3: 运行脚本

所有配置完成后，在命令行中执行以下命令即可启动监控：

```bash
python monitor.py
```

脚本启动后，会立即执行一次检查，然后进入后台循环。只要这个命令行窗口不关闭，监控就会一直持续。

## 📄 文件结构说明

- `monitor.py`: 项目的主程序，包含了所有的监控和通知逻辑。
- `config.json`: 您的个人配置文件，用于定义监控目标和通知方式。
- `requirements.txt`: 定义了项目运行所需的Python第三方库。
- `known_subdomains.json`: **自动生成的文件**。用于存储所有已经发现的子域名，请不要手动修改它。
- `README.md`: 本说明文档。
- `需求.txt`: 项目的原始需求记录。
