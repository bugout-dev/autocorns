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

if [ -z "$CU_ADDRESS" ]
then
    echo "Set CU_ADDRESS environment variable"
fi

if [ -z "$DATA_DIR" ]
then
    echo "Set DATA_DIR environment variable"
fi

LEADERBOARD_COMMAND=""
if [ -n "$LEADERBOARD_ID" ]
then
    LEADERBOARD_COMMAND="--leaderboard-id $LEADERBOARD_ID"
fi

set -e

TOTAL_SUPPLY=$(autocorns biologist total-supply --network $BROWNIE_NETWORK --address $CU_ADDRESS)

echo "Total supply: $TOTAL_SUPPLY"

time autocorns biologist dnas \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    --checkpoint "$DATA_DIR/dnas.json" \
    --leak-rate 0.05

time autocorns biologist metadata \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --start 1 \
    --end $TOTAL_SUPPLY \
    --checkpoint "$DATA_DIR/metadata.json" \
    --leak-rate 0.05

time autocorns biologist mythic-body-parts \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --dnas "$DATA_DIR/dnas.json" \
    --checkpoint "$DATA_DIR/mythic-body-parts.json" \
    --leak-rate 0.05

time autocorns biologist stats \
    --network $BROWNIE_NETWORK \
    --address $CU_ADDRESS \
    --dnas "$DATA_DIR/dnas.json" \
    --checkpoint "$DATA_DIR/stats.json" \
    --leak-rate 0.05

time autocorns biologist moonstream-events \
    -n breeding_hatching_leaderboard_events \
    --start 1680307200 \
    --end 1688169600 \
    --interval 15 \
    --max-retries 20 \
    -o "$DATA_DIR/breeding_hatching_leaderboard_events.json"

time autocorns biologist moonstream-events \
    -n evolution_leaderboard_events \
    --start 1680307200 \
    --end 1688169600 \
    --interval 15 \
    --max-retries 20 \
    -o "$DATA_DIR/evolution_leaderboard_events.json"

time autocorns biologist spring-event-2023  \
    --mythic-body-parts "$DATA_DIR/mythic-body-parts.json" \
    --stats "$DATA_DIR/stats.json" \
    --breeding-hatching-events "$DATA_DIR/breeding_hatching_leaderboard_events.json" \
    --evolution-events "$DATA_DIR/evolution_leaderboard_events.json" \
    --metadata "$DATA_DIR/metadata.json" \
    $LEADERBOARD_COMMAND \
    >"$DATA_DIR/leaderboard.json"

echo "Done!"
