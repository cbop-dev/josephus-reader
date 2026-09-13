import { writable } from 'svelte/store';

export type WorkId = 'antiquities' | 'war' | 'life' | 'apion';
export type ViewMode = 'parallel' | 'greek' | 'english' | 'stacked';
export type Theme = 'sepia' | 'dark' | 'light';

export interface SelectedWordInfo {
  word: string;
  lemma: string;
  parse: string;
  desc: string;
  definition?: string;
}

export const currentWork = writable<WorkId>('antiquities');
export const currentBook = writable<number>(1);
export const viewMode = writable<ViewMode>('parallel');
export const theme = writable<Theme>('sepia');
export const morphEnabled = writable<boolean>(true);
export const fontSize = writable<number>(19);
export const selectedWord = writable<SelectedWordInfo | null>(null);
export const showLexiconModal = writable<boolean>(false);
export const showPdfModal = writable<boolean>(false);
export const showAttributionModal = writable<boolean>(false);
export const searchQuery = writable<string>('');

