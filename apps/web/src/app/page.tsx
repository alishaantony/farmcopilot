"use client";
import { useState, FormEvent, ChangeEvent } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

type ChatResponse = {
  response: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hello! Please upload a document to begin." },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("No document uploaded.");

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;

    const file = e.target.files[0];
    if (!file) return;

    setUploadStatus("Uploading...");
    
    // For file uploads, we use FormData instead of JSON
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setUploadStatus(data.message || "Upload complete!");

    } catch (error) {
      setUploadStatus("Upload failed. Is the backend running?");
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    setIsLoading(true);
    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: input }),
    });

    setInput("");

    const data: ChatResponse = await response.json();
    
    const assistantMessage: Message = { role: "assistant", content: data.response };
    setMessages((prev) => [...prev, assistantMessage]);
    setIsLoading(false);
  };

  return (
    <main className="flex flex-col items-center justify-between min-h-screen p-6 bg-gray-900 text-white">
      <div className="w-full max-w-2xl flex-1 flex flex-col">
        <h1 className="text-2xl font-bold mb-4 text-center">FarmCopilot</h1>
        
        {/* --- NEW: File Upload Section --- */}
        <div className="mb-4 p-4 bg-gray-800 rounded-lg text-center">
            <label htmlFor="file-upload" className="cursor-pointer bg-blue-600 px-4 py-2 rounded-lg">
                Choose PDF File
            </label>
            <input id="file-upload" type="file" onChange={handleFileChange} accept=".pdf" className="hidden" />
            <p className="mt-2 text-sm text-gray-400">{uploadStatus}</p>
        </div>

        {/* Chat window */}
        <div className="flex-1 overflow-y-auto p-4 bg-gray-800 rounded-lg">
          {messages.map((msg, index) => (
            <div key={index} className={`my-2 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
              <span className={`inline-block px-4 py-2 rounded-lg ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                {msg.content}
              </span>
            </div>
          ))}
        </div>
        
        {/* Input form */}
        <form onSubmit={handleSubmit} className="mt-4 flex">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 p-2 bg-gray-700 rounded-l-lg border-none outline-none"
            placeholder={isLoading ? "Generating answer..." : "Ask a question about your document..."}
            disabled={isLoading}
          />
          <button type="submit" className="px-4 py-2 bg-blue-600 rounded-r-lg" disabled={isLoading}>
            {isLoading ? "..." : "Send"}
          </button>
        </form>
      </div>
    </main>
  );
}