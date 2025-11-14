// pages/index.js
import { useEffect } from "react";
import { useRouter } from "next/router";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const canvas = document.getElementById("matrix-canvas");
    const ctx = canvas.getContext("2d");
    let width = window.innerWidth;
    let height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;

    const letters = "01";
    const fontSize = 16;
    const columns = Math.floor(width / fontSize);
    const drops = Array(columns).fill(1);

    const draw = () => {
      ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
      ctx.fillRect(0, 0, width, height);

      ctx.fillStyle = "#a6c1ee"; // pastel tech blue
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
    window.addEventListener("resize", () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width;
      canvas.height = height;
    });

    return () => clearInterval(interval);
  }, []);

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center p-24 bg-black text-white overflow-hidden">
      {/* Matrix Canvas Background */}
      <canvas
        id="matrix-canvas"
        className="absolute top-0 left-0 w-full h-full z-0 opacity-30"
      ></canvas>

      {/* Overlay UI */}
      <div className="relative z-10 text-center">
        <h1 className="mb-8 text-5xl font-bold tracking-tight">
          English-Swahili Curriculum Tutor
        </h1>
        <p className="mb-6 text-lg text-gray-300 max-w-xl">
          A bilingual AI-powered study companion for Form 1 students in Kenya
        </p>
        <div className="mb-8 text-sm text-gray-400">
          <p>Summarize official textbook chapters</p>
          <p>Answer curriculum revision questions</p>
          <p>Utilize three learning modes</p>
          <p>Get curriculum- aligned answers in both English and Swahili </p>
        </div>
        <button
          onClick={() => router.push("/tutor")}
          className="bg-white text-black px-6 py-2 rounded-full font-semibold hover:bg-gray-200 transition"
        >
          Start Learning
        </button>
      </div>

      <footer className="absolute bottom-4 text-xs text-gray-500">
        &copy; {new Date().getFullYear()} Built for students · Made with ♥ in Kenya
      </footer>
    </main>
  );
}
