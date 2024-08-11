"""
This module defines the core of the RoofRealEstate Telegram bot.

Functions:
    - send_welcome: Greets the user and provides initial instructions.
    - handle_message: Processes incoming messages from users.
    - process_category: Handles the selection of property categories.
    - get_city: Retrieves the city information from the user.
    - process_city: Manages the city selection process.
    - (Additional functions for further steps.)

Third-party imports:
    - telebot: Used for interacting with the Telegram Bot API.

Local imports:
    - get_result: Module for calculating the estimated price of
        a real estate property.
    - cfg: Configuration settings for the bot.

The bot guides users through a series of inputs regarding real estate
property features (e.g., production year, etc.), constructs a
filter dictionary, and passes it to the get_result module to
obtain an estimated price for the property.
"""

import telebot
from telebot import types

import get_result
import cfg

bot = telebot.TeleBot(cfg.bot_api)

filters = {}
user_state = {}

STATE_CATEGORY = 1
STATE_CITY = 2
STATE_DISTRICT = 3
STATE_DAYS = 4
STATE_DETAILS = 5
STATE_CONFIRM = 6
GO_BACK = "بازگشت به مرحله قبل"


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_state[message.chat.id] = STATE_CATEGORY
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    for category in cfg.categories:
        markup.row(category)
    bot.send_message(
        message.chat.id,
        "دسته بندی مورد نظر را انتخاب کنید:",
        reply_markup=markup,
    )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    state = user_state.get(message.chat.id)
    if message.text == GO_BACK:
        go_back(message)
    elif state == STATE_CATEGORY:
        process_category(message)
    elif state == STATE_CITY:
        process_city(message)
    elif state == STATE_DISTRICT:
        process_district(message)
    elif state == STATE_DAYS:
        process_days(message)
    elif state == STATE_DETAILS:
        process_details(message)
    elif state == STATE_CONFIRM:
        process_confirmation(message)
    else:
        bot.send_message(
            message.chat.id, "لطفاً با استفاده از /start شروع کنید."
        )


def process_category(message):
    if check_inputs(message, cfg.categories):
        filters["category"] = {
            "en": cfg.categories[message.text],
            "fa": message.text,
        }
        bot.send_message(
            message.chat.id, f"شما {message.text} را انتخاب کردید."
        )
        user_state[message.chat.id] = STATE_CITY
        get_city(message)
    else:
        bot.send_message(
            message.chat.id,
            "انتخاب نامعتبر است. لطفاً یکی از گزینه‌ها را انتخاب کنید.",
        )
        send_welcome(message)


