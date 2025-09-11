// // pages/tutor.js
// import { useEffect, useState } from "react";
// import Head from "next/head";
// import { useTheme } from "next-themes";

// const SUBJECTS = ["Form 1 Biology", "Form 1 Geography"];
// const MODES = [
//   { key: "summarize", label: "Summarize Chapter" },
//   { key: "revision", label: "Answer Revision Questions" },
//   { key: "ask", label: "Ask a General Question" },
// ];
// const CHAPTERS = ["1", "2", "3", "4", "5"];

// export default function TutorPage() {
//   // Hooks (once, at the top)
//   const { theme, setTheme } = useTheme();
//   const [mounted, setMounted] = useState(false);
//   const [subject, setSubject] = useState("");
//   const [mode, setMode] = useState("");
//   const [chapter, setChapter] = useState("1");
//   const [question, setQuestion] = useState("");
//   const [response, setResponse] = useState(null);
//   const [history, setHistory] = useState([]);
//   const [loading, setLoading] = useState(false);

//   useEffect(() => setMounted(true), []);

//   // Canvas background effect (guarded by mounted)
//   useEffect(() => {
//     if (!mounted) return;

//     const canvas = document.getElementById("ambient-canvas");
//     if (!canvas) return;
//     const ctx = canvas.getContext("2d");

//     let width = window.innerWidth;
//     let height = window.innerHeight;
//     canvas.width = width;
//     canvas.height = height;

//     const colors = theme === "dark" ? ["#4f46e5", "#0ea5e9"] : ["#fcd5ce", "#fbc2eb"];
//     const particles = Array.from({ length: 60 }, () => createParticle());

//     function createParticle() {
//       return {
//         x: Math.random() * width,
//         y: Math.random() * height,
//         radius: Math.random() * 1.8 + 0.8,
//         dx: (Math.random() - 0.5) * 0.8,
//         dy: (Math.random() - 0.5) * 0.8,
//         color: colors[Math.floor(Math.random() * colors.length)],
//       };
//     }

//     function animate() {
//       ctx.clearRect(0, 0, width, height);
//       particles.forEach((p) => {
//         ctx.beginPath();
//         ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
//         ctx.fillStyle = p.color;
//         ctx.fill();
//         p.x += p.dx;
//         p.y += p.dy;

//         if (p.x < 0) p.x = width;
//         if (p.x > width) p.x = 0;
//         if (p.y < 0) p.y = height;
//         if (p.y > height) p.y = 0;
//       });
//       requestAnimationFrame(animate);
//     }

//     animate();

//     const onResize = () => {
//       width = window.innerWidth;
//       height = window.innerHeight;
//       canvas.width = width;
//       canvas.height = height;
//     };
//     window.addEventListener("resize", onResize);
//     return () => window.removeEventListener("resize", onResize);
//   }, [theme, mounted]);

//   const toggleTheme = () => setTheme(theme === "dark" ? "light" : "dark");

//   const parseApi = (data) => {
//     // Expect either an array of {english, swahili} or an object with result/answer arrays
//     if (Array.isArray(data)) return data;
//     if (Array.isArray(data?.result)) return data.result;
//     if (Array.isArray(data?.answer)) return data.answer;

//     const obj = data?.result || data?.answer;
//     if (obj && typeof obj === "object" && obj.english) return [obj];

//     // Fallback: string into english only
//     if (typeof obj === "string") return [{ english: obj, swahili: "" }];
//     return [{ english: "(Unexpected response format)", swahili: "" }];
//   };

//   const handleSubmit = async () => {
//     setLoading(true);
//     let endpoint = "";
//     let payload = {};

//     if (mode === "summarize") {
//       endpoint = "/summarize";
//       payload = { chapter };
//     } else if (mode === "revision") {
//       endpoint = "/revision";
//       payload = { chapter };
//     } else {
//       endpoint = "/ask";
//       payload = { question };
//     }

//     try {
//       const res = await fetch(`http://localhost:8000${endpoint}`, {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify(payload),
//       });

//       const data = await res.json();
//       const parsed = parseApi(data);

