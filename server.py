from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.types import FSInputFile

import asyncio
import logging
import json


BOT_TOKEN = "7289756303:AAGSPRCfyoa7_Hk7WcD3QkooSDfaOENvHjg"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
MASKS_DATA = "masks.json"


try:
    with open(MASKS_DATA, 'r', encoding='utf-8') as f:
        masks_data = json.load(f)
    logging.info("Данные о масках успешно загружены.")

except FileNotFoundError:
    logging.error(f"Файл {MASKS_DATA} не найден.  Бот не сможет работать.")
    masks_data = []
except json.JSONDecodeError:
    logging.error(f"Ошибка декодирования JSON в файле {MASKS_DATA}. Проверьте формат файла.")
    masks_data = []


class UserData(StatesGroup):
    skin_type = State()
    allergy = State()
    allergy_type = State()
    sensitivity = State()
    age_group = State()
    skin_problem = State()
    desired_effect = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_data = {}


def create_keyboard(items, row_width=2):
    builder = ReplyKeyboardBuilder()
    for item in items:
        builder.add(KeyboardButton(text=item))
    builder.adjust(row_width)
    return builder.as_markup(resize_keyboard=True)


def create_final_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔄 Новый подбор")],
            [KeyboardButton(text="🔚 Завершить работу")]
        ],
        resize_keyboard=True
    )


@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()  # Сброс состояния
    await message.answer(
        "🧴 Привет! Я помогу тебе подобрать идеальную маску для лица. "
        "Давай начнем с определения твоего типа кожи.",
        reply_markup=create_keyboard(["Жирная", "Сухая", "Комбинированная", "Нормальная"])
    )
    await state.set_state(UserData.skin_type)


@dp.message(UserData.skin_type, F.text.in_(["Жирная", "Сухая", "Комбинированная", "Нормальная"]))
async def handle_skin_type(message: types.Message, state: FSMContext):
    user_data["user_skin_type"] = message.text
    await message.answer("⚠️ Есть ли у тебя аллергии?", reply_markup=create_keyboard(["Да", "Нет"]))
    await state.set_state(UserData.allergy)


@dp.message(UserData.allergy, F.text == "Да")
async def handle_allergy_yes(message: types.Message, state: FSMContext):
    await message.answer(
        "Выбери аллергены:",
        reply_markup=create_keyboard(["Фруктовые кислоты", "Мёд", "Эфирные масла", "Следующий вопрос"])
    )
    await state.set_state(UserData.allergy_type)


@dp.message(UserData.allergy, F.text == "Нет")
async def handle_allergy_no(message: types.Message, state: FSMContext):
    user_data["allergy"] = False
    await message.answer("👌 Хорошо! А как насчет чувствительности кожи?",
                         reply_markup=create_keyboard(["Чувствительная", "Нечувствительная"]))
    await state.set_state(UserData.sensitivity)


@dp.message(UserData.allergy_type, F.text.in_(["Фруктовые кислоты", "Мёд", "Эфирные масла"]))
async def handle_allergy_type(message: types.Message, state: FSMContext):
    if "allergies" not in user_data:
        user_data["allergies"] = []
    user_data["allergies"].append(message.text)
    await message.answer("Добавлено! Есть ещё аллергены?", reply_markup=create_keyboard(
        ["Фруктовые кислоты", "Мёд", "Эфирные масла", "Следующий вопрос"]))


@dp.message(UserData.allergy_type, F.text == "Следующий вопрос")
async def handle_allergy_next(message: types.Message, state: FSMContext):
    await message.answer("👌 Хорошо! А как насчет чувствительности кожи?",
                         reply_markup=create_keyboard(["Чувствительная", "Нечувствительная"]))
    await state.set_state(UserData.sensitivity)


