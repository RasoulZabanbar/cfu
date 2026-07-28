from models.user import User, Participant
from services.bale_interactions import BaleClient
from services.phone import normalize_phone
bale_client = BaleClient()

from boot.config import get_env_setup


_config_env = get_env_setup()




def my_certificates_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "مشاهده گواهی های من", "callback_data": "show_certificates"}]
        ]
    }


admin_keyboard = {
    "keyboard": [
        [{"text": "📱 اشتراک شماره این حساب", "request_contact": True}]
        [{"text": "تحلیل رویداد ها", "web_app": {"url": "https://cfu.mirzahesab.ir/stats/loader_stats"}}],

    ],
    "resize_keyboard": True,
}


async def message_proccesor(message):
    bale_id = message["from"]["id"]
    chat_id = message["chat"]["id"]

    user, _ = await User.get_or_create(bale_id=bale_id)

    if "contact" in message:
        await _handle_contact(message, user, chat_id)
        return

    text = message.get("text", "")
    if text == "/start":
        await bale_client.send_message(
            chat_id=chat_id,
            text=(
                "سلام! 👋\n"
                "به ربات خوش آمدید.\n\n"
                "برای یافتن گواهینامه های شما  لطفاً با دکمه زیر شماره تماس خود را با ما به اشتراک بگذارید."
            ),
            reply_markup=my_certificates_keyboard(),
        )

        return

    # Fallback for any other text: re-prompt for phone if not linked yet
    existing = await Participant.get_or_none(user=user)
    if existing is None:
        await bale_client.send_message(
            chat_id=chat_id,
            text="لطفاً ابتدا شماره تماس خود را با استفاده از دکمه زیر ارسال کنید.",
            reply_markup=phone_keyboard(),
        )


async def _handle_contact(message, user: User, chat_id):
    contact = message["contact"]
    phone_number = normalize_phone(contact.get("phone_number", ""))

    participant = await Participant.get_or_none(phone_number=phone_number)

    if participant is None:
        await bale_client.send_message(
            chat_id=chat_id,
            text="متاسفانه شماره شما در لیست شرکت‌کنندگان یافت نشد. لطفاً با پشتیبانی تماس بگیرید.",
        )
        return

    # Assign this participant to the Bale user (idempotent — re-sharing contact is fine)
    if participant.user_id != user.id:
        participant.user_id = user.id
        await participant.save(update_fields=["user_id", "updated_at"])

    await bale_client.send_message(
        chat_id=chat_id,
        text=f"خوش آمدید {participant.full_name or ''} 👋\nشماره شما با موفقیت تایید شد.",
        reply_markup=my_certificates_keyboard(),
    )