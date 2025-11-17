# Subdomain Watcher - 子域名监控工具

一个轻量、自动化的Python脚本，用于监控指定域名下的新增子域名，并通过邮件实时通知您。集成了 GitHub Actions，支持云端自动化运行。

## ✨ 主要功能 (Features)

- **多域名支持**: 可同时监控任意多个主域名。
- **自动化发现**: 定期通过 `crt.sh` 公开的证书透明度日志，自动发现新出现的子域名。
- **增量监控**: 只在发现新的、从未记录过的子域名时触发通知，避免重复打扰。
- **邮件实时提醒**: 一旦发现新域名，立即将详细列表发送到您指定的邮箱。
- **双模式运行**: 支持在您自己的电脑上（本地）运行，也支持通过 GitHub Actions 实现完全托管的自动化监控。
- **后台持续运行**: 本地运行时，脚本可作为后台服务，根据设定的时间间隔持续执行。

## 🚀 工作原理 (How It Works)

1.  **加载配置/凭证**:
    - **本地模式**: 启动时读取 `config.json` 文件获取所有设置。
    - **Actions 模式**: 运行时从 GitHub Secrets 读取凭证和配置。
2.  **加载历史记录**: 读取 `known_subdomains.json` 文件，将已发现的子域名加载到内存中。
3.  **循环监控**:
    - **查询新域名**: 针对每个要监控的域名，请求 `crt.sh` 的API，获取当前全量子域名列表。
    - **比较差异**: 将API返回的列表与内存中的历史记录进行对比。
    - **发现新域名**: 如果出现差异（即发现了新域名），则触发通知。
    - **发送邮件**: 将新增的子域名列表通过邮件发送给管理员。
    - **更新记录**: 将新发现的子域名追加到 `known_subdomains.json` 文件中。
    - **Actions 模式下**: 自动将更新后的 `known_subdomains.json` 文件提交回您的代码仓库。
4.  **定时等待**:
    - **本地模式**: 完成一轮检查后，脚本会暂停运行，等待预设的时间后再次开始。
    - **Actions 模式**: 根据预设的 `cron` 计划（例如每2小时）自动唤醒并执行一次。

## 🛠️ 如何使用 (How to Use)

您可以根据需求选择以下任意一种方式来运行本项目。

### 方式一：本地运行 (适合快速测试和本地部署)

#### 步骤 1: 安装依赖

首先，请确保您的电脑已经安装了 Python。然后，在命令行中进入项目文件夹，运行以下命令来安装必需的库：

```bash
pip install -r requirements.txt
```

#### 步骤 2: 创建并修改配置文件

这是最关键的一步。请在项目根目录下**手动创建一个名为 `config.json` 的文件**，然后将以下内容复制进去，并根据您的实际情况修改：

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

**配置项说明:**
- `domains_to_monitor`: 您想要监控的主域名列表。
- `monitoring_interval_hours`: 每次检查的间隔时间（小时）。
- `email_settings`:
    - `smtp_server`: 发件邮箱的SMTP服务器地址 (例如: `smtp.qq.com`, `smtp.163.com`)。
    - `smtp_port`: SMTP端口 (推荐 `587`)。
    - `sender_email`: 发件邮箱地址。
    - `sender_password`: **极其重要！** 这里填写的**不是邮箱的登录密码**，而是邮箱服务商提供的**“授权码”**或“应用专用密码”。
    - `receiver_email`: 接收提醒邮件的地址。

#### 步骤 3: 运行脚本

所有配置完成后，在命令行中执行以下命令即可启动监控：

```bash
python monitor.py
```

脚本启动后，会立即执行一次检查，然后进入后台循环。只要这个命令行窗口不关闭，监控就会一直持续。

---

### 方式二：通过 GitHub Actions 自动监控 (推荐)

这种方式无需您自己准备服务器或电脑，也无需创建 `config.json` 文件，监控将完全自动化在云端进行。

#### 步骤 1: 设置仓库 Secrets

您需要将配置信息安全地存储在 GitHub 仓库的 Secrets 中。

1.  在您的 GitHub 仓库页面，点击 **Settings**。
2.  在左侧菜单中，找到并点击 **Secrets and variables** -> **Actions**。
3.  点击 **New repository secret** 按钮，然后依次创建以下 **4** 个 Secret：

| Secret 名称           | 说明                                                         | 示例值                               |
| --------------------- | ------------------------------------------------------------ | ------------------------------------ |
| `DOMAINS_TO_MONITOR`  | 要监控的域名列表，用**英文逗号**隔开。                       | `example.com,another-domain.org`     |
| `SENDER_EMAIL`        | 用来发送提醒邮件的邮箱地址。                                 | `your_sender@qq.com`                 |
| `SENDER_PASSWORD`     | 上述邮箱的**授权码** (不是登录密码)。                        | `abckdkeisowpwdn`                    |
| `RECEIVER_EMAIL`      | 用来接收新域名提醒的邮箱地址。                               | `your_receiver@example.com`          |

#### 步骤 2: 触发 Action

设置好 Secrets 后，Action 会通过以下两种方式被触发：

1.  **自动触发**: 根据预设，**每2小时会自动运行一次**。您无需任何操作。
2.  **手动触发**: 如果想立即测试，可以手动运行。
    - 进入仓库的 **Actions** 标签页。
    - 在左侧选择 **Subdomain Monitor**。
    - 点击 **Run workflow** 按钮。

当 Action 运行时，它会自动使用您设置的 Secrets 来执行监控任务，并将新发现的域名记录更新到 `known_subdomains.json` 文件中，然后自动提交回您的仓库。

## 📄 文件结构说明

- `monitor.py`: 项目的主程序，包含了所有的监控和通知逻辑。
- `config.json`: **(本地运行时需要)** 您的个人配置文件。
- `requirements.txt`: 定义了项目运行所需的Python第三方库。
- `known_subdomains.json`: **自动生成/更新的文件**。用于存储所有已经发现的子域名，请不要手动修改它。
- `.github/workflows/monitor.yml`: GitHub Actions 的配置文件，定义了自动化监控流程。
- `README.md`: 本说明文档。
- `需求.txt`: 项目的原始需求记录。