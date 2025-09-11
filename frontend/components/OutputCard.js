// import { useTheme } from "next-themes";
// import { useEffect, useState } from "react";


// export default function OutputCard({ question, english, swahili, mode = "summarize" }) {
//   const { theme } = useTheme();
//   const [mounted, setMounted] = useState(false);

//   useEffect(() => {
//     setMounted(true);
//   }, []);

//   if (!mounted) return null; // 👈 Prevent SSR crash

//   const isDark = theme === "dark";
//   const engBg = isDark ? "bg-gray-800 text-white" : "bg-gray-100 text-black";
//   const swaBg = isDark ? "bg-gray-900 text-white" : "bg-gray-200 text-black";

//   return (
//     <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
//       <div className={`${engBg} p-6 rounded-lg shadow-md transition`}>
//         <h3 className="font-semibold text-xl mb-2">
//           🇬🇧 {mode === "summarize" ? "English Summary" : "English Answer"}
//         </h3>
//         {question && <p className="text-sm mb-2 italic">❓ {question}</p>}
//         <p
//           className="whitespace-pre-wrap text-sm"
//           dangerouslySetInnerHTML={{
//             __html: (english || "(Not available)").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
//           }}
//         />
//       </div>

//       <div className={`${swaBg} p-6 rounded-lg shadow-md transition`}>
//         <h3 className="font-semibold text-xl mb-2">
//           🇰🇪 {mode === "summarize" ? "Swahili Summary" : "Swahili Answer"}
//         </h3>
//         <p
//           className="whitespace-pre-wrap text-sm"
//           dangerouslySetInnerHTML={{
//             __html: (swahili || "(Swahili version not available)").replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
//           }}
//         />
//       </div>
//     </div>
//   );
// }
