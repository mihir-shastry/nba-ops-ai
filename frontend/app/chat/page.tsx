"use client";

import { useMutation } from "@tanstack/react-query";
import { useState, useRef, useEffect } from "react";
import { askQuestion } from "@/lib/api";
import { Send, ChevronDown, ChevronUp } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  sql?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: askQuestion,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sql: data.sql },
      ]);
    },
    onError: (error) => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${error.message}` },
      ]);
    },
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || mutation.isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    mutation.mutate(input);
    setInput("");
  };

  const exampleQuestions = [
    "Who are the top 5 scorers?",
    "Compare team records",
    "How does Shai perform in away games?",
    "Which players have the best FG%?",
    "Who leads the league in assists?",
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-extrabold mb-1">AI Assistant</h1>
      <p className="text-court-muted mb-6">
        Ask questions about NBA players and teams — powered by Text-to-SQL
      </p>

      {/* Messages */}
      <div className="bg-court-card border border-court-border rounded-xl p-4 mb-6 h-[500px] overflow-auto">
        {messages.length === 0 && (
          <div className="text-center text-court-muted py-20">
            <p className="text-lg mb-2">Ask me anything about NBA data</p>
            <p className="text-sm">I&apos;ll generate SQL and query the database</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 ${msg.role === "user" ? "text-right" : ""}`}
          >
            <div
              className={`inline-block max-w-[80%] rounded-xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-gradient-to-r from-court-orange to-court-gold text-court-bg"
                  : "bg-white/5 border border-court-border"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
            {msg.sql && (
              <SqlBlock sql={msg.sql} />
            )}
          </div>
        ))}

        {mutation.isPending && (
          <div className="mb-4">
            <div className="inline-block bg-white/5 border border-court-border rounded-xl px-4 py-3">
              <div className="flex items-center gap-2 text-court-muted text-sm">
                <div className="w-2 h-2 bg-court-gold rounded-full animate-pulse" />
                Generating SQL and querying database...
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about NBA players, teams, or stats..."
          className="flex-1 bg-court-card border border-court-border rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-court-orange"
          disabled={mutation.isPending}
        />
        <button
          onClick={handleSend}
          disabled={mutation.isPending}
          className="px-4 py-3 bg-white text-black rounded-xl font-semibold hover:bg-white/90 transition-colors disabled:opacity-50"
        >
          <Send size={18} />
        </button>
      </div>

      {/* Example Questions */}
      <div className="mt-4">
        <p className="text-xs text-court-muted mb-2">Try asking:</p>
        <div className="flex flex-wrap gap-2">
          {exampleQuestions.map((q) => (
            <button
              key={q}
              onClick={() => setInput(q)}
              className="text-xs bg-court-card border border-court-border rounded-full px-3 py-1.5 text-court-muted hover:text-white hover:bg-white/5 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function SqlBlock({ sql }: { sql: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-court-muted hover:text-court-gold flex items-center gap-1"
      >
        {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
        Generated SQL
      </button>
      {expanded && (
        <pre className="mt-2 bg-black/30 border border-court-border rounded-lg p-3 text-xs font-mono text-court-muted overflow-auto">
          {sql}
        </pre>
      )}
    </div>
  );
}
