# autocorns

A team of Crypto Unicorns bots

## Disclaimer

I invoke `autocorns` to help my unicorns. You may choose to invoke `autocorns` to help *your* unicorns, too.
If you do choose to call upon `autocorns`, know that you are doing so at your own risk. I am not liable or
responsible for any damage or losses you may incur.

`autocorns` expect your account credentials to be stored as an Ethereum keystore file and for you to have access to the corresponding password.
If you do not know what this means, you probably shouldn't call upon the `autocorns`.


## Installation

`autocorns` is written in Python and uses:
1. [`moonworm`](https://github.com/bugout-dev/moonworm)
2. [`brownie`](https://github.com/eth-brownie/brownie)

You can install `autocorns` by running:

```
pip install autocorns
```

## Bots

### The Dark Forest Warden

The Dark Forest Warden escorts Crypto Unicorns safely through the Dark Forest.

To call on the Warden to help *your* unicorns (`42`, `69`, and `420`, say), use this spell:

```bash
autocorns warden \
    --network matic \
    --sender <path to keystore file> \
    --max-fee-per-gas "40 gwei" \
    --max-priority-fee-per-gas "30 gwei" \
    --confirmations 5 \
    --corns 42 69 420
```

You will be prompted to unlock your keystore with the password before the transactions are submitted.

### The Biologist

The Biologist can be used to inspect information about unicorn genetics and breeding.

To get this information, the Biologist crawls genetic data directly from the Crypto Unicorns smart
contract. It also queries the Moonstream database for some information.

Commands that use Moonstream data will require setting up a [Moonstream](https://moonstream.to) account
and loading the appropriate query into your account. If you need help with this, ask the Moonstream
team [on Discord](https://discord.gg/TS6fcHqqdZ).

#### Checkpointing

All Biologist subcommands that crawl data from the blockchain support checkpoints. This means that
you can start a crawl and then update it over time in case you get rate limited by your web3 provider
or you want to add data about new unicorns.

The `--checkpoint` argument allows you to load an existing checkpoint.

Any subcommand that supports `--checkpoint` also allows you to set the `--update-checkpoint` flag which
will update the checkpoint file in place with any new crawled data.

#### Unicorn DNAs

To build a [JSON Lines](https://jsonlines.org/) file containing the DNAs of each unicorn:

```bash
autocorns biologist dnas \
    --network matic \
    --address 0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f \
    --start <starting token ID> \
    --end <ending token ID> \
    --num-workers <number of threads to crawl with> \
    --timeout <number of seconds to wait before timing out> \
    >dnas.json
```

To resume crawling from a previously stored DNAs file:

```bash
autocorns biologist dnas \
    --network matic \
    --address 0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f \
    --start <starting token ID> \
    --end <ending token ID> \
    --num-workers <number of threads to crawl with> \
    --timeout <number of seconds to wait before timing out> \
    --checkpoint dnas.json \
    --update-checkpoint
```

#### Unicorn metadata (lifecycle stages, classes)

To retrieve the classes and lifecycle stages of unicorns, use:

```bash
autocorns biologist metadata \
    --network matic \
    --address 0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f \
    --start <starting token ID> \
    --end <ending token ID> \
    --num-workers <number of threads to crawl with> \
    --timeout <number of seconds to wait before timing out> \
    >metadata.json

```

To resume crawling from a previously stored metadata file:

```bash
autocorns biologist metadata \
    --network matic \
    --address 0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f \
    --start <starting token ID> \
    --end <ending token ID> \
    --num-workers <number of threads to crawl with> \
    --timeout <number of seconds to wait before timing out> \
    --checkpoint metadata.json \
    --update-checkpoint

```

#### Number of mythic body parts per unicorn

To calculate the number of mythic body parts per unicorn, we need the DNAs of those unicorns as an
input. Therefore, this command depends on the output of the `autocorns biologists dnas` command.

NOTE: Since unicorn eggs do not officially have body parts, and since solidity does not have any other
way of handling null values, eggs show up as having 6 mythic body parts. The merge command (described
below) takes care of this. But if you are just using the file produced by this command, then this is
something that you will also have to handle.

Once you have written the output of `autocorns biologists dnas` to a file, say `dnas.json`, you can
invoke this command as:

```bash
autocorns biologist mythic-body-parts \
    --network matic \
    --address 0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f \
    --dnas dnas.json \
    --num-workers <number of threads to crawl with> \
    --timeout <number of seconds to wait before timing out> \
    >mythic-body-parts.json

```

To resume crawling from a previously stored checkpoint:

```bash
autocorns biologist mythic-body-parts \
    --network matic \
    --address 0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f \
    --dnas dnas.json \
    --num-workers <number of threads to crawl with> \
    --timeout <number of seconds to wait before timing out> \
    --checkpoint mythic-body-parts.json \
    --update-checkpoint

```

#### Merging into a single file

You can use the `autocorns biologist merge` command to merge metadata and mythic body parts information
into a single file.

The merge command correctly sets the number of mythic body parts for unicorn eggs to 0 (from the default
of `6` that comes from the smart contract).

To run this command:

```bash
autocorns biologist merge \
    --metadata metadata.json \
    --mythic-body-parts mythic-body-parts.json \
    >merged.json

```
