import os
import logging
import random
import asyncio
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Poll, WebAppInfo, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PollAnswerHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
from config import BOT_TOKEN

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Словарь с вопросами для викторины
QUIZ_QUESTIONS = [
    {
        "question": "Где вы впервые встретились?",
        "options": ["В кафе", "На работе", "В университете", "В парке"],
        "correct": 1  # На работе
    },
    {
        "question": "Какое ваше любимое совместное занятие?",
        "options": ["Просмотр фильмов", "Путешествия", "Готовка", "Спорт"],
        "correct": 2  # Готовка
    },
    {
        "question": "Какой у вас любимый фильм для совместного просмотра?",
        "options": ["Романтическая комедия", "Триллер", "Драма", "Мультфильм"],
        "correct": 3  # Мультфильм
    },
    {
        "question": "Какое ваше любимое время года?",
        "options": ["Весна", "Лето", "Осень", "Зима"],
        "correct": 1  # Лето
    },
    {
        "question": "Какой у вас любимый ресторан для свиданий?",
        "options": ["Итальянский", "Японский", "Русский", "Французский"],
        "correct": 0  # Итальянский
    },
    {
        "question": "Какое ваше любимое место для прогулок?",
        "options": ["Парк", "Набережная", "Городской центр", "Природа"],
        "correct": 2  # Городской центр
    },
    {
        "question": "Какой у вас любимый праздник?",
        "options": ["Новый год", "День рождения", "День святого Валентина", "8 марта"],
        "correct": 0  # Новый год
    },
    {
        "question": "Какое ваше любимое время суток?",
        "options": ["Утро", "День", "Вечер", "Ночь"],
        "correct": 2  # Вечер
    }
]

# Словарь с романтическими заданиями
ROMANTIC_TASKS = [
    "Расскажите друг другу о своих мечтах",
    "Спойте друг другу песню",
    "Сделайте комплимент друг другу",
    "Расскажите о своих любимых воспоминаниях вместе",
    "Поделитесь своими планами на будущее",
    "Расскажите о том, что вас привлекает друг в друге",
    "Спойте дуэтом любимую песню",
    "Расскажите о своем идеальном свидании",
    "Сделайте друг другу массаж",
    "Напишите друг другу стихотворение"
]

# Словарь с вопросами для игры "Правда"
TRUTH_QUESTIONS = [
    "Какое твое самое счастливое воспоминание?",
    "Что ты больше всего ценишь в отношениях?",
    "Какой момент в нашей истории был для тебя самым важным?",
    "Что бы ты хотел(а) изменить в наших отношениях?",
    "Какое твое любимое качество в партнере?",
    "Что тебя больше всего привлекает в партнере?",
    "Какой момент в нашей истории был самым романтичным?",
    "Что бы ты хотел(а) сделать вместе в будущем?",
    "Какое твое любимое место для свиданий?",
    "Что тебя больше всего вдохновляет в отношениях?"
]

# Словарь с заданиями для игры "Действие"
DARE_TASKS = [
    "Сделай партнеру массаж",
    "Спой любимую песню партнера",
    "Станцуй под любимую музыку партнера",
    "Сделай партнеру комплимент",
    "Расскажи историю о том, как вы познакомились",
    "Сделай партнеру сюрприз",
    "Напиши стихотворение для партнера",
    "Сделай партнеру завтрак",
    "Устройте романтический ужин",
    "Сделайте фото вместе"
]

# Добавляем глобальную переменную для отслеживания текущего вопроса
current_question_index = 0

# Добавляем словарь для хранения состояния игр
games = {}

