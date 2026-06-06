/**
 * 텔레그램 복약 버튼 Webhook (Cloudflare Workers)
 * 버튼 탭 즉시 메시지를 "복용 완료"로 변경합니다.
 *
 * 환경 변수 (Worker Secrets):
 *   TELEGRAM_BOT_TOKEN  — @BotFather 토큰
 *   WEBHOOK_SECRET      — (선택) setWebhook secret_token 과 동일
 */

const CALLBACK_MED_TAKEN = "med_taken";

async function telegramApi(token, method, body) {
  const response = await fetch(
    `https://api.telegram.org/bot${token}/${method}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
  return response.json();
}

function cleanOriginalText(text) {
  return (text || "")
    .replace("💊 ", "")
    .replace("✅ ", "")
    .trim();
}

export default {
  async fetch(request, env) {
    if (request.method === "GET") {
      return new Response("telegram-medication-webhook ok");
    }
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const token = env.TELEGRAM_BOT_TOKEN;
    if (!token) {
      return new Response("TELEGRAM_BOT_TOKEN not configured", { status: 500 });
    }

    const secret = env.WEBHOOK_SECRET || "";
    if (secret) {
      const header = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
      if (header !== secret) {
        return new Response("Unauthorized", { status: 401 });
      }
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("Invalid JSON", { status: 400 });
    }

    const callback = update.callback_query;
    if (!callback || callback.data !== CALLBACK_MED_TAKEN) {
      return new Response("ok");
    }

    const msg = callback.message || {};
    const chatId = msg.chat?.id;
    const messageId = msg.message_id;
    const originalText = cleanOriginalText(msg.text);

    if (!chatId || !messageId || !originalText) {
      return new Response("ok");
    }

    if (originalText.includes("복용 완료")) {
      await telegramApi(token, "answerCallbackQuery", {
        callback_query_id: callback.id,
        text: "이미 체크했어요.",
      });
      return new Response("ok");
    }

    await telegramApi(token, "answerCallbackQuery", {
      callback_query_id: callback.id,
      text: "복용 완료!",
    });

    await telegramApi(token, "editMessageText", {
      chat_id: chatId,
      message_id: messageId,
      text: `✅ ${originalText}\n\n복용 완료`,
      reply_markup: { inline_keyboard: [] },
    });

    return new Response("ok");
  },
};
