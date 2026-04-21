// Nexus financial aggregation layer (read-only)
import { listFinancialEntities } from "@/lib/nexus/entities";
import { listSnapshotsForEntity, listTaxPositions } from "@/lib/nexus/snapshots";
import { listRecentTransactions } from "@/lib/nexus/transactions";

export type EntitySummary = {
  id: string;
  name?: string | null;
  type?: string | null;
  latestBalance?: number | null;
  latestSnapshotAt?: string | null;
  pendingTaxLiability?: number | null;
};

export type NexusDashboardSummary = {
  entities: EntitySummary[];
  recentTransactionsCount: number;
  lastTransactionAt?: string | null;
};

export async function getNexusDashboardSummary(input: {
  userId: string;
  workspaceId: string;
}): Promise<NexusDashboardSummary> {
  const entities = await listFinancialEntities(input);
  const summaries: EntitySummary[] = [];

  for (const entity of entities) {
    const snapshots = await listSnapshotsForEntity({
      userId: input.userId,
      workspaceId: input.workspaceId,
      entityId: String(entity.id),
      limit: 1,
    });

    const taxPositions = await listTaxPositions({
      userId: input.userId,
      workspaceId: input.workspaceId,
      entityId: String(entity.id),
    });

    const latestSnapshot = snapshots[0];
    const pendingTax = taxPositions.reduce((acc, t) => {
      const amount = (t as any).liability_amount ?? 0;
      return acc + (typeof amount === "number" ? amount : 0);
    }, 0);

    summaries.push({
      id: String(entity.id),
      name: (entity as any).name ?? null,
      type: (entity as any).type ?? null,
      latestBalance: latestSnapshot
        ? (latestSnapshot as any).balance ?? null
        : null,
      latestSnapshotAt: latestSnapshot?.created_at ?? null,
      pendingTaxLiability: pendingTax || null,
    });
  }

  const recent = await listRecentTransactions({
    userId: input.userId,
    workspaceId: input.workspaceId,
    limit: 1,
  });

  return {
    entities: summaries,
    recentTransactionsCount: recent.length,
    lastTransactionAt: recent[0]?.created_at ?? null,
  };
}

export async function getFinancialOverview(userId: string): Promise<any> {
  // Stub implementation for existing route
  // TODO: Implement proper financial overview
  return {
    entities: [],
    totalBalance: 0,
    recentTransactions: [],
  };
}

export async function getEntityFinancials(entityId: string): Promise<any> {
  // Stub implementation for existing route
  // TODO: Implement proper entity financials
  return {
    entityId,
    balance: 0,
    transactions: [],
    snapshots: [],
  };
}
