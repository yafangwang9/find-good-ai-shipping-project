[English](README.md)

# GitHub Trending Skill

> **说明：** 目前仅支持 GitHub Trending 渠道，后续会增加更多合适的发现渠道。

真正在 shipping 的 AI 项目，往往不在融资列表和新闻里。[GitHub Trending](https://github.com/trending) 是发现它们的好方式。这个 Skill 帮你按每天或每周获取热门开源项目，并借助 [TinyFish](https://tinyfish.ai) 获取项目作者发布的社交媒体帖子——帮你判断这个项目的团队/作者是否值得 follow。

## 工作流程

```
Step 0   询问：每日还是每周？中文还是英文？
            |
Phase 1  获取 GitHub Trending → 立即返回结果
            |
Phase 2  通过 GitHub API 解析作者 Twitter
(可选)      → 通过 TinyFish 搜索作者推文
            → 与项目信息一起展示
```

**Phase 1** 即时返回，无需 API key。**Phase 2** 可选，需要免费的 TinyFish API key，优先获取项目作者本人发布的推文，而非 KOL 转发。

## 安装

### Cursor

```bash
# 个人级别（所有项目可用）
cp -r github-trending/ ~/.cursor/skills/github-trending/

# 或项目级别
cp -r github-trending/ .cursor/skills/github-trending/
```

### Claude.ai

1. 将 `github-trending/` 文件夹打包为 zip
2. 设置 → 功能 → Skills → 上传

### Claude Code

```bash
cp -r github-trending/ ~/.claude/skills/github-trending/
```

## 首次使用配置

安装完成后，首次使用时 Skill 会引导你完成一次性配置：

1. **选择默认时间范围** — 今日 / 本周 / 本月
2. **选择输出语言** — 中文 / English
3. **配置 TinyFish API Key（可选）** — 用于获取作者推文

偏好设置会自动保存到 `config.json`，后续使用无需重复配置。

## 配置 TinyFish API Key（可选）

社交媒体内容获取需要 TinyFish API key。不配置也可以正常使用 GitHub Trending 功能。

获取 key：[agent.tinyfish.ai/api-keys](https://agent.tinyfish.ai/api-keys)

```bash
# 设置一次，以后不再询问
export TINYFISH_API_KEY="sk-tinyfish-your-key-here"
```

## 使用方式

安装后，当你提到 GitHub 热门相关话题时，Skill 会自动触发：

- "今日 GitHub 热门项目"
- "本周 Rust 热门项目"
- "帮我看看 GitHub 上什么项目火了"

### 你会得到什么

**Phase 1 — 热门项目（即时）：**

```
1. forrestchang/andrej-karpathy-skills — Stars 37,254 / 今日 +9,263
   基于 Karpathy 对 LLM 编程陷阱的观察，改善 Claude Code 行为

2. thedotmack/claude-mem — Stars 56,521 / 今日 +2,997
   Claude Code 持久化记忆插件
...
```

**Phase 2 — 作者推文（可选）：**

```
1. forrestchang/andrej-karpathy-skills — Stars 37,254 / 今日 +9,263
   作者：Jiayuan Zhang (@jiayuan_jy)

   - I let Claude Code turn @karpathy's post into agent skills.
     It first generated a bunch of skill files and around 800 lines...
```

### 手动运行脚本

```bash
# 获取热门项目（无需 API key）
python github-trending/scripts/fetch_trending.py --since daily --count 12 --format json

# 本周 Python 热门
python github-trending/scripts/fetch_trending.py --since weekly --language python

# 搜索指定项目的作者推文
python github-trending/scripts/search_social.py \
  --repos "microsoft/markitdown,forrestchang/andrej-karpathy-skills" \
  --api-key YOUR_KEY

# 完整流水线
python github-trending/scripts/fetch_trending_full.py \
  --tinyfish-key YOUR_KEY --since daily --count 12 --format markdown
```

## 作者推文搜索原理

这个 Skill 不是简单搜索"项目名"（那样会搜到 KOL 转发），而是：

1. 从 `owner/repo` 中提取仓库拥有者
2. 调用 GitHub API 获取拥有者的 **真实 Twitter 账号**
3. 搜索 `"项目名 from:作者账号 site:x.com"` 精准命中
4. 如果作者没设置 Twitter，降级为 `"owner 项目名 github site:x.com"`

| 场景 | 搜索策略 | 标注 |
|------|---------|------|
| 作者有 Twitter | `from:handle` 精准搜索 | 作者本人 |
| 组织有 Twitter | `from:org_handle` 搜索 | 组织官方 |
| 未设置 Twitter | `owner + repo + github` 降级 | 社区讨论 |

## 项目结构

```
github-trending/
├── SKILL.md                        # Skill 指令文件（AI 读取）
├── config.json                     # 用户偏好（首次使用时自动生成）
├── scripts/
│   ├── fetch_trending.py           # GitHub 热门抓取（零依赖）
│   ├── search_social.py            # 作者推文搜索（GitHub API + TinyFish）
│   └── fetch_trending_full.py      # 一键完整流水线
└── references/
    ├── api-guide.md                # API 细节和限流说明
    └── examples.md                 # 使用示例
```

## 依赖

- Python 3.7+
- 网络连接
- 无需安装任何第三方包（纯标准库）
- **可选：** TinyFish API key（用于社交媒体内容获取）

## 许可证

MIT

---

Built with [Cursor](https://cursor.com)
