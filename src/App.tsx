import { useState, useRef, useEffect } from "react";

type Message = {
  role: "user" | "assistant";
  text: string;
};

type ChatSession = {
  id: string;
  title: string;
  messages: Message[];
  intent: string;
  timestamp: number;
};

const CHAT_HISTORY_KEY = "glowChatHistory";
const USER_NAME_KEY = "glowUserName";
const CURRENT_CHAT_ID_KEY = "glowCurrentChatId";

type Topic = "learning" | "career" | "finance" | "wellness" | "general";

const TOPICS: Array<{ key: Topic; label: string; color: string; bg: string }> = [
  { key: "learning", label: "Learning", color: "#67e8f9", bg: "rgba(34,211,238,0.14)" },
  { key: "career", label: "Career", color: "#c4b5fd", bg: "rgba(139,92,246,0.16)" },
  { key: "finance", label: "Finance", color: "#86efac", bg: "rgba(34,197,94,0.14)" },
  { key: "wellness", label: "Wellness", color: "#fda4af", bg: "rgba(244,63,94,0.14)" },
  { key: "general", label: "General", color: "#cbd5e1", bg: "rgba(148,163,184,0.12)" },
];

const QUICK_SUGGESTIONS: Array<{ topic: Topic; title: string; prompt: string }> = [
  {
    topic: "learning",
    title: "Build a study plan",
    prompt: "Help me create a 7-day study plan for a topic I want to learn.",
  },
  {
    topic: "career",
    title: "Improve my resume",
    prompt: "Help me improve my resume and prepare for my next job application.",
  },
  {
    topic: "finance",
    title: "Plan my budget",
    prompt: "Help me make a simple monthly budget and debt payoff plan.",
  },
  {
    topic: "wellness",
    title: "Start a routine",
    prompt: "Help me create a realistic wellness routine for sleep, movement, and stress.",
  },
];

const GAMIFIED_FEATURES = [
  {
    title: "Daily Quest",
    prompt: "Give me a daily quest to improve one of my life domains today.",
    icon: "⚔️",
    color: "#f472b6"
  },
  {
    title: "Skill Quiz",
    prompt: "I want to test my knowledge. Please start a quiz on a random topic. Ask me only one question at a time and wait for my answer. Present multiple-choice options clearly using letters (A, B, C, D) on separate lines. When I answer, tell me if I am right or wrong, provide a brief explanation or trivia about the answer, and then present the next question.",
    icon: "🧠",
    color: "#fbbf24"
  },
  {
    title: "Inspire Me",
    prompt: "Give me an inspiring quote or a piece of unique advice related to personal growth and productivity.",
    icon: "✨",
    color: "#34d399"
  },
  {
    title: "Focus Mode",
    prompt: "Help me set up a 'Focus Session' for the next hour to crush my goals.",
    icon: "⏳",
    color: "#a78bfa"
  }
];

const RANDOM_PROMPTS = [
  "Tell me a productivity hack I've never heard of.",
  "Give me a 5-minute financial audit task.",
  "Suggest a quick mindfulness exercise for a busy day.",
  "Help me brainstorm a side-hustle based on my interests.",
  "How can I optimize my sleep for better learning?",
  "Give me a career 'power move' for this week.",
  "Surprise me with a health challenge!",
  "Analyze a hypothetical budget for a digital nomad."
];

const getTopicConfig = (topic: Topic) => TOPICS.find((item) => item.key === topic) || TOPICS[4];

const inferTopic = (chat: ChatSession): Topic => {
  const text = `${chat.title} ${chat.messages.map((message) => message.text).join(" ")}`.toLowerCase();

  const patterns: Record<Exclude<Topic, "general">, RegExp> = {
    learning: /(study|learn|lesson|exam|school|course|skill|quiz|topic)/,
    career: /(resume|job|career|interview|work|promotion|application|linkedin)/,
    finance: /(budget|debt|money|saving|finance|expense|income|investment|loan)/,
    wellness: /(wellness|health|sleep|stress|habit|routine|exercise|yoga|mental)/,
  };

  // Priority 1: Use the AI detected intent if it's specific
  if (["learning", "career", "finance", "wellness"].includes(chat.intent)) {
    return chat.intent as Topic;
  }

  // Priority 2: Pattern match text
  const matches = (Object.keys(patterns) as Array<Exclude<Topic, "general">>)
    .filter((topic) => patterns[topic].test(text));

  return matches[0] || "general";
};

