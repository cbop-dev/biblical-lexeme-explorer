import { LexQuery } from "$lib/components/LexQuery.svelte.js";
import { VocabEngine } from "$lib/engine/VocabEngine.js";
import { test, expect } from 'vitest';

test('fetchLexes-common', async () => {
    let query = new LexQuery();
    query.sections = [623751, 623752];
    query.common = true;
    await VocabEngine.fetchLexemes(query);
    expect(query.response.common.length).toBe(50);
    expect(query.results.lexemeArray.length).toBe(50);
});

test('fetchLexes-common-unique', async () => {
    let query = new LexQuery();
    query.sections = [623694, 623695];
    query.common = true;
    query.unique = true;
    await VocabEngine.fetchLexemes(query);
    expect(query.results.lexemeArray.length).toBe(4);
});

test('fetchLexes-unique', async () => {
    let query = new LexQuery();
    query.sections = [623694, 623695];
    query.unique = true;
    await VocabEngine.fetchLexemes(query);
    expect(query.results.lexemeArray.length).toBe(786);
});