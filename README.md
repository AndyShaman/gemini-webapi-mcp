[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/andyshaman-gemini-webapi-mcp-badge.png)](https://mseep.ai/app/andyshaman-gemini-webapi-mcp)

<h1 align="center">gemini-webapi-mcp</h1>

<p align="center">
  MCP-сервер для Google Gemini — генерация и редактирование изображений, чат и анализ файлов через браузерные cookies.<br>
  Без API-ключей. Бесплатно.
</p>

<p align="center">
  <a href="https://github.com/AndyShaman/gemini-webapi-mcp/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AndyShaman/gemini-webapi-mcp?style=flat-square&color=green" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/MCP-compatible-8A2BE2?style=flat-square" alt="MCP">
  <a href="https://github.com/AndyShaman/gemini-webapi-mcp/stargazers"><img src="https://img.shields.io/github/stars/AndyShaman/gemini-webapi-mcp?style=flat-square&color=yellow" alt="Stars"></a>
</p>

<p align="center">
  <a href="https://t.me/AI_Handler"><img src="https://img.shields.io/badge/Telegram-канал автора-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"></a>
  &nbsp;
  <a href="https://www.youtube.com/channel/UCLkP6wuW_P2hnagdaZMBtCw"><img src="https://img.shields.io/badge/YouTube-канал автора-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube"></a>
</p>

---

## Возможности

- **Генерация изображений** по текстовому описанию (Nano Banana 2 с поддержкой пропорций)
- **2x разрешение** — автоматически скачивает upscaled-версию (2048x2048 → 2816x1536 и выше)
- **Редактирование изображений** — отправьте картинку + промпт и получите изменённую версию
- **Анализ файлов** — видео, изображения, PDF, документы
- **Текстовый чат** с Gemini (Flash, Pro, Flash-Thinking)
- **Авто-удаление вотермарки** — математически точное удаление sparkle-метки Gemini (Reverse Alpha Blending)
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

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add-json gemini '{"command":"uv","args":["run","--with","gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git","gemini-webapi-mcp"]}'
```

Или добавьте вручную в `.mcp.json` в корне проекта:

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

</details>

<details>
<summary><b>Claude Desktop</b></summary>

Добавьте в конфиг Claude Desktop:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

</details>

<details>
<summary><b>Другие MCP-клиенты</b></summary>

Используйте стандартный MCP stdio-конфиг:

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

Путь к файлу конфига зависит от вашего MCP-клиента.

</details>
**Локальная установка (после клонирования)** — замените args на:

```json
"args": ["--directory", "/path/to/gemini-webapi-mcp", "run", "gemini-webapi-mcp"]
```

### 4. Установите скилл для Claude Code (опционально)

Папка [`skill/`](skill/) содержит скилл для Claude Code — подсказки по промптингу, документацию по тулам и гайд по генерации изображений. Скилл автоматически активируется при работе с Gemini.

```bash
cp -r skill ~/.claude/skills/gemini-mcp
```

### 5. Проверьте

Запустите сервер вручную — если инициализация прошла без ошибок, всё работает:

```bash
uv run --with "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git" gemini-webapi-mcp
```

После этого откройте Claude Code или Claude Desktop и попробуйте: *«Сгенерируй картинку кота в акварельном стиле через Gemini»*.

## Аутентификация

Сервер автоматически читает cookies из Chrome через `browser-cookie3`.

> **Несколько Google-аккаунтов?** Установите `GEMINI_ACCOUNT_INDEX` — номер аккаунта из Chrome (0 = первый, 1 = второй, ...). Посмотрите порядок: кликните на аватарку в gemini.google.com.

Если автоопределение cookies не работает, задайте их вручную:

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

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `GEMINI_PSID` | Значение cookie `__Secure-1PSID` | авто из Chrome |
| `GEMINI_PSIDTS` | Значение cookie `__Secure-1PSIDTS` | авто из Chrome |
| `GEMINI_LANGUAGE` | Язык ответов Gemini (`ru`, `en`, `ja`, ...) | `en` |
| `GEMINI_ACCOUNT_INDEX` | Индекс Google-аккаунта (0, 1, 2, ...) | `0` |

## Высокое разрешение (2x)

Сервер автоматически запрашивает у Google увеличенную версию сгенерированного изображения — тот же механизм, что использует кнопка "Download" в веб-интерфейсе Gemini. Google выполняет server-side upscale, и вы получаете изображение в 2x разрешении:

| Модель | Нативное | 2x (скачивается) |
|--------|----------|------------------|
| Flash-Thinking (16:9) | 1408x768 | 2816x1536 |
| Flash-Thinking (9:16) | 768x1376 | 1536x2752 |
| Flash-Thinking (1:1) | 1024x1024 | 2048x2048 |

Если 2x-версия недоступна (таймаут, ошибка сети), сервер автоматически использует нативное разрешение.

## Удаление вотермарки

Gemini добавляет sparkle-метку (четырёхконечную звёздочку) в правый нижний угол сгенерированных изображений. Сервер автоматически удаляет её с помощью алгоритма [Reverse Alpha Blending](https://github.com/allenk/GeminiWatermarkTool) — математически точного восстановления оригинальных пикселей. Никаких дополнительных зависимостей или скачивания моделей не требуется.

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
| `gemini-3.0-flash-thinking` | генерация изображений | Nano Banana 2, поддержка пропорций |
| `gemini-3.0-pro` | — | Альтернативная модель |

## Примеры использования

После настройки MCP-конфига Claude сам вызывает нужные инструменты. Просто попросите в чате:

| Задача | Что написать Claude |
|--------|---------------------|
| Сгенерировать изображение | *«Сгенерируй через Gemini кота в акварельном стиле»* |
| Отредактировать изображение | *«Отредактируй через Gemini /path/to/cat.png — сделай кота серым»* |
| Итеративная правка | *«Теперь сделай фон темнее»* (в том же разговоре) |
| Проанализировать видео | *«Проанализируй через Gemini это видео: https://youtube.com/watch?v=...»* |
| Проанализировать файл | *«Загрузи в Gemini /path/to/doc.pdf и сделай краткое резюме»* |

Инструменты, которые Claude вызовет:

```
gemini_generate_image(prompt="кот в акварельном стиле")
gemini_generate_image(prompt="сделай кота серым", files=["/path/to/cat.png"])
gemini_generate_image(prompt="сделай фон темнее", conversation_id=["c_abc", "r_123", "rc_456"])
gemini_analyze_url(url="https://youtube.com/watch?v=...", prompt="О чём это видео?")
gemini_upload_file(file_path="/path/to/doc.pdf", prompt="Сделай краткое резюме")
```

## Благодарности

Этот проект построен на основе библиотеки [gemini-webapi](https://github.com/HanaokaYuzu/Gemini-API) от [@HanaokaYuzu](https://github.com/HanaokaYuzu) (форк [@xob0t](https://github.com/xob0t/Gemini-API) с поддержкой curl_cffi) — реверс-инжиниринговой асинхронной Python-обёртки для веб-приложения Google Gemini. Лицензия: AGPL-3.0.

Удаление вотермарки основано на алгоритме [Reverse Alpha Blending](https://github.com/allenk/GeminiWatermarkTool) от [@allenk](https://github.com/allenk) (MIT License) и alpha-картах из [gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover) от [@GargantuaX](https://github.com/GargantuaX) (MIT License).

## Лицензия

[AGPL-3.0](LICENSE) — свободно используйте, модифицируйте и распространяйте при условии сохранения открытости исходного кода.

**[@AndyShaman](https://github.com/AndyShaman)** · [gemini-webapi-mcp](https://github.com/AndyShaman/gemini-webapi-mcp)

---

<h1 align="center">gemini-webapi-mcp</h1>

<p align="center">
  MCP server for Google Gemini — image generation/editing, chat and file analysis via browser cookies.<br>
  No API keys. Free.
</p>

<p align="center">
  <a href="https://github.com/AndyShaman/gemini-webapi-mcp/blob/main/LICENSE"><img src="https://img.shields.io/github/license/AndyShaman/gemini-webapi-mcp?style=flat-square&color=green" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/MCP-compatible-8A2BE2?style=flat-square" alt="MCP">
  <a href="https://github.com/AndyShaman/gemini-webapi-mcp/stargazers"><img src="https://img.shields.io/github/stars/AndyShaman/gemini-webapi-mcp?style=flat-square&color=yellow" alt="Stars"></a>
</p>

<p align="center">
  <a href="https://t.me/AI_Handler"><img src="https://img.shields.io/badge/Telegram-Author's_Channel-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram"></a>
  &nbsp;
  <a href="https://www.youtube.com/channel/UCLkP6wuW_P2hnagdaZMBtCw"><img src="https://img.shields.io/badge/YouTube-Author's_Channel-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="YouTube"></a>
</p>

---

## Features

- **Image generation** from text descriptions (Nano Banana 2 with aspect ratio support)
- **2x resolution** — automatically downloads upscaled version (2048x2048 → 2816x1536 and above)
- **Image editing** — send an image + prompt to get a modified version
- **File analysis** — video, images, PDF, documents
- **Text chat** with Gemini (Flash, Pro, Flash-Thinking)
- **Auto watermark removal** — lossless sparkle mark removal using Reverse Alpha Blending
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

<details>
<summary><b>Claude Code</b></summary>

```bash
claude mcp add-json gemini '{"command":"uv","args":["run","--with","gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git","gemini-webapi-mcp"]}'
```

Or add manually to `.mcp.json` in your project root:

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

</details>

<details>
<summary><b>Claude Desktop</b></summary>

Add to Claude Desktop config:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

</details>

<details>
<summary><b>Other MCP clients</b></summary>

Use the standard MCP stdio config:

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

Config file path depends on your MCP client.

</details>
**Local install (after cloning)** — replace args with:

```json
"args": ["--directory", "/path/to/gemini-webapi-mcp", "run", "gemini-webapi-mcp"]
```

### 4. Install the skill for Claude Code (optional)

The [`skill/`](skill/) folder contains a Claude Code skill — prompting tips, tool documentation and an image generation guide. The skill auto-activates when working with Gemini.

```bash
cp -r skill ~/.claude/skills/gemini-mcp
```

### 5. Verify

Run the server manually — if it initializes without errors, everything works:

```bash
uv run --with "gemini-webapi-mcp @ git+https://github.com/AndyShaman/gemini-webapi-mcp.git" gemini-webapi-mcp
```

Then open Claude Code or Claude Desktop and try: *"Generate a watercolor cat image with Gemini"*.

## Authentication

The server reads cookies from Chrome automatically via `browser-cookie3`.

> **Multiple Google accounts?** Set `GEMINI_ACCOUNT_INDEX` — the account number from Chrome (0 = first, 1 = second, ...). Check the order by clicking your avatar on gemini.google.com.

If cookie auto-detection fails, set them manually:

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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_PSID` | Cookie value `__Secure-1PSID` | auto from Chrome |
| `GEMINI_PSIDTS` | Cookie value `__Secure-1PSIDTS` | auto from Chrome |
| `GEMINI_LANGUAGE` | Gemini response language (`ru`, `en`, `ja`, ...) | `en` |
| `GEMINI_ACCOUNT_INDEX` | Google account index (0, 1, 2, ...) | `0` |

## High Resolution (2x)

The server automatically requests an upscaled version of each generated image — the same mechanism used by the "Download" button in Gemini's web interface. Google performs server-side upscaling, delivering images at 2x resolution:

| Model | Native | 2x (downloaded) |
|-------|--------|-----------------|
| Flash-Thinking (16:9) | 1408x768 | 2816x1536 |
| Flash-Thinking (9:16) | 768x1376 | 1536x2752 |
| Flash-Thinking (1:1) | 1024x1024 | 2048x2048 |

If the 2x version is unavailable (timeout, network error), the server automatically falls back to native resolution.

## Watermark Removal

Gemini adds a sparkle watermark (4-point star) to the bottom-right corner of generated images. The server automatically removes it using the [Reverse Alpha Blending](https://github.com/allenk/GeminiWatermarkTool) algorithm — a mathematically lossless recovery of original pixel values. No extra dependencies or model downloads required.

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
| `gemini-3.0-flash-thinking` | image generation | Nano Banana 2, supports aspect ratios |
| `gemini-3.0-pro` | — | Alternative model |

## Usage Examples

Once configured, Claude calls the right tools automatically. Just ask in chat:

| Task | What to tell Claude |
|------|---------------------|
| Generate an image | *"Generate a watercolor cat with Gemini"* |
| Edit an image | *"Edit /path/to/cat.png with Gemini — make the cat gray"* |
| Iterative refinement | *"Now make the background darker"* (same conversation) |
| Analyze a video | *"Analyze this video with Gemini: https://youtube.com/watch?v=..."* |
| Analyze a file | *"Upload /path/to/doc.pdf to Gemini and summarize it"* |

Tools that Claude will call:

```
gemini_generate_image(prompt="a cat in watercolor style")
gemini_generate_image(prompt="make it gray", files=["/path/to/cat.png"])
gemini_generate_image(prompt="make the background darker", conversation_id=["c_abc", "r_123", "rc_456"])
gemini_analyze_url(url="https://youtube.com/watch?v=...", prompt="Summarize this video")
gemini_upload_file(file_path="/path/to/doc.pdf", prompt="Summarize key points")
```

## Acknowledgements

This project is built on top of [gemini-webapi](https://github.com/HanaokaYuzu/Gemini-API) by [@HanaokaYuzu](https://github.com/HanaokaYuzu) (fork by [@xob0t](https://github.com/xob0t/Gemini-API) with curl_cffi support) — a reverse-engineered async Python wrapper for the Google Gemini web app. Licensed under AGPL-3.0.

Watermark removal based on the [Reverse Alpha Blending](https://github.com/allenk/GeminiWatermarkTool) algorithm by [@allenk](https://github.com/allenk) (MIT License) and alpha maps from [gemini-watermark-remover](https://github.com/GargantuaX/gemini-watermark-remover) by [@GargantuaX](https://github.com/GargantuaX) (MIT License).

## License

[AGPL-3.0](LICENSE) — free to use, modify, and distribute, provided the source code remains open.

**[@AndyShaman](https://github.com/AndyShaman)** · [gemini-webapi-mcp](https://github.com/AndyShaman/gemini-webapi-mcp)