const titleCase = (value: string) =>
  value
    .split(" ")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");

const createConversationTitle = (messages: Message[], fallback = "New Chat") => {
  const firstUserMessage = messages.find((message) => message.role === "user")?.text.trim();
  if (!firstUserMessage) {
    return fallback;
  }

  const cleaned = firstUserMessage
    .replace(/^(help me|can you|please|i need to|i want to|how do i|how to)\s+/i, "")
    .replace(/\b(create|make|build|prepare|improve|start|plan)\b/gi, "")
    .replace(/[?.!]+$/g, "")
    .replace(/\s+/g, " ")
    .trim();

  const topicTitle =
    cleaned || firstUserMessage.replace(/[?.!]+$/g, "").replace(/\s+/g, " ").trim();
  const shortTitle = topicTitle.split(" ").slice(0, 5).join(" ");

  return titleCase(shortTitle || fallback);
};

const renderInlineText = (text: string) =>
  text.replace(/`([^`]+)`/g, "$1").split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} style={styles.strongText}>
          {part.slice(2, -2)}
        </strong>
      );
    }

    return part;
  });

// 📝 Format text with markdown-style parsing
function formatText(text: string) {
  // Split by numbered lists and paragraphs
  const lines = text.split("\n");
  const elements = [];
  let currentParagraph = [];

  const flushParagraph = (key: string) => {
    if (currentParagraph.length > 0) {
      elements.push(
        <p key={key} style={styles.paragraph}>
          {renderInlineText(currentParagraph.join(" "))}
        </p>
      );
      currentParagraph = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const line = rawLine.trim();

    if (!line) {
      flushParagraph(`p-${i}`);
      continue;
    }

    // Handle lists: 1., -, A), a., etc.
    if (/^(\d+\.|-\s|[a-zA-Z][\).]\s)/.test(line)) {
      flushParagraph(`p-pre-${i}`);

      if (/^\d+\./.test(line)) {
        const number = line.match(/^\d+/)?.[0];
        const itemText = line.replace(/^\d+\.\s*/, "");
        elements.push(
          <div key={`li-${i}`} style={styles.listItem}>
            <span style={styles.listNumber}>{number}.</span>
            <span style={styles.listText}>{renderInlineText(itemText)}</span>
          </div>
        );
      } else if (/^-\s/.test(line)) {
        const itemText = line.replace(/^-\s*/, "");
        elements.push(
          <div key={`bullet-${i}`} style={styles.bulletItem}>
            <span style={styles.bullet}>•</span>
            <span style={styles.bulletText}>{renderInlineText(itemText)}</span>
          </div>
        );
      } else if (/^[a-zA-Z][\).]\s/.test(line)) {
        const label = line.match(/^[a-zA-Z][\).]/)?.[0];
        const itemText = line.replace(/^[a-zA-Z][\).]\s*/, "");
        elements.push(
          <div key={`alpha-${i}`} style={styles.listItem}>
            <span style={{ ...styles.listNumber, color: "#a78bfa" }}>{label}</span>
            <span style={styles.listText}>{renderInlineText(itemText)}</span>
          </div>
        );
      }
    } else {
      currentParagraph.push(line);
    }
  }

  flushParagraph("p-final");

  return elements;
}

function App() {
  const [input, setInput] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [intent, setIntent] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [chatHistory, setChatHistory] = useState<ChatSession[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string>("");
  const [showHistory, setShowHistory] = useState<boolean>(false);
  const [userName, setUserName] = useState<string>("");
  const [isListening, setIsListening] = useState<boolean>(false);
  const [viewportWidth, setViewportWidth] = useState<number>(() => window.innerWidth);
  const [hoveredChatId, setHoveredChatId] = useState<string>("");

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const recognitionRef = useRef<any>(null);
  const isCompact = viewportWidth < 900;
  const isPhone = viewportWidth < 560;

  const getChatTitle = (chat: ChatSession, nextMessages: Message[]) => {
    if (chat.title !== "New Chat" && !chat.title.startsWith("Help Me")) {
      return chat.title;
    }

    return createConversationTitle(nextMessages, chat.title);
  };

  const saveCurrentSession = (history: ChatSession[]) =>
    history.map((chat) =>
      chat.id === currentChatId
        ? { ...chat, messages, intent, title: getChatTitle(chat, messages) }
        : chat
    );

  const persistHistory = (history: ChatSession[]) => {
    localStorage.setItem(CHAT_HISTORY_KEY, JSON.stringify(history));
  };

  const loadChatSession = (chat: ChatSession) => {
    setCurrentChatId(chat.id);
    setMessages(chat.messages);
    setIntent(chat.intent);
  };

  // 💾 Reset to initial state on load/refresh
  useEffect(() => {
    // Clear persisted data to ensure a fresh start on every refresh
    localStorage.removeItem(CHAT_HISTORY_KEY);
    localStorage.removeItem(USER_NAME_KEY);
    localStorage.removeItem(CURRENT_CHAT_ID_KEY);
    
    createNewChat();
  }, []);

  useEffect(() => {
    const handleResize = () => {
      setViewportWidth(window.innerWidth);
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (isCompact) {
      setShowHistory(false);
    }
  }, [isCompact]);

  // 💾 Save chat history to localStorage whenever it changes
  useEffect(() => {
    if (currentChatId) {
      persistHistory(chatHistory);
    }
  }, [chatHistory, currentChatId]);

  // 📋 Create new chat
  const createNewChat = () => {
    const newChatId = Date.now().toString();
    const newChat: ChatSession = {
      id: newChatId,
      title: "New Chat",
      messages: [],
      intent: "",
      timestamp: Date.now(),
    };

    setChatHistory((prev) => {
      const updated = [newChat, ...saveCurrentSession(prev)].slice(0, 10); // Keep max 10 chats
      persistHistory(updated);
      return updated;
    });

    setCurrentChatId(newChatId);
    localStorage.setItem(CURRENT_CHAT_ID_KEY, newChatId);
    setMessages([]);
    setIntent("");
    setInput("");
  };

  // 📂 Load a specific chat
  const loadChat = (chatId: string) => {
    const updatedHistory = saveCurrentSession(chatHistory);
    const chat = updatedHistory.find((c) => c.id === chatId);
    if (chat) {
      setChatHistory(updatedHistory);
      persistHistory(updatedHistory);
      loadChatSession(chat);
    }
  };

  const groupedChatHistory = TOPICS.map((topic) => ({
    ...topic,
    chats: chatHistory.filter((chat) => inferTopic(chat) === topic.key),
  })).filter((group) => group.chats.length > 0);

  // 🗑️ Delete a chat
  const deleteChat = (chatId: string) => {
    const updated = chatHistory.filter((c) => c.id !== chatId);
    setChatHistory(updated);
    persistHistory(updated);

    if (currentChatId === chatId) {
      if (updated.length > 0) {
        loadChatSession(updated[0]);
      } else {
        createNewChat();
      }
    }
  };

  const handleRandomTopic = () => {
    const random = RANDOM_PROMPTS[Math.floor(Math.random() * RANDOM_PROMPTS.length)];
    handleSend(random);
  };

  const saveName = (name: string) => {
    setUserName(name);
    localStorage.setItem(USER_NAME_KEY, name);
  };

  const toggleVoiceInput = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setInput((prev) =>
        prev
          ? `${prev}\nVoice input is not supported in this browser.`
          : "Voice input is not supported in this browser."
      );
      return;
    }

    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.continuous = false;

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0]?.transcript || "")
        .join(" ")
        .trim();

      if (transcript) {
        setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognition.onerror = () => {
      setIsListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    setIsListening(true);
    recognition.start();
  };

  const handleSend = async (promptOverride?: string) => {
    const messageText = promptOverride || input;
    if (!messageText.trim()) return;

    const userMessage: Message = { role: "user", text: messageText };
    const currentInput = messageText;

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    // Open history sidebar when conversation starts
    if (!showHistory && !isCompact) {
      setShowHistory(true);
    }

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: currentInput,
          user_id: "chai",
        }),
      });

      const data = await res.json();

      const aiMessage: Message = {
        role: "assistant",
        text: data.response || "No response",
      };

      setMessages((prev) => [...prev, aiMessage]);
      setIntent(data.intent || "unknown");
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Error: Unable to generate response." },
      ]);
    }

    setLoading(false);
  };

  // 🔽 auto scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // 📝 Update current chat in history
  useEffect(() => {
    if (currentChatId) {
      setChatHistory((prev) =>
        prev.map((chat) => {
          if (chat.id === currentChatId) {
            // Update title based on first message
            let title = chat.title;
            if (messages.length > 0) {
              title = getChatTitle(chat, messages);
            }
            return { ...chat, messages, intent, title };
          }
          return chat;
        })
      );
    }
  }, [messages, intent, currentChatId]);

  return (
    <div
      style={{
        ...styles.container,
        ...(isCompact ? styles.containerCompact : {}),
      }}
    >
      {/* 📂 SIDEBAR - CHAT HISTORY */}
      {showHistory && !isCompact && (
        <div style={styles.sidebar}>
          <div style={styles.sidebarHeader}>
            <h3 style={styles.sidebarTitle}>Chat History</h3>
            <button
              onClick={() => setShowHistory(false)}
              style={styles.closeButton}
              title="Close"
            >
              ✕
            </button>
          </div>

          <button
            onClick={createNewChat}
            style={styles.newChatButton}
            title="New chat"
          >
            <span style={styles.iconGlyph}>+</span>
            <span>New Chat</span>
          </button>

          <div style={styles.chatList}>
            {groupedChatHistory.map((group) => (
              <section key={group.key} style={styles.historySection}>
                <div style={styles.historySectionHeader}>
                  <span
                    style={{
                      ...styles.topicDot,
                      background: group.color,
                      boxShadow: `0 0 12px ${group.color}`,
                    }}
                  />
                  <span>{group.label}</span>
                </div>

                {group.chats.map((chat) => {
                  const chatTopic = getTopicConfig(inferTopic(chat));

                  return (
                    <div
                      key={chat.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => loadChat(chat.id)}
                      onMouseEnter={() => setHoveredChatId(chat.id)}
                      onMouseLeave={() => setHoveredChatId("")}
                      onFocus={() => setHoveredChatId(chat.id)}
                      onBlur={() => setHoveredChatId("")}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          loadChat(chat.id);
                        }
                      }}
                      style={{
                        ...styles.chatListItem,
                        background:
                          currentChatId === chat.id
                            ? "rgba(99,102,241,0.25)"
                            : "transparent",
                        borderLeft:
                          currentChatId === chat.id
                            ? `3px solid ${chatTopic.color}`
                            : "3px solid transparent",
                      }}
                    >
                      <div style={styles.chatListContent}>
                        <div style={styles.chatTitleRow}>
                          <div style={styles.chatListTitle}>{chat.title}</div>
                          <span
                            style={{
                              ...styles.topicBadge,
                              color: chatTopic.color,
                              background: chatTopic.bg,
                            }}
                          >
                            {chatTopic.label}
                          </span>
                        </div>
                        <div style={styles.chatListTime}>
                          {new Date(chat.timestamp).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteChat(chat.id);
                        }}
                        style={styles.deleteButton}
                        title="Delete chat"
                      >
                        ×
                      </button>
                      {hoveredChatId === chat.id && (
                        <div style={styles.titleTooltip}>
                          {chat.title}
                        </div>
                      )}
                    </div>
                  );
                })}
              </section>
            ))}

            {groupedChatHistory.length === 0 && (
              <div style={styles.emptyHistory}>
                Start a chat and it will appear here by topic.
              </div>
            )}
          </div>
        </div>
      )}

      <div
        style={{
          ...styles.chatWrapper,
          ...(isCompact ? styles.chatWrapperCompact : {}),
        }}
      >
        {/* HEADER */}
        <div
          style={{
            ...styles.header,
            ...(isCompact ? styles.headerCompact : {}),
          }}
        >
          {!isCompact && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              style={styles.menuButton}
              title="Chat history"
            >
              ≡
            </button>
          )}
          <div style={styles.headerTitleContainer}>
            <h1 style={styles.title}>Glow</h1>
            {userName && (
              <div style={styles.xpBadge}>
                LVL 5 • 1,240 XP
              </div>
            )}
          </div>
          <button
            onClick={createNewChat}
            style={styles.newChatButtonTop}
            title="New chat"
          >
            +
          </button>
        </div>

        {/* CHAT AREA */}
        <div
          style={{
            ...styles.chatBox,
            ...(isCompact ? styles.chatBoxCompact : {}),
          }}
        >
          {/* 👇 GREETING SCREEN */}
          {messages.length === 0 && !userName && (
            <div style={styles.greetingPanel}>
              <div style={{ fontSize: "52px", marginBottom: "10px" }}>✨</div>
              <h2 style={styles.greetingTitle}>Welcome to Glow</h2>
              <p style={styles.greetingCopy}>To get started, what should I call you?</p>
              <div style={{ marginTop: "20px", display: "flex", gap: "10px", width: "100%", maxWidth: "300px" }}>
                <input 
                  type="text" 
                  placeholder="Your name" 
                  onKeyDown={(e) => {
                    if (e.key === "Enter") saveName((e.target as HTMLInputElement).value);
                  }}
                  style={{...styles.input, height: "40px"}} 
                />
                <button 
                  onClick={(e) => {
                    const input = (e.currentTarget.previousSibling as HTMLInputElement).value;
                    if(input) saveName(input);
                  }}
                  style={styles.button}
                >Go</button>
              </div>
            </div>
          )}

          {messages.length === 0 && userName && (
            <div style={styles.greetingPanel}>
              <div style={{ fontSize: "44px" }}>🏹</div>
              <h2 style={styles.greetingTitle}>Choose Your Mission, {userName}</h2>
              <p style={styles.greetingCopy}>
                Ready to level up your life? Pick a domain or try a challenge.
              </p>

              <div
                style={{
                  ...styles.suggestionGrid,
                  ...(isPhone ? styles.suggestionGridPhone : {}),
                }}
              >
                {/* 🎲 RANDOM BUTTON */}
                <button
                  onClick={handleRandomTopic}
                  style={{
                    ...styles.suggestionButton,
                    gridColumn: isPhone ? "span 1" : "span 2",
                    background: "linear-gradient(90deg, rgba(99,102,241,0.2), rgba(34,211,238,0.2))",
                    borderColor: "#6366f1",
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "12px",
                    minHeight: "50px"
                  }}
                >
                  <span style={{ fontSize: "20px" }}>🎲</span>
                  <span style={{ fontWeight: 800 }}>Surprise Me (Random Topic)</span>
                </button>

                {/* 🎮 GAMIFIED FEATURES */}
                {GAMIFIED_FEATURES.map((feature, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(feature.prompt)}
                    style={{
                      ...styles.suggestionButton,
                      borderColor: feature.color,
                      background: `rgba(${parseInt(feature.color.slice(1,3), 16)}, ${parseInt(feature.color.slice(3,5), 16)}, ${parseInt(feature.color.slice(5,7), 16)}, 0.1)`,
                    }}
                  >
                    <span style={{ fontSize: "18px" }}>{feature.icon}</span>
                    <span style={styles.suggestionTitle}>{feature.title}</span>
                  </button>
                ))}

                {QUICK_SUGGESTIONS.map((suggestion) => {
                  const topic = getTopicConfig(suggestion.topic);

                  return (
                    <button
                      key={suggestion.topic}
                      onClick={() => handleSend(suggestion.prompt)}
                      style={{
                        ...styles.suggestionButton,
                        ...(isPhone ? styles.suggestionButtonPhone : {}),
                        borderColor: topic.color,
                        background: topic.bg,
                      }}
                    >
                      <span style={{ ...styles.suggestionTopic, color: topic.color }}>
                        {topic.label}
                      </span>
                      <span style={styles.suggestionTitle}>{suggestion.title}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 👇 EXISTING MESSAGES */}
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                ...styles.message,
                ...(isPhone ? styles.messagePhone : {}),
                alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                background:
                  msg.role === "user"
                    ? "linear-gradient(135deg, #6366f1, #22d3ee)"
                    : "rgba(15,23,42,0.78)",
                border:
                  msg.role === "user"
                    ? "1px solid rgba(255,255,255,0.08)"
                    : "1px solid rgba(148,163,184,0.14)",
                borderRadius:
                  msg.role === "user"
                    ? "18px 6px 18px 18px"
                    : "6px 18px 18px 18px",
              }}
            >
              <span style={styles.messageLabel}>
                {msg.role === "user" ? "You" : "Glow"}
              </span>
              <div style={styles.messageBody}>
                {msg.role === "assistant" ? formatText(msg.text) : msg.text}
              </div>
            </div>
          ))}

          {/* 👇 LOADING INDICATOR */}
          {loading && (
            <div
              style={{
                ...styles.message,
                alignSelf: "flex-start",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <span
                style={{
                  fontSize: "18px",
                  animation: "pulse 1.5s ease-in-out infinite",
                }}
              >
                🤔
              </span>
              <span>Thinking...</span>
              <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* INPUT AREA */}
        <div
          style={{
            ...styles.inputRow,
            ...(isCompact ? styles.inputRowCompact : {}),
          }}
        >
          <textarea
            value={input}
            placeholder="Ask anything..."
            onChange={(e) => setInput(e.target.value)}
            style={styles.input}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
          />

          <button
            style={{
              ...styles.voiceButton,
              ...(isListening ? styles.voiceButtonActive : {}),
            }}
            onClick={toggleVoiceInput}
            title={isListening ? "Stop voice input" : "Start voice input"}
          >
            {isListening ? (
              <span style={{ color: "#fda4af", animation: "pulse 1.5s infinite" }}>●</span>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            )}
          </button>

          <button style={styles.button} onClick={() => handleSend()}>
            🚀
          </button>
        </div>

        {/* META */}
        <div style={styles.meta}>
          <span>Detected: {intent}</span>
          <span>Memory: active</span>
        </div>
      </div>
    </div>
  );
}

export default App;

const styles: { [key: string]: React.CSSProperties } = {
 container: {
  width: "100%",
  height: "100%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  boxShadow: "0 0 80px rgba(99,102,241,0.35)",
  background: `
    radial-gradient(circle at 20% 30%, rgba(99,102,241,0.25), transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(34,211,238,0.2), transparent 40%),
    linear-gradient(135deg, #020617, #0f172a, #020617)
  `,
},

  containerCompact: {
    height: "100dvh",
    minHeight: "100dvh",
    alignItems: "stretch",
    justifyContent: "stretch",
    boxShadow: "none",
    background: "linear-gradient(180deg, #020617, #0f172a)",
  },

  chatWrapper: {
    width: "100%",
    maxWidth: "760px",
    height: "90vh",
    display: "flex",
    flexDirection: "column",
    borderRadius: "20px",
    background: "rgba(255,255,255,0.05)",
    backdropFilter: "blur(20px)",
    boxShadow: "0 0 40px rgba(99,102,241,0.25)",
    border: "1px solid rgba(255,255,255,0.08)",
    overflow: "hidden",
  },

  chatWrapperCompact: {
    maxWidth: "none",
    height: "100dvh",
    minHeight: "100dvh",
    borderRadius: "0",
    border: "none",
    boxShadow: "none",
    background: "rgba(15,23,42,0.96)",
  },

  sidebar: {
    width: "260px",
    height: "90vh",
    padding: "18px 14px",
    boxSizing: "border-box",
    borderRadius: "20px 0 0 20px",
    background: "rgba(15,23,42,0.92)",
    border: "1px solid rgba(148,163,184,0.14)",
    borderRight: "none",
    boxShadow: "0 18px 60px rgba(2,6,23,0.35)",
    color: "#e2e8f0",
    display: "flex",
    flexDirection: "column",
    gap: "14px",
  },

  sidebarHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "10px",
  },

  sidebarTitle: {
    margin: 0,
    color: "#f8fafc",
    fontSize: "18px",
    fontWeight: 700,
    letterSpacing: "0",
  },

  closeButton: {
    width: "32px",
    height: "32px",
    borderRadius: "8px",
    border: "1px solid rgba(148,163,184,0.22)",
    background: "rgba(255,255,255,0.06)",
    color: "#cbd5e1",
    cursor: "pointer",
    fontSize: "18px",
    lineHeight: 1,
  },

  newChatButton: {
    height: "40px",
    borderRadius: "8px",
    border: "1px solid rgba(34,211,238,0.35)",
    background: "linear-gradient(135deg, rgba(99,102,241,0.35), rgba(34,211,238,0.18))",
    color: "#f8fafc",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    fontWeight: 700,
    fontSize: "14px",
  },

  iconGlyph: {
    width: "18px",
    height: "18px",
    borderRadius: "6px",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(255,255,255,0.14)",
    fontSize: "16px",
    lineHeight: 1,
  },

  chatList: {
    display: "flex",
    flexDirection: "column",
    gap: "14px",
    overflowY: "auto",
    paddingRight: "2px",
  },

  historySection: {
    display: "flex",
    flexDirection: "column",
    gap: "7px",
  },

  historySectionHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    color: "#cbd5e1",
    fontSize: "11px",
    fontWeight: 800,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    padding: "0 4px",
  },

  topicDot: {
    width: "7px",
    height: "7px",
    borderRadius: "999px",
    flex: "0 0 auto",
  },

  emptyHistory: {
    color: "#94a3b8",
    fontSize: "13px",
    lineHeight: "1.5",
    padding: "14px 8px",
    textAlign: "center",
  },

  chatListItem: {
    width: "100%",
    maxWidth: "100%",
    minHeight: "62px",
    padding: "10px 8px 10px 12px",
    boxSizing: "border-box",
    position: "relative",
    border: "none",
    borderRadius: "8px",
    color: "#e2e8f0",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "8px",
    textAlign: "left",
    overflow: "visible",
    transition: "background 160ms ease, transform 160ms ease, border-color 160ms ease",
  },

  chatListContent: {
    minWidth: 0,
    flex: 1,
    display: "flex",
    flexDirection: "column",
    gap: "5px",
  },

  chatTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    minWidth: 0,
    maxWidth: "100%",
    overflow: "hidden",
  },

  chatListTitle: {
    color: "#f8fafc",
    fontSize: "14px",
    fontWeight: 650,
    minWidth: 0,
    flex: "1 1 auto",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },

  topicBadge: {
    borderRadius: "999px",
    maxWidth: "64px",
    padding: "3px 6px",
    fontSize: "10px",
    fontWeight: 800,
    lineHeight: 1,
    flex: "0 0 auto",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },

  chatListTime: {
    color: "#94a3b8",
    fontSize: "12px",
  },

  deleteButton: {
    width: "24px",
    height: "24px",
    borderRadius: "7px",
    border: "1px solid rgba(248,113,113,0.22)",
    background: "rgba(248,113,113,0.08)",
    color: "#fecaca",
    cursor: "pointer",
    flex: "0 0 24px",
    fontSize: "16px",
    lineHeight: 1,
  },

  titleTooltip: {
    position: "absolute",
    left: "12px",
    right: "12px",
    top: "calc(100% - 4px)",
    zIndex: 20,
    padding: "8px 10px",
    borderRadius: "8px",
    border: "1px solid rgba(148,163,184,0.22)",
    background: "rgba(2,6,23,0.96)",
    color: "#f8fafc",
    fontSize: "12px",
    lineHeight: "1.35",
    fontWeight: 650,
    boxShadow: "0 14px 30px rgba(2,6,23,0.45)",
    pointerEvents: "none",
    whiteSpace: "normal",
    overflowWrap: "break-word",
  },

  header: {
    minHeight: "64px",
    display: "grid",
    gridTemplateColumns: "44px 1fr 44px",
    alignItems: "center",
    gap: "8px",
    padding: "0 14px",
    borderBottom: "1px solid rgba(255,255,255,0.05)",
  },

  headerCompact: {
    minHeight: "58px",
    gridTemplateColumns: "1fr 44px",
    padding: "0 12px 0 16px",
  },

  headerTitleContainer: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "2px",
  },

  xpBadge: {
    fontSize: "10px",
    fontWeight: 900,
    color: "#fbbf24",
    background: "rgba(251,191,36,0.1)",
    padding: "2px 8px",
    borderRadius: "99px",
    border: "1px solid rgba(251,191,36,0.3)",
    letterSpacing: "0.05em",
    textTransform: "uppercase",
    animation: "pulse 2s infinite",
  },

  menuButton: {
    width: "36px",
    height: "36px",
    borderRadius: "8px",
    border: "1px solid rgba(148,163,184,0.22)",
    background: "rgba(255,255,255,0.08)",
    color: "#e2e8f0",
    cursor: "pointer",
    fontSize: "22px",
    lineHeight: 1,
  },

  newChatButtonTop: {
    width: "36px",
    height: "36px",
    borderRadius: "8px",
    border: "1px solid rgba(34,211,238,0.35)",
    background: "rgba(34,211,238,0.12)",
    color: "#67e8f9",
    cursor: "pointer",
    fontSize: "22px",
    lineHeight: 1,
  },

  title: {
    textAlign: "center",
    margin: 0,
    color: "#f8fafc",
    fontFamily: "Georgia, 'Times New Roman', serif",
    fontSize: "31px",
    fontWeight: 700,
    fontStyle: "italic",
    letterSpacing: "0",
    textShadow: "0 0 24px rgba(34,211,238,0.34)",
  },

  chatBox: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    padding: "16px",
    gap: "10px",
    overflowY: "auto",
  },

  chatBoxCompact: {
    padding: "12px",
    gap: "9px",
  },

  greetingPanel: {
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    alignItems: "center",
    flex: 1,
    gap: "16px",
    maxWidth: "560px",
    width: "100%",
    margin: "0 auto",
  },

  greetingTitle: {
    color: "#f8fafc",
    fontSize: "27px",
    lineHeight: "1.15",
    margin: 0,
    fontWeight: 750,
  },

  greetingCopy: {
    color: "#94a3b8",
    fontSize: "14px",
    margin: 0,
  },

  suggestionGrid: {
    width: "100%",
    display: "grid",
    gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
    gap: "10px",
    marginTop: "8px",
  },

  suggestionGridPhone: {
    gridTemplateColumns: "1fr",
    gap: "8px",
  },

  suggestionButton: {
    minHeight: "88px",
    borderRadius: "8px",
    border: "1px solid",
    color: "#f8fafc",
    cursor: "pointer",
    padding: "14px",
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-start",
    justifyContent: "space-between",
    textAlign: "left",
    boxShadow: "inset 0 1px 0 rgba(255,255,255,0.08)",
  },

  suggestionButtonPhone: {
    minHeight: "76px",
    padding: "11px",
  },

  suggestionTopic: {
    fontSize: "11px",
    fontWeight: 850,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },

  suggestionTitle: {
    color: "#f8fafc",
    fontSize: "15px",
    fontWeight: 750,
    lineHeight: "1.25",
  },

  message: {
    maxWidth: "82%",
    padding: "12px 15px",
    color: "#e2e8f0",
    fontSize: "14.5px",
    lineHeight: "1.55",
    wordBreak: "break-word",
    display: "flex",
    flexDirection: "column",
    gap: "7px",
    boxShadow: "0 14px 30px rgba(2,6,23,0.16)",
  },

  messagePhone: {
    maxWidth: "90%",
    padding: "11px 13px",
    fontSize: "14px",
  },

  messageLabel: {
    color: "#94a3b8",
    fontSize: "11px",
    fontWeight: 850,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
  },

  messageBody: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },

  strongText: {
    color: "#f8fafc",
    fontWeight: 800,
  },

  inputRow: {
    display: "flex",
    gap: "8px",
    padding: "12px",
    borderTop: "1px solid rgba(255,255,255,0.05)",
  },

  inputRowCompact: {
    padding: "10px",
    gap: "7px",
  },

  input: {
    flex: 1,
    borderRadius: "12px",
    padding: "12px",
    border: "1px solid rgba(255,255,255,0.1)",
    background: "rgba(0,0,0,0.4)",
    color: "#e2e8f0",
    outline: "none",
    resize: "none",
  },

  button: {
    padding: "12px 16px",
    borderRadius: "12px",
    border: "none",
    cursor: "pointer",
    background: "linear-gradient(135deg, #6366f1, #22d3ee)",
    color: "white",
    fontWeight: 600,
    boxShadow: "0 0 15px rgba(99,102,241,0.6)",
  },

  voiceButton: {
    minWidth: "48px",
    padding: "0 12px",
    borderRadius: "12px",
    border: "1px solid rgba(148,163,184,0.24)",
    cursor: "pointer",
    background: "rgba(255,255,255,0.07)",
    color: "#cbd5e1",
    fontWeight: 800,
    fontSize: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },

  voiceButtonActive: {
    border: "1px solid rgba(244,63,94,0.55)",
    background: "rgba(244,63,94,0.18)",
    color: "#fda4af",
    boxShadow: "0 0 18px rgba(244,63,94,0.26)",
  },

  meta: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "11px",
    padding: "8px 12px",
    color: "#94a3b8",
    borderTop: "1px solid rgba(255,255,255,0.05)",
  },

  // 📝 Formatted text styles
  paragraph: {
    margin: "12px 0",
    lineHeight: "1.6",
    color: "#e2e8f0",
    fontSize: "14px",
  },

  listItem: {
    display: "flex",
    gap: "10px",
    margin: "8px 0",
    fontSize: "14px",
    lineHeight: "1.6",
  },

  listNumber: {
    color: "#22d3ee",
    fontWeight: 600,
    minWidth: "24px",
  },

  listText: {
    color: "#e2e8f0",
    flex: 1,
  },

  bulletItem: {
    display: "flex",
    gap: "10px",
    margin: "6px 0",
    fontSize: "14px",
    lineHeight: "1.6",
    paddingLeft: "8px",
  },

  bullet: {
    color: "#6366f1",
    fontWeight: 600,
    minWidth: "16px",
  },

  bulletText: {
    color: "#cbd5e1",
    flex: 1,
  },
};
