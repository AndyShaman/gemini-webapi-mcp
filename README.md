<h1 align="center">gemini-webapi-mcp</h1>

<p align="center">
  MCP-сервер для Google Gemini — генерация и редактирование изображений, чат и анализ файлов через браузерные cookies.<br>
  Без API-ключей. Бесплатно.
</p>

<p align="center">
  <a href="https://t.me/AI_Handler"><img src="https://img.shields.io/badge/Telegram-канал автора-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"></a>
  &nbsp;
  <a href="https://www.youtube.com/channel/UCLkP6wuW_P2hnagdaZMBtCw"><img src="https://img.shields.io/badge/YouTube-канал автора-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube"></a>
</p>

---

## Возможности

- **Генерация изображений** по текстовому описанию (модель Pro с поддержкой пропорций)
- **Редактирование изображений** — отправьте картинку + промпт и получите изменённую версию
- **Анализ файлов** — видео, изображения, PDF, документы
- **Текстовый чат** с Gemini (Flash, Pro, Flash-Thinking)
- **Авто-аутентификация** через cookies из Chrome

## Быстрый старт

### 1. Войдите в Gemini

Откройте Chrome, перейдите на [gemini.google.com](https://gemini.google.com) и войдите в свой Google-аккаунт.

### 2. Установите MCP-сервер

**Из GitHub (без клонирования):**

```bash
uv run --with "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git" gemini-webapi-mcp
```

**Локальная установка:**

```bash
git clone https://github.com/AndyShaman/gemini-webapi-mcp.git
cd gemini-webapi-mcp
uv sync
uv run gemini-webapi-mcp
```

### 3. Добавьте MCP-конфиг

Добавьте в `~/.config/mcp/mcp_servers.json`:

**Из GitHub:**

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uv",
      "args": ["run", "--with", "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git", "gemini-webapi-mcp"]
    }
  }
}
```

**Локально (после клонирования):**

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uv",
      "args": ["run", "--with", "/path/to/gemini-webapi-mcp", "gemini-webapi-mcp"]
    }
  }
}
```

### 4. Установите скилл для Claude Code (опционально)

Папка [`skill/`](skill/) содержит скилл для Claude Code — подсказки по промптингу, документацию по тулам и гайд по генерации изображений. Скилл автоматически активируется при работе с Gemini.

```bash
cp -r skill ~/.claude/skills/gemini-mcp
```

### 5. Проверьте

```bash
mcp-cli call gemini gemini_chat '{"prompt": "Привет!"}'
```

Если получили ответ — всё работает.

## Аутентификация

Сервер автоматически читает cookies из Chrome через `browser-cookie3`.

> **Несколько Google-аккаунтов?** При авто-определении выбор аккаунта непредсказуем. Используйте env vars `GEMINI_PSID` / `GEMINI_PSIDTS` чтобы явно указать нужный аккаунт.

Если автоопределение не работает или у вас несколько аккаунтов, задайте cookies вручную:

1. Откройте Chrome DevTools на gemini.google.com → Application → Cookies
2. Скопируйте значения `__Secure-1PSID` и `__Secure-1PSIDTS`
3. Добавьте в MCP-конфиг:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uv",
      "args": ["run", "--with", "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git", "gemini-webapi-mcp"],
      "env": {
        "GEMINI_PSID": "your__Secure-1PSID_value",
        "GEMINI_PSIDTS": "your__Secure-1PSIDTS_value"
      }
    }
  }
}
```

## Инструменты

| Инструмент | Описание |
|------------|----------|
| `gemini_generate_image` | Генерация новых или редактирование существующих изображений |
| `gemini_upload_file` | Анализ файлов — видео, изображения, PDF, документы |
| `gemini_analyze_url` | Анализ URL — YouTube-видео, веб-страницы, статьи |
| `gemini_chat` | Текстовый чат (одиночный или multi-turn) |
| `gemini_start_chat` | Начать multi-turn сессию |
| `gemini_reset` | Переинициализация клиента при ошибках авторизации |

## Модели

| Модель | По умолчанию для | Примечание |
|--------|------------------|------------|
| `gemini-3.0-flash` | чат, анализ файлов | Быстрая |
| `gemini-3.0-pro` | генерация изображений | Поддержка пропорций |
| `gemini-3.0-flash-thinking` | — | Показывает процесс рассуждения |

## Примеры использования

Сгенерировать изображение:
```bash
mcp-cli call gemini gemini_generate_image '{"prompt": "кот в акварельном стиле"}'
```

Отредактировать изображение:
```bash
mcp-cli call gemini gemini_generate_image '{"prompt": "сделай кота серым", "files": ["/path/to/cat.png"]}'
```

Проанализировать YouTube-видео или URL:
```bash
mcp-cli call gemini gemini_analyze_url '{"url": "https://youtube.com/watch?v=...", "prompt": "О чём это видео?"}'
```

Проанализировать файл:
```bash
mcp-cli call gemini gemini_upload_file '{"file_path": "/path/to/video.mp4", "prompt": "О чём это видео?"}'
```

## Лицензия

MIT — свободно используйте, модифицируйте и распространяйте.

**[@AndyShaman](https://github.com/AndyShaman)** · [gemini-webapi-mcp](https://github.com/AndyShaman/gemini-webapi-mcp)

---

<h1 align="center">gemini-webapi-mcp</h1>

<p align="center">
  MCP server for Google Gemini — image generation/editing, chat and file analysis via browser cookies.<br>
  No API keys. Free.
</p>

<p align="center">
  <a href="https://t.me/AI_Handler"><img src="https://img.shields.io/badge/Telegram-Author's_Channel-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"></a>
  &nbsp;
  <a href="https://www.youtube.com/channel/UCLkP6wuW_P2hnagdaZMBtCw"><img src="https://img.shields.io/badge/YouTube-Author's_Channel-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube"></a>
</p>

---

## Features

- **Image generation** from text descriptions (Pro model with aspect ratio support)
- **Image editing** — send an image + prompt to get a modified version
- **File analysis** — video, images, PDF, documents
- **Text chat** with Gemini (Flash, Pro, Flash-Thinking)
- **Auto-authentication** via Chrome browser cookies

## Quick Start

### 1. Log into Gemini

Open Chrome, go to [gemini.google.com](https://gemini.google.com) and sign in.

### 2. Install the MCP server

**From GitHub (no clone needed):**

```bash
uv run --with "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git" gemini-webapi-mcp
```

**Local install:**

```bash
git clone https://github.com/AndyShaman/gemini-webapi-mcp.git
cd gemini-webapi-mcp
uv sync
uv run gemini-webapi-mcp
```

### 3. Add MCP config

Add to `~/.config/mcp/mcp_servers.json`:

**From GitHub:**

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uv",
      "args": ["run", "--with", "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git", "gemini-webapi-mcp"]
    }
  }
}
```

