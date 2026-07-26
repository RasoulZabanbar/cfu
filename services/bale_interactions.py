import json
import mimetypes
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import httpx

from boot.config import get_env_setup


class BaleClient:
    """
    Client for the Bale Bot API.

    Wraps both the JSON-based endpoints (sendMessage, editMessageText,
    deleteMessage) and the multipart/form-data endpoints (sendPhoto,
    sendDocument, sendVideo, sendVoice), and caches file_ids for
    previously-uploaded *static* media (files under `image_dir`) so
    repeat sends reuse them instead of re-uploading.

    The `send_*_from_path` variants below are for one-off files that
    live at an arbitrary path (e.g. admin-uploaded button scenarios
    under static/uploads/buttons/{button_id}/) — no file_id caching,
    since there's nothing to reuse a second time for those.
    """

    IMAGE_DIR = "static/images"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        api_base: Optional[str] = None,
        image_dir: Optional[str] = None,
    ):
        env_setup = get_env_setup()

        self.bot_token = bot_token or env_setup.bale_bot_token
        base = api_base or env_setup.bale_api_base
        self.api_base = f"{base}{self.bot_token}"
        self.image_dir = image_dir or self.IMAGE_DIR

        # file_id caches, keyed by local filename
        self._photo_file_ids: dict[str, str] = {}
        self._video_file_ids: dict[str, str] = {}
        self._voice_file_ids: dict[str, str] = {}

    # ------------------------------------------------------------------
    # low-level request helpers
    # ------------------------------------------------------------------

    async def _request(self, method: str, payload: dict) -> dict:
        """Call a Bale API method with a JSON payload."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.api_base}/{method}", json=payload)

        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            raise Exception(
                f"Bale API Error: {data.get('error_code')} - {data.get('description')}"
            )

        return data["result"]

    async def _post_form(self, method: str, *, data=None, files=None) -> dict:
        """Call a Bale API method using form fields (multipart for file uploads)."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.api_base}/{method}", data=data, files=files)

        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            raise Exception(
                f"Bale API Error: {result.get('error_code')} - {result.get('description')}"
            )

        return result["result"]

    @staticmethod
    def _encode_reply_markup(data: dict, reply_markup) -> None:
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)

    # ------------------------------------------------------------------
    # messages
    # ------------------------------------------------------------------

    async def send_message(self, chat_id, text=None, reply_markup=None) -> dict:
        payload = {"chat_id": chat_id}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        if text:
            payload["text"] = text

        return await self._request("sendMessage", payload)

    async def edit_message_text(
        self,
        chat_id: Union[str, int],
        message_id: int,
        text=None,
        reply_markup=None,
    ) -> dict:
        """
        Edit the text (and optionally the inline keyboard) of an existing message.
        Omitting reply_markup clears any inline keyboard attached to the message.
        """
        payload = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        if text:
            payload["text"] = text

        return await self._request("editMessageText", payload)

    async def delete_message(self, chat_id: Union[str, int], message_id: int) -> dict:
        payload = {"chat_id": str(chat_id), "message_id": message_id}
        return await self._request("deleteMessage", payload)

    async def answer_callback_query(self, callback_query_id: str) -> dict:
        """Answer a callback query to remove the loading state."""
        payload = {"callback_query_id": callback_query_id}
        return await self._request("answerCallbackQuery", payload)

    # ------------------------------------------------------------------
    # media — static assets under self.image_dir, cached by file_id
    # ------------------------------------------------------------------

    async def send_photo(
        self,
        chat_id: Union[str, int],
        image_name: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        image_path = f"{self.image_dir}/{image_name}"
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)

        if image_name in self._photo_file_ids:
            data["photo"] = self._photo_file_ids[image_name]
            return await self._post_form("sendPhoto", data=data)

        with open(image_path, "rb") as f:
            files = {"photo": (image_name, f, "image/png")}
            sent = await self._post_form("sendPhoto", data=data, files=files)

        photos = sent.get("photo", [])
        if photos:
            # last entry corresponds to the largest size
            self._photo_file_ids[image_name] = photos[-1]["file_id"]

        return sent

    async def send_document(
        self,
        chat_id: Union[str, int],
        file_bytes: BytesIO,
        filename: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        """Send a document (e.g. PDF) to a chat via the Bale Bot API."""
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)

        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"

        files = {"document": (filename, file_bytes, content_type)}

        return await self._post_form("sendDocument", data=data, files=files)

    async def send_video(
        self,
        chat_id: Union[str, int],
        file_name: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        file_path = f"{self.image_dir}/{file_name}"
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)

        if file_name in self._video_file_ids:
            data["video"] = self._video_file_ids[file_name]
            return await self._post_form("sendVideo", data=data)

        with open(file_path, "rb") as f:
            files = {"video": (file_name, f, "video/mp4")}
            sent = await self._post_form("sendVideo", data=data, files=files)

        video = sent.get("video", {})
        if video and "file_id" in video:
            self._video_file_ids[file_name] = video["file_id"]

        return sent

    async def send_voice(
        self,
        chat_id: Union[str, int],
        file_name: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        file_path = f"{self.image_dir}/{file_name}"
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)

        if file_name in self._voice_file_ids:
            data["voice"] = self._voice_file_ids[file_name]
            return await self._post_form("sendVoice", data=data)

        with open(file_path, "rb") as f:
            files = {"voice": (file_name, f, "audio/ogg")}
            sent = await self._post_form("sendVoice", data=data, files=files)

        voice = sent.get("voice", {})
        if voice and "file_id" in voice:
            self._voice_file_ids[file_name] = voice["file_id"]

        return sent

    # ------------------------------------------------------------------
    # media — one-off files at an arbitrary absolute path, no caching
    # (used for admin-uploaded button scenario attachments)
    # ------------------------------------------------------------------

    async def send_photo_from_path(
        self,
        chat_id: Union[str, int],
        file_path: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)
        content_type = mimetypes.guess_type(file_path)[0] or "image/jpeg"
        with open(file_path, "rb") as f:
            files = {"photo": (Path(file_path).name, f, content_type)}
            return await self._post_form("sendPhoto", data=data, files=files)

    async def send_video_from_path(
        self,
        chat_id: Union[str, int],
        file_path: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)
        content_type = mimetypes.guess_type(file_path)[0] or "video/mp4"
        with open(file_path, "rb") as f:
            files = {"video": (Path(file_path).name, f, content_type)}
            return await self._post_form("sendVideo", data=data, files=files)

    async def send_voice_from_path(
        self,
        chat_id: Union[str, int],
        file_path: str,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        data = {"chat_id": str(chat_id), "caption": caption}
        self._encode_reply_markup(data, reply_markup)
        content_type = mimetypes.guess_type(file_path)[0] or "audio/ogg"
        with open(file_path, "rb") as f:
            files = {"voice": (Path(file_path).name, f, content_type)}
            return await self._post_form("sendVoice", data=data, files=files)

    async def send_document_from_path(
        self,
        chat_id: Union[str, int],
        file_path: str,
        filename: Optional[str] = None,
        caption: str = "",
        reply_markup=None,
    ) -> dict:
        with open(file_path, "rb") as f:
            return await self.send_document(
                chat_id,
                BytesIO(f.read()),
                filename or Path(file_path).name,
                caption=caption,
                reply_markup=reply_markup,
            )



    async def set_webhook(self, url: str) -> dict:
        """Register `url` (without the trailing /webhook — that's appended here)."""
        return await self._request("setWebhook", {"url": f"{url}/webhook"})

    async def delete_webhook(self) -> dict:
        """Unregister the current webhook (e.g. before switching to polling)."""
        return await self._request("deleteWebhook", {})

    async def get_webhook_info(self) -> dict:
        """Fetch Bale's current webhook registration, for sanity-checking."""
        return await self._request("getWebhookInfo", {})
# ----------------------------------------------------------------------
# Usage:
#
#   bale_client = BaleClient()  # module-level singleton, e.g. in a bale_client.py
#
#   await bale_client.send_message(chat_id, "hello")
#   await bale_client.send_photo(chat_id, "welcome.png", caption="hi")
#
# In DDD terms this fits naturally as an infrastructure-layer adapter,
# injected into use cases / repositories rather than imported as a set
# of bare functions.
# ----------------------------------------------------------------------