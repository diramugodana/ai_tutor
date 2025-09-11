// // components/LayoutTutor.js
// import { useTheme } from "next-themes";
// import { useEffect, useState } from "react";

// export default function LayoutTutor({ children, toggleTheme }) {
//   const { theme } = useTheme();
//   const [mounted, setMounted] = useState(false);

//   // Prevent SSR error from useTheme on initial render
//   useEffect(() => setMounted(true), []);
//   if (!mounted) return null;

//   useEffect(() => {
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
//         color: colors[Math.floor(Math.random() * colors.length)]
//       };
//     }

//     function animate() {
//       ctx.clearRect(0, 0, width, height);
//       particles.forEach(p => {
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

//     window.addEventListener("resize", () => {
//       width = window.innerWidth;
//       height = window.innerHeight;
//       canvas.width = width;
//       canvas.height = height;
//     });
//   }, [theme]);

//   const backgroundClass = theme === "dark" ? "bg-gray-950 text-white" : "bg-white text-black";

//   return (
//     <div className={`relative ${backgroundClass} min-h-screen transition duration-500`}>
//       <canvas id="ambient-canvas" className="fixed top-0 left-0 w-full h-full opacity-20 z-0" />

//       <button
//         onClick={toggleTheme}
//         className="fixed top-4 right-4 z-50 bg-gray-800 text-white px-4 py-1 rounded shadow hover:bg-gray-700 dark:bg-white dark:text-black dark:hover:bg-gray-100"
//       >
//         {theme === "dark" ? "☀ Light" : "🌙 Dark"} Mode
//       </button>

//       <div className="relative z-10 max-w-7xl mx-auto px-6 py-10">
//         {children || (
//           <div className="text-center text-gray-400 dark:text-gray-500 mt-20">
//             <p className="italic">This is where your AI-powered answers will appear.</p>
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }
