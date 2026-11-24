// Talking to the Python API.
//
// The types below describe the JSON the API sends back. All money is whole PAISE.
// Think of each `type` as a Python dataclass: a list of fields and their types.

export type Member = { id: number; name: string; upi_id: string | null };
export type Share = { member_id: number; share: number };

export type Expense = {
  id: number;
  description: string;
  paid_by: number;
  amount: number;
  split_type: "equal" | "exact";
  created_at: string;
  shares: Share[];
};

export type Balance = { member_id: number; name: string; balance: number };

export type Group = {
  id: string;
  name: string;
  is_demo: boolean;
  members: Member[];
  expenses: Expense[];
  balances: Balance[];
};

export type Debt = { from_name: string; to_name: string; amount: number };

export type Payment = {
  from_id: number;
  from_name: string;
  to_id: number;
  to_name: string;
  to_upi_id: string | null;
  amount: number;
  upi_link: string | null;
};

export type PersonLeft = { name: string; amount: number };

export type Step = {
  from_name: string;
  to_name: string;
  amount: number;
  debtors_left: PersonLeft[];
  creditors_left: PersonLeft[];
};

export type Settlement = {
  before_debts: number;
  after_payments: number;
  debts: Debt[];
  payments: Payment[];
  steps: Step[];
};

export type Stats = { groups: number; expenses: number; demo_groups: number };

export type NewMember = { name: string; upi_id: string };

export type NewExpense = {
  description: string;
  paid_by: number;
  amount: string; // rupees as typed, e.g. "250.50". The server turns it into paise.
  split_type: "equal" | "exact";
  participants: number[];
  shares: Record<number, string>;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// The API sends errors as {"detail": "..."} (or a list of problems for bad input).
function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    return (first.msg ?? "Something in the form is not right").replace("Value error, ", "");
  }
  return `The server answered with an error (${status}). Try again.`;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(API_URL + path, {
      ...options,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    throw new Error("Can't reach the server. Check your internet connection and try again.");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(errorMessage(body, response.status));
  }
  return response.json();
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
}

export const api = {
  stats: () => request<Stats>("/api/stats"),
  createGroup: (name: string, members: NewMember[]) => post<Group>("/api/groups", { name, members }),
  createDemoGroup: () => post<Group>("/api/groups/demo"),
  getGroup: (id: string) => request<Group>(`/api/groups/${id}`),
  addMember: (id: string, member: NewMember) => post<Member>(`/api/groups/${id}/members`, member),
  setUpiId: (id: string, memberId: number, upiId: string) =>
    request<Member>(`/api/groups/${id}/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify({ upi_id: upiId }),
    }),
  addExpense: (id: string, expense: NewExpense) => post<Expense>(`/api/groups/${id}/expenses`, expense),
  deleteExpense: (id: string, expenseId: number) =>
    request<{ deleted: number }>(`/api/groups/${id}/expenses/${expenseId}`, { method: "DELETE" }),
  settle: (id: string) => request<Settlement>(`/api/groups/${id}/settle`),
};
