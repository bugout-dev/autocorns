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