//       setResponse(parsed);
//       setHistory((prev) => [
//         ...prev,
//         {
//           mode,
//           question: mode === "ask" ? question : `${MODES.find((m) => m.key === mode)?.label} for Chapter ${chapter}`,
//           english: parsed?.[0]?.english || "",
//           swahili: parsed?.[0]?.swahili || "",
//         },
//       ]);
//     } catch (err) {
//       console.error("Error fetching:", err);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const isDark = theme === "dark";
//   const engBg = isDark ? "bg-gray-800 text-white" : "bg-purple-100 text-black";
//   const swaBg = isDark ? "bg-gray-900 text-white" : "bg-pink-100 text-black";
//   const backgroundClass = isDark ? "bg-gray-950 text-white" : "bg-white text-black";

//   if (!mounted) return <div style={{ visibility: "hidden" }} />;

//   return (
//     <div className={`relative ${backgroundClass} min-h-screen transition duration-500`}>
//       <Head>
//         <title>Curriculum Tutor</title>
//       </Head>

//       <canvas
//         id="ambient-canvas"
//         className="fixed top-0 left-0 w-full h-full opacity-20 z-0"
//       />

//       <button
//         onClick={toggleTheme}
//         className="fixed top-4 right-4 z-50 bg-gray-800 text-white px-4 py-1 rounded shadow hover:bg-gray-700 dark:bg-white dark:text-black dark:hover:bg-gray-100"
//       >
//         {theme === "dark" ? "☀ Light Mode" : "🌙 Dark Mode"}
//       </button>

//       <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">
//         <h1 className="text-3xl font-bold text-center mb-6">📘 Curriculum Tutor</h1>

//         <div className="flex flex-col lg:flex-row gap-8">
//           {/* Control Panel */}
//           <div className="w-full lg:w-1/3 space-y-6 bg-white dark:bg-gray-900 p-6 rounded-xl shadow-md">
//             <h2 className="text-xl font-bold mb-2">📚 Tutor Panel</h2>

//             <div>
//               <label className="block font-semibold mb-1">Subject</label>
//               <select
//                 value={subject}
//                 onChange={(e) => setSubject(e.target.value)}
//                 className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 text-black dark:text-white"
//               >
//                 <option value="">-- Choose Subject --</option>
//                 {SUBJECTS.map((s) => (
//                   <option key={s} value={s}>
//                     {s}
//                   </option>
//                 ))}
//               </select>
//             </div>

//             <div>
//               <label className="block font-semibold mb-1">Mode</label>
//               <div className="flex flex-wrap gap-2">
//                 {MODES.map((m) => (
//                   <button
//                     key={m.key}
//                     onClick={() => setMode(m.key)}
//                     className={`px-3 py-1 rounded-full border font-medium ${
//                       mode === m.key
//                         ? "bg-blue-600 text-white"
//                         : "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-white"
//                     }`}
//                   >
//                     {m.label}
//                   </button>
//                 ))}
//               </div>
//             </div>

//             {/* Chapter field only for summarize/revision */}
//             {mode !== "ask" && (
//               <div>
//                 <label className="block font-semibold mb-1">Chapter</label>
//                 <select
//                   value={chapter}
//                   onChange={(e) => setChapter(e.target.value)}
//                   className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 text-black dark:text-white"
//                 >
//                   {CHAPTERS.map((ch) => (
//                     <option key={ch} value={ch}>
//                       {ch}
//                     </option>
//                   ))}
//                 </select>
//               </div>
//             )}

//             {/* Question field only for ask */}
//             {mode === "ask" && (
//               <div>
//                 <label className="block font-semibold mb-1">Your Question</label>
//                 <textarea
//                   className="w-full p-2 h-28 rounded bg-gray-100 dark:bg-gray-800 text-black dark:text-white resize-none"
//                   placeholder="e.g., What is osmosis?"
//                   value={question}
//                   onChange={(e) => setQuestion(e.target.value)}
//                 />
//               </div>
//             )}

//             <button
//               onClick={handleSubmit}
//               disabled={
//                 loading ||
//                 !subject ||
//                 !mode ||
//                 (mode === "ask" && !question)
//               }
//               className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white py-2 rounded transition"
//             >
//               {loading ? "Thinking..." : "Submit"}
//             </button>
//           </div>

//           {/* Response Area */}
//           <div className="w-full lg:w-2/3">
//             {history.length === 0 && (
//               <div className="text-gray-400 dark:text-gray-500 italic text-center py-10">
//                 This is where your AI-generated answers will appear.
//               </div>
//             )}

