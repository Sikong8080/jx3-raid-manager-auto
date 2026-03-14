# 本地开发指南

本文档介绍如何在本地搭建开发环境、启动项目、运行测试以及构建生产版本。

## 环境要求

| 工具 | 版本要求 | 说明 |
|------|---------|------|
| [Node.js](https://nodejs.org/) | >= 18 | 前端运行时 |
| [Rust](https://www.rust-lang.org/tools/install) | >= 1.70 | Tauri 后端编译 |
| [npm](https://www.npmjs.com/) | >= 9 | 包管理器（随 Node.js 安装） |

### Windows 额外依赖

Tauri v2 在 Windows 上还需要：

- [Microsoft Visual Studio C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — 安装时勾选 "使用 C++ 的桌面开发" 工作负载
- [WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) — Windows 10/11 通常已预装

> 详细的平台依赖说明请参考 [Tauri v2 官方文档](https://v2.tauri.app/start/prerequisites/)。

## 安装依赖

```bash
# 克隆项目
git clone https://github.com/Sikong8080/jx3-raid-manager-auto.git
cd jx3-raid-manager-auto

# 安装前端依赖
npm install
```

Rust 依赖会在首次运行 `tauri dev` 或 `tauri build` 时自动下载和编译，无需手动操作。

## 开发模式

### 完整开发（前端 + Tauri 桌面端）

```bash
npm run tauri dev
```

该命令会同时启动：

- **Vite 前端开发服务器**（`http://localhost:1420`），支持 HMR 热更新
- **Tauri Rust 后端**，自动编译并启动桌面窗口

前端代码修改后会自动热更新，Rust 代码修改后会自动重新编译。

> 首次运行需要编译所有 Rust 依赖，耗时较长，后续启动会快很多。

### 仅前端开发（不启动 Tauri）

```bash
npm run dev
```

仅启动 Vite 前端开发服务器。适用于只需要调试 UI/样式的场景。

> 注意：此模式下 Tauri `invoke` 调用将不可用，涉及后端数据的功能无法正常工作。

## TypeScript 类型检查

```bash
npm run build
```

该命令运行 `tsc && vite build`，可用于检查 TypeScript 是否有类型错误，并生成前端构建产物到 `dist/` 目录。

## 运行测试

```bash
# 单次运行
npm run test

# 监听模式（文件变更自动重跑）
npm run test:watch
```

测试框架为 [Vitest](https://vitest.dev/)。

## 生产构建（打包）

```bash
npm run tauri build
```

该命令会依次执行：

1. TypeScript 类型检查
2. Vite 构建前端产物到 `dist/` 目录
3. 编译 Rust 后端（Release 模式）
4. 生成 NSIS 安装包

### 构建产物位置

```
src-tauri/target/release/
├── JX3RaidManager.exe                              # 可执行文件
└── bundle/
    └── nsis/
        └── JX3RaidManager_x.x.x_x64-setup.exe     # NSIS 安装包
```

## 项目结构

```
jx3-raid-manager-auto/
├── components/          # React 组件
│   ├── Dashboard.tsx           # 数据概览
│   ├── AccountManager.tsx      # 账号管理
│   ├── RaidManager.tsx         # 副本管理
│   ├── RaidDetail.tsx          # 副本详情（角色列表 + CD 追踪）
│   ├── RaidLogger.tsx          # 快速记录副本
│   ├── BaizhanManager.tsx      # 百战管理
│   ├── TrialPlaceManager.tsx   # 试炼之地
│   ├── IncomeDetail.tsx        # 收支明细
│   ├── CrystalDetail.tsx       # 玄晶统计
│   ├── ConfigManager.tsx       # 配置管理
│   └── *Modal.tsx              # 各类弹窗组件
├── contexts/            # React Context
│   └── ThemeContext.tsx         # 主题管理
├── data/                # 静态数据
│   ├── staticRaids.ts          # 预制副本配置
│   ├── raidBosses.ts           # BOSS 配置
│   └── baizhanBosses.ts        # 百战 BOSS 配置
├── hooks/               # 自定义 Hooks
├── services/            # 业务逻辑层
│   ├── db.ts                   # 数据库服务（Tauri IPC 封装）
│   ├── migration.ts            # 数据迁移
│   ├── jx3BoxApi.ts            # JX3Box API 集成
│   ├── gameDirectoryScanner.ts # 游戏目录扫描
│   └── ai/                     # AI 辅助服务
├── utils/               # 工具函数
│   ├── cooldownManager.ts      # 副本 CD 计算
│   ├── bossCooldownManager.ts  # BOSS CD 计算
│   ├── recordUtils.ts          # 记录去重/格式化
│   └── toastManager.ts         # Toast 通知
├── types.ts             # TypeScript 类型定义
├── constants.ts         # 全局常量
├── App.tsx              # 根组件
├── index.tsx            # 入口文件
├── index.css            # 全局样式（CSS 变量 + Tailwind）
├── vite.config.ts       # Vite 配置
├── tailwind.config.js   # Tailwind CSS 配置
├── tsconfig.json        # TypeScript 配置
├── package.json         # 前端依赖 & 脚本
└── src-tauri/           # Tauri Rust 后端
    ├── Cargo.toml              # Rust 依赖配置
    ├── tauri.conf.json         # Tauri 应用配置
    └── src/
        ├── main.rs             # Rust 入口
        ├── db.rs               # 数据库模块
        ├── db/                 # 数据库子模块
        ├── chatlog_parser.rs   # 聊天日志解析
        └── gkp_parser.rs       # GKP 解析
```

## 命令速查

| 命令 | 说明 |
|------|------|
| `npm install` | 安装前端依赖 |
| `npm run tauri dev` | 启动完整开发环境（前端 + Tauri） |
| `npm run dev` | 仅启动前端开发服务器 |
| `npm run build` | TypeScript 类型检查 + 前端构建 |
| `npm run test` | 运行测试 |
| `npm run test:watch` | 监听模式运行测试 |
| `npm run tauri build` | 生产构建（打包为安装程序） |

## 数据存储

应用数据存储在用户主目录下：

- **路径**: `C:\Users\<用户名>\.jx3-raid-manager\`
- **数据库文件**: `jx3-raid-manager.db`（SQLite 格式）
- 数据完全本地化，不经过任何云端服务器
