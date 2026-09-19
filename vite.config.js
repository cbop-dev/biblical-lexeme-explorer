import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';
import { readFileSync } from 'node:fs';

const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf-8'));

export default defineConfig({
	plugins: [
		sveltekit()
	],
	define: {
		__APP_VERSION__: JSON.stringify(pkg.version),
		__APP_REPO__: JSON.stringify(pkg.repository?.url || pkg.repository || 'https://github.com/cbop-dev/biblical-lexeme-explorer')
	},
	server: {
		fs: {
			allow: ['.']
		}
	},
	test: {
		include: ['tests/**/*.{test,spec}.{js,ts}']
	}
});