//             {/* Show the latest response at the top */}
//             {response && (
//               <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
//                 <div className={`${engBg} p-6 rounded-lg shadow-md transition`}>
//                   <h3 className="font-semibold text-xl mb-2">
//                     🇬🇧 {mode === "summarize" ? "English Summary" : "English Answer"}
//                   </h3>
//                   {mode === "ask" ? (
//                     <p className="text-sm mb-2 italic">❓ {question}</p>
//                   ) : (
//                     <p className="text-sm mb-2 italic">
//                       ❓ {MODES.find((m) => m.key === mode)?.label}
//                       {mode !== "ask" ? ` — Chapter ${chapter}` : ""}
//                     </p>
//                   )}
//                   <div
//                     className="whitespace-pre-wrap text-sm"
//                     dangerouslySetInnerHTML={{
//                       __html: (response?.[0]?.english || "(Not available)").replace(
//                         /\*\*(.*?)\*\*/g,
//                         "<strong>$1</strong>"
//                       ),
//                     }}
//                   />
//                 </div>

//                 <div className={`${swaBg} p-6 rounded-lg shadow-md transition`}>
//                   <h3 className="font-semibold text-xl mb-2">🇰🇪 Swahili Answer</h3>
//                   <div
//                     className="whitespace-pre-wrap text-sm"
//                     dangerouslySetInnerHTML={{
//                       __html: (response?.[0]?.swahili || "(Swahili version not available)").replace(
//                         /\*\*(.*?)\*\*/g,
//                         "<strong>$1</strong>"
//                       ),
//                     }}
//                   />
//                 </div>
//               </div>
//             )}

//             {/* History below */}
//             {history.length > 0 && (
//               <div className="mt-8 space-y-6">
//                 {history.map((entry, i) => (
//                   <div key={i} className="grid grid-cols-1 md:grid-cols-2 gap-6">
//                     <div className={`${engBg} p-6 rounded-lg shadow-md transition`}>
//                       <h3 className="font-semibold text-xl mb-2">
//                         🇬🇧 {entry.mode === "summarize" ? "English Summary" : "English Answer"}
//                       </h3>
//                       <p className="text-sm mb-2 italic">❓ {entry.question}</p>
//                       <div
//                         className="whitespace-pre-wrap text-sm"
//                         dangerouslySetInnerHTML={{
//                           __html: (entry.english || "(Not available)").replace(
//                             /\*\*(.*?)\*\*/g,
//                             "<strong>$1</strong>"
//                           ),
//                         }}
//                       />
//                     </div>

//                     <div className={`${swaBg} p-6 rounded-lg shadow-md transition`}>
//                       <h3 className="font-semibold text-xl mb-2">🇰🇪 Swahili Answer</h3>
//                       <div
//                         className="whitespace-pre-wrap text-sm"
//                         dangerouslySetInnerHTML={{
//                           __html: (entry.swahili || "(Swahili version not available)").replace(
//                             /\*\*(.*?)\*\*/g,
//                             "<strong>$1</strong>"
//                           ),
//                         }}
//                       />
//                     </div>
//                   </div>
//                 ))}
//               </div>
//             )}

