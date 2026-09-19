<script>
	import { lsjProvider, removeDiacritics } from '$lib/engine/LsjProvider.js';
	import { untrack } from 'svelte';

	/**
	 * @typedef LSJEntryProps
	 * @property {any} lemma - Lexeme object or string
	 * @property {string} [lang='greek']
	 * @property {string} [dbAbbrev='lxx']
	 */
	/** @type {LSJEntryProps} */
	let { lemma, lang = 'greek', dbAbbrev = 'lxx' } = $props();

	let isOpen = $state(false);
	let loading = $state(false);
	let loadedLemma = $state('');
	let entry = $state(null);
	let isProper = $state(false);
	let hasSearched = $state(false);

	let lemmaText = $derived(
		typeof lemma === 'string' ? lemma : lemma?.lemma || ''
	);
	let plainText = $derived(
		typeof lemma === 'object' ? lemma?.plain || '' : ''
	);

	/**
	 * Asynchronously fetch the LSJ entry without blocking the main thread or modal render
	 */
	async function fetchLsj() {
		const target = lemmaText;
		const plain = plainText;

		if (lang !== 'greek' || !target) {
			loading = false;
			entry = null;
			isProper = false;
			hasSearched = false;
			loadedLemma = '';
			return;
		}

		if (loadedLemma === target && hasSearched) {
			return;
		}

		loading = true;
		try {
			const res = await lsjProvider.getEntry(target, plain);
			entry = res.entry || null;
			isProper = res.isProper || false;
			hasSearched = true;
			loadedLemma = target;
		} catch (err) {
			console.error('Error loading LSJ entry:', err);
			entry = null;
		} finally {
			loading = false;
		}
	}

	function handleToggle(e) {
		isOpen = e.currentTarget.open;
		if (isOpen && loadedLemma !== lemmaText) {
			fetchLsj();
		}
	}

	// If the user already has the drawer open and switches to a different lemma, refresh it
	$effect(() => {
		const target = lemmaText;
		if (isOpen && target && target !== loadedLemma) {
			untrack(() => {
				fetchLsj();
			});
		} else if (target !== loadedLemma) {
			hasSearched = false;
			entry = null;
			loadedLemma = '';
		}
	});

	/**
	 * Formats markdown from LSJ CEX edition into readable HTML
	 * @param {string} raw
	 * @returns {string}
	 */
	function formatLsjMarkdown(raw) {
		if (!raw) return '';

		let html = raw
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;');

		html = html.replace(/\*\*([^*]+?)\*\*/g, '<strong class="lsj-strong font-semibold text-primary">$1</strong>');
		html = html.replace(/\*([^*\n]+?)\*/g, '<em class="lsj-em italic opacity-90">$1</em>');
		html = html.replace(/`([^`\n]+?)`/g, '<span class="lsj-sense-badge font-mono text-xs px-1.5 py-0.5 rounded bg-base-300 text-base-content font-bold mx-0.5">$1</span>');
		html = html.replace(/;\s*(`[A-Z](\.[I|V|X]+)?`|[A-Z]\.[I|V|X]+|[I|V|X]+\.)\s*/g, ';<br/><span class="inline-block mt-2 mb-1"></span>$1 ');

		return html;
	}

	let formattedDef = $derived(
		entry?.def ? formatLsjMarkdown(entry.def) : ''
	);

	let cleanHeadword = $derived(
		entry?.headword ? removeDiacritics(entry.headword) : ''
	);

	let logeionUrl = $derived(
		cleanHeadword ? `https://logeion.uchicago.edu/${encodeURIComponent(entry.headword)}` : ''
	);

	let matchTypeBadge = $derived.by(() => {
		if (!entry?.matchType) return '';
		switch (entry.matchType) {
			case 'deponent_to_active':
				return 'Deponent → Active';
			case 'koine_phonetic':
				return 'Koine Form';
			case 'manual_override':
				return 'Headword Mapping';
			case 'variation':
				return 'Phonetic Variant';
			case 'neuter_adjective':
				return 'Neuter → Headword';
			default:
				return '';
		}
	});
</script>

