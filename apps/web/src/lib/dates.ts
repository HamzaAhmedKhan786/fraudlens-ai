/** SQLite read models can omit the UTC suffix; all stored application timestamps are UTC. */
export function utcDate(value: string) {
  return new Date(/(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : `${value}Z`);
}
