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