@dp.message(UserData.sensitivity, F.text.in_(["Чувствительная", "Нечувствительная"]))
async def handle_sensitivity(message: types.Message, state: FSMContext):
    user_data["sensitivity"] = message.text
    await message.answer("👵 В какой возрастной категории ты находишься?",
                         reply_markup=create_keyboard(["До 18", "18–25", "25–35", "35+"]))
    await state.set_state(UserData.age_group)


@dp.message(UserData.age_group, F.text.in_(["До 18", "18–25", "25–35", "35+"]))
async def handle_age_group(message: types.Message, state: FSMContext):
    user_data["age_group"] = message.text
    await message.answer(
        "👩‍🔬 Какая у тебя основная проблема кожи?",
        reply_markup=create_keyboard(["Акне", "Пигментация", "Шелушение", "Воспаления", "Постакне", "Морщины"])
    )
    await state.set_state(UserData.skin_problem)


@dp.message(UserData.skin_problem,
            F.text.in_(["Акне", "Пигментация", "Шелушение", "Воспаления", "Постакне", "Морщины"]))
async def handle_skin_problem(message: types.Message, state: FSMContext):
    user_data["skin_problem"] = message.text
    await message.answer(
        "✨ Какой эффект ты хочешь получить от маски?",
        reply_markup=create_keyboard(
            ["Увлажнение", "Отшелушивание", "Матирование", "Подсушивание", "Осветление", "Лифтинг"])
    )
    await state.set_state(UserData.desired_effect)


@dp.message(UserData.desired_effect,
            F.text.in_(["Увлажнение", "Отшелушивание", "Матирование", "Подсушивание", "Осветление", "Лифтинг"]))
async def handle_desired_effect(message: types.Message, state: FSMContext):
    user_data["desired_effect"] = message.text
    await message.answer("🔍 Ищу подходящие маски...")
    recommendations = []
    for mask in masks_data:
        user_allergies = user_data.get('allergies', [])
        is_suitable = True
        if user_allergies:
            for allergy in user_allergies:
                if allergy.lower() in mask["ingredients"]:
                    is_suitable = False
        if (user_data["user_skin_type"] in mask["skin_type"] and
                user_data["desired_effect"] in mask["effect"] and user_data["skin_problem"] in mask["skin_problem"]
                and is_suitable):
            recommendations.append(mask)

    if recommendations:
        response = "🎉 Вот твои рекомендации:\n\n"
        await message.answer(
            response,
            parse_mode="Markdown"
        )
        for mask in recommendations:
            response_ = (
                f"🧴 {mask['name']}\n"
                f"📝 {mask['description']}\n"
                f"🔗 Ссылки: {', '.join([f'[{market}]({link})' for market, link in mask['market_links'].items()])}\n   "
            )
            try:  # Обрабатываем возможные ошибки при отправке фото
                async with ChatActionSender.upload_photo(bot=message.bot, chat_id=message.chat.id):
                    media = MediaGroupBuilder(caption="")
                    media.add_photo(FSInputFile(mask["image_url"]), mask["name"])
                    await asyncio.sleep(1)
                    await message.reply_media_group(media=media.build())
                await message.answer(
                    response_,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Ошибка при отправке маски {mask['name']}: {e}")
                await message.answer(
                    f"Ошибка при отправке маски {mask['name']}. Попробуйте позже.")
        await message.answer("Что делаем дальше?", reply_markup=create_final_menu())
    else:
        await message.answer("😔 К сожалению, подходящих масок не найдено.", reply_markup=create_final_menu())


@dp.message(F.text == "🔚 Завершить работу")
async def handle_finish(message: types.Message):
    await message.answer(
        "✅ Работа завершена. Спасибо за использование бота!",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔄 Начать заново")]],
            resize_keyboard=True
        )
    )


@dp.message(F.text == "🔄 Начать заново")
async def handle_restart(message: types.Message, state: FSMContext):
    await start_handler(message, state)


@dp.message(F.text == "🔄 Новый подбор")
async def handle_restart(message: types.Message, state: FSMContext):
    await start_handler(message, state)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
