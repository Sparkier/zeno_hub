<script lang="ts">
	import { goto } from '$app/navigation';
	import type { ApiError, ZenoService } from '$lib/zenoapi';
	import Button from '@smui/button';
	import { Content } from '@smui/paper';
	import Textfield from '@smui/textfield';
	import { createEventDispatcher, getContext } from 'svelte';
	import Popup from './Popup.svelte';

	export let showNewReport: boolean;

	const dispatch = createEventDispatcher();
	const zenoClient = getContext('zenoClient') as ZenoService;

	let reportName = '';
	let errorMessage = '';
	let input: Textfield;

	$: invalidName = reportName.match(/[/]/g) !== null || reportName.length === 0;
	$: if (input) {
		input.getElement().focus();
	}

	async function addReport() {
		try {
			const id = await zenoClient.addReport(reportName);
			showNewReport = false;
			goto(`/report/${id}/${encodeURIComponent(reportName)}`);
		} catch (e) {
			errorMessage = (e as ApiError).body.detail;
		}
	}

	function submit(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			dispatch('close');
		}
		if (e.key === 'Enter') {
			if (!invalidName && reportName.length > 0) addReport();
		}
	}
</script>

<svelte:window on:keydown={submit} />
<Popup on:close>
	<Content class="flex items-center">
		<Textfield bind:value={reportName} label="Report Name" bind:this={input} />
		<Button class="ml-4" variant="outlined" on:click={() => dispatch('close')}>Cancel</Button>
		<Button class="ml-2" variant="outlined" disabled={invalidName} on:click={addReport}>
			Create
		</Button>
	</Content>
	<p class="mt-2 text-primary">
		{#if reportName.match(/[/]/g) !== null}
			A report name cannot contain a "/".
		{/if}
		{#if errorMessage}
			{errorMessage}
		{/if}
	</p>
</Popup>
