
import { LexQuery } from "$lib/components/LexQuery.svelte";
import { Lexeme } from '$lib/Lexeme';
//import { LxxGreekLexeme, TfLxxDataset } from "$lib/lxx/tfLXX";
import { TfBhsDataset } from "$lib/bhs/bhs";
//import {Lexeme} from '$lib/Lexeme';
import * as BibleUtils from "$lib/utils/bible-utils.js";
import { GreekLexeme } from "$lib/Lexeme";
import { test, expect } from 'vitest'

const tfBHS = new TfBhsDataset

test('test', () => {
    expect(true).toBe(true);
})

test('combineRefs test', () => {
    const testData = [
        {
            in: ["Jonah 1:5", "Jonah 1:6"],
            out: "Jonah 1:5-6"
        },
        {
            in: ["Jonah 1:5", "Jonah 1:2", "Jonah 1:6"],
            out: "Jonah 1:2,5-6"
        },
        {
            in: ["2Sam 4:26"],
            out: "2Sam 4:26"
        },
        {
            in: ["SongofSongs"],
            out: "Cant"
        }
        


    ]
    for (const test of testData) {
        expect(tfBHS.booksDict.combineRefs(test.in)).toEqual(test.out);
    }
    expect(true).toBe(true);
});


test('lookupBookAbbrev',()=>{
    expect(true).toBe(true);
    const tests = [
        {input:'2 Sam', output: "2Sam"},
        {input:'Song of Songs', output: "Cant"},
    ]



    for (const t of tests){
        
      expect(tfBHS.booksDict.lookupBookAbbrev(t.input)).toEqual(t.output);
    }

})
