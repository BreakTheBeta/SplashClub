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
    };
    background: {
      card: string;
      page: string;
      toast: string;
    };
  };
  
  export const defaultTheme: ThemeColors = {
    primary: "bg-green-600",
    primaryHover: "hover:bg-green-700",
    secondary: "bg-gray-400",
    secondaryHover: "hover:bg-gray-500",
    error: "bg-red-500",
    success: "bg-green-500",
    border: "border-gray-300",
    successBorder: "border-green-500",
    errorBorder: "border-red-500",
    text: {
      primary: "text-gray-800",
      secondary: "text-gray-600",
      error: "text-red-500",
    },
    background: {
      card: "bg-white",
      page: "bg-gray-50",
      toast: "bg-red-500",
    },
  };
  
  // You can create alternative themes
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
    },
    background: {
      card: "bg-gray-800",
      page: "bg-gray-900",
      toast: "bg-red-600",
    },
  };
  
  // Create a theme context to easily switch themes
  // This could be expanded in the future
  export const activeTheme = defaultTheme;