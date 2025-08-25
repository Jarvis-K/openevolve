# AlphaEvolve Demo (Next.js, App Router)

> 多文件工程版本，包含 Project Hub（含宣传 Hero + 上传/配置）、Monitor（整体曲线 + 多岛屿状态与变化）、Compare、Results。首次进入需在 Project Hub 顶部点击 **Start** 才会展示导航 Tab 并解锁功能；在 Hub 内点击 **Start Evolution** 后会跳转到 **/monitor**。

---

## 项目结构

```
alphaevolve-demo/
├─ README.md
├─ package.json
├─ tsconfig.json
├─ next.config.js
├─ postcss.config.js
├─ tailwind.config.ts
├─ .gitignore
├─ app/
│  ├─ globals.css
│  ├─ layout.tsx
│  ├─ page.tsx                 # 入口：重定向到 /project-hub
│  ├─ project-hub/
│  │  └─ page.tsx              # Hero + Hub（上传/配置/Start Evolution）
│  ├─ monitor/
│  │  └─ page.tsx              # 总体曲线 + 多岛屿卡片（sparkline+top code-score）
│  ├─ compare/
│  │  └─ page.tsx
│  └─ results/
│     └─ page.tsx
├─ components/
│  ├─ TopNav.tsx
│  ├─ LineChart.tsx
│  ├─ Sparkline.tsx
│  └─ MonacoEditor.tsx         # 无依赖文本域降级版
└─ lib/
   ├─ state.tsx                # started 门控（Start 后显示 Tabs），sessionStorage 持久化
   ├─ world.ts                 # 类型、随机生成 demo 数据、movingMax
   └─ api.ts                   # startEvolution 调用 API，启动 openevolve 后端运行
```

---

## 安装与运行

### 依赖安装

该前端需要 **Node.js 18+** 以及可执行的 **Python** 环境。若要实际调用 `openevolve-run.py`，请先在仓库根目录安装 OpenEvolve 依赖：

```bash
pip install -e ..
```

随后在本目录安装前端依赖：

```bash
pnpm install   # 或 npm install / yarn

# 可选：安装 Playwright 浏览器以运行 E2E 测试
npx playwright install
```

### 启动开发服务器

```bash
pnpm dev      # http://localhost:3000 （自动重定向到 /project-hub）
```

### 最小 Playwright E2E（可选）
> 如需回归：上传种子/评估器 → 配置 → 启动 → 跳转 monitor。

在 `package.json` 已预置 `test:e2e` 脚本（需安装 `playwright`）：

```ts
// e2e/start-and-monitor.spec.ts
import { test, expect } from '@playwright/test';

test('unlock tabs then start evolution → monitor', async ({ page }) => {
  await page.goto('/project-hub');
  await expect(page.getByTestId('nav-tabs').locator('button')).toHaveCount(0);
  await page.getByTestId('hero-start').click();
  await page.waitForSelector('#hub');
  await expect(page.getByTestId('nav-tabs').locator('button')).toHaveCount(4);
  await Promise.all([
    page.waitForURL('**/monitor'),
    page.getByTestId('start-evolution').click(),
  ]);
  await expect(page.getByTestId('chart-overall')).toBeVisible();
});
```

---

## 关键交互与说明
- **Start 门控**：`lib/state.tsx` 持久化 `started`；`components/TopNav.tsx` 在 `started=false` 时隐藏 Tabs。
 - **Project Hub**：顶部 Hero 介绍；点击 **Start** → 设置 `started=true` 并 **scroll 到 #hub**；点击 **Start Evolution** 调用 `lib/api.ts`，通过 Next.js API 将 Seed/Evaluator 写入临时目录、生成 `config.yaml` 并运行 `openevolve-run.py`，随后 `router.push('/monitor')`。
- **Monitor**：展示 **Overall Best Fitness 折线图** 与 **多岛屿卡片**（每岛 sparkline=该岛每代最大分数的运行最大值；并显示当前代 Top3 代码-分数对）。
- **白色主题**：`app/globals.css` + Tailwind；无深色模式。
- **无外部依赖**：自绘 `LineChart`/`Sparkline`（SVG）。

---

## 源码

> 将以下文件按路径写入到本地工程（已按上方目录分组）。
