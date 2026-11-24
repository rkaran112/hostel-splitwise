// Money helpers. Like the Python side, we only do whole-number maths on PAISE.
//   Rs 12.50  ->  1250 paise

// 1250 -> "₹12.50", 240000 -> "₹2,400", -500 -> "-₹5".
// toLocaleString("en-IN") puts commas the Indian way (12,34,567).
export function formatPaise(paise: number): string {
  const sign = paise < 0 ? "-" : "";
  const absolute = Math.abs(paise);
  const rupees = Math.floor(absolute / 100);
  const leftoverPaise = absolute % 100;

  const rupeesText = rupees.toLocaleString("en-IN");
  if (leftoverPaise === 0) {
    return `${sign}₹${rupeesText}`;
  }
  return `${sign}₹${rupeesText}.${String(leftoverPaise).padStart(2, "0")}`;
}

// What a person typed -> paise, or null if it is not a valid amount.
// "12" -> 1200, "12.5" -> 1250, "12.50" -> 1250, "abc" -> null.
// Same rule as the Python parser: up to 2 digits after the dot, no floats.
export function parseRupees(text: string): number | null {
  const match = /^(\d+)(?:\.(\d{1,2}))?$/.exec(text.trim());
  if (match === null) {
    return null;
  }
  const rupees = Number(match[1]);
  const paiseText = (match[2] ?? "").padEnd(2, "0");
  return rupees * 100 + Number(paiseText);
}
