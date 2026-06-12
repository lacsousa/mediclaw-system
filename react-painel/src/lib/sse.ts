interface SSECallbacks {
  onToken: (content: string) => void;
  onCitation: (citation: { source: string; chunk_id: string }) => void;
  onDone: (result: {
    tokens_used: number;
    blocked: boolean;
    patient_id?: number;
    patient_first_name?: string;
    patient_created?: boolean;
  }) => void;
  onError: (error: { code: string; message: string }) => void;
}

export function openStream(url: string, callbacks: SSECallbacks): () => void {
  const es = new EventSource(url);

  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data as string);
      switch (data.type) {
        case "token":
          callbacks.onToken(data.content as string);
          break;
        case "citation":
          callbacks.onCitation(data as { source: string; chunk_id: string });
          break;
        case "done":
          callbacks.onDone(data);
          es.close();
          break;
        case "error":
          callbacks.onError(data as { code: string; message: string });
          es.close();
          break;
      }
    } catch {
      callbacks.onError({ code: "PARSE_ERROR", message: "Erro ao processar resposta" });
      es.close();
    }
  };

  es.onerror = () => {
    callbacks.onError({ code: "SSE_ERROR", message: "Conexão interrompida" });
    es.close();
  };

  return () => es.close();
}
