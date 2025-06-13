// src/shared/store.ts
import { create } from 'zustand';

interface AppState {
  token: string | null;
  setToken: (token: string) => void;

  profitUsd: number;
  setProfitUsd: (value: number) => void;
}


export const useStore = create<AppState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),

  profitUsd: 0,
  setProfitUsd: (value) => set({ profitUsd: value }),
}));

