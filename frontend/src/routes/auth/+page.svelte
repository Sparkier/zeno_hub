<script>
	import { goto } from '$app/navigation';
	import Button from '@smui/button';
</script>

<div class="m-auto h-full bg-primary pt-20 text-center">
	<div class="m-auto flex w-96 flex-col items-center rounded-md bg-background p-10">
		<img src="/zeno.png" alt="zeno logo" class="w-10" />
		<h1 class="mt-4 text-xl font-semibold text-primary">Unauthorized</h1>
		<h1 class="text-xl text-primary">
			The resource you requested cannot be accessed from your account. Please contact the owner to
			share this resource with you.
		</h1>
		<div class="flex">
			<Button on:click={() => history.back()}>Retry</Button>
			<Button on:click={() => goto('/')}>Home</Button>
		</div>
	</div>
</div>
