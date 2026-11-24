"use client";

import { useEffect, useRef, useState } from "react";

import { formatPaise } from "@/lib/money";

// A picture of the group: everyone sits on a circle, an arrow goes from the person who
// owes to the person who is owed, and thicker arrows mean more money.
//   Before = every debt between every pair   (a tangle)
//   After  = the settle-up payments          (a few clean arrows)
// The picture starts on Before, then fades to After once, so the saving is easy to see.

export type Edge = { from: string; to: string; amount: number };

const WIDTH = 360;
const HEIGHT = 316;
const CENTER_X = 180;
const CENTER_Y = 158;
const RING_RADIUS = 96; // distance from the middle to each person
const LABEL_RADIUS = 124; // distance from the middle to each name
const NODE_RADIUS = 19;

type Point = { x: number; y: number };

function shortName(name: string): string {
  return name.length > 9 ? name.slice(0, 8) + "…" : name;
}

function pointOnRing(index: number, count: number, radius: number): Point {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / count; // start at the top, go clockwise
  return { x: CENTER_X + radius * Math.cos(angle), y: CENTER_Y + radius * Math.sin(angle) };
}

export function DebtDiagram({ before, after }: { before: Edge[]; after: Edge[] }) {
  const [mode, setMode] = useState<"before" | "after">("before");
  const touched = useRef(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timer = setTimeout(
      () => {
        if (!touched.current) {
          setMode("after");
        }
      },
      reducedMotion ? 0 : 1600,
    );
    return () => clearTimeout(timer);
  }, []);

  function choose(newMode: "before" | "after") {
    touched.current = true;
    setMode(newMode);
  }

  const names: string[] = [];
  for (const edge of [...before, ...after]) {
    for (const name of [edge.from, edge.to]) {
      if (!names.includes(name)) {
        names.push(name);
      }
    }
  }

  const positions: Record<string, Point> = {};
  names.forEach((name, index) => {
    positions[name] = pointOnRing(index, names.length, RING_RADIUS);
  });

  const biggest = Math.max(1, ...before.map((edge) => edge.amount), ...after.map((edge) => edge.amount));

  function drawEdges(edges: Edge[], colour: string, markerId: string, showAmounts: boolean) {
    return edges.map((edge) => {
      const start = positions[edge.from];
      const end = positions[edge.to];
      const length = Math.hypot(end.x - start.x, end.y - start.y);
      const unitX = (end.x - start.x) / length;
      const unitY = (end.y - start.y) / length;

      // Stop the line at the edge of each circle, and leave room for the arrow head.
      const lineStart = { x: start.x + unitX * NODE_RADIUS, y: start.y + unitY * NODE_RADIUS };
      const lineEnd = { x: end.x - unitX * (NODE_RADIUS + 6), y: end.y - unitY * (NODE_RADIUS + 6) };
      const middle = { x: (start.x + end.x) / 2, y: (start.y + end.y) / 2 };

      return (
        <g key={`${edge.from}-${edge.to}`}>
          <line
            x1={lineStart.x}
            y1={lineStart.y}
            x2={lineEnd.x}
            y2={lineEnd.y}
            stroke={colour}
            strokeWidth={1.5 + (3.5 * edge.amount) / biggest}
            strokeLinecap="round"
            markerEnd={`url(#${markerId})`}
          />
          {showAmounts && (
            <text
              x={middle.x}
              y={middle.y}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize="11"
              fontWeight="700"
              fill="var(--color-ink)"
              stroke="var(--color-paper)"
              strokeWidth="4"
              paintOrder="stroke"
            >
              {formatPaise(edge.amount)}
            </text>
          )}
        </g>
      );
    });
  }

  return (
    <figure>
      <div role="group" aria-label="Show the debts before or after settling up" className="grid grid-cols-2 gap-1 rounded-full bg-surface p-1">
        <button
          type="button"
          aria-pressed={mode === "before"}
          onClick={() => choose("before")}
          className={`min-h-11 rounded-full font-semibold ${mode === "before" ? "bg-ink text-white" : "text-muted"}`}
        >
          Before: {before.length} debts
        </button>
        <button
          type="button"
          aria-pressed={mode === "after"}
          onClick={() => choose("after")}
          className={`min-h-11 rounded-full font-semibold ${mode === "after" ? "bg-brand text-white" : "text-muted"}`}
        >
          After: {after.length} payments
        </button>
      </div>

      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={
          mode === "before"
            ? `${before.length} debts between ${names.length} people`
            : `${after.length} payments settle all ${names.length} people`
        }
        className="mt-2 w-full"
      >
        <defs>
          <marker id="head-before" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b98ad" />
          </marker>
          <marker id="head-after" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="var(--color-brand)" />
          </marker>
        </defs>

        <g className="fade-layer" style={{ opacity: mode === "before" ? 1 : 0 }}>
          {drawEdges(before, "#8b98ad", "head-before", false)}
        </g>
        <g className="fade-layer" style={{ opacity: mode === "after" ? 1 : 0 }}>
          {drawEdges(after, "var(--color-brand)", "head-after", true)}
        </g>

        {names.map((name, index) => {
          const node = positions[name];
          const label = pointOnRing(index, names.length, LABEL_RADIUS);
          const sideways = (label.x - CENTER_X) / LABEL_RADIUS;
          const anchor = sideways > 0.3 ? "start" : sideways < -0.3 ? "end" : "middle";
          return (
            <g key={name}>
              <circle cx={node.x} cy={node.y} r={NODE_RADIUS} fill="var(--color-ink)" />
              <text
                x={node.x}
                y={node.y}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="15"
                fontWeight="700"
                fill="white"
              >
                {name.charAt(0).toUpperCase()}
              </text>
              <text
                x={label.x}
                y={label.y + 4}
                textAnchor={anchor}
                fontSize="12"
                fontWeight="600"
                fill="var(--color-ink)"
              >
                {shortName(name)}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption className="sr-only">
        Arrows point from the person who owes money to the person who is owed.
      </figcaption>
    </figure>
  );
}
