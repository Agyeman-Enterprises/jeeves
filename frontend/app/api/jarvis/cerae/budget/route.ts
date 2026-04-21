import { NextRequest, NextResponse } from "next/server";
import { generateCognitiveBudget, getCognitiveBudget } from "@/lib/jarvis/cerae/cognitive";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { budget_date } = body;
    const userId = req.headers.get("x-user-id") || body.user_id;

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const budget = await generateCognitiveBudget(userId, budget_date);

    return NextResponse.json({ ok: true, budget });
  } catch (error: any) {
    console.error("Cognitive budget error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

export async function GET(req: NextRequest) {
  try {
    const userId = req.headers.get("x-user-id") || req.nextUrl.searchParams.get("user_id");
    const budgetDate = req.nextUrl.searchParams.get("budget_date");

    if (!userId) {
      return NextResponse.json(
        { error: "Missing user_id" },
        { status: 400 }
      );
    }

    const budget = await getCognitiveBudget(userId, budgetDate || undefined);

    if (!budget) {
      // Generate if doesn't exist
      const newBudget = await generateCognitiveBudget(userId, budgetDate || undefined);
      return NextResponse.json({ budget: newBudget });
    }

    return NextResponse.json({ budget });
  } catch (error: any) {
    console.error("Cognitive budget error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message },
      { status: 500 }
    );
  }
}