//             {response && (
//               <div className="mt-6">
//                 <button
//                   onClick={() => {
//                     setQuestion("");
//                     setResponse(null);
//                     setMode("");
//                   }}
//                   className="bg-purple-600 px-4 py-2 text-white rounded hover:bg-purple-700"
//                 >
//                   Ask Another
//                 </button>
//               </div>
//             )}
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// }

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

  useEffect(() => {
    if (!mounted) return;
    const canvas = document.getElementById("ambient-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
    const colors = theme === "dark" ? ["#4f46e5", "#0ea5e9"] : ["#fcd5ce", "#fbc2eb"];
    const particles = Array.from({ length: 60 }, () => createParticle());
    function createParticle() {
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 1.8 + 0.8,
        dx: (Math.random() - 0.5) * 0.8,
        dy: (Math.random() - 0.5) * 0.8,
        color: colors[Math.floor(Math.random() * colors.length)],
      };
    }
    function animate() {
      ctx.clearRect(0, 0, width, height);
      particles.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.fill();
        p.x += p.dx;
        p.y += p.dy;
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;
      });
      requestAnimationFrame(animate);
    }
    animate();
    const onResize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
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
      const parsed = Array.isArray(data.result || data.answer)
        ? (data.result || data.answer)
        : [data.result || data.answer || { english: "⚠️ Unexpected format.", swahili: "" }];

      setResponse(parsed);

      // ✅ FIX: save ALL answers to history (newest first), preserving per-item question when provided
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
    } catch (err) {
      console.error("Error fetching:", err);
    } finally {
      setLoading(false);
    }
  };

  const isDark = theme === "dark";
  const engBg = isDark ? "bg-gray-800 text-white" : "bg-purple-100 text-black";
  const swaBg = isDark ? "bg-gray-900 text-white" : "bg-pink-100 text-black";
  const backgroundClass = isDark ? "bg-gray-950 text-white" : "bg-white text-black";

  if (!mounted) return <div style={{ visibility: "hidden" }} />;

  return (
    <div className={`relative ${backgroundClass} min-h-screen transition duration-500`}>
      <Head><title>Curriculum Tutor</title></Head>
      <canvas id="ambient-canvas" className="fixed top-0 left-0 w-full h-full opacity-20 z-0" />
      <button
        onClick={toggleTheme}
        className="fixed top-4 right-4 z-50 bg-gray-800 text-white px-4 py-1 rounded shadow hover:bg-gray-700 dark:bg-white dark:text-black dark:hover:bg-gray-100"
      >
        {theme === "dark" ? "☀ Light Mode" : "🌙 Dark Mode"}
      </button>
      <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">
        <h1 className="text-3xl font-bold text-center mb-6">📘 Curriculum Tutor</h1>

        <div className="flex flex-col lg:flex-row gap-8">
          <div className="w-full lg:w-1/3 space-y-6 bg-white dark:bg-gray-900 p-6 rounded-xl shadow-md">
            <h2 className="text-xl font-bold mb-2">📚 Tutor Panel</h2>
            <div>
              <label className="block font-semibold mb-1">Subject</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 text-black dark:text-white"
              >
                <option value="">-- Choose Subject --</option>
                {SUBJECTS.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block font-semibold mb-1">Mode</label>
              <div className="flex flex-wrap gap-2">
                {MODES.map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setMode(m.key)}
                    className={`px-3 py-1 rounded-full border font-medium ${mode === m.key ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-white"}`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>
            {mode !== "ask" && (
              <div>
                <label className="block font-semibold mb-1">Chapter</label>
                <select
                  value={chapter}
                  onChange={(e) => setChapter(e.target.value)}
                  className="w-full p-2 rounded bg-gray-100 dark:bg-gray-800 text-black dark:text-white"
                >
                  {CHAPTERS.map((ch) => <option key={ch}>{ch}</option>)}
                </select>
              </div>
            )}
            {mode === "ask" && (
              <div>
                <label className="block font-semibold mb-1">Your Question</label>
                <textarea
                  className="w-full p-2 h-28 rounded bg-gray-100 dark:bg-gray-800 text-black dark:text-white resize-none"
                  placeholder="e.g., What is osmosis?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                />
              </div>
            )}
            <button
              onClick={handleSubmit}
              disabled={loading || !subject || !mode || (mode === "ask" && !question)}
              className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white py-2 rounded transition"
            >
              {loading ? "Thinking..." : "Submit"}
            </button>
          </div>

          <div className="w-full lg:w-2/3">
            {history.length === 0 && (
              <div className="text-gray-400 dark:text-gray-500 italic text-center py-10">
                This is where your AI-generated answers will appear.
              </div>
            )}

            {history.map((entry, i) => (
              <div key={i} className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div className={`${engBg} p-6 rounded-lg shadow-md transition`}>
                  <h3 className="font-semibold text-xl mb-2">❓ Question: {entry.question}</h3>
                  <div
                    className="whitespace-pre-wrap text-sm"
                    dangerouslySetInnerHTML={{ __html: (entry.english || "(Not available)").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") }}
                  />
                </div>
                <div className={`${swaBg} p-6 rounded-lg shadow-md transition`}>
                  <h3 className="font-semibold text-xl mb-2">🇰🇪 Swahili Answer</h3>
                  <div
                    className="whitespace-pre-wrap text-sm"
                    dangerouslySetInnerHTML={{ __html: (entry.swahili || "(Swahili version not available)").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>") }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
