# GitHub AI Star 月报

工作流计划于每月 1 日北京时间 09:00 执行，收集 GitHub Trending 月榜中名称或简介含 AI 相关关键词的项目，按页面显示的本月新增 Stars 排序，邮件发送前 10 名到 chenhello892@gmail.com。

## 还需要设置 Gmail 密钥

在仓库页面打开 **Settings → Secrets and variables → Actions → New repository secret**，添加：

- `GMAIL_ADDRESS`：用于发信的 Gmail 地址
- `GMAIL_APP_PASSWORD`：该 Gmail 账号生成的应用专用密码（不是 Gmail 登录密码）

设置完成后，可以在 **Actions → Monthly GitHub AI Star report → Run workflow** 手动试发一次。定时工作流需保持启用。
