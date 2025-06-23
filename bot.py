import os, json, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from fpdf import FPDF

HISTORY_FILE = 'history.json'
WORKS = ["демонтаж_дер_пола", "демонтаж_плитки", "демонтаж_дверей", "укладка_плитки", "укладка_пола", "штукатурка", "армстронг"]

def load_history():
    if os.path.exists(HISTORY_FILE):
        return json.load(open(HISTORY_FILE, 'r', encoding='utf-8'))
    base = {'meta': {'totals': {}}, 'days': {}}
    for w in WORKS: base['meta']['totals'][w] = None
    return base

def save_history(h): json.dump(h, open(HISTORY_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

async def start(u, c):
    await u.message.reply_text("Бот запущен.\nКоманды:\n/сегодня <работа> <объем>\n/set объем <работа> <всего>\n/отчет [дата]")

async def set_total(u, c):
    work, total = c.args[0].lower(), float(c.args[1])
    h = load_history()
    if work not in WORKS: return await u.message.reply_text("Неизвестная работа")
    h['meta']['totals'][work] = total
    save_history(h)
    await u.message.reply_text(f"Установлен общий объем по {work} = {total}")

async def today(u, c):
    work, amt = c.args[0].lower(), float(c.args[1])
    if work not in WORKS: return await u.message.reply_text("Неизвестная работа")
    h = load_history()
    today = datetime.date.today().isoformat()
    h['days'].setdefault(today, {})
    h['days'][today][work] = h['days'][today].get(work, 0) + amt
    save_history(h)
    await u.message.reply_text(f"Добавлено {amt} к {work} за {today}")

def make_pdf(report_date=None):
    h = load_history()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=f"Отчет за {report_date or 'все время'}", ln=1)

    if report_date:
        day = h['days'].get(report_date, {})
        for w, a in day.items():
            tot = h['meta']['totals'][w]
            pct = f" — {round(a / tot * 100)}%" if tot else ""
            pdf.cell(0, 8, f"{w}: {a}{pct}", ln=1)
    else:
        for w in WORKS:
            total = sum(d.get(w, 0) for d in h['days'].values())
            plan = h['meta']['totals'][w]
            pct = f" — {round(total / plan * 100)}%" if plan else ""
            pdf.cell(0, 8, f"{w}: {total}/{plan or '?'}{pct}", ln=1)

    filename = f"report_{report_date or 'all'}.pdf"
    pdf.output(filename)
    return filename

async def report(u, c):
    date = c.args[0] if c.args else None
    fn = make_pdf(date)
    await u.message.reply_document(open(fn, 'rb'))

app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_total))
app.add_handler(CommandHandler("сегодня", today))
app.add_handler(CommandHandler("отчет", report))
app.run_polling()
