"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Patient, PatientDetail } from "@/types/api";

interface PaginatedResponse {
  results: Patient[];
  count: number;
  next: string | null;
}

export function usePatients() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pageRef = useRef(1);

  const fetchPatients = useCallback(async (reset = false) => {
    if (reset) pageRef.current = 1;
    setIsLoading(true);
    setError(null);
    try {
      const res = await api.get<PaginatedResponse>(`/api/v1/patients/?page=${pageRef.current}`);
      const { results, next } = res.data;
      setPatients((prev) => (reset ? results : [...prev, ...results]));
      setHasMore(next !== null);
      pageRef.current += 1;
    } catch (err) {
      console.error("[usePatients] erro:", err);
      setError("Erro ao carregar pacientes.");
    } finally {
      setIsLoading(false);
    }
  }, []); // sem dependências — função estável

  const deletePatient = async (id: number): Promise<boolean> => {
    try {
      await api.delete(`/api/v1/patients/${id}/`);
      setPatients((prev) => prev.filter((p) => p.id !== id));
      return true;
    } catch (err) {
      console.error("[usePatients] erro ao deletar:", err);
      return false;
    }
  };

  return { patients, isLoading, hasMore, error, fetchPatients, deletePatient };
}

export function usePatient(id: number) {
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const fetchPatient = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get<PatientDetail>(`/api/v1/patients/${id}/`);
      setPatient(res.data);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 404) {
        setNotFound(true);
      } else {
        console.error("[usePatient] erro:", err);
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]); // dependência estável: só muda se `id` mudar

  return { patient, isLoading, notFound, fetchPatient };
}
