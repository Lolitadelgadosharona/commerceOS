"use client";

import { useActionState } from "react";
import type { ReactNode } from "react";
import type { GrowthActionState } from "../app/growth/actions";

export function GrowthActionForm({action,children,label,variant="primary"}:{action:(state:GrowthActionState,form:FormData)=>Promise<GrowthActionState>;children:ReactNode;label:string;variant?:"primary"|"secondary"}){
  const initialState:GrowthActionState={kind:"idle",message:""};
  const [state,formAction,pending]=useActionState(action,initialState);
  return <form action={formAction} className="growth-form">{children}<button className={`growth-button ${variant}`} disabled={pending}>{pending?"Working…":label}</button>{state.message?<p className={`form-message ${state.kind}`} role="status">{state.message}</p>:null}</form>;
}
