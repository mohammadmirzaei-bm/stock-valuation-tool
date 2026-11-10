import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { usePersistentState } from "./usePersistentState";

beforeEach(() => {
  localStorage.clear();
  vi.useFakeTimers();
});
afterEach(() => vi.useRealTimers());

describe("usePersistentState — reload survival", () => {
  it("restores a primitive (number), not an empty object", () => {
    localStorage.setItem("sv-form:dcf-terminal-growth", JSON.stringify(3));
    const { result } = renderHook(() => usePersistentState<number>("dcf-terminal-growth", 7));
    expect(result.current[0]).toBe(3);
  });

  it("rejects a legacy {} entry poisoning a number field (falls back to initial)", () => {
    localStorage.setItem("sv-form:dcf-terminal-growth", "{}"); // written by an older build
    const { result } = renderHook(() => usePersistentState<number>("dcf-terminal-growth", 3));
    expect(result.current[0]).toBe(3);
  });

  it("falls back to the initial value when nothing is stored", () => {
    const { result } = renderHook(() => usePersistentState<number>("missing", 7));
    expect(result.current[0]).toBe(7);
  });

  it("restores an array verbatim (scenarios list)", () => {
    localStorage.setItem("sv-form:analyses-scenarios", JSON.stringify([{ name: "a" }, { name: "b" }]));
    const { result } = renderHook(() =>
      usePersistentState<{ name: string }[]>("analyses-scenarios", []),
    );
    expect(Array.isArray(result.current[0])).toBe(true);
    expect(result.current[0]).toEqual([{ name: "a" }, { name: "b" }]);
  });

  it("shallow-merges stored fields over default object fields", () => {
    localStorage.setItem("sv-form:obj", JSON.stringify({ a: 2 }));
    const { result } = renderHook(() => usePersistentState<{ a: number; b: number }>("obj", { a: 1, b: 3 }));
    expect(result.current[0]).toEqual({ a: 2, b: 3 });
  });

  it("writes updates back to localStorage (debounced)", () => {
    const { result } = renderHook(() => usePersistentState<number>("counter", 0));
    act(() => {
      result.current[1](5);
    });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(JSON.parse(localStorage.getItem("sv-form:counter")!)).toBe(5);
  });

  it("flushes the last edit on unmount inside the debounce window", () => {
    const { result, unmount } = renderHook(() => usePersistentState<number>("quick-nav", 0));
    act(() => {
      result.current[1](42);
    });
    // Navigate away before the 250ms debounce fires.
    unmount();
    expect(JSON.parse(localStorage.getItem("sv-form:quick-nav")!)).toBe(42);
  });
});
