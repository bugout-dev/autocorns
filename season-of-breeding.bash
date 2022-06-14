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

SNAPSHOT_BLOCK_NUMBER=29254405

END_MOONSTREAM_TIMESTAMP=1654560000

DATA_DIR_DIR="./breeding-milestone-snapshot"

echo $DATA_DIR_DIR

set -e

ls ./

mkdir -p $$DATA_DIR_DIR

TOTAL_SUPPLY=$(autocorns biologist total-supply --network $BROWNIE_NETWORK --address $CU_ADDRESS --block-number $SNAPSHOT_BLOCK_NUMBER)

echo "Total supply: $TOTAL_SUPPLY"

time autocorns biologist dnas \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    --block-number $SNAPSHOT_BLOCK_NUMBER \
    >$DATA_DIR_DIR/dnas.json

time autocorns biologist metadata \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    --block-number $SNAPSHOT_BLOCK_NUMBER \
    >$DATA_DIR_DIR/metadata.json


time autocorns biologist mythic-body-parts \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --dnas $DATA_DIR_DIR/dnas.json \
    --block-number $SNAPSHOT_BLOCK_NUMBER \
    >$DATA_DIR_DIR/mythic-body-parts.json

time autocorns biologist merge \
    --metadata $DATA_DIR/metadata.json \
    --mythic-body-parts $DATA_DIR/mythic-body-parts.json \
    >$DATA_DIR/merged.json

time autocorns biologist moonstream-events \
    --start 1651363200 \
    -n breeding_hatching_leaderboard_events \
    --interval 5.0 \
    --max-retries 6 \
    -o $DATA_DIR/moonstream.json

time autocorns biologist moonstream-events \
    --start 1651363200 \
    --end $END_MOONSTREAM_TIMESTAMP \
    -n evolution_leaderboard_events \
    --interval 5.0 \
    --max-retries 6 \
    -o $DATA_DIR/evolution.json

time autocorns biologist sob \
    --merged $DATA_DIR/merged.json \
    --moonstream $DATA_DIR/moonstream.json \
    --evolution $DATA_DIR/evolution.json \
    >$DATA_DIR/leaderboard.json