class TicTacToeGame:
    def __init__(self):
        self.board = ['' for _ in range(9)]
        self.players = {'X': None, 'O': None}
        self.current_turn = 'X'
        self.ready_players = set()
        self.game_active = False
        
    def add_player(self, user_id):
        if user_id not in self.ready_players:
            self.ready_players.add(user_id)
            if len(self.ready_players) == 2:
                # Назначаем символы игрокам
                players_list = list(self.ready_players)
                self.players['X'] = players_list[0]
                self.players['O'] = players_list[1]
                self.game_active = True
                return True
        return False
        
    def make_move(self, user_id, index):
        if not self.game_active:
            return None, "Игра еще не началась"
            
        player_symbol = 'X' if self.players['X'] == user_id else 'O'
        
        if user_id != self.players[self.current_turn]:
            return None, "Сейчас не ваш ход"
            
        if self.board[index] != '':
            return None, "Эта клетка уже занята"
            
        self.board[index] = player_symbol
        self.current_turn = 'O' if player_symbol == 'X' else 'X'
        
        # Проверяем победу
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # горизонтали
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # вертикали
            [0, 4, 8], [2, 4, 6]  # диагонали
        ]
        
        for combo in winning_combinations:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != '':
                self.game_active = False
                return combo, f"Победитель: {player_symbol}!"
                
        if '' not in self.board:
            self.game_active = False
            return None, "Ничья!"
            
        return None, None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("Начать викторину", callback_data='start_quiz')],
        [InlineKeyboardButton("Получить романтическое задание", callback_data='get_task')],
        [InlineKeyboardButton("Игра 'Правда или Действие'", callback_data='start_game')],
        [InlineKeyboardButton("Сыграть в крестики-нолики", web_app=WebAppInfo(url="https://arsentystreltsov.github.io/tic-tac-toe-telegram/"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет! Я бот для романтического свидания! 🥰\n"
        "Я помогу сделать ваше свидание более интересным и запоминающимся.\n"
        "Что бы вы хотели сделать?",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_quiz':
        await start_quiz(query, context)
    elif query.data == 'get_task':
        await get_romantic_task(query, context)
    elif query.data == 'start_game':
        await start_game(query, context)
    elif query.data == 'truth':
        await get_truth_question(query, context)
    elif query.data == 'dare':
        await get_dare_task(query, context)
    elif query.data == 'back_to_menu':
        await back_to_menu(query, context)
    elif query.data.startswith('answer_'):
        await handle_quiz_answer(update, context)

async def start_quiz(query, context):
    """Начало викторины"""
    global current_question_index
    question = QUIZ_QUESTIONS[current_question_index]
    
    # Отправляем сообщение с информацией о вопросе
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"Вопрос {current_question_index + 1} из {len(QUIZ_QUESTIONS)}:"
    )
    
    # Создаем опрос
    message = await context.bot.send_poll(
        chat_id=query.message.chat_id,
        question=question['question'],
        options=question['options'],
        type=Poll.QUIZ,
        correct_option_id=question['correct'],
        is_anonymous=False
    )
    
    # Сохраняем информацию об активном опросе
    context.bot_data.update({
        message.poll.id: {
            "chat_id": query.message.chat_id,
            "message_id": message.message_id,
            "correct_option": question['correct']
        }
    })
    
    # Удаляем предыдущее сообщение с кнопками
    await query.message.delete()

async def get_romantic_task(query, context):
    """Получение романтического задания"""
    task = random.choice(ROMANTIC_TASKS)
    keyboard = [[InlineKeyboardButton("Получить другое задание", callback_data='get_task')],
                [InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Ваше романтическое задание: {task} 💝",
        reply_markup=reply_markup
    )

async def start_game(query, context):
    """Начало игры"""
    keyboard = [
        [InlineKeyboardButton("Правда", callback_data='truth')],
        [InlineKeyboardButton("Действие", callback_data='dare')],
        [InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Давайте сыграем в игру 'Правда или Действие'!\n"
        "Выберите, что хотите:",
        reply_markup=reply_markup
    )

async def get_truth_question(query, context):
    """Получение вопроса для игры 'Правда'"""
    question = random.choice(TRUTH_QUESTIONS)
    keyboard = [
        [InlineKeyboardButton("Другой вопрос", callback_data='truth')],
        [InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Вопрос: {question}",
        reply_markup=reply_markup
    )

async def get_dare_task(query, context):
    """Получение задания для игры 'Действие'"""
    task = random.choice(DARE_TASKS)
    keyboard = [
        [InlineKeyboardButton("Другое задание", callback_data='dare')],
        [InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Задание: {task}",
        reply_markup=reply_markup
    )

async def back_to_menu(query, context):
    """Возврат в главное меню"""
    keyboard = [
        [InlineKeyboardButton("Начать викторину", callback_data='start_quiz')],
        [InlineKeyboardButton("Получить романтическое задание", callback_data='get_task')],
        [InlineKeyboardButton("Игра 'Правда или Действие'", callback_data='start_game')],
        [InlineKeyboardButton("Сыграть в крестики-нолики", web_app=WebAppInfo(url="https://arsentystreltsov.github.io/tic-tac-toe-telegram/"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Выберите, что хотите сделать:",
        reply_markup=reply_markup
    )

async def handle_quiz_answer(update: Update, context):
    """Обработка ответа на опрос"""
    global current_question_index
    answer = update.poll_answer
    poll_data = context.bot_data.get(answer.poll_id)
    
    if poll_data:
        if answer.option_ids[0] != QUIZ_QUESTIONS[current_question_index]['correct']:
            # Показываем правильный ответ только при неправильном ответе
            correct_answer = QUIZ_QUESTIONS[current_question_index]['options'][QUIZ_QUESTIONS[current_question_index]['correct']]
            await context.bot.send_message(
                chat_id=poll_data["chat_id"],
                text=f"❌ Неправильно. Правильный ответ: {correct_answer}"
            )
        
        # Переходим к следующему вопросу
        current_question_index = (current_question_index + 1) % len(QUIZ_QUESTIONS)
        
        # Предлагаем продолжить или вернуться в меню
        keyboard = [
            [InlineKeyboardButton("Следующий вопрос", callback_data='start_quiz')],
            [InlineKeyboardButton("Вернуться в меню", callback_data='back_to_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=poll_data["chat_id"],
            text="Хотите продолжить викторину?",
            reply_markup=reply_markup
        )

async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик данных от веб-приложения"""
    try:
        print("\n=== ПОЛУЧЕНЫ ДАННЫЕ ОТ ВЕБ-ПРИЛОЖЕНИЯ ===")
        print(f"Update ID: {update.update_id}")
        print(f"User ID: {update.effective_user.id}")
        print(f"Username: {update.effective_user.username}")
        print(f"Chat ID: {update.effective_chat.id}")
        print(f"Raw data: {update.effective_message.web_app_data.data}")
        
        # Пробуем разобрать данные
        data = json.loads(update.effective_message.web_app_data.data)
        print(f"Parsed data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        # Отправляем простой ответ
        message = {
            'type': 'playersUpdate',
            'readyCount': 1,  # Для теста
            'timestamp': data.get('timestamp')
        }
        
        print(f"Отправляем ответ: {json.dumps(message, indent=2, ensure_ascii=False)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=json.dumps(message)
        )
        
    except Exception as e:
        print(f"\n=== ОШИБКА ===")
        print(f"Тип: {type(e).__name__}")
        print(f"Сообщение: {str(e)}")
        if hasattr(update, 'effective_message'):
            await update.effective_message.reply_text(f"Произошла ошибка: {str(e)}")

def main() -> None:
    """Запуск бота"""
    # Получаем токен бота из переменных окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(PollAnswerHandler(handle_quiz_answer))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
    
    # Запускаем бота
    print("Запускаем бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Бот остановлен") 