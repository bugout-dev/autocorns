#!/usr/bin/env bash

if [ -z "$BROWNIE_NETWORK" ]
then
    echo "Set BROWNIE_NETWORK environment variable"
    exit 1
fi

if [ -z "$MOONSTREAM_ACCESS_TOKEN" ]
then
    echo "Set MOONSTREAM_ACCESS_TOKEN environment variable"
    exit 1
fi


CU_ADDRESS=0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f

set -e

TOTAL_SUPPLY=$(autocorns biologist total-supply --network $BROWNIE_NETWORK --address $CU_ADDRESS)

echo "Total supply: $TOTAL_SUPPLY"

time autocorns biologist dnas \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    --num-workers 5 \
    --timeout 5.0 \
    --checkpoint data/dnas.json \
    -u

time autocorns biologist metadata \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    --num-workers 5 \
    --timeout 5.0 \
    --checkpoint data/metadata.json \
    -u


time autocorns biologist mythic-body-parts \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --dnas data/dnas.json \
    --num-workers 5 \
    --timeout 5.0 \
    --checkpoint data/mythic-body-parts.json \
    --update-checkpoint

time autocorns biologist merge \
    --metadata data/metadata.json \
    --mythic-body-parts data/mythic-body-parts.json \
    >data/merged.json

time autocorns biologist moonstream-events \
    --start 1651363200 \
    -n breeding_hatching_leaderboard_events \
    --interval 5.0 \
    --max-retries 6 \
    -o data/moonstream.json

time autocorns biologist sob \
    --merged data/merged.json \
    --moonstream data/moonstream.json \
    >data/leaderboard.json
