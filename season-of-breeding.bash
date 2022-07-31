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

if [ -z "$DATA_DIR" ]
then
    echo "Set DATA_DIR environment variable"
    exit 1
fi

BLOCK_NUMBER_ARG=""
if [ ! -z "$BLOCK_NUMBER" ]
then
    BLOCK_NUMBER_ARG="--block-number $BLOCK_NUMBER"
fi

END_TIMESTAMP_ARG=""
if [ ! -z "$END_TIMESTAMP" ]
then
    END_TIMESTAMP_ARG="--end $END_TIMESTAMP"
fi

CU_ADDRESS=0xdC0479CC5BbA033B3e7De9F178607150B3AbCe1f

set -e

TOTAL_SUPPLY=$(autocorns biologist total-supply --network $BROWNIE_NETWORK $BLOCK_NUMBER_ARG --address $CU_ADDRESS)

echo "Total supply: $TOTAL_SUPPLY"

time autocorns biologist dnas \
    --network $BROWNIE_NETWORK \
    $BLOCK_NUMBER_ARG \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    >$DATA_DIR/dnas.json

time autocorns biologist metadata \
    --network $BROWNIE_NETWORK \
    $BLOCK_NUMBER_ARG \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    >$DATA_DIR/metadata.json


time autocorns biologist mythic-body-parts \
    --network $BROWNIE_NETWORK \
    $BLOCK_NUMBER_ARG \
    --address $CU_ADDRESS \
    --dnas $DATA_DIR/dnas.json \
    >$DATA_DIR/mythic-body-parts.json

time autocorns biologist merge \
    --metadata $DATA_DIR/metadata.json \
    --mythic-body-parts $DATA_DIR/mythic-body-parts.json \
    >$DATA_DIR/merged.json

time autocorns biologist moonstream-events \
    --start 1651363200 \
    $END_TIMESTAMP_ARG \
    -n breeding_hatching_leaderboard_events \
    --interval 5.0 \
    --max-retries 6 \
    -o $DATA_DIR/moonstream.json

time autocorns biologist moonstream-events \
    --start 1651363200 \
    $END_TIMESTAMP_ARG \
    -n evolution_leaderboard_events \
    --interval 5.0 \
    --max-retries 6 \
    -o $DATA_DIR/evolution.json

time autocorns biologist sob \
    --merged $DATA_DIR/merged.json \
    --moonstream $DATA_DIR/moonstream.json \
    --evolution $DATA_DIR/evolution.json \
    >$DATA_DIR/leaderboard.json
