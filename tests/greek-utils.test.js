import {test,expect} from 'vitest'
import { GreekUtils as gu} from '$lib/utils/greek-utils'


test('test',()=>{
    expect(true).toBe(true);
})


test('remove diacritics test',()=>{
    const gMap = {"ᾤ":"ω"};
    for (const [g1,g2] of Object.entries(gMap)) {
        expect(gu.removeDiacritics(g1)).toBe(g2);
    }
        
})


