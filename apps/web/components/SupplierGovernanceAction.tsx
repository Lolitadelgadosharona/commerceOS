"use client";
import { useActionState } from "react";
import { requestSupplierSelection, type SupplierActionState } from "../app/suppliers/actions";

const initial:SupplierActionState={kind:"idle",message:""};
export function SupplierGovernanceAction({supplierId,productId,ready}:{supplierId:string;productId:string;ready:boolean}){
  const [state,action,pending]=useActionState(requestSupplierSelection,initial);
  return <section className="investment-action-panel"><p className="eyebrow">Human authority</p><h2>Supplier selection decision</h2><p>{ready?"Qualification blockers are clear. Request a Product-specific human decision.":"Qualification blockers must be resolved before selection can enter review."}</p>{ready&&<form action={action}><input type="hidden" name="supplier_id" value={supplierId}/><input type="hidden" name="product_id" value={productId}/><label>Decision reason<textarea name="reason" required placeholder="Explain why this supplier should advance for this Product."/></label><button className="primary-button" disabled={pending}>{pending?"Submitting…":"Request supplier approval"}</button></form>}<p className={`action-message action-${state.kind}`} role="status">{state.message}</p><small>Approval selects a supplier candidate only. It never sends, orders, negotiates, or pays.</small></section>;
}
