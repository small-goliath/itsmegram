import { redirect, notFound } from "next/navigation";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

async function getReportIdByUsername(username: string): Promise<string | null> {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/report/by-username/${encodeURIComponent(username)}`,
      { cache: "no-store" }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return data.id ?? null;
  } catch {
    return null;
  }
}

export default async function ReportByUsernamePage({
  params,
}: {
  params: Promise<{ username: string }>;
}) {
  const { username } = await params;
  const reportId = await getReportIdByUsername(username);

  if (!reportId) {
    notFound();
  }

  redirect(`/report/${reportId}`);
}