**Local (after cloning):**

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uv",
      "args": ["run", "--with", "/path/to/gemini-webapi-mcp", "gemini-webapi-mcp"]
    }
  }
}
```

### 4. Install the skill for Claude Code (optional)

The [`skill/`](skill/) folder contains a Claude Code skill — prompting tips, tool documentation and an image generation guide. The skill auto-activates when working with Gemini.

```bash
cp -r skill ~/.claude/skills/gemini-mcp
```

### 5. Verify

```bash
mcp-cli call gemini gemini_chat '{"prompt": "Hello!"}'
```

## Authentication

The server reads cookies from Chrome automatically via `browser-cookie3`.

> **Multiple Google accounts?** Auto-detection picks an unpredictable account. Use env vars `GEMINI_PSID` / `GEMINI_PSIDTS` to explicitly select the desired account.

If auto-detection fails or you have multiple accounts, set cookies manually:

1. Open Chrome DevTools on gemini.google.com → Application → Cookies
2. Copy `__Secure-1PSID` and `__Secure-1PSIDTS` values
3. Add to your MCP config:

```json
{
  "mcpServers": {
    "gemini": {
      "command": "uv",
      "args": ["run", "--with", "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git", "gemini-webapi-mcp"],
      "env": {
        "GEMINI_PSID": "your__Secure-1PSID_value",
        "GEMINI_PSIDTS": "your__Secure-1PSIDTS_value"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `gemini_generate_image` | Generate new or edit existing images |
| `gemini_upload_file` | Analyze files — video, images, PDF, documents |
| `gemini_analyze_url` | Analyze URLs — YouTube videos, webpages, articles |
| `gemini_chat` | Text chat (single or multi-turn) |
| `gemini_start_chat` | Start a multi-turn session |
| `gemini_reset` | Re-initialize client on auth errors |

## Models

| Model | Default for | Notes |
|-------|-------------|-------|
| `gemini-3.0-flash` | chat, file analysis | Fast |
| `gemini-3.0-pro` | image generation | Supports aspect ratios |
| `gemini-3.0-flash-thinking` | — | Shows reasoning process |

## Usage Examples

Generate an image:
```bash
mcp-cli call gemini gemini_generate_image '{"prompt": "a cat in watercolor style"}'
```

Edit an image:
```bash
mcp-cli call gemini gemini_generate_image '{"prompt": "make it gray", "files": ["/path/to/cat.png"]}'
```

Analyze a YouTube video or URL:
```bash
mcp-cli call gemini gemini_analyze_url '{"url": "https://youtube.com/watch?v=...", "prompt": "Summarize this video"}'
```

Analyze a file:
```bash
mcp-cli call gemini gemini_upload_file '{"file_path": "/path/to/video.mp4", "prompt": "What happens here?"}'
```

## License

MIT — free to use, modify, and distribute.

**[@AndyShaman](https://github.com/AndyShaman)** · [gemini-webapi-mcp](https://github.com/AndyShaman/gemini-webapi-mcp)
