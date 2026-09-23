<script>
	import { bdbProvider, removeHebrewDiacritics } from '$lib/engine/BdbProvider.js';
	import { untrack } from 'svelte';

	/**
	 * @typedef BDBEntryProps
	 * @property {any} lemma - Lexeme object or string
	 * @property {string} [lang='hebrew']
	 * @property {string} [dbAbbrev='bhs']
	 */
	/** @type {BDBEntryProps} */
	let { lemma, lang = 'hebrew', dbAbbrev = 'bhs' } = $props();

	let isOpen = $state(false);
	let loading = $state(false);
	let loadedLemma = $state('');
	let entry = $state(null);
	let hasSearched = $state(false);

	let lemmaText = $derived(
		typeof lemma === 'string' ? lemma : lemma?.lemma || ''
	);
	let plainText = $derived(
		typeof lemma === 'object' ? lemma?.plain || '' : ''
	);

	/**
	 * Asynchronously fetch the BDB entry without blocking the main thread or modal render
	 */
	async function fetchBdb() {
		const target = lemmaText;
		const plain = plainText;

		if (lang !== 'hebrew' && dbAbbrev !== 'bhs' || !target) {
			loading = false;
			entry = null;
			hasSearched = false;
			loadedLemma = '';
			return;
		}

		if (loadedLemma === target && hasSearched) {
			return;
		}

		loading = true;
		try {
			const res = await bdbProvider.getEntry(target, plain);
			entry = res.entry || null;
			hasSearched = true;
			loadedLemma = target;
		} catch (err) {
			console.error('Error loading BDB entry:', err);
			entry = null;
		} finally {
			loading = false;
		}
	}

	function handleToggle(e) {
		isOpen = e.currentTarget.open;
		if (isOpen && loadedLemma !== lemmaText) {
			fetchBdb();
		}
	}

	// If the user already has the drawer open and switches to a different lemma, refresh it
	$effect(() => {
		const target = lemmaText;
		if (isOpen && target && target !== loadedLemma) {
			untrack(() => {
				fetchBdb();
			});
		} else if (target !== loadedLemma) {
			hasSearched = false;
			entry = null;
			loadedLemma = '';
		}
	});

	let formattedDef = $derived(
		entry?.def ? entry.def : ''
	);

</script>

{#if lang === 'hebrew' || dbAbbrev === 'bhs'}
	<div class="bdb-container my-3 text-left">
		<details
			class="collapse collapse-arrow border border-base-300 bg-base-100/60 shadow-sm rounded-box"
			bind:open={isOpen}
			ontoggle={handleToggle}
		>
			<summary class="collapse-title font-medium py-3 px-4 flex items-center justify-between gap-2 cursor-pointer hover:bg-base-200/50">
				<div class="flex items-center gap-2 flex-wrap">
					<span class="badge badge-outline badge-primary font-serif font-bold text-xs uppercase tracking-wide">
						BDB
					</span>
					<span class="font-semibold text-sm">
						Brown-Driver-Briggs Lexicon
					</span>
					{#if loading}
						<span class="loading loading-spinner loading-xs text-primary ml-1"></span>
					{:else if hasSearched && entry}
						<span class="hebrew text-base text-primary font-bold ml-1" dir="rtl">
							{entry.headword}
						</span>
						{#if entry.strongs}
							<span class="badge badge-ghost badge-sm text-[11px] opacity-80">
								{entry.strongs}
							</span>
						{/if}
					{/if}
				</div>
			</summary>

			<div class="collapse-content px-4 pb-4 pt-1">
				{#if !isOpen}
					<!-- Empty when closed -->
				{:else if loading}
					<div class="py-4 text-center text-sm opacity-70 flex items-center justify-center gap-2">
						<span class="loading loading-dots loading-sm text-primary"></span>
						Loading BDB entry...
					</div>
				{:else if entry}
					<div class="bdb-entry-body">
						<div class="bdb-text font-serif leading-relaxed text-sm md:text-[15px] max-h-96 overflow-y-auto pr-2 custom-scrollbar">
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							{@html formattedDef}
						</div>
					</div>
				{:else}
					<div class="py-2 text-xs opacity-80 text-center">
						<p>No direct BDB entry found for <strong class="hebrew font-normal" dir="rtl">{lemmaText}</strong>.</p>
					</div>
				{/if}
			</div>
		</details>
	</div>
{/if}

<style>
	:global(.bdb-text) {
		font-family: "SBL BibLit", "Gentium", "Cardo", Georgia, serif;
		line-height: 1.65;
		color: inherit;
		word-break: break-word;
	}

	:global(.bdb-text strong) {
		color: var(--fallback-p, #1f6f7a);
	}
    
    :global(.bdb-text heb) {
        direction: rtl;
        display: inline-block;
        font-family: "SBL BibLit", "Ezra SIL", serif;
        font-size: 1.1em;
    }

	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: rgba(0, 0, 0, 0.05);
		border-radius: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 4px;
	}
</style>
