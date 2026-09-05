"use client";

import { useActionState } from "react";

import {
  executeSupplierRelationship,
  promoteSupplierCandidate,
  type BuildActionState,
} from "../app/build/actions";

const initial: BuildActionState = { kind: "idle", message: "" };

export function RelationshipExecutionAction({
  productId,
  supplierId,
  approvalId,
  role,
}: {
  productId: string;
  supplierId: string;
  approvalId: string;
  role: string;
}) {
  const [state, action, pending] = useActionState(executeSupplierRelationship, initial);
  return (
    <form action={action} className="build-inline-action">
      <input type="hidden" name="product_id" value={productId} />
      <input type="hidden" name="supplier_id" value={supplierId} />
      <input type="hidden" name="approval_request_id" value={approvalId} />
      <input type="hidden" name="role" value={role} />
      <button className="primary-button" disabled={pending}>
        {pending ? "Executing…" : "Execute approved relationship"}
      </button>
      <small>No supplier contact, order, purchase, or payment occurs.</small>
      <p className={`action-message action-${state.kind}`} role="status">
        {state.message}
      </p>
    </form>
  );
}

export function CandidatePromotionAction({
  productId,
  candidateId,
}: {
  productId: string;
  candidateId: string;
}) {
  const [state, action, pending] = useActionState(promoteSupplierCandidate, initial);
  return (
    <form action={action} className="build-inline-action">
      <input type="hidden" name="product_id" value={productId} />
      <input type="hidden" name="candidate_id" value={candidateId} />
      <label>
        Verified supplier name
        <input name="name" required />
      </label>
      <label>
        Country
        <input name="country" required />
      </label>
      <button className="primary-button" disabled={pending}>
        {pending ? "Confirming…" : "Confirm canonical Supplier Profile"}
      </button>
      <small>Human confirmation preserves Candidate history and never auto-merges by name.</small>
      <p className={`action-message action-${state.kind}`} role="status">
        {state.message}
      </p>
    </form>
  );
}
