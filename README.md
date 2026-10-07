# GitHub AI Star 月报

每月 1 日北京时间 09:00，工作流会收集 GitHub Trending 月榜中项目名称或简介含 AI 关键词的项目，按近 30 天新增 Stars 排序，并将前 10 名发到飞书群。

## 设置飞书机器人

1. 在飞书群里添加自定义机器人，复制它提供的 Webhook 地址。
2. 在本仓库打开 **Settings → Secrets and variables → Actions → New repository secret**。
3. 名称填 `FEISHU_WEBHOOK`，值填机器人的 Webhook 地址。不要把地址发到聊天里。
4. 到 **Actions → Monthly GitHub AI Star report (Feishu) → Run workflow** 手动运行一次验证。

榜单按 GitHub Trending 月榜和项目名称、简介中的 AI 关键词筛选，可能不包含未出现在榜单上的项目。
