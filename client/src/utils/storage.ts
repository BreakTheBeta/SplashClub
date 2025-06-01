export const USER_ID_KEY = 'game_user_id';

export const saveUserId = (userId: string) => {
  try {
    sessionStorage.setItem(USER_ID_KEY, userId);
  } catch (error) {
    console.error('Failed to save user ID to localStorage:', error);
  }
};

export const getUserId = (): string | null => {
  try {
    return sessionStorage.getItem(USER_ID_KEY);
  } catch (error) {
    console.error('Failed to get user ID from localStorage:', error);
    return null;
  }
};

export const clearUserId = () => {
  try {
    sessionStorage.removeItem(USER_ID_KEY);
  } catch (error) {
    console.error('Failed to clear user ID from localStorage:', error);
  }
}; 