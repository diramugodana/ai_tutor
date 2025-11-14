
// pages/tutor.js
import { useEffect, useState } from "react";
import Head from "next/head";
import { useTheme } from "next-themes";

const SUBJECTS = ["Form 1 Biology", "Form 1 Geography"];
const MODES = [
  { key: "summarize", label: "Summarize Chapter" },
  { key: "revision", label: "Answer Revision Questions" },
  { key: "ask", label: "Ask a General Question" },
];
const CHAPTERS = ["1", "2", "3", "4", "5"];

export default function TutorPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [subject, setSubject] = useState("");
  const [mode, setMode] = useState("");
  const [chapter, setChapter] = useState("1");
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => setMounted(true), []);

  // Matrix/Strobe effect like the index page
  useEffect(() => {
    if (!mounted) return;
    const canvas = document.getElementById("matrix-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    
    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;

    const letters = theme === "dark" ? "01" : "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    const fontSize = 16;
    const columns = Math.floor(width / fontSize);
    const drops = Array(columns).fill(1);

    const draw = () => {
      ctx.fillStyle = theme === "dark" 
        ? "rgba(0, 0, 0, 0.05)" 
        : "rgba(255, 255, 255, 0.05)";
      ctx.fillRect(0, 0, width, height);

      ctx.fillStyle = theme === "dark" ? "#a6c1ee" : "#e0aaff";
      ctx.font = fontSize + "px monospace";

      for (let i = 0; i < drops.length; i++) {
        const text = letters[Math.floor(Math.random() * letters.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    };

    const interval = setInterval(draw, 50);
    
    const onResize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    
    window.addEventListener("resize", onResize);
    return () => {
      clearInterval(interval);
      window.removeEventListener("resize", onResize);
    };
  }, [theme, mounted]);

  const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

  const handleSubmit = async () => {
    setLoading(true);
    let endpoint = mode === "ask" ? "/ask" : mode === "revision" ? "/revision" : "/summarize";
    const payload = mode === "ask" ? { question } : { chapter };

    try {
      const res = await fetch(`http://localhost:8000${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      
      let parsed = [];
      
      if (mode === "summarize") {
        parsed = [{
          english: data.response?.english || "No summary available",
          swahili: data.response?.swahili || "(Swahili version not available)"
        }];
      } else if (mode === "revision") {
        parsed = (data.questions || []).map(q => ({
          question: q.question_text,
          swahiliQuestion: q.swahili_question || q.question_text,
          english: q.answer?.english || "No answer available",
          swahili: q.answer?.swahili || "(Swahili version not available)"
        }));
      } else if (mode === "ask") {
        parsed = [{
          english: data.response?.english || "No answer available",
          swahili: data.response?.swahili || "(Swahili version not available)"
        }];
      }

      setResponse(parsed);

      // For revision mode, group all questions into one history entry
      if (mode === "revision") {
        setHistory((prev) => [
          {
            mode,
            question: `Answer Revision Questions for Chapter ${chapter}`,
            questions: parsed, // Store all questions in array
            english: "", // Will render questions array instead
            swahili: "",
          },
          ...prev,
        ]);
      } else {
        // For other modes, add each answer as separate history entry
        setHistory((prev) => [
          ...parsed.map((ans) => ({
            mode,
            question:
              ans.question ||
              (mode === "ask"
                ? question
                : `${MODES.find((m) => m.key === mode)?.label} for Chapter ${chapter}`),
            english: ans.english || "",
            swahili: ans.swahili || "",
          })),
          ...prev,
        ]);
      }
    } catch (err) {
      console.error("Error fetching:", err);
    } finally {
      setLoading(false);
    }
  };

  const isDark = theme === "dark";
  const engBg = isDark 
    ? "bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-gray-700" 
    : "bg-gradient-to-br from-purple-50 to-pink-50 text-gray-900 border border-purple-200";
  const swaBg = isDark 
    ? "bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-gray-700" 
    : "bg-gradient-to-br from-pink-50 to-rose-50 text-gray-900 border border-pink-200";
  const backgroundClass = isDark 
    ? "bg-black text-white" 
    : "bg-gradient-to-br from-white to-purple-50 text-black";

  if (!mounted) return <div style={{ visibility: "hidden" }} />;

  return (
    <div className={`relative ${backgroundClass} min-h-screen transition duration-500 overflow-x-hidden`}>
      <Head><title>Curriculum Tutor</title></Head>
      
      {/* Matrix Canvas Background */}
      <canvas 
        id="matrix-canvas" 
        className="fixed top-0 left-0 w-full h-full z-0 opacity-30"
      />

      {/* Navigation Buttons */}
      <div className="fixed top-6 right-6 z-50 flex gap-3">
        <button
          onClick={() => window.location.href = '/'}
          className="bg-white text-black px-5 py-2.5 rounded-full font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 dark:bg-gray-800 dark:text-white border-2 border-gray-200 dark:border-gray-700"
        >
          Home
        </button>
        <button
          onClick={toggleTheme}
          className="bg-white text-black px-5 py-2.5 rounded-full font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 dark:bg-gray-800 dark:text-white border-2 border-gray-200 dark:border-gray-700"
        >
          {theme === "dark" ? "Light" : "Dark"}
        </button>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-12">
        <h1 className="text-4xl md:text-5xl font-bold text-center mb-3 bg-gradient-to-r from-purple-600 to-pink-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
          📘 Curriculum Tutor
        </h1>
        <p className="text-center text-gray-600 dark:text-gray-400 mb-10 text-sm">
          Your AI-powered bilingual study companion
        </p>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Control Panel - Enhanced Design */}
          <div className="w-full lg:w-1/3 space-y-6 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm p-8 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-xl">
                📚
              </div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
                Tutor Panel
              </h2>
            </div>

            {/* Subject Selection */}
            <div>
              <label className="block font-semibold mb-2 text-sm text-gray-700 dark:text-gray-300">
                Subject
              </label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-black dark:text-white border-2 border-gray-200 dark:border-gray-700 focus:border-purple-500 dark:focus:border-blue-500 transition-all outline-none font-medium"
              >
                <option value="">-- Choose Subject --</option>
                {SUBJECTS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Mode Selection */}
            <div>
              <label className="block font-semibold mb-3 text-sm text-gray-700 dark:text-gray-300">
                Learning Mode
              </label>
              <div className="flex flex-col gap-2">
                {MODES.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setMode(m.key)}
                    className={`px-4 py-3 rounded-xl font-medium transition-all duration-300 text-left ${
                      mode === m.key
                        ? "bg-gradient-to-r from-purple-600 to-pink-600 dark:from-blue-600 dark:to-purple-600 text-white shadow-lg scale-105"
                        : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Chapter Selection */}
            {mode !== "ask" && (
              <div>
                <label className="block font-semibold mb-2 text-sm text-gray-700 dark:text-gray-300">
                  Chapter
                </label>
                <select
                  value={chapter}
                  onChange={(e) => setChapter(e.target.value)}
                  className="w-full p-3 rounded-xl bg-gray-50 dark:bg-gray-800 text-black dark:text-white border-2 border-gray-200 dark:border-gray-700 focus:border-purple-500 dark:focus:border-blue-500 transition-all outline-none font-medium"
                >
                  {CHAPTERS.map((ch) => <option key={ch} value={ch}>Chapter {ch}</option>)}
                </select>
              </div>
            )}

            {/* Question Input */}
            {mode === "ask" && (
              <div>
                <label className="block font-semibold mb-2 text-sm text-gray-700 dark:text-gray-300">
                  ❓ Your Question
                </label>
                <textarea
                  className="w-full p-3 h-32 rounded-xl bg-gray-50 dark:bg-gray-800 text-black dark:text-white border-2 border-gray-200 dark:border-gray-700 focus:border-purple-500 dark:focus:border-blue-500 transition-all outline-none resize-none font-medium"
                  placeholder="e.g., What is osmosis?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </div>
            )}

            {/* Submit Button */}
            <button
              onClick={handleSubmit}
              disabled={loading || !subject || !mode || (mode === "ask" && !question)}
              className="w-full mt-4 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed text-white py-4 rounded-xl font-bold text-lg shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Thinking...
                </span>
              ) : (
                "Submit"
              )}
            </button>
          </div>

          {/* Response Area - Enhanced Design */}
          <div className="w-full lg:w-2/3">
            {loading && (
              <div className="bg-gradient-to-br from-purple-100 to-pink-100 dark:from-gray-900 dark:to-gray-800 backdrop-blur-sm rounded-2xl shadow-xl border-2 border-purple-300 dark:border-purple-700 p-16 text-center mb-8 animate-pulse">
                <div className="text-6xl mb-4 animate-bounce">🤔</div>
                <p className="text-purple-700 dark:text-purple-300 text-xl font-bold mb-2">
                  AI is thinking...
                </p>
                <p className="text-purple-600 dark:text-purple-400 text-sm">
                  Generating bilingual response
                </p>
              </div>
            )}

            {!loading && history.length === 0 && (
              <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-16 text-center">
                <div className="text-6xl mb-4">🤖</div>
                <p className="text-gray-500 dark:text-gray-400 text-lg font-medium">
                  AI-generated answers will appear here
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                  Select a mode and submit to get started
                </p>
              </div>
            )}

            {history.map((entry, i) => (
              <div key={i} className="mb-8 animate-fadeIn">
                {entry.mode === "revision" && entry.questions ? (
                  // Revision mode: show all questions grouped together
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className={`${engBg} p-8 rounded-2xl shadow-2xl transition-all hover:shadow-3xl backdrop-blur-sm`}>
                      <h3 className="font-bold text-2xl mb-4 flex items-center gap-2">
                        🇬🇧 <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">English Answers</span>
                      </h3>
                      <p className="text-sm mb-6 font-semibold opacity-80 bg-white/20 dark:bg-black/20 p-3 rounded-lg">
                        ❓ {entry.question}
                      </p>
                      <div className="space-y-6">
                        {entry.questions.map((q, qi) => (
                          <div key={qi} className="border-b border-white/20 dark:border-gray-700 pb-5 last:border-0">
                            <p className="text-sm font-bold mb-3 bg-blue-500/20 dark:bg-blue-900/30 p-2 rounded-lg">
                              Question {qi + 1}: {q.question}
                            </p>
                            <div
                              className="whitespace-pre-wrap text-sm leading-relaxed"
                              dangerouslySetInnerHTML={{ __html: (q.english || "(Not available)").replace(/\*\*(.*?)\*\*/g, "<strong class='font-bold text-blue-600 dark:text-blue-400'>$1</strong>") }}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className={`${swaBg} p-8 rounded-2xl shadow-2xl transition-all hover:shadow-3xl backdrop-blur-sm`}>
                      <h3 className="font-bold text-2xl mb-4 flex items-center gap-2">
                        🇰🇪 <span className="bg-gradient-to-r from-pink-600 to-rose-600 dark:from-pink-400 dark:to-rose-400 bg-clip-text text-transparent">Swahili Answers</span>
                      </h3>
                      <p className="text-sm mb-6 font-semibold opacity-80 bg-white/20 dark:bg-black/20 p-3 rounded-lg">
                        ❓ {entry.question}
                      </p>
                      <div className="space-y-6">
                        {entry.questions.map((q, qi) => (
                          <div key={qi} className="border-b border-white/20 dark:border-gray-700 pb-5 last:border-0">
                            <p className="text-sm font-bold mb-3 bg-pink-500/20 dark:bg-pink-900/30 p-2 rounded-lg">
                              Swali {qi + 1}: {q.swahiliQuestion || q.question}
                            </p>
                            <div
                              className="whitespace-pre-wrap text-sm leading-relaxed"
                              dangerouslySetInnerHTML={{ __html: (q.swahili || "(Swahili version not available)").replace(/\*\*(.*?)\*\*/g, "<strong class='font-bold text-pink-600 dark:text-pink-400'>$1</strong>") }}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  // Other modes: show single answer
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className={`${engBg} p-8 rounded-2xl shadow-2xl transition-all hover:shadow-3xl backdrop-blur-sm`}>
                      <h3 className="font-bold text-2xl mb-4 flex items-center gap-2">
                        🇬🇧 <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">English Answer</span>
                      </h3>
                      <p className="text-sm mb-5 font-semibold opacity-80 bg-white/20 dark:bg-black/20 p-3 rounded-lg">
                        ❓ {entry.question}
                      </p>
                      <div
                        className="whitespace-pre-wrap text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: (entry.english || "(Not available)").replace(/\*\*(.*?)\*\*/g, "<strong class='font-bold text-blue-600 dark:text-blue-400'>$1</strong>") }}
                      />
                    </div>
                    <div className={`${swaBg} p-8 rounded-2xl shadow-2xl transition-all hover:shadow-3xl backdrop-blur-sm`}>
                      <h3 className="font-bold text-2xl mb-4 flex items-center gap-2">
                        🇰🇪 <span className="bg-gradient-to-r from-pink-600 to-rose-600 dark:from-pink-400 dark:to-rose-400 bg-clip-text text-transparent">Swahili Answer</span>
                      </h3>
                      <p className="text-sm mb-5 font-semibold opacity-80 bg-white/20 dark:bg-black/20 p-3 rounded-lg">
                        ❓ {entry.question}
                      </p>
                      <div
                        className="whitespace-pre-wrap text-sm leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: (entry.swahili || "(Swahili version not available)").replace(/\*\*(.*?)\*\*/g, "<strong class='font-bold text-pink-600 dark:text-pink-400'>$1</strong>") }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Clear History Button */}
            {history.length > 0 && (
              <div className="flex justify-center mt-8">
                <button
                  onClick={() => {
                    setHistory([]);
                    setResponse(null);
                    setQuestion("");
                    setMode("");
                  }}
                  className="bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 border-2 border-gray-300 dark:border-gray-700"
                >
                  🗑️ Clear History
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="text-center mt-16 pb-8 text-xs text-gray-500 dark:text-gray-600">
          &copy; {new Date().getFullYear()} Built for students · Made with ♥ in Kenya
        </footer>
      </div>
    </div>
  );
}
