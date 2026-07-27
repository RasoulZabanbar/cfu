# scripts/set_webhook.py
"""
Standalone script to (re)register the Bale bot webhook.

Run directly, separate from the app:
    python -m scripts.set_webhook
or:
    python scripts/set_webhook.py

Useful whenever BALE_WEBHOOK_URL changes (new domain, ngrok tunnel,
staging vs prod) without having to restart/redeploy the whole bot.
"""
import asyncio

from boot.config import get_env_setup
from services.bale_interactions import BaleClient

env_setup = get_env_setup()
BALE_WEBHOOK_URL = env_setup.bale_webhook_url

bale_client = BaleClient()


async def set_webhook():
    if not BALE_WEBHOOK_URL:
        print("⚠️ BALE_WEBHOOK_URL is not configured.")
        return

    try:
        await bale_client.set_webhook(BALE_WEBHOOK_URL)
        print(f"✅ Webhook set successfully: {BALE_WEBHOOK_URL}/webhook")
    except Exception as e:
        print(f"❌ Failed to set webhook: {e}")


async def delete_webhook():
    """Handy when switching back to polling or tearing down a staging bot."""
    try:
        await bale_client.delete_webhook()
        print("✅ Webhook deleted successfully.")
    except Exception as e:
        print(f"❌ Failed to delete webhook: {e}")


async def get_webhook_info():
    """Quick sanity check for what Bale currently has registered."""
    try:
        info = await bale_client.get_webhook_info()
        print(f"ℹ️ Current webhook info: {info}")
        return info
    except Exception as e:
        print(f"❌ Failed to fetch webhook info: {e}")


if __name__ == "__main__":
    asyncio.run(set_webhook())