def get_city(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    markup.row(GO_BACK)
    for city in cfg.cities:
        markup.row(city)

    bot.send_message(
        message.chat.id,
        "شهر مورد نظر را انتخاب کنید:",
        reply_markup=markup,
    )


def process_city(message):
    if check_inputs(message, cfg.cities):
        filters["city"] = {"en": cfg.cities[message.text], "fa": message.text}
        bot.send_message(
            message.chat.id, f"شما {message.text} را انتخاب کردید."
        )
        user_state[message.chat.id] = STATE_DISTRICT
        get_district(message)
    else:
        bot.send_message(
            message.chat.id,
            "انتخاب نامعتبر است. لطفاً یکی از گزینه‌ها را انتخاب کنید.",
        )
        get_city(message)


def get_district(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    markup.row(GO_BACK)
    for district in cfg.districts[filters["city"]["en"]].values():
        markup.add(district)
    bot.send_message(
        message.chat.id,
        "لطفاً منطقه مورد نظر را وارد کنید:",
        reply_markup=markup,
    )


def process_district(message):
    en, fa = find_district(message.text)
    if fa:
        filters["district"] = {"en": en, "fa": fa}
        bot.send_message(message.chat.id, f"شما {fa} را انتخاب کردید.")
        user_state[message.chat.id] = STATE_DAYS
        get_days(message)
    else:
        bot.send_message(
            message.chat.id,
            "منطقه نامعتبر است. لطفاً دوباره تلاش کنید.",
        )
        get_district(message)


def get_days(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    markup.row(GO_BACK)
    bot.send_message(
        message.chat.id,
        "لطفاً تعداد روزها را وارد کنید (بین 1 تا 90):",
        reply_markup=markup,
    )


def process_days(message):
    try:
        days = int(message.text)
        if 1 <= days <= 90:
            filters["days"] = days
            bot.send_message(
                message.chat.id, f"شما {days} روز را انتخاب کردید."
            )
            if filters["category"]["en"] in ["Apartment", "Villa"]:
                user_state[message.chat.id] = STATE_DETAILS
                get_details(message)
            else:
                confirm_filters(message)
        else:
            bot.send_message(
                message.chat.id,
                "تعداد روز نامعتبر است. لطفاً عددی بین 1 تا 90 وارد کنید.",
            )
            get_days(message)
    except ValueError:
        bot.send_message(
            message.chat.id,
            "ورودی نامعتبر است. لطفاً عددی بین 1 تا 90 وارد کنید.",
        )
        get_days(message)


def get_details(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    markup.row(GO_BACK)
    apartment_msg = "لطفا جزئیات آپارتمان را به شکل زیر وارد کنید:\n"
    apartment_msg += (
        "طبقه:2،کل طبقات:4،ساخت:1390،اتاق:3،آسانسور،پارکینگ،انباری"
    )
    apartment_msg = """
        لطفا جزئیات آپارتمان را به شکل زیر وارد کنید:

        طبقه:2
        کل طبقات:4
        ساخت:1390
        اتاق:3
        آسانسور
        پارکینگ
        انباری

        نکته 1: میتوانید یک یا چند بخش را وارد نکنید.
        مثلا فقط طبقه را وارد کنید.
        مثال:
        طبقه:3
        آسانسور
        وجود آسانسور، پارکینگ و انباری به این معنی ست که ملک مورد نظر،
        حتما این موارد را داشته باشد،
        در صورتی که مهم نیست، این موارد را ننویسید.
        نکته 2: حتما از دونقطه و ویرگول، بدون فاصله های اضافی
        و به شکل گفته شده (هر سطر یک مورد) استفاده کنید.
        نکته 3: در صورتی که موردی را اشتباه وارد کنید،
        امکان بازگشت و اصلاح وجود دارد.
    """
    villa_msg = """
        لطفا جزئیات ملک ویلایی را به شکل زیر وارد کنید:

        ساخت:1390
        اتاق:3
        بالکن
        پارکینگ
        انباری

        نکته 1: میتوانید یک یا چند بخش را وارد نکنید.
        مثلا فقط ساخت را وارد کنید.
        مثال:
        ساخت:1400
        بالکن
        وجود بالکن، پارکینگ و انباری به این معنی ست که ملک مورد نظر،
        حتما این موارد را داشته باشد،
        در صورتی که مهم نیست، این موارد را ننویسید.
        نکته 2: حتما از دونقطه و ویرگول، بدون فاصله های اضافی
        و به شکل گفته شده استفاده کنید.
        نکته 3: در صورتی که موردی را اشتباه وارد کنید،
        امکان بازگشت و اصلاح وجود دارد.
    """
    msg = ""
    match filters["category"]["en"]:
        case "Apartment":
            msg = apartment_msg
        case "Villa":
            msg = villa_msg
    if filters["category"]["en"] in ("Apartment", "Villa"):
        bot.send_message(
            message.chat.id,
            msg,
            reply_markup=markup,
        )
    else:
        confirm_filters(message)


def process_details(message):
    details = message.text.strip().split("\n")
    all_details = [item.split(":") for item in details]
    filters["details"] = all_details
    confirm_filters(message)


def confirm_filters(message):
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=True
    )
    markup.row("تائید فیلتر ها و ادامه", "شروع مجدد از اول")
    markup.row(GO_BACK)
    filter_summary = "\n".join(
        [f"{key}: {value}" for key, value in filters.items()]
    )
    bot.send_message(
        message.chat.id,
        f"فیلترهای شما:\n{filter_summary}\nآیا تأیید می‌کنید؟",
        reply_markup=markup,
    )
    user_state[message.chat.id] = STATE_CONFIRM


def process_confirmation(message):
    global filters
    if message.text == "تائید فیلتر ها و ادامه":
        bot.send_message(
            message.chat.id, "فیلترها تأیید شدند. لطفا کمی صبر کنید..."
        )
        result = escape_markdown_v2(
            get_result.request_to_webapp(
                {
                    "days": filters["days"],
                    "category": filters["category"]["en"],
                    "city": filters["city"]["en"],
                    "district": filters["district"]["en"],
                    "details": filters.get("details"),
                }
            )
        )
        bot.send_message(message.chat.id, result, parse_mode="MarkdownV2")
        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True, one_time_keyboard=True
        )
        markup.row("شروع مجدد از اول")
        markup.row(GO_BACK)
        bot.send_message(
            message.chat.id,
            "لطفا انتخاب کنید:",
            reply_markup=markup,
        )
    elif message.text == "شروع مجدد از اول":
        bot.send_message(message.chat.id, "لطفاً دوباره تلاش کنید.")
        filters = {}
        send_welcome(message)
    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌ها را انتخاب کنید")


def check_inputs(message, valid_values):
    return message.text in valid_values


def find_district(input_text):
    for en, fa in cfg.districts[filters["city"]["en"]].items():
        if input_text in fa:
            return en, fa
    return None, None


def go_back(message):
    state = user_state.get(message.chat.id)
    if state == STATE_CITY:
        user_state[message.chat.id] = STATE_CATEGORY
        send_welcome(message)
    elif state == STATE_DISTRICT:
        user_state[message.chat.id] = STATE_CITY
        get_city(message)
    elif state == STATE_DAYS:
        user_state[message.chat.id] = STATE_DISTRICT
        get_district(message)
    elif state == STATE_DETAILS:
        user_state[message.chat.id] = STATE_DAYS
        get_days(message)
    elif state == STATE_CONFIRM:
        user_state[message.chat.id] = STATE_DETAILS
        if filters.get("category").get("en") == "Land":
            get_days(message)
        else:
            get_details(message)
    else:
        bot.send_message(
            message.chat.id, "لطفاً با استفاده از /start شروع کنید."
        )


def escape_markdown_v2(text) -> str:
    escape_chars = r"\_~`>#+-=|{}.!"
    return "".join(
        ["\\" + char if char in escape_chars else char for char in text]
    )


bot.infinity_polling()
