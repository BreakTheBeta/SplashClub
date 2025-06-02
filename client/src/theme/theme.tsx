// src/theme/theme.ts
export type ThemeColors = {
  primary: string;
  primaryHover: string;
  secondary: string;
  secondaryHover: string;
  error: string;
  success: string;
  border: string;
  successBorder: string;
  errorBorder: string;
  text: {
    primary: string;
    secondary: string;
    error: string;
    accent: string;
  };
  background: {
    card: string;
    page: string;
    toast: string;
    highlight: string;
  };
};

export const defaultTheme: ThemeColors = {
  primary: "bg-cyan-500",
  primaryHover: "hover:bg-cyan-600",
  secondary: "bg-indigo-400",
  secondaryHover: "hover:bg-indigo-500",
  error: "bg-purple-600",
  success: "bg-teal-500",
  border: "border-cyan-300",
  successBorder: "border-teal-500",
  errorBorder: "border-purple-500",
  text: {
    primary: "text-slate-100",
    secondary: "text-cyan-200",
    error: "text-purple-400",
    accent: "text-cyan-400"
  },
  background: {
    card: "bg-slate-800",
    page: "bg-slate-900",
    toast: "bg-indigo-500",
    highlight: "bg-slate-700"
  },
}; 

export const darkTheme: ThemeColors = {
  primary: "bg-blue-600",
  primaryHover: "hover:bg-blue-700",
  secondary: "bg-gray-600",
  secondaryHover: "hover:bg-gray-700",
  error: "bg-red-600",
  success: "bg-green-600",
  border: "border-gray-600",
  successBorder: "border-green-600",
  errorBorder: "border-red-600",
  text: {
    primary: "text-white",
    secondary: "text-gray-300",
    error: "text-red-400",
    accent: "text-blue-400"
  },
  background: {
    card: "bg-gray-800",
    page: "bg-gray-900",
    toast: "bg-red-600",
    highlight: "bg-gray-700"
  },
};

// Early 2000s British Gameshow Theme - Think "Who Wants to Be a Millionaire" meets "The Weakest Link"
export const gameshowTheme: ThemeColors = {
  primary: "bg-gradient-to-r from-yellow-400 via-amber-500 to-orange-500 shadow-lg shadow-amber-500/50",
  primaryHover: "hover:from-yellow-300 hover:via-amber-400 hover:to-orange-400 hover:shadow-xl hover:shadow-amber-500/60 transform hover:scale-105 transition-all duration-200",
  secondary: "bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-800 shadow-md shadow-blue-500/30",
  secondaryHover: "hover:from-blue-500 hover:via-blue-600 hover:to-indigo-700 hover:shadow-lg hover:shadow-blue-500/40 transform hover:scale-105 transition-all duration-200",
  error: "bg-gradient-to-r from-red-600 via-red-700 to-red-800 shadow-md shadow-red-500/30",
  success: "bg-gradient-to-r from-green-500 via-emerald-600 to-green-700 shadow-md shadow-green-500/30",
  border: "border-2 border-amber-400 shadow-sm shadow-amber-300/20",
  successBorder: "border-2 border-green-400 shadow-sm shadow-green-300/20",
  errorBorder: "border-2 border-red-400 shadow-sm shadow-red-300/20",
  text: {
    primary: "text-white font-bold drop-shadow-md",
    secondary: "text-slate-200 font-semibold drop-shadow-sm",
    error: "text-purple-700 font-semibold drop-shadow-md",
    accent: "text-blue-200 font-bold drop-shadow-md"
  },
  background: {
    card: "bg-gradient-to-br from-slate-800 via-slate-900 to-blue-900 border-2 border-amber-400/30 shadow-2xl shadow-amber-500/20 backdrop-blur-sm",
    page: "bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900",
    toast: "bg-gradient-to-r from-purple-600 via-purple-700 to-indigo-800 shadow-lg shadow-purple-500/30",
    highlight: "bg-gradient-to-r from-amber-500/20 via-yellow-400/20 to-orange-500/20 border border-amber-400/40"
  },
};