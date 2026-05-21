import pathlib
import asyncio
import json
import math
import pandas as pd
import numpy as np
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from razdel import sentenize

from funcs import get_best_bert_chunks, aggregate_economic_data, get_macro_models_results
from macro_models import sign_to_text, is_lm_bp, is_mp_pc, ad_as, solow_hr, ramsey_model

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

TELEGRAM_BOT_TOKEN = ""

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

class MacroBotStates(StatesGroup):
    waiting_for_news = State()
    choosing_difficulty = State()
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📰 Начать")],
    ],
    resize_keyboard=True
)

difficulty_kb = InlineKeyboardMarkup(
    inline_keyboard=[[
        InlineKeyboardButton(text="💡 Просто разобраться", callback_data="easy"),
        InlineKeyboardButton(text="📊 Глубокий разбор", callback_data="hard")
    ]]
)

new_news_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="➕ Проанализировать новую макроэкономическую новость")]],
    resize_keyboard=True
)


# Команда /start
@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear() # Сбрасываем стейт на старте
    await message.answer(
        "Привет, я макро-бот! 📉📈\n\n"
        "Я помогаю анализировать макроэкономические новости с помощью моделей.\n"
        "Нажми кнопку «Начать», чтобы отправить новость.",
        reply_markup=main_menu_kb
    )

@dp.message(F.text.in_({"📰 Начать", "➕ Проанализировать новую макроэкономическую новость"}))
async def ask_for_news(message: types.Message, state: FSMContext):
    await message.answer("Пришли мне свою макроэкономическую новость, и я займусь её разбором:")
    await state.set_state(MacroBotStates.waiting_for_news)

# Обработка самой новости
@dp.message(MacroBotStates.waiting_for_news)
async def process_news_handler(message: types.Message, state: FSMContext):
    prompt = message.text.strip()
    await message.answer(f"⏳ Проверяю наличие макроэкономического содержания в новости:\n\n*{prompt}*", parse_mode="Markdown")

    try:
        chunks = get_best_bert_chunks(prompt)

        await state.update_data(news_prompt=prompt, chunks=chunks)

        macro_chunks_detected = len(chunks)

        if macro_chunks_detected == 0:
            await message.answer("Макроэкономическое содержание в новости не найдено ❌", reply_markup=new_news_kb)
            await state.clear()
        else:
            await message.answer(
                f"Найдено подходящих фрагментов: {len(chunks)}.\n"
                "Выбери глубину анализа:",
                reply_markup=difficulty_kb
            )
            await state.set_state(MacroBotStates.choosing_difficulty)

    except Exception as e:
        await message.answer(f"❌ Ошибка при первичном анализе: {e}", reply_markup=new_news_kb)
        await state.clear()

@dp.callback_query(MacroBotStates.choosing_difficulty, F.data.in_({"easy", "hard"}))
async def handle_difficulty_choice(callback: types.CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    prompt = user_data.get("news_prompt")
    chunks = user_data.get("chunks", [])

    await callback.answer()

    await callback.message.answer(f"🔄 Выполняю анализ в режиме: *{ 'Простой' if callback.data == 'easy' else 'Глубокий разбор' }*", parse_mode="Markdown")

    try:
        results = []
        for chunk in chunks:
            # ## macro_chunks += model_bert(chunk)
            # ## results.append(model_qwen(chunk))
            pass

        res = aggregate_economic_data(results)
        ans_final = get_macro_models_results(res) if res is not None else "ВВП вырастет"

        if callback.data == "easy":
            await callback.message.answer(f"💡 **Краткий вывод:**\nВВП реагирует на новость.")
        else:
            await callback.message.answer(f"📊 **Финальный макро-вердикт:**\n{ans_final}\n\nДетальный анализ завершен.")

        await callback.message.answer("Хочешь проанализировать что-то еще?", reply_markup=new_news_kb)
        await state.clear()

    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при генерации финального ответа: {e}", reply_markup=new_news_kb)
        await state.clear()


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    print('Запускаем макро-бота...')
    asyncio.run(main())