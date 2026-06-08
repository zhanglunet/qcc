# site/ — qcc 项目落地页

静态单文件落地页，零依赖，Cloudflare Pages 直接托管。

## 本地预览

```bash
cd site && python3 -m http.server 8765
open http://localhost:8765/
```

## 部署到 Cloudflare Pages

### 方式 A：Wrangler 直传（推荐，无需 GitHub 集成）

```bash
# 一次性：装 wrangler 并登录
npm install -g wrangler
wrangler login

# 首次部署：创建项目 qcc-agent
wrangler pages deploy site --project-name=qcc-agent --branch=main

# 后续更新：同一命令即可
wrangler pages deploy site --project-name=qcc-agent --branch=main
```

部署完成后会拿到 `https://qcc-agent.pages.dev`。

### 方式 B：Git 集成（自动 CI）

1. Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git
2. 选 `zhanglunet/qcc` 仓库
3. Build settings：
   - Build command: *(留空)*
   - Build output directory: `site`
   - Root directory: *(留空)*
4. 每次 push 到 main 自动部署，PR 自动出 preview URL

## 自定义域名

部署后在 Cloudflare Dashboard 的 Pages 项目里加 Custom Domain，例如 `qcc.your-domain.com`，CF 自动签证书。

## 文件清单

- `index.html` — 单文件，全部样式内联在 `<style>` 标签
- `_headers` — Cloudflare Pages 安全头 + 缓存策略
- `README.md` — 本文件
