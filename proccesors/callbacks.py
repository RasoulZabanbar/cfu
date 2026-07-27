from models.user import User, Participant, EventParticipant
from services.bale_interactions import BaleClient

bale_client = BaleClient()


async def handle_callback(callback: dict):
    callback_query_id = callback["id"]
    bale_id = callback["from"]["id"]

    chat_id = callback["message"]["chat"]["id"]
    message_id = callback["message"]["message_id"]

    data = callback["data"]

    await bale_client.answer_callback_query(callback_query_id)

    user = await User.get_or_none(bale_id=bale_id)
    if user is None:
        return

    participant = await Participant.get_or_none(user=user)
    if participant is None:
        await bale_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="ابتدا باید شماره تماس خود را ثبت کنید.",
        )
        return

    if data == "show_certificates":
        await _show_certificates(
            chat_id,
            message_id,
            participant,
        )

    elif data.startswith("event:"):
        event_id = int(data.split(":", 1)[1])

        await _send_license(
            chat_id,
            message_id,
            participant,
            event_id,
        )

        
async def _show_certificates(
    chat_id,
    message_id,
    participant: Participant,
):
    event_participants = (
        await EventParticipant.filter(participant=participant)
        .select_related("event")
    )

    if not event_participants:
        await bale_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="گواهی‌ای برای شما ثبت نشده است.",
        )
        return

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": ep.event.name,
                    "callback_data": f"event:{ep.event.id}",
                }
            ]
            for ep in event_participants
        ]
    }

    await bale_client.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text="یکی از رویدادهای زیر را انتخاب کنید:",
        reply_markup=keyboard,
    )



async def _send_license(
    chat_id,
    message_id,
    participant: Participant,
    event_id: int,
):
    ep = (
        await EventParticipant.get_or_none(
            participant=participant,
            event_id=event_id,
        )
        .select_related("event")
    )

    if ep is None or not ep.license_file:
        await bale_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="فایل گواهی برای این رویداد یافت نشد.",
        )
        return

    await bale_client.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=f"✅ گواهی «{ep.event.name}» در پیام بعدی برای شما ارسال شد.",
    )

    await bale_client.send_document_from_path(
        chat_id=chat_id,
        file_path=ep.license_file,
        filename=ep.original_filename or f"{ep.event.name}.pdf",
        caption=f"گواهی شما برای رویداد {ep.event.name}",
    )