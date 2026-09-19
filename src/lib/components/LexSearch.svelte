<script>
	import { LexQuery, LexQueryFilter } from '$lib/components/LexQuery.svelte.js';
	import LemmaInfo from '$lib/components/LemmaInfo.svelte';
	import * as StringUtils from '$lib/utils/string-utils.js';

	import { VocabDataset, TfDataset } from '$lib/data/VocabDataset.js';
	import { VocabEngine, TF } from '$lib/engine/VocabEngine.js';
	import { Lexeme } from '$lib/Lexeme.js';
	import Button from '$lib/components/ui/Button.svelte';
	import SearchBox from './ui/SearchBox.svelte';

	import Modal from '$lib/components/ui/Modal.svelte';
	import LexFilterInput from '$lib/components/LexFilterInput.svelte';
	import Modal2 from '$lib/components/ui/Modal2.svelte';
	import { LexRefQueries } from '$lib/LexRefQueries.svelte';
	/**
	 * @typedef LexSearchProps
	 * @propery {TfDataset} tfData
	 */
	/**
	 * @type {LexSearchProps} props
	 */
	let { tfData } = $props();

	let lang = $derived(tfData?.lang || 'greek');
	/**
	 * @type {number[]} matchedIndexes
	 */
	let bestMatchedIndexes = $state([]);

	/**
	 * @type {number[]} matchedIndexes
	 */
	let otherMatchedIndexes = $state([]);

	let selectedLexeme = $state();
	let showModal = $state(false);

	/**
	 *
	 * @param {string} beta
	 * @returns {Object[]}
	 */

	/**
	 *
	 * @param {number} id
	 */
	async function selectLemma(id) {
		selectedLexeme = id;
		fetchLemma();
	}
	async function fetchLemma() {
		let id = Number(selectedLexeme);
		//console.debug("fetching lemma " + id);
		showModal = true;
		let lemma = new Lexeme();

		if (id >= 0) {
			queryReady = false;
			await VocabEngine.fetchLexInfo(id, lemma, tfData);
			if (lemma.id == id) {
				foundLemma = lemma;
				lexRefsQueries.checkGetLemmaRefs(lemma);
				queryReady = true;
			} else {
				// didn't work
			}
		} else {
			null;
		}
	}
	let queryReady = $state(false);
	/**
	 * @type {Lexeme} foundLemma
	 */
	let foundLemma = $state(new Lexeme());
	let lexRefsQueries=$derived(new LexRefQueries(tfData))
	/**
	 *
	 * @param {string} input
	 * @returns {string[]}
	 */
	function betaFilter(input) {
		input = input
			.trim()
			.toLowerCase()
			.replace('w', 'o')
			.replace(/[^a-z]/g, '');
		return [input, input.replace('h', 'e')];
	}

	let filter = new LexQueryFilter();
</script>

<hr class="thick" />
<div class="block items-center text-center">
	<h1>Lookup {tfData.name} Lexemes</h1>
	<hr class="thick" />
	<h2>Search for a Lexeme:</h2>

	<LexFilterInput
		lang={tfData.lang}
		filter={(input) => {}}
		itemsList={tfData.lexemes.plain}
		bind:bestMatches={bestMatchedIndexes}
		bind:otherMatches={otherMatchedIndexes}
		tooltip="Enter (case-sensitive) Latin characters, which will convert automatically to {StringUtils.capitalize(
			lang
		)}!"
		casesensitive={true}
	/>
</div>
<hr class="m-2" />

<div>
	{#if bestMatchedIndexes.length > 0 || otherMatchedIndexes.length > 0}
		<div>
			{#if bestMatchedIndexes.length > 0}
				<h2>Best Matches:</h2>
				{#each bestMatchedIndexes as key}
					<Button
						buttonText={tfData.lexemes[tfData.lang][key]}
						toggled={() => {
							selectLemma(tfData.lexemes.id[key]);
						}}
						textSize="text-2xl "
						buttonColors="btn-lemma"
						style="font-bold greek "
					/> &nbsp;
				{/each}
			{/if}

			{#if otherMatchedIndexes.length > 0}
				{#if bestMatchedIndexes.length > 0}<hr />{/if}
				<h2>
					{#if bestMatchedIndexes.length > 0}Other{/if} Matches:
				</h2>
				{#each otherMatchedIndexes as key}
					<Button
						buttonText={tfData.lexemes[tfData.lang][key]}
						toggled={() => {
							selectLemma(tfData.lexemes.id[key]);
						}}
						textSize="text-2xl "
						buttonColors="btn-lemma"
						style="font-bold greek "
					/> &nbsp;
				{/each}
			{/if}
		</div>
	{:else}
		Type some text above to search for {StringUtils.capitalize(lang)} words.
	{/if}
</div>
<Modal2 bind:showModal title="{StringUtils.capitalize(lang)} Lemma Details">
	{#if queryReady == true && foundLemma.id >= 0 && lexRefsQueries.corpusRefsQueries[foundLemma.id].ready}
		<LemmaInfo {tfData} lemma={foundLemma} corpusRefsQuery={lexRefsQueries.corpusRefsQueries[foundLemma.id]}/>
	{:else}
		Retreiving Lemma information...<span class="loading loading-spinner loading-lg"></span>
	{/if}
</Modal2>

<style>
	h1,
	h2,
	input,
	p,
	select,
	div {
		@apply items-center self-center text-center;
	}

	h1,
	h2 {
		@apply break-after-all break-after-column;
	}
	hr.thick {
		@apply mb-2 border-b-2 border-b-black;
	}
</style>
