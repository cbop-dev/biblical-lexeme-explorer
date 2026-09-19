<script>
	import LexInBooks from '$lib/components/LexInBooks.svelte';
	import LexSearch from '$lib/components/LexSearch.svelte';
	import WordCloud2 from '$lib/components/WordCloud2.svelte';
	import { LxxVocabDataset } from '$lib/lxx/lxxDataset.js';
	import { SblGntVocabDataset } from '$lib/sblgnt/sblgntDataset.js';
	import { BhsVocabDataset } from '$lib/bhs/bhsDataset.js';
	import { onMount } from 'svelte';

	/** @type {{ data: import('./$types').PageData }} */
	let { data } = $props();

	const db = data.db;

	const panes = ['book', 'lex', 'wc'];
	let selectedPane = $state(0);

	let tfData = $derived.by(() => {
		if (db === 'sblgnt') return new SblGntVocabDataset();
		if (db === 'bhs') return new BhsVocabDataset();
		return new LxxVocabDataset();
	});

	let options = $derived(data?.options);
	$effect(() => {
		if (options?.view?.panel && panes.includes(options.view.panel)) {
			selectedPane = panes.indexOf(options.view.panel);
		}
	});
	onMount(() => {
		if (typeof window !== 'undefined') {
			window.history.pushState({}, document.title, window.location.pathname);
		}
	});
</script>

<svelte:head>
	<title>{tfData.name || tfData.abbrev} Lexemes</title>
</svelte:head>
<div role="tablist" class="tabs tabs-lifted">
	<a
		role="tab"
		class="tab {selectedPane == 0 ? 'tab-active' : ''} "
		tabindex="0"
		onclick={() => {
			selectedPane = 0;
		}}
	>
		<span class="sm:hidden">Book</span>
		<span class="hidden sm:inline">Book Search</span>
	</a>
	<a
		role="tab"
		class="tab {selectedPane == 1 ? 'tab-active' : ''} "
		tabindex="1"
		onclick={() => {
			selectedPane = 1;
		}}
	>
		<span class="sm:hidden">Lexeme</span>
		<span class="hidden sm:inline">Lexeme Search</span>
	</a>
	<a
		role="tab"
		class="tab {selectedPane == 2 ? 'tab-active' : ''} "
		tabindex="2"
		onclick={() => {
			selectedPane = 2;
		}}
	>
		<span class="sm:hidden">Cloud</span>
		<span class="hidden sm:inline">Word Cloud</span>
	</a>
</div>
<div class={panes[selectedPane] == 'book' ? 'block' : 'hidden'}>
	<LexInBooks {tfData} hidden={panes[selectedPane] != 'book'} />
</div>

<div class={panes[selectedPane] == 'lex' ? 'block' : 'hidden'}>
	<LexSearch {tfData} />
</div>
<div class={panes[selectedPane] == 'wc' ? 'block' : 'hidden'}>
	<WordCloud2 {tfData} {options} />
</div>

<style>
	.tabs .tab-active {
		@apply bg-accent !important;
		font-weight: bold;
	}

	.tab {
		height: auto;
	}
</style>
