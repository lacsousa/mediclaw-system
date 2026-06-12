const EDUCATIONAL_DISCLAIMER =
  /não substitui.*(consulta|profissional|avaliação|diagnóstico|tratamento)/i;

/** Mensagens do agente podem já incluir o aviso educativo no corpo. */
export function hasEducationalDisclaimer(content: string): boolean {
  return EDUCATIONAL_DISCLAIMER.test(content);
}
