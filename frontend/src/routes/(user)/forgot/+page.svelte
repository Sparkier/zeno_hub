<script lang="ts">
	import { enhance } from '$app/forms';
	import Button from '@smui/button';
	import Textfield from '@smui/textfield';

	let username = '';
</script>

<svelte:head>
	<title>Reset Password</title>
</svelte:head>

<form
	method="POST"
	class="flex flex-col items-center justify-center rounded-xl bg-background p-12"
	action="?/code"
	use:enhance
>
	<div class="flex flex-col items-center">
		<a href="/">
			<img src="/zeno-logo.png" alt="Zeno logo" width="200px" class="mb-5" />
		</a>
		<Textfield input$name="username" bind:value={username} label="Username" class="mb-3 w-56" />
		<Button type="submit" variant="raised" disabled={username.length === 0}>Send Reset Link</Button>
	</div>
</form>
