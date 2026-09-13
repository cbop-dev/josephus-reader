import { getWork } from './works';

export type SchemeId = 'niese';

export interface ParsedLocation {
  column: string;
  line: number | null;
}

export interface CitationScheme {
  readonly id: SchemeId;
  readonly columnRegex: RegExp;
  readonly hasUserFacingLines: boolean;
  readonly jumpPlaceholder: string;
  readonly label: string;
  parseColumnToken(raw: string): string | null;
  parseLocation(raw: string): ParsedLocation | null;
  formatCitation(column: string, line?: number | null): string;
}

const NIESE_COLUMN_RE = /^§?\s*(\d+)$/;

function normalize(raw: string): string {
  return raw.trim().toLowerCase().replace(/\s+/g, '');
}

function makeNieseScheme(): CitationScheme {
  function parseColumnToken(raw: string): string | null {
    const norm = normalize(raw);
    const m = NIESE_COLUMN_RE.exec(norm);
    return m ? m[1] : null;
  }

  function parseLocation(raw: string): ParsedLocation | null {
    const norm = normalize(raw);
    if (!norm) return null;
    const m = NIESE_COLUMN_RE.exec(norm);
    if (m) return { column: m[1], line: null };
    return null;
  }

  function formatCitation(column: string, _line?: number | null): string {
    return `§ ${column}`;
  }

  return {
    id: 'niese',
    columnRegex: NIESE_COLUMN_RE,
    hasUserFacingLines: false,
    jumpPlaceholder: 'e.g. § 15 or 15',
    label: 'Niese Section',
    parseColumnToken,
    parseLocation,
    formatCitation
  };
}

const NIESE_SCHEME = makeNieseScheme();

export function scheme(_id?: string | null): CitationScheme {
  return NIESE_SCHEME;
}

export function schemeFor(_work?: string): CitationScheme {
  return NIESE_SCHEME;
}

export function formatCite(work: string, column: string, line?: number | null): string {
  return schemeFor(work).formatCitation(column, line);
}

export function formatHash(work: string, column: string, line?: number | null): string {
  return `#${formatCite(work, column, line)}`;
}

export function formatLocValue(_work: string, column: string): string {
  return column;
}
