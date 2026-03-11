Markdown
 
Plain Text
# 📚 TermHelper (极速缩略词典)
一款专为高效办公打造的桌面级、沉浸式缩略词查询与管理工具。
基于 Python + Tkinter + SQLite 构建，拥有极速的响应体验和全局快捷键唤醒功能，帮助团队沉淀和快速检索海量业务/技术缩略语。
## ✨ 核心特性* **⚡ 极速响应 & 毫秒级检索**：底层采用 SQLite 数据库重构，支持十万级数据量秒开、秒搜、秒存，内存占用极低。* **⌨️ 全局沉浸式唤醒**：无论当前在使用什么软件，按下 `Alt + Q` 瞬间呼出（并自动置顶+锁定搜索框），用完按下 `Esc` 瞬间隐藏，打断感为零。* **📋 剪贴板智能嗅探**：在邮件或文档中复制一段文本，点击“剪贴板提取”，自动抓取未知的缩略词（如 SOP, B2B），并弹出极简窗口辅助极速录入。* **🏷️ 模块化隔离与筛选**：支持为词条打上“所属模块”标签，可通过下拉菜单一键过滤特定业务线的词汇。* **💡 智能悬停卡片 (Tooltip)**：遇到超长解释无需拖动滚动条，鼠标悬停半秒自动弹出排版精美的中英对照完整信息卡片。* **🧠 布局肌肉记忆**：自由拖拽调整列宽，退出时自动记录配置，下次启动完美还原你的专属布局。
## 🚀 快速运行 (开发环境)
本项目极其轻量，除了用于绑定全局快捷键的库之外，全部使用 Python 内置标准库。
**1. 克隆仓库**```bash
git clone [https://github.com/你的名字/TermHelper.git](https://github.com/你的名字/TermHelper.git)
cd TermHelper
2. 安装唯一依赖
Bash
 
Plain Text
pip install keyboard
3. 运行程序
Bash
 
Plain Text
python TermHelper.py
(首次运行会自动在同级目录下生成 term_data.db 数据库文件。)
📦 打包为独立桌面软件 (.exe)
如果你想把这个工具发给没有安装 Python 环境的同事使用，可以使用 PyInstaller 将其打包为单文件免安装版：
1. 安装打包工具
Bash
 
Plain Text
pip install pyinstaller
2. 执行打包命令
Bash
 
Plain Text
python -m PyInstaller --noconsole --onefile TermHelper.py
打包完成后，在 dist 文件夹中会生成 TermHelper.exe。 你可以将其重命名，并为其创建一个快捷方式放入 Windows 的“启动”文件夹（shell:startup）中，实现开机静默自启。
🗄️ 团队数据共享与迁移
数据都在哪？ 所有的词条数据和你的列宽配置，都极其紧凑地保存在程序同目录下的 term_data.db 文件中。
如何发给同事？ 只需要把打包好的 TermHelper.exe 和你本地的 term_data.db 一起发给同事放在同一个文件夹里，他们打开就能拥有和你一模一样的海量词库！
旧版数据兼容：如果你有旧版的 xxx_lib.json 词库文件，只需将它们和程序放在同一目录下，程序启动时会自动将其吸入数据库，并添加 .imported 后缀防止重复导入。
🕹️ 操作指南
呼出/隐藏: Alt + Q 呼出，Esc 隐藏。
编辑词条: 在表格中双击任意一行，即可弹出编辑窗口。
删除词条: 选中一行或多行，点击“删除选中”按钮（内置防误删 ID 校验）。
查看详情: 鼠标停留在任意词条所在行 0.5 秒，即可预览完整卡片。
Built with ❤️ for better productivity.