{#if lang === 'greek'}
	<div class="lsj-container my-3 text-left">
		<details
			class="collapse collapse-arrow border border-base-300 bg-base-100/60 shadow-sm rounded-box"
			bind:open={isOpen}
			ontoggle={handleToggle}
		>
			<summary class="collapse-title font-medium py-3 px-4 flex items-center justify-between gap-2 cursor-pointer hover:bg-base-200/50">
				<div class="flex items-center gap-2 flex-wrap">
					<span class="badge badge-outline badge-primary font-serif font-bold text-xs uppercase tracking-wide">
						LSJ
					</span>
					<span class="font-semibold text-sm">
						Liddell-Scott-Jones Lexicon
					</span>
					{#if loading}
						<span class="loading loading-spinner loading-xs text-primary ml-1"></span>
					{:else if hasSearched && entry}
						<span class="greek text-base text-primary font-bold ml-1">
							{entry.headword}
						</span>
						{#if matchTypeBadge}
							<span class="badge badge-ghost badge-sm text-[11px] opacity-80">
								{matchTypeBadge}
							</span>
						{/if}
					{:else if hasSearched && isProper}
						<span class="badge badge-warning badge-sm text-[11px]">
							Proper Name
						</span>
					{/if}
				</div>
			</summary>

			<div class="collapse-content px-4 pb-4 pt-1">
				{#if !isOpen}
					<!-- Empty when closed: 0 DOM nodes, instant close -->
				{:else if loading}
					<div class="py-4 text-center text-sm opacity-70 flex items-center justify-center gap-2">
						<span class="loading loading-dots loading-sm text-primary"></span>
						Loading LSJ entry...
					</div>
				{:else if entry}
					<div class="lsj-entry-body">
						<!-- Metadata bar -->
						<div class="flex items-center justify-between pb-2 mb-3 border-b border-base-200 text-xs opacity-75">
							<div class="flex items-center gap-2">
								<span class="font-semibold">Entry: {entry.lsjIndex}</span>
								{#if entry.headword !== lemmaText}
									<span>(LXX Lemma: <strong class="greek">{lemmaText}</strong>)</span>
								{/if}
							</div>
							{#if logeionUrl}
								<div class="flex items-center gap-3">
									<a
										href={logeionUrl}
										target="_blank"
										rel="noopener noreferrer"
										class="link link-hover link-primary inline-flex items-center gap-1 font-medium"
										title="Lookup on University of Chicago Logeion"
									>
										Logeion ↗
									</a>
								</div>
							{/if}
						</div>

						<!-- Lexicon definition (only rendered in DOM when accordion is open) -->
						<div class="lsj-text font-serif leading-relaxed text-sm md:text-[15px] max-h-96 overflow-y-auto pr-2 custom-scrollbar">
							<!-- eslint-disable-next-line svelte/no-at-html-tags -->
							{@html formattedDef}
						</div>
					</div>
				{:else if isProper}
					<div class="alert alert-info bg-info/10 border-info/30 text-xs py-2 px-3 my-1">
						<div>
							<strong class="font-semibold block mb-0.5">Proper Noun / Semitic Transliteration</strong>
							<p class="opacity-90">
								<strong>{lemmaText}</strong> is a proper personal or geographic name (often transliterated from Hebrew/Aramaic). Classical Greek lexica (LSJ) typically omit Semitic proper names.
							</p>
						</div>
					</div>
				{:else}
					<div class="py-2 text-xs opacity-80 text-center">
						<p>No direct classical LSJ entry found for <strong class="greek font-normal">{lemmaText}</strong>.</p>
						{#if lemmaText}
							<div class="mt-2 flex justify-center gap-3">
								<a
									href="https://logeion.uchicago.edu/{encodeURIComponent(lemmaText)}"
									target="_blank"
									rel="noopener noreferrer"
									class="btn btn-xs btn-outline btn-primary"
								>
									Search Logeion ↗
								</a>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</details>
	</div>
{/if}

<style>
	:global(.lsj-text) {
		font-family: "SBL BibLit", "Gentium", "Cardo", Georgia, serif;
		line-height: 1.65;
		color: inherit;
		word-break: break-word;
	}

	:global(.lsj-text strong) {
		color: var(--fallback-p, #1f6f7a);
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
