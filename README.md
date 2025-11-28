## Netlib 自动登录保活脚本
这是一个用于自动登录 Netlib 网站以保持账户活跃的脚本，配合 GitHub Actions 实现自动定时执行。

注册地址：https://www.netlib.re

视频教程地址：https://youtu.be/7laVmEfgC9o


### 功能特点
- 🔐 自动登录 Netlib 账户(单账户或多账户)
- 👥 支持多账户批量处理
- ⏰ 每10天自动执行一次
- 📱 执行结果可通过 Telegram 通知

### 使用方法
1. fork 此项目
2. 在Actions菜单允许 `I understand my workflows, go ahead and enable them` 按钮

3. 在 GitHub 仓库的 Settings → Secrets and variables → Actions 中添加以下环境变量
-  账号密码之间用英文冒号分隔，账号与账号之间英文逗号分隔
- `ACCOUNTS`  Netlib账户(必填)，格式(单账号)：user:pass   格式(多账号)：user1:pass1,user2:pass2 

- telegram为可选环境变量,不需要通知可不填写
- `BOT_TOKEN` 	Telegram机器人Token https://t.me/BotFather 创建bot后获取
- `CHAT_ID`     Telegram 聊天ID https://t.me/laowang_serv00_bot 发送 /start 获取
	    
4. GitHub Actions 初始手动执行检查是否有配置错误，脚本会自动每10天执行一次,可手动执行

### 注意事项
1. 确保 Netlib 账户密码正确
2. 首次运行 GitHub Actions 需要授权
3. 脚本执行时间为 UTC 0:00（香港时间 8:00）
4. 如果不需要 Telegram 通知，可不配置相关环境变量


### 许可证
GPL 3.0
