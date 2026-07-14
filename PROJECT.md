# YouTube Transcriber — Project Info

## О проекте
Скачивает видео с YouTube (или берёт локальный файл), транскрибирует речь через Whisper и сохраняет текст с таймкодами. поддерживает русский, английский, украинский языки.

**GitHub:** https://github.com/viketvova/youtube-transcriber
**Путь:** `G:\!!!Python-for-L2-C1\youtube-transcriber\`
**Автор:** viketvova

---

## Стек технологий
- **faster-whisper** — транскрипция (модель medium по умолчанию)
- **yt-dlp** — скачивание видео с YouTube (через CLI с `--js-runtimes node`)
- **ffmpeg** — извлечение и конвертация аудио
- **tkinter** — GUI (Blender-style дизайн)
- **keyboard** — глобальный перехват Ctrl+V
- **pyperclip** — чтение буфера обмена
- **python-docx** — экспорт в DOCX
- **fpdf2** — экспорт в PDF
- **pystray** — минимизация в трей

---

## Структура файлов
```
youtube-transcriber/
├── gui.py              # GUI приложение (tkinter)
├── transcribe.py       # Ядро транскрипции + CLI
├── requirements.txt    # Зависимости
├── config.txt          # Настройки (theme, save_dir) — не коммитится
├── PROJECT.md          # Этот файл
├── transcriptions/     # Сохранённые транскрипции
├── downloads/          # Скачанные аудио файлы
└── error.log           # Лог ошибок (если есть)
```

---

## Что реализовано

### Основной функционал
- [x] Скачивание видео с YouTube (через yt-dlp CLI)
- [x] Транскрипция через faster-whisper (medium модель)
- [x] Авто-определение языка (auto/ru/en/uk)
- [x] Выбор временного промежутка (From/To)
- [x] Выбор модели (tiny/base/small/medium/large)
- [x] Пакетная обработка (несколько URL через Enter)
- [x] Транскрипция локальных файлов (mp3, mp4, ogg, wav, flac и др.)

### GUI
- [x] Blender-style дизайн (тёмный #303030, оранжевые акценты #e87d0d)
- [x] Две темы: Dark/Light с переключением
- [x] Сохранение темы между перезапусками (config.txt)
- [x] Вкладки: Transcribe, History, Settings
- [x] Прогресс-бар с ETA
- [x] Прогресс в заголовке окна [XX%]
- [x] Кнопка Copy Log
- [x] Минимизация в трей (pystray)

### History
- [x] Список файлов с поиском по имени
- [x] Превью содержимого файла
- [x] Поиск по тексту с find-next (как в Word)
- [x] Экспорт в DOCX/PDF из History
- [x] Кнопки "Transcriptions" и "Downloads" для открытия папок
- [x] Авто-обновление списка при переключении на вкладку
- [x] Обработка удалённых файлов (сообщение "File not found")

### Экспорт
- [x] TXT (основной формат)
- [x] DOCX (python-docx)
- [x] PDF (fpdf2)
- [x] Кнопки экспорта в Log и History

### Settings
- [x] Переключение темы (Dark/Light)
- [x] Кастомная папка сохранения
- [x] About секция

### Прочее
- [x] Ctrl+V работает через keyboard библиотеку (глобальный hotkey)
- [x] URL поле — multiline Text виджет (3 строки)
- [x] Скрытие окон subprocess (CREATE_NO_WINDOW)
- [x] Очистка temp файлов после транскрипции
- [x] Правильный язык в output файле (не хардкод "Russian")
- [x] Batch лог показывает реальное количество обработанных видео
- [x] Имя файла = название видео на YouTube

---

## Известные баги

| Баг | Серьёзность | Описание |
|-----|-------------|----------|
| Stop button | Высокая | Не останавливает транскрипцию mid-way (нужен threading.Event) |
| Export код | Средняя | Дублируется (4 метода вместо 2) — DOCX/PDF для Log и History |

---

## TODO (предложено, но не реализовано)

| Приоритет | Фича | Описание |
|-----------|------|----------|
| 1 | SRT/VTT субтитры | Форматирование для YouTube/видеоредакторов |
| 2 | Суммаризация AI | Gemini API (бесплатно) — краткое содержание |
| 3 | Перевод | Gemini API — перевод транскрипции |
| 4 | Speaker diarization | Кто говорит (pyannote) |
| 5 | Плейлисты | Обработка всего плейлиста |
| 6 | 1000+ сайтов | yt-dlp уже поддерживает (TikTok, Vimeo и др.) |

---

## Установка
```bash
pip install faster-whisper yt-dlp python-docx fpdf2 pystray keyboard pyperclip
```
ffmpeg должен быть в PATH.

---

## Запуск
```bash
python gui.py          # GUI
python transcribe.py URL  # CLI
```

---

## Конкуренты
| Инструмент | Цена | Что особенного |
|-----------|------|----------------|
| WhisperX (23k ★) | Бесплатно | Word-level timestamps, diarization |
| Descript | $24/мес | Редактирование видео через текст |
| Otter.ai | $17/мес | Real-time транскрипция |
| EchoQuill | $5/мес | AI суммаризация |
| Faster-Whisper-XXL-GUI | Бесплатно | SRT/VTT/JSON экспорт |

---

## Правила для будущих сессий
- **Git коммиты только после подтверждения пользователя** — не пушить пока не скажет "ок, пуш"
- Пользователь предпочитает короткие описания коммитов
- Пользователь на русском языке

---

## История изменений (ключевые)
- **Начало:** Базовый GUI + CLI транскрипция
- **Blender дизайн:** Тёмная тема, оранжевые акценты
- **Batch:** Несколько URL через Enter
- **Local files:** Поддержка mp3/mp4/ogg/wav и др.
- **Ctrl+V:** Через keyboard библиотеку (глобальный hotkey)
- **Minimize to tray:** Через pystray
- **Export:** DOCX/PDF из GUI
- **History:** Поиск, find-next, экспорт
- **Auto-detect language:** Whisper определяет язык
