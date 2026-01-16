const BACKEND_URL = "http://127.0.0.1:5001";

const I18N = {
  en: {
    title: "Kingston Waste Collection Assistant",
    subtitle: "Ask me anything about your waste, recycling, and organics pickup!",
    changeLang: "Change language",
    intro: "Hi! I can help you with waste collection in Kingston. Try asking:",
    ex1: "\"When is my next garbage pickup on Princess Street?\"",
    ex2: "\"Where do batteries go?\"",
    ex3: "\"Can I recycle a pizza box?\"",
    tip: "Tip: For this demo, I recognize a limited set of streets (try: Princess, Gardiners, Chelsea, Napier, Evergreen).",
    placeholder: "Ask about your waste collection...",
    send: "Send",
    disclaimer: "Demo for Kingston Civic Hackathon • Data may not reflect current schedules",
    thinking: "Thinking..."
  },
  fr: {
    title: " Assistant de collecte des déchets – Kingston",
    subtitle: "Posez une question sur les ordures, le recyclage et les matières organiques.",
    changeLang: "Changer de langue",
    intro: "Salut! Je peux vous aider avec la collecte des déchets à Kingston. Essayez :",
    ex1: "\"Quand est ma prochaine collecte sur Princess Street?\"",
    ex2: "\"Où vont les piles?\"",
    ex3: "\"Puis-je recycler une boîte à pizza?\"",
    tip: "Astuce : cette démo reconnaît un nombre limité de rues (ex. Princess, Gardiners, Chelsea, Napier, Evergreen).",
    placeholder: "Posez une question…",
    send: "Envoyer",
    disclaimer: "Démo • Les données peuvent ne pas être à jour",
    thinking: "Réflexion..."
  },
  es: {
    title: " Asistente de recolección de residuos – Kingston",
    subtitle: "Pregunta sobre basura, reciclaje y orgánicos.",
    changeLang: "Cambiar idioma",
    intro: "¡Hola! Puedo ayudarte con la recolección de residuos en Kingston. Prueba:",
    ex1: "\"¿Cuándo es mi próxima recolección en Princess Street?\"",
    ex2: "\"¿Dónde van las baterías?\"",
    ex3: "\"¿Puedo reciclar una caja de pizza?\"",
    tip: "Consejo: esta demo reconoce un conjunto limitado de calles (p. ej., Princess, Gardiners, Chelsea, Napier, Evergreen).",
    placeholder: "Escribe tu pregunta…",
    send: "Enviar",
    disclaimer: "Demo • Los datos pueden no estar actualizados",
    thinking: "Pensando..."
  },
  zh: {
    title: "Kingston 垃圾回收助手",
    subtitle: "可查询垃圾、回收与厨余（绿桶）收集信息。",
    changeLang: "更改语言",
    intro: "你好！我可以帮助你查询 Kingston 的垃圾收集。试试：",
    ex1: "“Princess Street 的下次收集是什么时候？”",
    ex2: "“电池应该丢到哪里？”",
    ex3: "“披萨盒可以回收吗？”",
    tip: "提示：此演示只识别少量街道（如 Princess、Gardiners、Chelsea、Napier、Evergreen）。",
    placeholder: "输入你的问题…",
    send: "发送",
    disclaimer: "演示版 • 数据可能不是最新",
    thinking: "思考中…"
  }
};

function getLang() {
  return localStorage.getItem("kw_lang") || "en";
}

function applyUiLanguage() {
  const lang = getLang();
  const t = I18N[lang] || I18N.en;

  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };

  setText("ui_title", t.title);
  setText("ui_subtitle", t.subtitle);
  setText("ui_change_lang", t.changeLang);
  setText("ui_intro", t.intro);
  setText("ui_ex1", t.ex1);
  setText("ui_ex2", t.ex2);
  setText("ui_ex3", t.ex3);
  setText("ui_tip", t.tip);
  setText("ui_send", t.send);
  setText("ui_disclaimer", t.disclaimer);

  const input = document.getElementById("userInput");
  if (input) input.placeholder = t.placeholder;
}

document.addEventListener("DOMContentLoaded", () => {
  // If user lands on chat without choosing a language, default to English
  if (!localStorage.getItem("kw_lang")) localStorage.setItem("kw_lang", "en");
  applyUiLanguage();
});

async function sendMessage() {
  const input = document.getElementById("userInput");
  const message = input.value.trim();
  if (!message) return;

  const lang = getLang();
  const t = I18N[lang] || I18N.en;

  addMessage(escapeHtml(message), "user");
  input.value = "";

  const loadingId = addMessage(t.thinking, "loading");

  try {
    const res = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, lang })
    });

    const data = await res.json();
    document.getElementById(loadingId).remove();

    if (!res.ok || !data.ok) {
      addMessage(escapeHtml(data.error || "Something went wrong."), "assistant");
      return;
    }

    addMessage(data.reply, "assistant", { isHtml: true });
  } catch (err) {
    document.getElementById(loadingId).remove();
    addMessage("Sorry — I couldn't reach the server. Is the backend running?", "assistant");
    console.error(err);
  }
}

function addMessage(text, type, opts = {}) {
  const container = document.getElementById("chatContainer");
  const messageDiv = document.createElement("div");
  const id = "msg-" + Date.now() + "-" + Math.floor(Math.random() * 10000);
  messageDiv.id = id;
  messageDiv.className = `message ${type}`;

  if (opts.isHtml) {
    messageDiv.innerHTML = `<p>${text}</p>`;
  } else {
    let formattedText = text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");
    messageDiv.innerHTML = `<p>${formattedText}</p>`;
  }

  container.appendChild(messageDiv);
  container.scrollTop = container.scrollHeight;
  return id;
}

function escapeHtml(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
