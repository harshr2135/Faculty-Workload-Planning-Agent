import { apiGet } from "./client";
import type { PolicyOverview } from "@/types/api";

export function fetchPolicies(): Promise<PolicyOverview> {
  return apiGet<PolicyOverview>("/policies");
}
