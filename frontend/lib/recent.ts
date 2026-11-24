"use client";

import { useSyncExternalStore } from "react";

// "Your groups": a list of groups opened on THIS phone, kept in the browser's localStorage.
// There are no accounts, so this is only a convenience. Every access is wrapped in
// try/catch because storage can be blocked (private mode, strict settings).

const KEY = "hostel-splitwise-recent";
const MAX_REMEMBERED = 6;

export type RecentGroup = { id: string; name: string };

function readRaw(): string {
  try {
    return localStorage.getItem(KEY) ?? "[]";
  } catch {
    return "[]";
  }
}

function parse(raw: string): RecentGroup[] {
  try {
    return JSON.parse(raw) as RecentGroup[];
  } catch {
    return [];
  }
}

export function rememberGroup(group: RecentGroup) {
  const others = parse(readRaw()).filter((item) => item.id !== group.id);
  const updated = [group, ...others].slice(0, MAX_REMEMBERED);
  try {
    localStorage.setItem(KEY, JSON.stringify(updated));
  } catch {
    // Storage is blocked. Nothing to do: the group still works, it just is not listed.
  }
}

function subscribe(onChange: () => void) {
  window.addEventListener("storage", onChange);
  return () => window.removeEventListener("storage", onChange);
}

// useSyncExternalStore lets React read from outside data (here: localStorage) safely.
// On the server there is no localStorage, so the third argument gives an empty list.
export function useRecentGroups(): RecentGroup[] {
  const raw = useSyncExternalStore(subscribe, readRaw, () => "[]");
  return parse(raw);
}
