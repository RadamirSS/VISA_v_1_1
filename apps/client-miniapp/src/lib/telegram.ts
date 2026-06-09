export type TelegramMiniAppUser = {
  id?: number;
  username?: string;
  first_name?: string;
  last_name?: string;
};

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        initDataUnsafe?: { user?: TelegramMiniAppUser };
        ready?: () => void;
        expand?: () => void;
      };
    };
  }
}

export function getTelegramUser(): TelegramMiniAppUser | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.Telegram?.WebApp?.initDataUnsafe?.user;
}

export function getTelegramInitData(): string | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }
  return window.Telegram?.WebApp?.initData;
}

export function setupTelegramWebApp() {
  if (typeof window === "undefined") {
    return;
  }
  window.Telegram?.WebApp?.ready?.();
  window.Telegram?.WebApp?.expand?.();
}
